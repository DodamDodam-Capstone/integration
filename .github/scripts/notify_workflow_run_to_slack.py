#!/usr/bin/env python3
"""완료된 GitHub Actions 실행을 저장소 전용 Slack 채널에 알린다."""

from __future__ import annotations

from datetime import datetime
import html
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


GITHUB_API_VERSION = "2022-11-28"
RETRYABLE_HTTP = {429, 500, 502, 503, 504}


def safe_text(value: object, limit: int = 500) -> str:
    """Slack mrkdwn에서 링크/멘션으로 해석될 수 있는 문자를 무력화한다."""
    normalized = " ".join(str(value or "—").split())
    normalized = normalized.replace("`", "ʼ")
    return html.escape(normalized, quote=False)[:limit]


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def duration_text(run: dict) -> str:
    started = parse_time(run.get("run_started_at") or run.get("created_at"))
    finished = parse_time(run.get("updated_at"))
    if not started or not finished:
        return "알 수 없음"
    total = max(0, int((finished - started).total_seconds()))
    minutes, seconds = divmod(total, 60)
    return f"{minutes}분 {seconds}초" if minutes else f"{seconds}초"


def github_json(url: str, token: str, *, attempts: int = 3):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code not in RETRYABLE_HTTP or attempt == attempts:
                raise RuntimeError(f"GitHub API가 HTTP {error.code}를 반환했습니다.") from error
        except urllib.error.URLError as error:
            if attempt == attempts:
                raise RuntimeError("GitHub API 네트워크 요청에 실패했습니다.") from error
        time.sleep(attempt)
    raise AssertionError("도달할 수 없는 재시도 상태")


def associated_pull_requests(run: dict, token: str) -> list[dict]:
    existing = run.get("pull_requests") or []
    if existing:
        return existing

    trigger = run.get("event") or "unknown"
    sha = run.get("head_sha") or ""
    repository = (run.get("repository") or {}).get("full_name") or ""
    if trigger not in {"pull_request", "pull_request_target", "push"} or not sha or not repository:
        return []

    try:
        return github_json(
            f"https://api.github.com/repos/{repository}/commits/{sha}/pulls", token
        )
    except RuntimeError as error:
        # Slack 알림 자체는 보내되, 복구할 수 없었던 PR 메타데이터만 생략한다.
        print(f"경고: PR 메타데이터 조회 실패: {error}", file=sys.stderr)
        return []


def select_pull_request(run: dict, pull_requests: list[dict]) -> dict | None:
    if not pull_requests:
        return None
    trigger = run.get("event") or "unknown"
    branch = run.get("head_branch") or ""
    sha = run.get("head_sha") or ""

    if trigger == "pull_request":
        for pull_request in pull_requests:
            if (pull_request.get("head") or {}).get("ref") == branch:
                return pull_request
        return None
    if trigger == "push":
        for pull_request in pull_requests:
            if (
                pull_request.get("merge_commit_sha") == sha
                and (pull_request.get("base") or {}).get("ref") == branch
            ):
                return pull_request
        return None
    if trigger == "pull_request_target":
        for pull_request in pull_requests:
            if (pull_request.get("base") or {}).get("ref") == branch:
                return pull_request
        return None
    return None


def branch_flow(run: dict, pull_request: dict | None) -> tuple[str, str]:
    head_branch = run.get("head_branch") or "—"
    trigger = run.get("event") or "unknown"
    if pull_request:
        source = (pull_request.get("head") or {}).get("ref") or head_branch
        target = (pull_request.get("base") or {}).get("ref") or "—"
        return source, target
    if trigger == "push":
        return "— (push 이벤트)", head_branch
    if trigger == "workflow_dispatch":
        return head_branch, f"{head_branch} (수동 실행)"
    return head_branch, "—"


def build_payload(event: dict, token: str) -> dict:
    run = event["workflow_run"]
    repository_data = run["repository"]
    repository = repository_data["full_name"]
    repository_url = repository_data["html_url"]
    workflow = run["name"]
    conclusion = run.get("conclusion") or "unknown"
    trigger = run.get("event") or "unknown"
    actor = (run.get("actor") or {}).get("login") or "unknown"
    run_url = run["html_url"]
    head_sha = run.get("head_sha") or ""

    pull_request = select_pull_request(run, associated_pull_requests(run, token))
    source_branch, target_branch = branch_flow(run, pull_request)
    pr_number = pull_request.get("number") if pull_request else None
    pr_url = f"{repository_url}/pull/{pr_number}" if pr_number else ""

    icon = {
        "success": "✅",
        "failure": "❌",
        "cancelled": "⚪",
        "timed_out": "⏰",
        "action_required": "⚠️",
    }.get(conclusion, "ℹ️")
    result = conclusion.upper()
    sha_short = head_sha[:7] if head_sha else "unknown"
    header = f"{icon} {result} | {repository} | {workflow}"[:150]
    flow = f"`{safe_text(source_branch)}` → `{safe_text(target_branch)}`"
    pr_text = f"<{pr_url}|#{pr_number}>" if pr_url else "—"
    commit_url = f"{repository_url}/commit/{head_sha}"
    commit_text = f"<{commit_url}|`{safe_text(sha_short)}`>" if head_sha else "unknown"

    buttons = [
        {
            "type": "button",
            "text": {"type": "plain_text", "text": "GitHub Actions 보기"},
            "url": run_url,
        }
    ]
    if pr_url:
        buttons.append(
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Pull Request 보기"},
                "url": pr_url,
            }
        )

    return {
        "text": header,
        "unfurl_links": False,
        "unfurl_media": False,
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": header}},
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*브랜치 흐름*\n{flow}"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*소스 브랜치*\n`{safe_text(source_branch)}`"},
                    {"type": "mrkdwn", "text": f"*대상 브랜치*\n`{safe_text(target_branch)}`"},
                    {"type": "mrkdwn", "text": f"*결과*\n`{safe_text(result)}`"},
                    {"type": "mrkdwn", "text": f"*트리거*\n`{safe_text(trigger)}`"},
                    {"type": "mrkdwn", "text": f"*Pull Request*\n{pr_text}"},
                    {"type": "mrkdwn", "text": f"*커밋*\n{commit_text}"},
                    {"type": "mrkdwn", "text": f"*실행자*\n`{safe_text(actor)}`"},
                    {
                        "type": "mrkdwn",
                        "text": (
                            f"*실행 번호*\n#{run['run_number']} "
                            f"(시도 {run.get('run_attempt', 1)})"
                        ),
                    },
                    {"type": "mrkdwn", "text": f"*소요 시간*\n{duration_text(run)}"},
                ],
            },
            {"type": "actions", "elements": buttons},
        ],
    }


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
    raise AssertionError("도달할 수 없는 재시도 상태")


def main() -> int:
    webhook = os.environ.get("SLACK_WEBHOOK_URL", "").strip()
    if not webhook:
        raise RuntimeError("필수 secret SLACK_WEBHOOK_URL이 설정되지 않았습니다.")
    event_path = os.environ.get("GITHUB_EVENT_PATH", "").strip()
    if not event_path:
        raise RuntimeError("GITHUB_EVENT_PATH가 설정되지 않았습니다.")
    with open(event_path, encoding="utf-8") as event_file:
        event = json.load(event_file)
    payload = build_payload(event, os.environ.get("GITHUB_API_TOKEN", ""))
    post_slack(webhook, payload)
    print("Slack 알림 전송 완료")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Slack 알림 실패: {error}", file=sys.stderr)
        raise SystemExit(1)
