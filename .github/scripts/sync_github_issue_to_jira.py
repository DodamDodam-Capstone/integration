#!/usr/bin/env python3
"""GitHub Issue를 Jira 업무로 생성하고 양쪽 링크를 기록한다."""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

JIRA_KEY_RE = re.compile(r"\bSCRUM-\d+\b", re.IGNORECASE)
PARENT_SECTION_RE = re.compile(
    r"###\s*상위 Jira 키[^\n]*\n+(.*?)(?=\n###|\Z)", re.IGNORECASE | re.DOTALL
)
ISSUE_TYPE_IDS = {"에픽": "10001", "작업": "10003", "버그": "10006"}
LINK_MARKER = "<!-- jira-auto-link -->"


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
        raise RuntimeError(f"{method} {url} 실패 ({error.code}): {detail}") from error


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
    if "epic" in labels:
        return "에픽"
    if "bug" in labels:
        return "버그"
    return "작업"


def summary_for(title: str, prefix: str) -> str:
    clean = JIRA_KEY_RE.sub("", title).strip()
    clean = re.sub(r"^\[(?:FE|BE|AI|INT|EPIC)\]\s*", "", clean, flags=re.I)
    return f"[{prefix}] {clean}"[:255]


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
        {"type": "mrkdwn", "text": f"*Repository*\n`{repository}`"},
        {"type": "mrkdwn", "text": f"*Event*\nGitHub Issue #{issue['number']} opened"},
        {"type": "mrkdwn", "text": f"*Source*\n<{issue['html_url']}|GitHub Issue #{issue['number']}>"},
        {"type": "mrkdwn", "text": f"*Target*\n<{jira_url}|{jira_key}>" if jira_key else "*Target*\nJira 생성 실패"},
        {"type": "mrkdwn", "text": f"*Actor*\n`{issue.get('user', {}).get('login', 'unknown')}`"},
        {"type": "mrkdwn", "text": f"*Result*\n{'연결 완료' if ok else detail[:200]}"},
    ]
    payload = {
        "text": f"{icon} [{repository}] {title}: GitHub Issue #{issue['number']} → {jira_key or '실패'}",
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": f"{icon} {title}"}},
            {"type": "section", "fields": fields},
            {"type": "context", "elements": [{"type": "mrkdwn", "text": f"*Title:* {issue['title']}"}]},
        ],
    }
    request_json("POST", webhook, headers={"Content-Type": "application/json"}, payload=payload)


def main() -> int:
    github_token = required_env("GITHUB_TOKEN")
    jira_token = required_env("JIRA_API_TOKEN")
    repository = required_env("GITHUB_REPOSITORY")
    number = required_env("ISSUE_NUMBER")
    jira_api = required_env("JIRA_API_URL").rstrip("/")
    jira_site = required_env("JIRA_SITE_URL").rstrip("/")
    project = required_env("JIRA_PROJECT_KEY")
    prefix = required_env("REPOSITORY_PREFIX")
    slack_webhook = os.environ.get("SLACK_WEBHOOK_URL", "").strip()

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
    title_key = JIRA_KEY_RE.search(issue["title"])
    if title_key:
        jira_key = title_key.group(0).upper()
    else:
        jql = f'project = "{project}" AND labels = "{unique_label}" ORDER BY created DESC'
        query = urllib.parse.urlencode({"jql": jql, "fields": "key", "maxResults": 1})
        search = request_json("GET", f"{jira_api}/rest/api/3/search/jql?{query}", headers=headers)
        existing = search.get("issues", [])
        if existing:
            jira_key = existing[0]["key"]
        else:
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
            created = request_json("POST", f"{jira_api}/rest/api/3/issue", headers=headers, payload={"fields": fields})
            jira_key = created["key"]

    jira_url = f"{jira_site}/browse/{jira_key}"
    new_title = f"{jira_key} {summary_for(issue['title'], target_prefix)}"
    if issue["title"] != new_title:
        request_json("PATCH", f"{gh_api}/issues/{number}", headers=github_headers(github_token), payload={"title": new_title})

    comments = request_json(
        "GET", f"{gh_api}/issues/{number}/comments?per_page=100", headers=github_headers(github_token)
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
