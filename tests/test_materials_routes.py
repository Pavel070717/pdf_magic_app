"""
Tests for routes/materials.py — materials CRUD with PDF storage.
"""

import io
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

    def test_missing_arrival_date(self, app_client, temp_db_all):
        resp = app_client.post(
            "/api/materials/add",
            data={"doc_name": "Cert", "material_name": "Steel"},
        )
        assert resp.status_code == 400
        assert "поступления" in resp.get_json()["error"]

    def test_missing_file(self, app_client, temp_db_all, temp_dir):
        with patch("routes.materials.MATERIALS_DIR", temp_dir):
            resp = app_client.post(
                "/api/materials/add",
                data={
                    "doc_name": "Cert",
                    "material_name": "Steel",
                    "arrival_date": "2026-09-26",
                },
            )
        assert resp.status_code == 400
        assert "PDF" in resp.get_json()["error"]

    def test_valid_add(self, app_client, temp_db_all, temp_dir):
        with patch("routes.materials.MATERIALS_DIR", temp_dir):
            data = {
                "doc_name": "Certificate",
                "material_name": "Steel",
                "number": "N-001",
                "date": "2026-01-01",
                "producer": "Steel Corp",
                "arrival_date": "26.09.2026",  # ДД.ММ.ГГГГ → папка 2026-09-26
                "quantity": "12.5",
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
        assert result["folder"] == "2026-09-26"
        folder = temp_dir / "2026-09-26"
        assert folder.is_dir()
        files = list(folder.glob("*.pdf"))
        assert len(files) == 1
        assert files[0].name.startswith("01_")

    def test_same_day_numbering(self, app_client, temp_db_all, temp_dir):
        """Два материала в один день — файлы 01_, 02_ в одной папке."""
        with patch("routes.materials.MATERIALS_DIR", temp_dir):
            for name in ("Steel", "Concrete"):
                resp = app_client.post(
                    "/api/materials/add",
                    data={
                        "doc_name": "Cert",
                        "material_name": name,
                        "arrival_date": "2026-09-26",
                        "quantity": "5",
                        "file": (io.BytesIO(b"%PDF-1.4 fake"), f"{name}.pdf"),
                    },
                    content_type="multipart/form-data",
                )
                assert resp.status_code == 200
        names = sorted(p.name for p in (temp_dir / "2026-09-26").glob("*.pdf"))
        assert names[0].startswith("01_") and names[1].startswith("02_")

    def test_same_passport_other_day_new_folder(
        self, app_client, temp_db_all, temp_dir
    ):
        """Тот же паспорт в другой день — появляется в папке новой даты."""
        with patch("routes.materials.MATERIALS_DIR", temp_dir):
            for day in ("2026-09-26", "2026-10-05"):
                resp = app_client.post(
                    "/api/materials/add",
                    data={
                        "doc_name": "Сертификат качества",
                        "material_name": "Сваи",
                        "number": "255",
                        "arrival_date": day,
                        "quantity": "10",
                        "file": (io.BytesIO(b"%PDF-1.4 fake"), "svai.pdf"),
                    },
                    content_type="multipart/form-data",
                )
                assert resp.status_code == 200
        assert (temp_dir / "2026-09-26").is_dir()
        assert (temp_dir / "2026-10-05").is_dir()
        assert len(list((temp_dir / "2026-10-05").glob("*.pdf"))) == 1

    def test_folders_sortable_iso(self, app_client, temp_db_all, temp_dir):
        """Имена папок — ISO-даты, проводник сортирует старые → новые."""
        with patch("routes.materials.MATERIALS_DIR", temp_dir):
            for day in ("2025-12-01", "2026-09-26", "2026-01-15"):
                resp = app_client.post(
                    "/api/materials/add",
                    data={
                        "doc_name": "Cert",
                        "material_name": "X",
                        "arrival_date": day,
                        "file": (io.BytesIO(b"%PDF-1.4 fake"), "x.pdf"),
                    },
                    content_type="multipart/form-data",
                )
                assert resp.status_code == 200
        folders = sorted(p.name for p in temp_dir.iterdir() if p.is_dir())
        assert folders == ["2025-12-01", "2026-01-15", "2026-09-26"]

    def test_non_pdf_content_type(self, app_client, temp_db_all, temp_dir):
        with patch("routes.materials.MATERIALS_DIR", temp_dir):
            data = {
                "doc_name": "Doc",
                "material_name": "Mat",
                "arrival_date": "2026-09-26",
                "file": (io.BytesIO(b"not pdf"), "file.txt"),
            }
            resp = app_client.post(
                "/api/materials/add",
                data=data,
                content_type="multipart/form-data",
            )
        assert resp.status_code == 400

    def test_add_without_optional_fields(self, app_client, temp_db_all, temp_dir):
        data = {
            "doc_name": "Doc",
            "material_name": "Mat",
            "arrival_date": "2026-09-26",
            "file": (io.BytesIO(b"%PDF-1.4"), "doc.pdf"),
        }
        with patch("routes.materials.MATERIALS_DIR", temp_dir):
            resp = app_client.post(
                "/api/materials/add",
                data=data,
                content_type="multipart/form-data",
            )
        assert resp.status_code == 200


class TestPassports:
    def test_passports_list_groups_unique(self, app_client, temp_db_all, temp_dir):
        with patch("routes.materials.MATERIALS_DIR", temp_dir):
            for day in ("2026-09-26", "2026-10-05"):
                app_client.post(
                    "/api/materials/add",
                    data={
                        "doc_name": "Сертификат",
                        "material_name": "Сваи",
                        "number": "255",
                        "date": "2026-01-01",
                        "producer": "Завод",
                        "arrival_date": day,
                        "file": (io.BytesIO(b"%PDF-1.4 fake"), "svai.pdf"),
                    },
                    content_type="multipart/form-data",
                )
            app_client.post(
                "/api/materials/add",
                data={
                    "doc_name": "Сертификат",
                    "material_name": "Арматура",
                    "number": "300",
                    "date": "2026-02-02",
                    "producer": "Завод",
                    "arrival_date": "2026-09-26",
                    "file": (io.BytesIO(b"%PDF-1.4 fake"), "arm.pdf"),
                },
                content_type="multipart/form-data",
            )
        data = app_client.get("/api/materials/passports").get_json()
        assert data["success"] is True
        passports = data["passports"]
        assert len(passports) == 2
        labels = [p["label"] for p in passports]
        assert any("Сваи" in label and "255" in label for label in labels)
        assert any("Арматура" in label and "300" in label for label in labels)


class TestResetMaterials:
    def test_reset_clears_section(self, app_client, temp_db_all, temp_dir):
        from utils.database import get_all_materials

        with patch("routes.materials.MATERIALS_DIR", temp_dir):
            app_client.post(
                "/api/materials/add",
                data={
                    "doc_name": "Cert",
                    "material_name": "X",
                    "arrival_date": "2026-09-26",
                    "file": (io.BytesIO(b"%PDF-1.4 fake"), "x.pdf"),
                },
                content_type="multipart/form-data",
            )
            assert len(get_all_materials()) == 1
            (temp_dir / "2026-09-26" / "x.pdf").write_bytes(b"%PDF-1.4")

            resp = app_client.post("/api/materials/reset")
            assert resp.get_json()["success"] is True

            assert get_all_materials() == []
            assert list(temp_dir.iterdir()) == []


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
