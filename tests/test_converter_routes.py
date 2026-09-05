"""
Tests for routes/converter.py — PDF conversion endpoints.
"""

import io
import json
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestConvertPDF:
    def test_no_file_uploaded(self, app_client):
        resp = app_client.post(
            "/api/converter/convert", content_type="multipart/form-data"
        )
        assert resp.status_code == 400
        assert "No file uploaded" in resp.get_json()["error"]

    def test_non_pdf_file(self, app_client):
        data = {"file": (io.BytesIO(b"not pdf"), "test.txt")}
        resp = app_client.post(
            "/api/converter/convert",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400
        assert "PDF" in resp.get_json()["error"]

    def test_invalid_format(self, app_client):
        data = {
            "file": (io.BytesIO(b"%PDF-1.4 fake"), "test.pdf"),
            "format": "invalid_format",
        }
        resp = app_client.post(
            "/api/converter/convert",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400
        assert "Недопустимый формат" in resp.get_json()["error"]

    @patch("utils.database.add_conversion", return_value=1)
    @patch("routes.converter.threading.Thread")
    def test_valid_pdf_upload(self, mock_thread, mock_add, app_client):
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        data = {
            "file": (io.BytesIO(b"%PDF-1.4 fake content"), "test.pdf"),
            "format": "markdown",
        }
        resp = app_client.post(
            "/api/converter/convert",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        result = resp.get_json()
        assert result["success"] is True
        assert "job_id" in result
        mock_thread_instance.start.assert_called_once()

    @patch("utils.database.add_conversion", return_value=1)
    @patch("routes.converter.threading.Thread")
    def test_default_format_is_markdown(self, mock_thread, mock_add, app_client):
        mock_thread.return_value = MagicMock()
        data = {"file": (io.BytesIO(b"%PDF-1.4"), "doc.pdf")}
        resp = app_client.post(
            "/api/converter/convert",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200

    @patch("utils.database.add_conversion", return_value=1)
    @patch("routes.converter.threading.Thread")
    def test_no_filename_uses_doc(self, mock_thread, mock_add, app_client):
        mock_thread.return_value = MagicMock()
        data = {"file": (io.BytesIO(b"%PDF-1.4"), "doc.pdf")}
        resp = app_client.post(
            "/api/converter/convert",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200


class TestGetProgress:
    def test_job_not_found(self, app_client):
        resp = app_client.get("/api/converter/progress/nonexistent")
        assert resp.status_code == 404

    def test_job_found(self, app_client):
        from routes.converter import _jobs, _jobs_lock

        with _jobs_lock:
            _jobs["test123"] = {
                "id": "test123",
                "status": "running",
                "progress": 50,
            }
        try:
            resp = app_client.get("/api/converter/progress/test123")
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["success"] is True
            assert data["job"]["status"] == "running"
        finally:
            with _jobs_lock:
                _jobs.pop("test123", None)


class TestDownloadResult:
    def test_no_job(self, app_client):
        resp = app_client.get("/api/converter/download/nonexistent")
        assert resp.status_code == 404

    def test_job_no_result_path(self, app_client):
        from routes.converter import _jobs, _jobs_lock

        with _jobs_lock:
            _jobs["noresult"] = {"id": "noresult", "result_path": None}
        try:
            resp = app_client.get("/api/converter/download/noresult")
            assert resp.status_code == 404
        finally:
            with _jobs_lock:
                _jobs.pop("noresult", None)

    def test_result_file_not_found(self, app_client):
        from routes.converter import _jobs, _jobs_lock

        with _jobs_lock:
            _jobs["missing"] = {
                "id": "missing",
                "result_path": "/nonexistent/path/file.md",
            }
        try:
            resp = app_client.get("/api/converter/download/missing")
            assert resp.status_code == 404
        finally:
            with _jobs_lock:
                _jobs.pop("missing", None)

    def test_download_existing_file(self, app_client, temp_dir):
        from routes.converter import _jobs, _jobs_lock

        result_file = temp_dir / "result.md"
        result_file.write_text("test content")
        with _jobs_lock:
            _jobs["dl_test"] = {
                "id": "dl_test",
                "result_path": str(result_file),
            }
        try:
            resp = app_client.get("/api/converter/download/dl_test")
            assert resp.status_code == 200
        finally:
            with _jobs_lock:
                _jobs.pop("dl_test", None)


class TestConverterHistory:
    def test_get_history_empty(self, app_client):
        resp = app_client.get("/api/converter/history")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_delete_nonexistent(self, app_client):
        resp = app_client.delete("/api/converter/history/99999")
        assert resp.status_code == 404


class TestUpdateJob:
    def test_update_existing_job(self):
        from routes.converter import _jobs, _jobs_lock, _update_job

        with _jobs_lock:
            _jobs["upd1"] = {"id": "upd1", "status": "pending", "progress": 0}
        try:
            _update_job("upd1", status="running", progress=50)
            with _jobs_lock:
                job = _jobs["upd1"]
            assert job["status"] == "running"
            assert job["progress"] == 50
        finally:
            with _jobs_lock:
                _jobs.pop("upd1", None)

    def test_update_nonexistent_job(self):
        from routes.converter import _update_job

        _update_job("nonexistent", status="done")


class TestFindJar:
    def test_find_jar_returns_path(self):
        from routes.converter import _find_jar

        jar = _find_jar()
        assert isinstance(jar, Path)
