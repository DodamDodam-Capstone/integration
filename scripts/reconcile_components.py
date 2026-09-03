#!/usr/bin/env python3
"""Reconcile integration component pins with each component's current main."""

import argparse
import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import component_lock


GITHUB_API_URL = "https://api.github.com"
INTEGRATION_REPOSITORY = "DodamDodam-Capstone/integration"
TARGET_BRANCH = "development"


class GitHubAPIError(RuntimeError):
    def __init__(self, status: int, path: str):
        super().__init__(f"GitHub API returned HTTP {status} for {path}")
        self.status = status
        self.path = path


class GitHubClient:
    def __init__(self, token: str):
        if not token:
            raise ValueError("GitHub token is required")
        self.token = token

    def request(self, method: str, path: str, payload=None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{GITHUB_API_URL}{path}",
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                if response.status == 204:
                    return None
                return json.load(response)
        except urllib.error.HTTPError as error:
            raise GitHubAPIError(error.code, path) from error
        except urllib.error.URLError as error:
            raise RuntimeError(f"GitHub API request failed for {path}: {error.reason}") from error

    def get(self, path: str):
        return self.request("GET", path)

    def post(self, path: str, payload):
        return self.request("POST", path, payload)


def branch_lock_sha(component: str, branch: str, integration_get):
    query = urllib.parse.urlencode({"ref": branch})
    path = f"/repos/{INTEGRATION_REPOSITORY}/contents/components.lock.json?{query}"
    try:
        response = integration_get(path)
    except GitHubAPIError as error:
        if error.status == 404:
            return None
        raise

    content = base64.b64decode(response["content"]).decode("utf-8")
    data = json.loads(content)
    return data.get("components", {}).get(component, {}).get("sha")


def has_current_open_pr(component: str, desired_sha: str, integration_get) -> bool:
    branch = f"bot/update-{component}"
    owner = INTEGRATION_REPOSITORY.split("/", 1)[0]
    query = urllib.parse.urlencode(
        {
            "state": "open",
            "base": TARGET_BRANCH,
            "head": f"{owner}:{branch}",
        }
    )
    pulls = integration_get(f"/repos/{INTEGRATION_REPOSITORY}/pulls?{query}")
    if not pulls or branch_lock_sha(component, branch, integration_get) != desired_sha:
        return False

    comparison_ref = urllib.parse.quote(f"{TARGET_BRANCH}...{branch}", safe=".")
    comparison = integration_get(
        f"/repos/{INTEGRATION_REPOSITORY}/compare/{comparison_ref}"
    )
    return comparison.get("status") == "ahead" and comparison.get("behind_by") == 0


def discover_updates(lock_path: Path, source_get, integration_get):
    lock_data = component_lock.load_and_validate(lock_path)
    updates = []
    for component, repository in component_lock.EXPECTED.items():
        response = source_get(f"/repos/{repository}/commits/main")
        desired_sha = response.get("sha", "")
        if not component_lock.SHA_PATTERN.fullmatch(desired_sha):
            raise ValueError(f"GitHub returned an invalid main SHA for {component}")

        locked_sha = lock_data["components"][component]["sha"]
        if locked_sha == desired_sha:
            print(f"{component} already points to current main {desired_sha}")
            continue
        if has_current_open_pr(component, desired_sha, integration_get):
            print(f"{component} already has an up-to-date Bot PR for {desired_sha}")
            continue

        updates.append(
            {"component": component, "repository": repository, "sha": desired_sha}
        )
    return updates


def dispatch_updates(updates, run_url: str, integration_post) -> None:
    for update in updates:
        component_lock.validate_run_url(update["repository"], run_url)
        integration_post(
            f"/repos/{INTEGRATION_REPOSITORY}/dispatches",
            {
                "event_type": "component-main-updated",
                "client_payload": {
                    **update,
                    "jira_key": "",
                    "run_url": run_url,
                },
            },
        )
        print(f"Dispatched reconciliation for {update['component']} {update['sha']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock-path", default=str(component_lock.LOCK_PATH))
    args = parser.parse_args()

    source = GitHubClient(os.environ.get("GH_SOURCE_TOKEN", ""))
    integration = GitHubClient(os.environ.get("GH_INTEGRATION_TOKEN", ""))
    run_url = (
        f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/"
        f"{os.environ.get('GITHUB_REPOSITORY', INTEGRATION_REPOSITORY)}/actions/runs/"
        f"{os.environ.get('GITHUB_RUN_ID', '')}"
    )

    updates = discover_updates(Path(args.lock_path), source.get, integration.get)
    dispatch_updates(updates, run_url, integration.post)
    if not updates:
        print("All component references are reconciled.")


if __name__ == "__main__":
    main()
