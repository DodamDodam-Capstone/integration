import argparse
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path


LOCK_PATH = Path("components.lock.json")
EXPECTED = {
    "frontend": "DodamDodam-Capstone/frontend",
    "backend": "DodamDodam-Capstone/backend",
    "ai": "DodamDodam-Capstone/ai",
}
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
GITHUB_API_URL = "https://api.github.com"


def resolve_lock_path(lock_path=None) -> Path:
    return Path(lock_path) if lock_path else LOCK_PATH


def load_and_validate(lock_path=None) -> dict:
    path = resolve_lock_path(lock_path)
    data = json.loads(path.read_text())
    components = data.get("components")
    if not isinstance(components, dict) or set(components) != set(EXPECTED):
        raise ValueError("components.lock.json must contain frontend, backend, and ai")

    for component, repository in EXPECTED.items():
        entry = components[component]
        if entry.get("repository") != repository:
            raise ValueError(f"Unexpected repository for {component}")
        sha = entry.get("sha", "")
        if not SHA_PATTERN.fullmatch(sha):
            raise ValueError(f"Invalid full commit SHA for {component}")
    return data


def validate(write_outputs: bool, lock_path=None) -> None:
    data = load_and_validate(lock_path)
    if write_outputs:
        output_path = os.environ.get("GITHUB_OUTPUT")
        if not output_path:
            raise ValueError("GITHUB_OUTPUT is not set")
        with open(output_path, "a", encoding="utf-8") as output:
            for component in EXPECTED:
                output.write(f"{component}-sha={data['components'][component]['sha']}\n")
    print("components.lock.json is valid")


def validate_run_url(repository: str, run_url: str) -> None:
    expected_urls = (
        rf"^https://github\.com/{re.escape(repository)}/actions/runs/[1-9]\d*$",
        r"^https://github\.com/DodamDodam-Capstone/integration/actions/runs/[1-9]\d*$",
    )
    if not any(re.fullmatch(expected, run_url) for expected in expected_urls):
        raise ValueError("Trigger workflow URL is not an allowed component or reconciliation run")


def update(component: str, repository: str, sha: str, run_url: str, lock_path=None) -> None:
    if component not in EXPECTED:
        raise ValueError(f"Unsupported component: {component}")
    if repository != EXPECTED[component]:
        raise ValueError(f"Repository does not match component {component}")
    if not SHA_PATTERN.fullmatch(sha):
        raise ValueError("SHA must be 40 lowercase hexadecimal characters")
    validate_run_url(repository, run_url)

    path = resolve_lock_path(lock_path)
    data = load_and_validate(path)
    data["components"][component]["sha"] = sha
    path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Updated {component} to {sha}")


def github_api_get(path: str, token: str) -> dict:
    request = urllib.request.Request(
        f"{GITHUB_API_URL}{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise ValueError(f"GitHub API returned HTTP {error.code} for {path}") from error
    except urllib.error.URLError as error:
        raise ValueError(f"GitHub API request failed for {path}: {error.reason}") from error


def verify_references(token: str, exact_component=None, lock_path=None, api_getter=None) -> None:
    if not token:
        raise ValueError("A GitHub token is required to verify component references")
    if exact_component and exact_component not in EXPECTED:
        raise ValueError(f"Unsupported exact component: {exact_component}")

    getter = api_getter or github_api_get
    data = load_and_validate(lock_path)
    for component, repository in EXPECTED.items():
        locked_sha = data["components"][component]["sha"]
        main_data = getter(f"/repos/{repository}/commits/main", token)
        main_sha = main_data.get("sha", "")
        if not SHA_PATTERN.fullmatch(main_sha):
            raise ValueError(f"GitHub returned an invalid main SHA for {component}")

        if component == exact_component and locked_sha != main_sha:
            raise ValueError(
                f"{component} bot update must point to current main {main_sha}, got {locked_sha}"
            )

        if locked_sha != main_sha:
            comparison = getter(
                f"/repos/{repository}/compare/{locked_sha}...{main_sha}", token
            )
            if comparison.get("status") != "ahead":
                raise ValueError(
                    f"{component} SHA {locked_sha} is not an ancestor of main {main_sha}"
                )
        print(f"Verified {component} {locked_sha} against main {main_sha}")


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--github-output", action="store_true")
    validate_parser.add_argument("--lock-path", default=str(LOCK_PATH))
    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("--component", required=True)
    update_parser.add_argument("--repository", required=True)
    update_parser.add_argument("--sha", required=True)
    update_parser.add_argument("--run-url", required=True)
    update_parser.add_argument("--lock-path", default=str(LOCK_PATH))
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--exact-component", choices=EXPECTED)
    verify_parser.add_argument("--lock-path", default=str(LOCK_PATH))
    verify_parser.add_argument("--token-env", default="GH_TOKEN")
    args = parser.parse_args()

    if args.command == "validate":
        validate(args.github_output, args.lock_path)
    elif args.command == "update":
        update(args.component, args.repository, args.sha, args.run_url, args.lock_path)
    else:
        verify_references(
            os.environ.get(args.token_env, ""),
            exact_component=args.exact_component,
            lock_path=args.lock_path,
        )


if __name__ == "__main__":
    main()
