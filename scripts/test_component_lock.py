#!/usr/bin/env python3
"""컴포넌트 잠금 파일 helper의 외부 통신 없는 단위 테스트."""

import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

import component_lock


class ComponentLockTest(unittest.TestCase):
    def lock_data(self):
        return {
            "components": {
                component: {"repository": repository, "sha": "a" * 40}
                for component, repository in component_lock.EXPECTED.items()
            }
        }

    def test_update_accepts_only_matching_repository_and_run_url(self):
        with tempfile.TemporaryDirectory() as directory:
            lock_path = pathlib.Path(directory) / "components.lock.json"
            lock_path.write_text(json.dumps(self.lock_data()), encoding="utf-8")
            with patch.object(component_lock, "LOCK_PATH", lock_path):
                component_lock.update(
                    "frontend",
                    "DodamDodam-Capstone/frontend",
                    "b" * 40,
                    "https://github.com/DodamDodam-Capstone/frontend/actions/runs/123",
                )
            updated = json.loads(lock_path.read_text(encoding="utf-8"))
            self.assertEqual(updated["components"]["frontend"]["sha"], "b" * 40)

    def test_update_rejects_mismatched_source_url(self):
        with tempfile.TemporaryDirectory() as directory:
            lock_path = pathlib.Path(directory) / "components.lock.json"
            lock_path.write_text(json.dumps(self.lock_data()), encoding="utf-8")
            with patch.object(component_lock, "LOCK_PATH", lock_path):
                with self.assertRaises(ValueError):
                    component_lock.update(
                        "frontend",
                        "DodamDodam-Capstone/frontend",
                        "b" * 40,
                        "https://example.com/injected",
                    )

    def test_update_rejects_wrong_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            lock_path = pathlib.Path(directory) / "components.lock.json"
            lock_path.write_text(json.dumps(self.lock_data()), encoding="utf-8")
            with patch.object(component_lock, "LOCK_PATH", lock_path):
                with self.assertRaises(ValueError):
                    component_lock.update(
                        "frontend",
                        "DodamDodam-Capstone/backend",
                        "b" * 40,
                        "https://github.com/DodamDodam-Capstone/backend/actions/runs/123",
                    )


if __name__ == "__main__":
    unittest.main()
