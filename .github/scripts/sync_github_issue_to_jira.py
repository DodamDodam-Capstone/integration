#!/usr/bin/env python3
"""GitHub Issue를 Jira 업무로 생성하고 양쪽 링크를 기록한다."""

from __future__ import annotations

import json
import html
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

JIRA_KEY_RE = re.compile(r"\bSCRUM-\d+\b", re.IGNORECASE)
PARENT_SECTION_RE = re.compile(
    r"###\s*상위 Jira 키[^\n]*\n+(.*?)(?=\n###|\Z)", re.IGNORECASE | re.DOTALL
)
ISSUE_TYPE_IDS = {"에픽": "10001", "작업": "10003", "버그": "10006"}
LINK_MARKER = "<!-- jira-auto-link -->"
RETRYABLE_HTTP = {429, 500, 502, 503, 504}


class HttpRequestError(RuntimeError):
    def __init__(self, method: str, url: str, code: int, detail: str):
        super().__init__(f"{method} {url} 실패 ({code}): {detail}")
        self.code = code


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"필수 환경 변수 {name}이(가) 없습니다.")
    return value


def request_json(method: str, url: str, *, headers: dict[str, str], payload=None):
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode()
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
            if not raw:
                return {}
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                # Slack Incoming Webhook은 성공 시 JSON 대신 plain text "ok"를 반환한다.
                return {"raw": raw.decode(errors="replace")}
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")[:1000]
        raise HttpRequestError(method, url, error.code, detail) from error


def github_headers(token: str) -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def jira_headers(token: str) -> dict[str, str]:
    return {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def extract_parent(body: str) -> str | None:
    section = PARENT_SECTION_RE.search(body or "")
    if not section:
        return None
    key = JIRA_KEY_RE.search(section.group(1))
    return key.group(0).upper() if key else None


def issue_type(labels: set[str]) -> str:
    selected = labels & {"epic", "bug", "task"}
    if len(selected) > 1:
        raise ValueError(
            "epic, bug, task 유형 레이블은 정확히 하나만 지정해야 합니다: "
            + ", ".join(sorted(selected))
        )
    return {"epic": "에픽", "bug": "버그", "task": "작업"}.get(
        next(iter(selected), "task"), "작업"
    )


def summary_for(title: str, prefix: str) -> str:
    clean = JIRA_KEY_RE.sub("", title).strip()
    clean = re.sub(r"^\[(?:FE|BE|AI|INT|EPIC)\]\s*", "", clean, flags=re.I)
    if not clean:
        raise ValueError("Jira summary로 사용할 GitHub Issue 제목이 비어 있습니다.")
    return f"[{prefix}] {clean}"[:255]


def slack_text(value: object, limit: int = 500) -> str:
    normalized = " ".join(str(value or "—").split()).replace("`", "ʼ")
    return html.escape(normalized, quote=False)[:limit]


def adf_description(issue: dict, repository: str) -> dict:
    body = (issue.get("body") or "내용 없음").strip()[:20000]
    source = issue["html_url"]
    author = issue.get("user", {}).get("login", "알 수 없음")
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": "GitHub Issue에서 자동 생성되었습니다."}]},
            {"type": "paragraph", "content": [{"type": "text", "text": f"저장소: {repository}"}]},
            {"type": "paragraph", "content": [{"type": "text", "text": f"작성자: @{author}"}]},
            {"type": "paragraph", "content": [{"type": "text", "text": f"원본: {source}", "marks": [{"type": "link", "attrs": {"href": source}}]}]},
            {"type": "rule"},
            {"type": "paragraph", "content": [{"type": "text", "text": body}]},
        ],
    }


def slack_notify(webhook: str, *, ok: bool, repository: str, issue: dict, jira_key="", jira_url="", detail=""):
    if not webhook:
        return
    icon = ":white_check_mark:" if ok else ":x:"
    title = "Jira 업무 자동 생성 완료" if ok else "Jira 업무 자동 생성 실패"
    fields = [
        {"type": "mrkdwn", "text": f"*Repository*\n`{slack_text(repository)}`"},
        {"type": "mrkdwn", "text": f"*Event*\nGitHub Issue #{issue['number']} opened"},
        {"type": "mrkdwn", "text": f"*Source*\n<{issue['html_url']}|GitHub Issue #{issue['number']}>"},
        {"type": "mrkdwn", "text": f"*Target*\n<{jira_url}|{jira_key}>" if jira_key else "*Target*\nJira 생성 실패"},
        {"type": "mrkdwn", "text": f"*Actor*\n`{slack_text(issue.get('user', {}).get('login', 'unknown'))}`"},
        {"type": "mrkdwn", "text": f"*Result*\n{'연결 완료' if ok else slack_text(detail, 200)}"},
    ]
    payload = {
        "text": f"{icon} [{repository}] {title}: GitHub Issue #{issue['number']} → {jira_key or '실패'}",
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": f"{icon} {title}"}},
            {"type": "section", "fields": fields},
            {"type": "context", "elements": [{"type": "mrkdwn", "text": f"*Title:* {slack_text(issue['title'], 500)}"}]},
        ],
    }
    post_slack(webhook, payload)


def post_slack(webhook: str, payload: dict, *, attempts: int = 3) -> None:
    parsed = urllib.parse.urlparse(webhook)
    if parsed.scheme != "https" or parsed.hostname != "hooks.slack.com":
        raise RuntimeError("SLACK_WEBHOOK_URL이 허용된 Slack HTTPS 주소가 아닙니다.")
    data = json.dumps(payload, ensure_ascii=False).encode()
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(
            webhook,
            data=data,
            method="POST",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                body = response.read().decode(errors="replace").strip()
                if response.status == 200 and body == "ok":
                    return
                raise RuntimeError(
                    f"Slack webhook이 예상치 못한 응답을 반환했습니다(HTTP {response.status})."
                )
        except urllib.error.HTTPError as error:
            if error.code not in RETRYABLE_HTTP or attempt == attempts:
                raise RuntimeError(f"Slack webhook이 HTTP {error.code}를 반환했습니다.") from error
        except urllib.error.URLError as error:
            if attempt == attempts:
                raise RuntimeError("Slack webhook 네트워크 요청에 실패했습니다.") from error
        time.sleep(attempt)


def all_github_comments(api: str, headers: dict[str, str]) -> list[dict]:
    comments: list[dict] = []
    for page in range(1, 101):
        batch = request_json(
            "GET", f"{api}/comments?per_page=100&page={page}", headers=headers
        )
        comments.extend(batch)
        if len(batch) < 100:
            return comments
    raise RuntimeError("GitHub Issue 댓글이 10,000개를 초과하여 자동 링크를 확인할 수 없습니다.")


def find_existing_jira_key(
    jira_api: str,
    headers: dict[str, str],
    project: str,
    unique_label: str,
    title: str,
) -> str | None:
    jql = f'project = "{project}" AND labels = "{unique_label}" ORDER BY created DESC'
    query = urllib.parse.urlencode({"jql": jql, "fields": "key", "maxResults": 2})
    search = request_json("GET", f"{jira_api}/rest/api/3/search/jql?{query}", headers=headers)
    existing = search.get("issues", [])
    if len(existing) > 1:
        raise RuntimeError(f"Jira 중복 감지: {unique_label} 레이블 업무가 둘 이상입니다.")
    if existing:
        return existing[0]["key"]

    title_key = JIRA_KEY_RE.search(title)
    if not title_key:
        return None
    candidate = title_key.group(0).upper()
    try:
        jira_issue = request_json(
            "GET",
            f"{jira_api}/rest/api/3/issue/{candidate}?fields=labels,project",
            headers=headers,
        )
    except HttpRequestError as error:
        if error.code == 404:
            return None
        raise
    fields = jira_issue.get("fields") or {}
    same_project = (fields.get("project") or {}).get("key") == project
    owned = unique_label in (fields.get("labels") or [])
    return candidate if same_project and owned else None


def main() -> int:
    github_token = required_env("GITHUB_TOKEN")
    jira_token = required_env("JIRA_API_TOKEN")
    repository = required_env("GITHUB_REPOSITORY")
    number = required_env("ISSUE_NUMBER")
    if not re.fullmatch(r"[1-9]\d*", number):
        raise ValueError("ISSUE_NUMBER는 1 이상의 정수여야 합니다.")
    jira_api = required_env("JIRA_API_URL").rstrip("/")
    jira_site = required_env("JIRA_SITE_URL").rstrip("/")
    project = required_env("JIRA_PROJECT_KEY")
    prefix = required_env("REPOSITORY_PREFIX")
    slack_webhook = required_env("SLACK_WEBHOOK_URL")

    gh_api = f"https://api.github.com/repos/{repository}"
    issue = request_json("GET", f"{gh_api}/issues/{number}", headers=github_headers(github_token))
    if "pull_request" in issue:
        print("Pull Request 이벤트이므로 건너뜁니다.")
        return 0

    labels = {item["name"].lower() for item in issue.get("labels", [])}
    if "jira-skip" in labels:
        print("jira-skip 레이블이 있어 건너뜁니다.")
        return 0
    unique_label = f"github-{repository.split('/')[-1]}-{number}"
    headers = jira_headers(jira_token)
    kind = issue_type(labels)
    target_prefix = "EPIC" if kind == "에픽" else prefix
    jira_key = find_existing_jira_key(
        jira_api, headers, project, unique_label, issue["title"]
    )
    if not jira_key:
        fields = {
            "project": {"key": project},
            "summary": summary_for(issue["title"], target_prefix),
            "issuetype": {"id": ISSUE_TYPE_IDS[kind]},
            "description": adf_description(issue, repository),
            "labels": ["github-sync", unique_label],
        }
        parent = extract_parent(issue.get("body") or "")
        if parent and kind != "에픽":
            fields["parent"] = {"key": parent}
        created = request_json(
            "POST", f"{jira_api}/rest/api/3/issue", headers=headers, payload={"fields": fields}
        )
        jira_key = created["key"]

    jira_url = f"{jira_site}/browse/{jira_key}"
    new_title = f"{jira_key} {summary_for(issue['title'], target_prefix)}"
    if issue["title"] != new_title:
        request_json("PATCH", f"{gh_api}/issues/{number}", headers=github_headers(github_token), payload={"title": new_title})

    comments = all_github_comments(
        f"{gh_api}/issues/{number}", github_headers(github_token)
    )
    if not any(LINK_MARKER in (comment.get("body") or "") for comment in comments):
        request_json(
            "POST",
            f"{gh_api}/issues/{number}/comments",
            headers=github_headers(github_token),
            payload={"body": f"{LINK_MARKER}\nJira 업무가 자동 연결되었습니다: [{jira_key}]({jira_url})\n\n이 키를 branch, commit, PR 제목에 사용하세요."},
        )
    request_json("POST", f"{gh_api}/issues/{number}/labels", headers=github_headers(github_token), payload={"labels": ["jira-linked"]})
    if "jira-notified" not in labels:
        slack_notify(slack_webhook, ok=True, repository=repository, issue=issue, jira_key=jira_key, jira_url=jira_url)
        request_json("POST", f"{gh_api}/issues/{number}/labels", headers=github_headers(github_token), payload={"labels": ["jira-notified"]})
    print(f"{repository}#{number} → {jira_key} 연결 완료")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        try:
            repo = os.environ.get("GITHUB_REPOSITORY", "unknown")
            issue_no = os.environ.get("ISSUE_NUMBER", "0")
            slack_notify(
                os.environ.get("SLACK_WEBHOOK_URL", ""),
                ok=False,
                repository=repo,
                issue={"number": issue_no, "html_url": f"https://github.com/{repo}/issues/{issue_no}", "title": "자동 동기화", "user": {"login": os.environ.get("GITHUB_ACTOR", "unknown")}},
                detail=str(error),
            )
        except Exception as notify_error:
            print(f"Slack 실패 알림 전송도 실패했습니다: {notify_error}", file=sys.stderr)
        print(str(error), file=sys.stderr)
        raise
