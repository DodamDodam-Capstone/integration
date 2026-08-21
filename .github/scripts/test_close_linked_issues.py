#!/usr/bin/env python3
"""PR 연결 Issue helper의 외부 통신 없는 단위 테스트."""

import importlib.util
import pathlib
import unittest
from unittest.mock import patch


SCRIPT = pathlib.Path(__file__).with_name("close_linked_issues.py")
SPEC = importlib.util.spec_from_file_location("close_linked", SCRIPT)
close_linked = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(close_linked)


class CloseLinkedIssuesTest(unittest.TestCase):
    def test_template_comment_does_not_close_example_issue(self):
        body = "<!-- 예: Resolves #123 -->\n\nResolves #7"
        self.assertEqual(close_linked.linked_numbers(body), ["7"])

    def test_code_examples_are_ignored(self):
        body = "```text\nFixes #1\n```\n`Closes #2`\nFixes #3"
        self.assertEqual(close_linked.linked_numbers(body), ["3"])

    def test_multiple_keywords_are_deduplicated_and_sorted(self):
        body = "Fixes #20\nCloses #3\nResolved #20"
        self.assertEqual(close_linked.linked_numbers(body), ["3", "20"])

    def test_pull_requests_and_closed_issues_are_not_patched(self):
        responses = [
            {"number": 1, "pull_request": {}},
            {"number": 2, "state": "closed"},
            {"number": 3, "state": "open"},
            {"number": 3, "state": "closed"},
        ]
        with patch.object(close_linked, "github_request", side_effect=responses) as request:
            closed = close_linked.close_linked(
                "DodamDodam-Capstone/frontend",
                "Fixes #1\nFixes #2\nFixes #3",
                "token",
            )
        self.assertEqual(closed, ["3"])
        self.assertEqual(request.call_count, 4)


if __name__ == "__main__":
    unittest.main()
