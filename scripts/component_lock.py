import argparse
import json
import os
import re
from pathlib import Path


LOCK_PATH = Path("components.lock.json")
EXPECTED = {
    "frontend": "DodamDodam-Capstone/frontend",
    "backend": "DodamDodam-Capstone/backend",
    "ai": "DodamDodam-Capstone/ai",
}
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def load_and_validate() -> dict:
    data = json.loads(LOCK_PATH.read_text())
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


def validate(write_outputs: bool) -> None:
    data = load_and_validate()
    if write_outputs:
        output_path = os.environ.get("GITHUB_OUTPUT")
        if not output_path:
            raise ValueError("GITHUB_OUTPUT is not set")
        with open(output_path, "a", encoding="utf-8") as output:
            for component in EXPECTED:
                output.write(f"{component}-sha={data['components'][component]['sha']}\n")
    print("components.lock.json is valid")


def update(component: str, repository: str, sha: str) -> None:
    if component not in EXPECTED:
        raise ValueError(f"Unsupported component: {component}")
    if repository != EXPECTED[component]:
        raise ValueError(f"Repository does not match component {component}")
    if not SHA_PATTERN.fullmatch(sha):
        raise ValueError("SHA must be 40 lowercase hexadecimal characters")

    data = load_and_validate()
    data["components"][component]["sha"] = sha
    LOCK_PATH.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Updated {component} to {sha}")


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--github-output", action="store_true")
    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("--component", required=True)
    update_parser.add_argument("--repository", required=True)
    update_parser.add_argument("--sha", required=True)
    args = parser.parse_args()

    if args.command == "validate":
        validate(args.github_output)
    else:
        update(args.component, args.repository, args.sha)


if __name__ == "__main__":
    main()

