"""
Tests for routes/files.py — file upload, list, reorder, delete.
"""

import io
import json


class TestGetFiles:
    def test_empty_list(self, app_client, clean_state):
        resp = app_client.get("/api/files")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "files" in data
        assert isinstance(data["files"], list)

    def test_files_have_display_order(self, app_client, clean_state):
        from utils.state import load_state, save_state

        state = load_state()
        state["files"] = [
            {"id": "a", "name": "a.pdf", "path": "/a"},
            {"id": "b", "name": "b.pdf", "path": "/b"},
        ]
        save_state(state)
        resp = app_client.get("/api/files")
        files = resp.get_json()["files"]
        assert files[0]["display_order"] == 1
        assert files[1]["display_order"] == 2


class TestAddFiles:
    def test_no_files_key(self, app_client):
        resp = app_client.post(
            "/api/files/add",
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400

    def test_add_valid_pdf(self, app_client, clean_state):
        data = {"files": (io.BytesIO(b"fake pdf content"), "test.pdf")}
        resp = app_client.post(
            "/api/files/add",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        result = resp.get_json()
        assert result["success"] is True
        assert len(result["files"]) == 1

    def test_add_invalid_extension(self, app_client, clean_state):
        data = {"files": (io.BytesIO(b"content"), "test.exe")}
        resp = app_client.post(
            "/api/files/add",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400

    def test_add_empty_filename(self, app_client, clean_state):
        data = {"files": (io.BytesIO(b"content"), "")}
        resp = app_client.post(
            "/api/files/add",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400

    def test_add_multiple_files(self, app_client, clean_state):
        data = {
            "files": [
                (io.BytesIO(b"pdf1"), "file1.pdf"),
                (io.BytesIO(b"pdf2"), "file2.pdf"),
            ]
        }
        resp = app_client.post(
            "/api/files/add",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        assert len(resp.get_json()["files"]) == 2

    def test_add_png_file(self, app_client, clean_state):
        data = {"files": (io.BytesIO(b"png data"), "image.png")}
        resp = app_client.post(
            "/api/files/add",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200

    def test_add_doc_file(self, app_client, clean_state):
        data = {"files": (io.BytesIO(b"doc data"), "report.doc")}
        resp = app_client.post(
            "/api/files/add",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200

    def test_add_xlsx_file(self, app_client, clean_state):
        data = {"files": (io.BytesIO(b"xlsx data"), "spreadsheet.xlsx")}
        resp = app_client.post(
            "/api/files/add",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200


class TestRemoveFile:
    def test_no_id(self, app_client):
        resp = app_client.post(
            "/api/files/remove",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_empty_id(self, app_client):
        resp = app_client.post(
            "/api/files/remove",
            data=json.dumps({"id": ""}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_nonexistent_id(self, app_client, clean_state):
        resp = app_client.post(
            "/api/files/remove",
            data=json.dumps({"id": "nonexistent"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["files"] == []

    def test_remove_existing(self, app_client, clean_state):
        from utils.state import load_state, save_state

        state = load_state()
        state["files"] = [
            {"id": "file1", "name": "a.pdf", "path": "/a", "original_path": "/a"}
        ]
        save_state(state)
        resp = app_client.post(
            "/api/files/remove",
            data=json.dumps({"id": "file1"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert len(resp.get_json()["files"]) == 0


class TestReorderFiles:
    def test_invalid_order_type(self, app_client):
        resp = app_client.post(
            "/api/files/reorder",
            data=json.dumps({"order": "not a list"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_empty_order(self, app_client, clean_state):
        resp = app_client.post(
            "/api/files/reorder",
            data=json.dumps({"order": []}),
            content_type="application/json",
        )
        assert resp.status_code == 200

    def test_reorder(self, app_client, clean_state):
        from utils.state import load_state, save_state

        state = load_state()
        state["files"] = [
            {"id": "a", "name": "a.pdf"},
            {"id": "b", "name": "b.pdf"},
            {"id": "c", "name": "c.pdf"},
        ]
        save_state(state)
        resp = app_client.post(
            "/api/files/reorder",
            data=json.dumps({"order": ["c", "a", "b"]}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        files = resp.get_json()["files"]
        assert files[0]["id"] == "c"
        assert files[1]["id"] == "a"
        assert files[2]["id"] == "b"

    def test_partial_order(self, app_client, clean_state):
        from utils.state import load_state, save_state

        state = load_state()
        state["files"] = [
            {"id": "a", "name": "a.pdf"},
            {"id": "b", "name": "b.pdf"},
            {"id": "c", "name": "c.pdf"},
        ]
        save_state(state)
        resp = app_client.post(
            "/api/files/reorder",
            data=json.dumps({"order": ["b"]}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        files = resp.get_json()["files"]
        assert files[0]["id"] == "b"
