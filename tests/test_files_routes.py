"""
Tests for routes/files.py — file upload, list, reorder, delete.
"""

import io
import json
from pathlib import Path


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


class TestAddFilesFromDir:
    def test_missing_path(self, app_client):
        resp = app_client.post(
            "/api/files/add-from-dir",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_empty_path(self, app_client):
        resp = app_client.post(
            "/api/files/add-from-dir",
            data=json.dumps({"path": ""}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_nonexistent_folder(self, app_client):
        resp = app_client.post(
            "/api/files/add-from-dir",
            data=json.dumps({"path": "Z:/no/such/folder"}),
            content_type="application/json",
        )
        assert resp.status_code == 404

    def test_path_is_file(self, app_client, temp_dir):
        some_file = temp_dir / "x.pdf"
        some_file.write_bytes(b"pdf")
        resp = app_client.post(
            "/api/files/add-from-dir",
            data=json.dumps({"path": str(some_file)}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_import_flat_folder_sorted(self, app_client, clean_state, temp_dir):
        for name in ["03.pdf", "10.pdf", "01.pdf"]:
            (temp_dir / name).write_bytes(b"pdf")
        (temp_dir / "02.txt").write_text("not allowed")

        resp = app_client.post(
            "/api/files/add-from-dir",
            data=json.dumps({"path": str(temp_dir)}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["added"] == 3
        names = [f["name"] for f in data["files"]]
        assert names == ["01.pdf", "03.pdf", "10.pdf"]
        assert [r["name"] for r in data["rejected"]] == ["02.txt"]

    def test_import_recursive(self, app_client, clean_state, temp_dir):
        (temp_dir / "01.pdf").write_bytes(b"pdf")
        (temp_dir / "02.pdf").write_bytes(b"pdf")
        sub = temp_dir / "подпапка"
        sub.mkdir()
        (sub / "03.pdf").write_bytes(b"pdf")
        (sub / "04.pdf").write_bytes(b"pdf")

        resp = app_client.post(
            "/api/files/add-from-dir",
            data=json.dumps({"path": str(temp_dir)}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["added"] == 4
        assert [f["name"] for f in data["files"]] == [
            "01.pdf",
            "02.pdf",
            "03.pdf",
            "04.pdf",
        ]

    def test_import_sources_not_deleted(self, app_client, clean_state, temp_dir):
        src = temp_dir / "01.pdf"
        src.write_bytes(b"original")
        resp = app_client.post(
            "/api/files/add-from-dir",
            data=json.dumps({"path": str(temp_dir)}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert src.exists()
        entry = resp.get_json()["files"][0]
        assert Path(entry["path"]).exists()
        assert entry["name"] == "01.pdf"

    def test_import_empty_folder(self, app_client, clean_state, temp_dir):
        resp = app_client.post(
            "/api/files/add-from-dir",
            data=json.dumps({"path": str(temp_dir)}),
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert "Нет допустимых файлов" in resp.get_json()["error"]


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


class TestClearFiles:
    def test_clear_empty(self, app_client, clean_state):
        resp = app_client.post("/api/files/clear")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["files"] == []

    def test_clear_existing(self, app_client, clean_state, temp_dir):
        from utils.state import load_state, save_state

        existing = temp_dir / "old.pdf"
        existing.write_bytes(b"x")
        state = load_state()
        state["files"] = [
            {
                "id": "f1",
                "name": "old.pdf",
                "path": "/tmp",
                "original_path": str(existing),
            }
        ]
        save_state(state)

        resp = app_client.post("/api/files/clear")
        assert resp.status_code == 200
        assert resp.get_json()["files"] == []
        assert not existing.exists()
        assert load_state()["files"] == []


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
