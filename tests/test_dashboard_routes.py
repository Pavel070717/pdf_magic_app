"""
Tests for routes/dashboard.py — dashboard statistics.
"""

import json
from datetime import datetime, timezone
from unittest.mock import patch


class TestDashboardStats:
    def test_basic_stats(self, app_client, clean_state):
        resp = app_client.get("/api/dashboard/stats")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "total_files" in data
        assert "total_dirs" in data
        assert "total_materials" in data
        assert "total_rules" in data
        assert "activity" in data
        assert "recent_events" in data

    def test_stats_with_files(self, app_client, clean_state):
        from utils.state import load_state, save_state

        state = load_state()
        state["files"] = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
        save_state(state)
        resp = app_client.get("/api/dashboard/stats")
        data = resp.get_json()
        assert data["total_files"] == 3

    def test_stats_with_rules(self, app_client, clean_state):
        from utils.state import load_state, save_state

        state = load_state()
        state["replace_rules"] = [{"id": 1}, {"id": 2}]
        save_state(state)
        resp = app_client.get("/api/dashboard/stats")
        data = resp.get_json()
        assert data["total_rules"] == 2

    def test_stats_with_created_dirs(self, app_client, clean_state, temp_dir):
        from utils.state import load_state, save_state

        state = load_state()
        test_dir = temp_dir / "test_dir"
        test_dir.mkdir()
        state["created_directories"] = [
            {
                "path": str(test_dir),
                "project_code": "test",
                "date": "01.01.2026",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        ]
        save_state(state)
        resp = app_client.get("/api/dashboard/stats")
        data = resp.get_json()
        assert data["success"] is True
        assert data["total_dirs"] >= 1

    def test_stats_with_last_magic_run(self, app_client, clean_state):
        from utils.state import load_state, save_state

        state = load_state()
        state["last_magic_run"] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "files_copied": 5,
            "output_dir": "/test/dir",
            "registry_name": "registry.xlsx",
        }
        save_state(state)
        resp = app_client.get("/api/dashboard/stats")
        data = resp.get_json()
        assert len(data["recent_events"]) >= 1

    def test_activity_data_length(self, app_client, clean_state):
        resp = app_client.get("/api/dashboard/stats")
        data = resp.get_json()
        assert len(data["activity"]) == 7

    def test_stats_empty_state(self, app_client, clean_state):
        resp = app_client.get("/api/dashboard/stats")
        data = resp.get_json()
        assert data["total_files"] == 0
        assert data["total_dirs"] == 0
        assert data["total_materials"] == 0
        assert data["total_rules"] == 0
