#!/usr/bin/env python3
"""Actions → Slack helper의 외부 통신 없는 단위 테스트."""

import importlib.util
import pathlib
import unittest
from unittest.mock import patch


SCRIPT = pathlib.Path(__file__).with_name("notify_workflow_run_to_slack.py")
SPEC = importlib.util.spec_from_file_location("slack_notify", SCRIPT)
slack_notify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(slack_notify)


def run_payload(event="pull_request"):
    return {
        "name": "Frontend CI",
        "conclusion": "success",
        "event": event,
        "head_branch": "feature/SCRUM-1-login",
        "head_sha": "a" * 40,
        "html_url": "https://github.com/org/repo/actions/runs/1",
        "run_number": 7,
        "run_attempt": 2,
        "run_started_at": "2026-08-22T00:00:00Z",
        "updated_at": "2026-08-22T00:01:05Z",
        "actor": {"login": "member"},
        "repository": {
            "full_name": "org/repo",
            "html_url": "https://github.com/org/repo",
        },
        "pull_requests": [],
    }


class Response:
    status = 200

    def __init__(self, body=b"ok"):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.body


class SlackNotifyTest(unittest.TestCase):
    def test_pull_request_branch_flow(self):
        run = run_payload()
        pull_request = {
            "number": 12,
            "head": {"ref": "feature/SCRUM-1-login"},
            "base": {"ref": "development"},
        }
        self.assertEqual(
            slack_notify.branch_flow(run, pull_request),
            ("feature/SCRUM-1-login", "development"),
        )

    def test_push_without_exact_pr_is_explicit(self):
        run = run_payload("push")
        run["head_branch"] = "main"
        self.assertEqual(
            slack_notify.branch_flow(run, None), ("— (push 이벤트)", "main")
        )

    def test_push_selects_only_exact_merged_pull_request(self):
        run = run_payload("push")
        run["head_branch"] = "development"
        exact = {
            "number": 20,
            "merge_commit_sha": run["head_sha"],
            "head": {"ref": "feature/SCRUM-1-login"},
            "base": {"ref": "development"},
        }
        unrelated_release = {
            "number": 19,
            "merge_commit_sha": "b" * 40,
            "head": {"ref": "development"},
            "base": {"ref": "main"},
        }
        self.assertIs(
            slack_notify.select_pull_request(run, [unrelated_release, exact]), exact
        )

    def test_push_does_not_guess_open_release_pull_request(self):
        run = run_payload("push")
        run["head_branch"] = "development"
        unrelated_release = {
            "number": 19,
            "merge_commit_sha": "b" * 40,
            "head": {"ref": "development"},
            "base": {"ref": "main"},
        }
        self.assertIsNone(
            slack_notify.select_pull_request(run, [unrelated_release])
        )

    def test_mrkdwn_characters_are_escaped(self):
        self.assertEqual(slack_notify.safe_text("<@channel>&`x`"), "&lt;@channel&gt;&amp;ʼxʼ")

    def test_payload_contains_source_target_and_pr(self):
        run = run_payload()
        run["pull_requests"] = [
            {
                "number": 12,
                "head": {"ref": "feature/SCRUM-1-login"},
                "base": {"ref": "development"},
            }
        ]
        payload = slack_notify.build_payload({"workflow_run": run}, "token")
        rendered = str(payload)
        self.assertIn("feature/SCRUM-1-login", rendered)
        self.assertIn("development", rendered)
        self.assertIn("/pull/12", rendered)
        self.assertIn("1분 5초", rendered)

    def test_slack_requires_plain_text_ok(self):
        with patch.object(slack_notify.urllib.request, "urlopen", return_value=Response()):
            slack_notify.post_slack(
                "https://hooks.slack.com/services/T/B/secret", {"text": "test"}, attempts=1
            )
        with patch.object(
            slack_notify.urllib.request, "urlopen", return_value=Response(b"unexpected")
        ):
            with self.assertRaises(RuntimeError):
                slack_notify.post_slack(
                    "https://hooks.slack.com/services/T/B/secret", {"text": "test"}, attempts=1
                )


if __name__ == "__main__":
    unittest.main()
