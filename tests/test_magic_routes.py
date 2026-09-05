"""
Tests for routes/magic.py — file copy/numbering/registry endpoints.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from routes.magic import generate_numbered_filename


class TestGenerateNumberedFilename:
    def test_basic(self):
        result = generate_numbered_filename(1, "document", ".pdf")
        assert result == "01.document.pdf"

    def test_double_digit(self):
        result = generate_numbered_filename(42, "report", ".docx")
        assert result == "42.report.docx"

    def test_triple_digit(self):
        result = generate_numbered_filename(100, "file", ".txt")
        assert result == "100.file.txt"

    def test_zero_padded(self):
        result = generate_numbered_filename(5, "name", ".ext")
        assert result == "05.name.ext"


class TestStartMagic:
    def test_no_files_in_state(self, app_client, clean_state):
        resp = app_client.post(
            "/api/magic/start",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert "Нет файлов" in resp.get_json()["error"]

    def test_nonexistent_target_dir(self, app_client, clean_state):
        resp = app_client.post(
            "/api/magic/start",
            data=json.dumps({"target_dir": "/nonexistent/path"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_existing_numbered_files(self, app_client, clean_state, temp_dir):
        from utils.state import load_state, save_state

        state = load_state()
        state["files"] = [{"path": "/fake/file.pdf", "name": "file.pdf"}]
        save_state(state)
        (temp_dir / "01.existing.pdf").touch()
        resp = app_client.post(
            "/api/magic/start",
            data=json.dumps({"target_dir": str(temp_dir)}),
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert "пронумерованные" in resp.get_json()["error"]

    @patch("routes.magic.threading.Thread")
    def test_success_starts_thread(
        self, mock_thread, app_client, clean_state, temp_dir
    ):
        from utils.state import load_state, save_state

        state = load_state()
        state["files"] = [{"path": "/fake/file.pdf", "name": "file.pdf"}]
        save_state(state)
        mock_thread.return_value = MagicMock()
        resp = app_client.post(
            "/api/magic/start",
            data=json.dumps({"target_dir": str(temp_dir)}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_invalid_target_dir_fallback(self, app_client, clean_state):
        from utils.state import load_state, save_state

        state = load_state()
        state["files"] = [{"path": "/fake/file.pdf", "name": "file.pdf"}]
        save_state(state)
        resp = app_client.post(
            "/api/magic/start",
            data=json.dumps({"target_dir": "/nonexistent/dir"}),
            content_type="application/json",
        )
        assert resp.status_code in (200, 400)


class TestCancelMagic:
    def test_cancel(self, app_client):
        resp = app_client.post(
            "/api/magic/cancel",
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True


class TestMagicProgress:
    def test_get_progress(self, app_client):
        resp = app_client.get("/api/magic/progress")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "progress" in data


class TestMagicResult:
    def test_get_result(self, app_client, clean_state):
        resp = app_client.get("/api/magic/result")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "last_magic_run" in data
        assert "files" in data
