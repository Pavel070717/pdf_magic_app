"""
Tests for routes/materials.py — materials CRUD with PDF storage.
"""

import io
import json
from pathlib import Path
from unittest.mock import patch


class TestGetMaterials:
    def test_empty_list(self, app_client, temp_db_all):
        resp = app_client.get("/api/materials")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert isinstance(data["materials"], list)

    def test_search_empty(self, app_client, temp_db_all):
        resp = app_client.get("/api/materials?q=")
        assert resp.status_code == 200

    def test_search_with_query(self, app_client, temp_db_all):
        resp = app_client.get("/api/materials?q=steel")
        assert resp.status_code == 200


class TestAddMaterial:
    def test_missing_doc_name(self, app_client, temp_db_all):
        resp = app_client.post(
            "/api/materials/add",
            data={"material_name": "Steel"},
        )
        assert resp.status_code == 400
        assert "документа" in resp.get_json()["error"]

    def test_missing_material_name(self, app_client, temp_db_all):
        resp = app_client.post(
            "/api/materials/add",
            data={"doc_name": "Certificate"},
        )
        assert resp.status_code == 400
        assert "материала" in resp.get_json()["error"]

    def test_missing_file(self, app_client, temp_db_all):
        resp = app_client.post(
            "/api/materials/add",
            data={"doc_name": "Cert", "material_name": "Steel"},
        )
        assert resp.status_code == 400
        assert "PDF" in resp.get_json()["error"]

    def test_valid_add(self, app_client, temp_db_all):
        data = {
            "doc_name": "Certificate",
            "material_name": "Steel",
            "number": "N-001",
            "date": "01.01.2026",
            "producer": "Steel Corp",
            "file": (io.BytesIO(b"%PDF-1.4 fake"), "cert.pdf"),
        }
        resp = app_client.post(
            "/api/materials/add",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        result = resp.get_json()
        assert result["success"] is True
        assert "material_id" in result

    def test_non_pdf_content_type(self, app_client, temp_db_all):
        data = {
            "doc_name": "Doc",
            "material_name": "Mat",
            "file": (io.BytesIO(b"not pdf"), "file.txt"),
        }
        resp = app_client.post(
            "/api/materials/add",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400

    def test_add_without_optional_fields(self, app_client, temp_db_all):
        data = {
            "doc_name": "Doc",
            "material_name": "Mat",
            "file": (io.BytesIO(b"%PDF-1.4"), "doc.pdf"),
        }
        resp = app_client.post(
            "/api/materials/add",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200


class TestGetMaterialPDF:
    def test_nonexistent_material(self, app_client, temp_db_all):
        resp = app_client.get("/api/materials/pdf/99999")
        assert resp.status_code == 404

    def test_material_pdf_not_found(self, app_client, temp_db_all):
        from utils.database import add_material

        mat_id = add_material(
            doc_name="Doc",
            material_name="Mat",
            number="N-1",
            date="01.01.2026",
            producer="Corp",
            filename="nonexistent.pdf",
            original_filename="doc.pdf",
        )
        resp = app_client.get(f"/api/materials/pdf/{mat_id}")
        assert resp.status_code == 404


class TestDeleteMaterial:
    def test_nonexistent(self, app_client, temp_db_all):
        resp = app_client.delete("/api/materials/99999")
        assert resp.status_code == 404

    def test_delete_existing(self, app_client, temp_db_all, temp_dir):
        from utils.database import add_material

        fake_pdf = temp_dir / "material.pdf"
        fake_pdf.write_bytes(b"%PDF-1.4 fake")
        mat_id = add_material(
            doc_name="Doc",
            material_name="Mat",
            number="N-1",
            date="01.01.2026",
            producer="Corp",
            filename=str(fake_pdf.name),
            original_filename="doc.pdf",
        )
        with patch("routes.materials.MATERIALS_DIR", temp_dir):
            resp = app_client.delete(f"/api/materials/{mat_id}")
            assert resp.status_code == 200
