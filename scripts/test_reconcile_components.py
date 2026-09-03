#!/usr/bin/env python3
"""Unit tests for component reconciliation without external communication."""

import base64
import json
import pathlib
import tempfile
import unittest

import component_lock
import reconcile_components


class ReconcileComponentsTest(unittest.TestCase):
    def write_lock(self, directory, sha="a" * 40):
        path = pathlib.Path(directory) / "components.lock.json"
        path.write_text(
            json.dumps(
                {
                    "components": {
                        component: {"repository": repository, "sha": sha}
                        for component, repository in component_lock.EXPECTED.items()
                    }
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_discover_skips_components_already_at_main(self):
        with tempfile.TemporaryDirectory() as directory:
            lock_path = self.write_lock(directory)

            def source_get(_path):
                return {"sha": "a" * 40}

            def integration_get(_path):
                self.fail("integration API should not be called for matching pins")

            self.assertEqual(
                reconcile_components.discover_updates(
                    lock_path, source_get, integration_get
                ),
                [],
            )

    def test_discover_requests_update_when_pr_is_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            lock_path = self.write_lock(directory)

            def source_get(_path):
                return {"sha": "b" * 40}

            def integration_get(path):
                if "/pulls?" in path:
                    return []
                self.fail(f"unexpected path {path}")

            updates = reconcile_components.discover_updates(
                lock_path, source_get, integration_get
            )
            self.assertEqual(len(updates), 3)
            self.assertEqual(updates[0]["component"], "frontend")

    def test_discover_skips_current_open_pr(self):
        desired_sha = "b" * 40
        branch_data = {
            "components": {
                component: {"repository": repository, "sha": desired_sha}
                for component, repository in component_lock.EXPECTED.items()
            }
        }
        encoded_lock = base64.b64encode(json.dumps(branch_data).encode()).decode()

        with tempfile.TemporaryDirectory() as directory:
            lock_path = self.write_lock(directory)

            def source_get(_path):
                return {"sha": desired_sha}

            def integration_get(path):
                if "/pulls?" in path:
                    return [{"number": 1}]
                if "/contents/components.lock.json?" in path:
                    return {"content": encoded_lock}
                if "/compare/" in path:
                    return {"status": "ahead", "behind_by": 0}
                self.fail(f"unexpected path {path}")

            self.assertEqual(
                reconcile_components.discover_updates(
                    lock_path, source_get, integration_get
                ),
                [],
            )

    def test_discover_refreshes_pr_behind_development(self):
        desired_sha = "b" * 40
        branch_data = {
            "components": {
                component: {"repository": repository, "sha": desired_sha}
                for component, repository in component_lock.EXPECTED.items()
            }
        }
        encoded_lock = base64.b64encode(json.dumps(branch_data).encode()).decode()

        with tempfile.TemporaryDirectory() as directory:
            lock_path = self.write_lock(directory)

            def source_get(_path):
                return {"sha": desired_sha}

            def integration_get(path):
                if "/pulls?" in path:
                    return [{"number": 1}]
                if "/contents/components.lock.json?" in path:
                    return {"content": encoded_lock}
                if "/compare/" in path:
                    return {"status": "diverged", "behind_by": 1}
                self.fail(f"unexpected path {path}")

            updates = reconcile_components.discover_updates(
                lock_path, source_get, integration_get
            )
            self.assertEqual(len(updates), 3)

    def test_dispatch_uses_repository_dispatch_payload(self):
        calls = []
        updates = [
            {
                "component": "frontend",
                "repository": "DodamDodam-Capstone/frontend",
                "sha": "b" * 40,
            }
        ]
        reconcile_components.dispatch_updates(
            updates,
            "https://github.com/DodamDodam-Capstone/integration/actions/runs/123",
            lambda path, payload: calls.append((path, payload)),
        )
        self.assertEqual(calls[0][1]["event_type"], "component-main-updated")
        self.assertEqual(calls[0][1]["client_payload"]["sha"], "b" * 40)


if __name__ == "__main__":
    unittest.main()
