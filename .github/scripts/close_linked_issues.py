#!/usr/bin/env python3
"""병합된 PR 본문에서 명시적으로 연결한 같은 저장소 Issue를 완료 처리한다."""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request


REPOSITORY_RE = re.compile(
    r"^DodamDodam-Capstone/(?:frontend|backend|ai|integration)$"
)
CLOSING_RE = re.compile(
    r"(?im)\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#([1-9]\d*)"
)


def executable_text(body: str) -> str:
    """템플릿 주석과 코드 예시에 적힌 closing keyword를 실행 대상에서 제외한다."""
    text = re.sub(r"<!--[\s\S]*?-->", "", body or "")
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`[^`\n]*`", "", text)
    return text


def linked_numbers(body: str) -> list[str]:
    return sorted(set(CLOSING_RE.findall(executable_text(body))), key=int)


def github_request(method: str, url: str, token: str, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")[:500]
        raise RuntimeError(f"GitHub API HTTP {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise RuntimeError("GitHub API 네트워크 요청에 실패했습니다.") from error


def close_linked(repository: str, body: str, token: str) -> list[str]:
    if not REPOSITORY_RE.fullmatch(repository):
        raise ValueError("허용되지 않은 GitHub 저장소입니다.")
    if not token:
        raise RuntimeError("GITHUB_TOKEN이 설정되지 않았습니다.")

    closed: list[str] = []
    for number in linked_numbers(body):
        url = f"https://api.github.com/repos/{repository}/issues/{number}"
        issue = github_request("GET", url, token)
        if "pull_request" in issue:
            print(f"#{number}은 Pull Request이므로 종료하지 않습니다.")
            continue
        if issue.get("state") == "closed":
            print(f"Issue #{number}은 이미 종료되어 있습니다.")
            continue
        github_request(
            "PATCH",
            url,
            token,
            {"state": "closed", "state_reason": "completed"},
        )
        closed.append(number)
        print(f"Issue #{number} 완료 처리")
    return closed


def main() -> int:
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    body = os.environ.get("PR_BODY", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    numbers = linked_numbers(body)
    if not numbers:
        print("종료할 연결 Issue가 없습니다.")
        return 0
    close_linked(repository, body, token)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"연결 Issue 완료 처리 실패: {error}", file=sys.stderr)
        raise SystemExit(1)
