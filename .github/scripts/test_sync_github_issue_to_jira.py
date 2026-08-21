#!/usr/bin/env python3
"""GitHub Issue → Jira 중앙 helper의 외부 통신 없는 단위 테스트."""

import importlib.util
import pathlib
import unittest
from unittest.mock import patch

SCRIPT = pathlib.Path(__file__).with_name("sync_github_issue_to_jira.py")
SPEC = importlib.util.spec_from_file_location("issue_sync", SCRIPT)
issue_sync = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(issue_sync)


class Response:
    def __init__(self, body: bytes):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.body


class IssueSyncTest(unittest.TestCase):
    def test_extract_parent(self):
        body = "### 상위 Jira 키 (선택)\n\nSCRUM-6\n\n### 완료 목표\n\n검증"
        self.assertEqual(issue_sync.extract_parent(body), "SCRUM-6")
        self.assertIsNone(issue_sync.extract_parent("### 상위 Jira 키 (선택)\n\n_No response_"))

    def test_issue_type_priority(self):
        self.assertEqual(issue_sync.issue_type({"epic", "bug"}), "에픽")
        self.assertEqual(issue_sync.issue_type({"bug"}), "버그")
        self.assertEqual(issue_sync.issue_type({"task"}), "작업")

    def test_summary_is_normalized(self):
        self.assertEqual(issue_sync.summary_for("[FE] 로그인 구현", "FE"), "[FE] 로그인 구현")
        self.assertEqual(
            issue_sync.summary_for("SCRUM-99 [BE] 로그인 API", "BE"), "[BE] 로그인 API"
        )

    def test_jira_issue_type_ids_are_pinned(self):
        self.assertEqual(
            issue_sync.ISSUE_TYPE_IDS,
            {"에픽": "10001", "작업": "10003", "버그": "10006"},
        )

    def test_json_and_plain_text_responses(self):
        with patch.object(issue_sync.urllib.request, "urlopen", return_value=Response(b'ok')):
            self.assertEqual(
                issue_sync.request_json("POST", "https://example.invalid", headers={}),
                {"raw": "ok"},
            )
        with patch.object(
            issue_sync.urllib.request,
            "urlopen",
            return_value=Response(b'{"key":"SCRUM-11"}'),
        ):
            self.assertEqual(
                issue_sync.request_json("POST", "https://example.invalid", headers={}),
                {"key": "SCRUM-11"},
            )


if __name__ == "__main__":
    unittest.main()
