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

    def test_update_accepts_integration_reconciliation_url(self):
        with tempfile.TemporaryDirectory() as directory:
            lock_path = pathlib.Path(directory) / "components.lock.json"
            lock_path.write_text(json.dumps(self.lock_data()), encoding="utf-8")
            component_lock.update(
                "frontend",
                "DodamDodam-Capstone/frontend",
                "b" * 40,
                "https://github.com/DodamDodam-Capstone/integration/actions/runs/123",
                lock_path,
            )
            updated = json.loads(lock_path.read_text(encoding="utf-8"))
            self.assertEqual(updated["components"]["frontend"]["sha"], "b" * 40)

    def test_verify_accepts_main_and_ancestor_commits(self):
        main_shas = {
            repository: chr(ord("b") + index) * 40
            for index, repository in enumerate(component_lock.EXPECTED.values())
        }

        def api_getter(path, token):
            self.assertEqual(token, "test-token")
            if path.endswith("/commits/main"):
                repository = path.split("/repos/", 1)[1].rsplit("/commits/main", 1)[0]
                return {"sha": main_shas[repository]}
            return {"status": "ahead"}

        with tempfile.TemporaryDirectory() as directory:
            lock_path = pathlib.Path(directory) / "components.lock.json"
            lock_path.write_text(json.dumps(self.lock_data()), encoding="utf-8")
            component_lock.verify_references(
                "test-token", lock_path=lock_path, api_getter=api_getter
            )

    def test_verify_rejects_diverged_commit(self):
        def api_getter(path, _token):
            if path.endswith("/commits/main"):
                return {"sha": "b" * 40}
            return {"status": "diverged"}

        with tempfile.TemporaryDirectory() as directory:
            lock_path = pathlib.Path(directory) / "components.lock.json"
            lock_path.write_text(json.dumps(self.lock_data()), encoding="utf-8")
            with self.assertRaises(ValueError):
                component_lock.verify_references(
                    "test-token", lock_path=lock_path, api_getter=api_getter
                )

    def test_verify_requires_bot_component_to_match_main(self):
        def api_getter(path, _token):
            if path.endswith("/commits/main"):
                return {"sha": "b" * 40}
            return {"status": "ahead"}

        with tempfile.TemporaryDirectory() as directory:
            lock_path = pathlib.Path(directory) / "components.lock.json"
            lock_path.write_text(json.dumps(self.lock_data()), encoding="utf-8")
            with self.assertRaises(ValueError):
                component_lock.verify_references(
                    "test-token",
                    exact_component="frontend",
                    lock_path=lock_path,
                    api_getter=api_getter,
                )


if __name__ == "__main__":
    unittest.main()
