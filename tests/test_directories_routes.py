"""
Tests for routes/directories.py — directory CRUD endpoints.
"""

import json
from pathlib import Path
from unittest.mock import patch


class TestCreateDirectory:
    def test_no_data(self, app_client):
        resp = app_client.post(
            "/api/directory/create",
            data=json.dumps(None),
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert "Нет данных" in resp.get_json()["error"]

    def test_empty_project_code(self, app_client):
        resp = app_client.post(
            "/api/directory/create",
            data=json.dumps({"project_code": ""}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_whitespace_project_code(self, app_client):
        resp = app_client.post(
            "/api/directory/create",
            data=json.dumps({"project_code": "   "}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_invalid_project_code(self, app_client, temp_dir):
        with patch("routes.directories.DESKTOP_PATH", temp_dir):
            resp = app_client.post(
                "/api/directory/create",
                data=json.dumps({"project_code": '\\/:*?"<>|'}),
                content_type="application/json",
            )
            data = resp.get_json()
            assert data["success"] is True
            assert data["project_code"] == "_________"

    def test_is_creating_lock(self, app_client, temp_state_file):
        from utils.state import load_state, save_state

        state = load_state()
        state["is_creating"] = True
        save_state(state)
        resp = app_client.post(
            "/api/directory/create",
            data=json.dumps({"project_code": "TestProject"}),
            content_type="application/json",
        )
        assert resp.status_code == 429

    def test_subfolders_tree_not_list(self, app_client):
        resp = app_client.post(
            "/api/directory/create",
            data=json.dumps({"project_code": "Test", "subfolders_tree": "not a list"}),
            content_type="application/json",
        )
        assert resp.status_code in (200, 500)

    def test_valid_create(self, app_client, temp_dir):
        with patch("routes.directories.DESKTOP_PATH", temp_dir):
            resp = app_client.post(
                "/api/directory/create",
                data=json.dumps(
                    {
                        "project_code": "TestProject",
                        "subfolders_tree": [{"name": "docs", "children": []}],
                    }
                ),
                content_type="application/json",
            )
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["success"] is True
            assert data["project_code"] == "TestProject"


class TestDeleteDirectory:
    def test_no_data(self, app_client):
        resp = app_client.post(
            "/api/directory/delete",
            data=json.dumps(None),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_empty_path(self, app_client):
        resp = app_client.post(
            "/api/directory/delete",
            data=json.dumps({"full_path": ""}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_path_not_on_desktop(self, app_client):
        resp = app_client.post(
            "/api/directory/delete",
            data=json.dumps({"full_path": "C:\\Windows\\System32"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_delete_nonexistent_dir(self, app_client, temp_dir, temp_state_file):
        fake_path = str(temp_dir / "nonexistent")
        with patch("routes.directories.DESKTOP_PATH", temp_dir):
            resp = app_client.post(
                "/api/directory/delete",
                data=json.dumps({"full_path": fake_path}),
                content_type="application/json",
            )
            assert resp.status_code == 200

    def test_delete_existing_dir(self, app_client, temp_dir, temp_state_file):
        test_dir = temp_dir / "test_del"
        test_dir.mkdir()
        with patch("routes.directories.DESKTOP_PATH", temp_dir):
            resp = app_client.post(
                "/api/directory/delete",
                data=json.dumps({"full_path": str(test_dir)}),
                content_type="application/json",
            )
            assert resp.status_code == 200


class TestAddSubfolder:
    def test_no_data(self, app_client):
        resp = app_client.post(
            "/api/directory/add-folder",
            data=json.dumps(None),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_missing_fields(self, app_client):
        resp = app_client.post(
            "/api/directory/add-folder",
            data=json.dumps({"parent_path": "", "folder_name": ""}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_invalid_folder_name(self, app_client, temp_dir, clean_state):
        parent = temp_dir / "parent"
        parent.mkdir()
        resp = app_client.post(
            "/api/directory/add-folder",
            data=json.dumps({"parent_path": str(parent), "folder_name": "   "}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_parent_not_found(self, app_client):
        resp = app_client.post(
            "/api/directory/add-folder",
            data=json.dumps(
                {"parent_path": "/nonexistent/path", "folder_name": "test"}
            ),
            content_type="application/json",
        )
        assert resp.status_code == 404

    def test_folder_already_exists(self, app_client, temp_dir):
        parent = temp_dir / "parent2"
        parent.mkdir()
        (parent / "existing").mkdir()
        resp = app_client.post(
            "/api/directory/add-folder",
            data=json.dumps({"parent_path": str(parent), "folder_name": "existing"}),
            content_type="application/json",
        )
        assert resp.status_code == 409

    def test_success(self, app_client, temp_dir, clean_state):
        parent = temp_dir / "parent3"
        parent.mkdir()
        resp = app_client.post(
            "/api/directory/add-folder",
            data=json.dumps({"parent_path": str(parent), "folder_name": "new_folder"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert (parent / "new_folder").exists()


class TestRenameDirectory:
    def test_no_data(self, app_client):
        resp = app_client.post(
            "/api/directory/rename",
            data=json.dumps(None),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_missing_fields(self, app_client):
        resp = app_client.post(
            "/api/directory/rename",
            data=json.dumps({"old_path": "", "new_name": ""}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_invalid_new_name(self, app_client, temp_dir, clean_state):
        old = temp_dir / "old_name"
        old.mkdir()
        resp = app_client.post(
            "/api/directory/rename",
            data=json.dumps({"old_path": str(old), "new_name": "   "}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_nonexistent_folder(self, app_client, temp_dir):
        resp = app_client.post(
            "/api/directory/rename",
            data=json.dumps(
                {
                    "old_path": str(temp_dir / "nonexistent"),
                    "new_name": "new_name",
                }
            ),
            content_type="application/json",
        )
        assert resp.status_code == 404

    def test_new_name_conflict(self, app_client, temp_dir):
        old = temp_dir / "old_dir"
        old.mkdir()
        conflict = temp_dir / "conflict"
        conflict.mkdir()
        resp = app_client.post(
            "/api/directory/rename",
            data=json.dumps({"old_path": str(old), "new_name": "conflict"}),
            content_type="application/json",
        )
        assert resp.status_code == 409

    def test_success(self, app_client, temp_dir, clean_state):
        old = temp_dir / "rename_me"
        old.mkdir()
        resp = app_client.post(
            "/api/directory/rename",
            data=json.dumps({"old_path": str(old), "new_name": "renamed"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert not old.exists()
        assert (temp_dir / "renamed").exists()


class TestRecreateDirectory:
    def test_no_data(self, app_client):
        resp = app_client.post(
            "/api/directory/recreate",
            data=json.dumps(None),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_empty_path(self, app_client):
        resp = app_client.post(
            "/api/directory/recreate",
            data=json.dumps({"full_path": ""}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_not_in_state(self, app_client, temp_dir):
        resp = app_client.post(
            "/api/directory/recreate",
            data=json.dumps({"full_path": str(temp_dir / "ghost")}),
            content_type="application/json",
        )
        assert resp.status_code == 404

    def test_recreate_success(self, app_client, temp_dir, temp_state_file):
        from utils.state import load_state, save_state

        target = temp_dir / "recreate_me"
        target.mkdir()
        state = load_state()
        state["created_directories"] = [
            {
                "path": str(target),
                "project_code": "recreate_me",
                "date": "01.01.2026",
                "subfolders_tree": [],
            }
        ]
        save_state(state)
        resp = app_client.post(
            "/api/directory/recreate",
            data=json.dumps({"full_path": str(target)}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True


class TestScanDirectories:
    def test_scan(self, app_client, temp_dir, temp_state_file):
        with patch("routes.directories.DESKTOP_PATH", temp_dir):
            resp = app_client.post(
                "/api/directory/scan",
                content_type="application/json",
            )
            assert resp.status_code == 200
            assert resp.get_json()["success"] is True


class TestGetCurrentDirectory:
    def test_get_current(self, app_client):
        resp = app_client.get("/api/directory/current")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "current_dir" in data
        assert "exists" in data
        assert "info" in data


class TestListDirectories:
    def test_list(self, app_client, temp_dir, temp_state_file):
        with patch("routes.directories.DESKTOP_PATH", temp_dir):
            resp = app_client.get("/api/directories/list")
            assert resp.status_code == 200
            assert resp.get_json()["success"] is True
