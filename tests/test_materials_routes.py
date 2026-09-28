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

    def test_missing_file_and_reason(self, app_client, temp_db_all, temp_dir):
        """Без файла и без причины — материал не добавляется."""
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
        assert "причин" in resp.get_json()["error"]

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
        assert files[0].name.startswith("01.")

    def test_same_day_numbering(self, app_client, temp_db_all, temp_dir):
        """Два материала в один день — файлы 01., 02. в одной папке."""
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
        assert names[0].startswith("01.") and names[1].startswith("02.")

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

    def test_no_date_uses_bez_daty_token(self, app_client, temp_db_all, temp_dir):
        """Пустая дата документа → в имени файла токен «без даты»."""
        with patch("routes.materials.MATERIALS_DIR", temp_dir):
            resp = app_client.post(
                "/api/materials/add",
                data={
                    "doc_name": "Сертификат",
                    "material_name": "Сваи",
                    "arrival_date": "2026-09-26",
                    "file": (io.BytesIO(b"%PDF-1.4 fake"), "svai.pdf"),
                },
                content_type="multipart/form-data",
            )
            assert resp.status_code == 200
        files = list((temp_dir / "2026-09-26").glob("*.pdf"))
        assert len(files) == 1
        assert ";без даты.pdf" in files[0].name

    def test_slash_in_name_becomes_underscore(self, app_client, temp_db_all, temp_dir):
        """'/' в наименовании документа/материала на выходе заменяется на '_'."""
        with patch("routes.materials.MATERIALS_DIR", temp_dir):
            resp = app_client.post(
                "/api/materials/add",
                data={
                    "doc_name": "Акт/Приёмка",
                    "material_name": "Бетон/раствор",
                    "number": "255/1",
                    "arrival_date": "2026-09-26",
                    "file": (io.BytesIO(b"%PDF-1.4 fake"), "x.pdf"),
                },
                content_type="multipart/form-data",
            )
            assert resp.status_code == 200
        files = list((temp_dir / "2026-09-26").glob("*.pdf"))
        assert len(files) == 1
        name = files[0].name
        assert "/" not in name
        assert name.startswith("01.Акт_Приёмка Бетон_раствор;№ 255_1;без даты.")

    def test_multiple_passports_saved_separately(
        self, app_client, temp_db_all, temp_dir
    ):
        """Несколько паспортов одного материала → отдельная запись и свой
        порядковый номер на каждый файл."""
        from utils.database import get_all_materials

        with patch("routes.materials.MATERIALS_DIR", temp_dir):
            resp = app_client.post(
                "/api/materials/add",
                data={
                    "doc_name": "Паспорт на песок",
                    "material_name": "Песок карьера Ламга",
                    "number": "12",
                    "arrival_date": "2026-09-26",
                    "file": [
                        (io.BytesIO(b"%PDF-1.4 fake"), "pass1.pdf"),
                        (io.BytesIO(b"%PDF-1.4 fake"), "pass2.pdf"),
                    ],
                },
                content_type="multipart/form-data",
            )
            assert resp.status_code == 200
            assert resp.get_json()["count"] == 2
        files = sorted(p.name for p in (temp_dir / "2026-09-26").glob("*.pdf"))
        assert len(files) == 2
        assert files[0].startswith("01.")
        assert files[1].startswith("02.")
        assert len(get_all_materials()) == 2

    def test_filename_doc_plus_material_number_with_num_prefix(
        self, app_client, temp_db_all, temp_dir
    ):
        """Имя файла начинается с «Документ Материал» (через пробел), перед
        номером добавляется «№ », дата в имени — «ДД.ММ.ГГГГ», а уже
        введённый «№» не дублируется."""
        with patch("routes.materials.MATERIALS_DIR", temp_dir):
            resp = app_client.post(
                "/api/materials/add",
                data={
                    "doc_name": "Паспорт",
                    "material_name": "на песок из карьера Ламга",
                    "number": "15",
                    "date": "2026-08-03",
                    "arrival_date": "2026-09-26",
                    "file": (io.BytesIO(b"%PDF-1.4 fake"), "x.pdf"),
                },
                content_type="multipart/form-data",
            )
            assert resp.status_code == 200
        files = list((temp_dir / "2026-09-26").glob("*.pdf"))
        assert len(files) == 1
        name = files[0].name
        assert name.startswith(
            "01.Паспорт на песок из карьера Ламга;№ 15;03.08.2026.pdf"
        )

        with patch("routes.materials.MATERIALS_DIR", temp_dir):
            resp = app_client.post(
                "/api/materials/add",
                data={
                    "doc_name": "Паспорт",
                    "material_name": "на песок из карьера Ламга",
                    "number": "№ 90",
                    "date": "2026-09-02",
                    "arrival_date": "2026-09-26",
                    "file": (io.BytesIO(b"%PDF-1.4 fake"), "y.pdf"),
                },
                content_type="multipart/form-data",
            )
            assert resp.status_code == 200
        files = sorted(p.name for p in (temp_dir / "2026-09-26").glob("*.pdf"))
        assert files[1].startswith("02.")
        assert "№ №" not in files[1]
        assert ";№ 90;02.09.2026.pdf" in files[1]

    def test_readd_passport_copies_file_from_previous(
        self, app_client, temp_db_all, temp_dir
    ):
        """Повторное добавление паспорта (copy_from = id ранее добавленного)
        без файла: сопроводительный файл копируется в папку новой даты,
        поле не требуется и причина не нужна."""
        from utils.database import get_all_materials

        with patch("routes.materials.MATERIALS_DIR", temp_dir):
            first = app_client.post(
                "/api/materials/add",
                data={
                    "doc_name": "Паспорт",
                    "material_name": "на песок из карьера Ламга",
                    "number": "15",
                    "date": "2026-08-03",
                    "arrival_date": "2026-09-26",
                    "file": (io.BytesIO(b"%PDF-1.4 fake content"), "pass.pdf"),
                },
                content_type="multipart/form-data",
            )
            assert first.status_code == 200
            src_id = first.get_json()["material_id"]

            second = app_client.post(
                "/api/materials/add",
                data={
                    "doc_name": "Паспорт",
                    "material_name": "на песок из карьера Ламга",
                    "number": "15",
                    "date": "2026-08-03",
                    "arrival_date": "2026-10-05",
                    "copy_from": str(src_id),
                },
                content_type="multipart/form-data",
            )
            assert second.status_code == 200
            assert second.get_json()["count"] == 1

        copied = list((temp_dir / "2026-10-05").glob("*.pdf"))
        assert len(copied) == 1
        assert copied[0].read_bytes() == b"%PDF-1.4 fake content"
        assert copied[0].name.startswith("01.")
        assert len(get_all_materials()) == 2

    def test_multiple_passports_distinct_number_date_file(
        self, app_client, temp_db_all, temp_dir
    ):
        """Несколько паспортов в одном добавлении (file_0/file_1): у каждого
        свой номер и дата — файлы именуются по своим номерам/датам."""
        from utils.database import get_all_materials

        with patch("routes.materials.MATERIALS_DIR", temp_dir):
            resp = app_client.post(
                "/api/materials/add",
                data={
                    "doc_name": "Паспорт на песок",
                    "material_name": "Песок из карьера Ламга",
                    "number": ["15", "16"],
                    "date": ["2026-08-03", "2026-08-10"],
                    "arrival_date": "2026-09-26",
                    "file_0": (io.BytesIO(b"%PDF-1.4 fake A"), "a.pdf"),
                    "file_1": (io.BytesIO(b"%PDF-1.4 fake B"), "b.pdf"),
                },
                content_type="multipart/form-data",
            )
            assert resp.status_code == 200
            assert resp.get_json()["count"] == 2
        files = sorted(p.name for p in (temp_dir / "2026-09-26").glob("*.pdf"))
        assert len(files) == 2
        assert files[0].startswith(
            "01.Паспорт на песок Песок из карьера Ламга;№ 15;03.08.2026."
        )
        assert files[1].startswith(
            "02.Паспорт на песок Песок из карьера Ламга;№ 16;10.08.2026."
        )
        assert len(get_all_materials()) == 2

    def test_any_file_type_accepted(self, app_client, temp_db_all, temp_dir):
        """Прикреплять можно любой файл (не только PDF) — сохраняется с его
        расширением."""
        with patch("routes.materials.MATERIALS_DIR", temp_dir):
            data = {
                "doc_name": "Фото",
                "material_name": "Узел",
                "arrival_date": "2026-09-26",
                "file": (io.BytesIO(b"\xff\xd8\xff\xe0 jpeg"), "foto.jpg"),
            }
            resp = app_client.post(
                "/api/materials/add",
                data=data,
                content_type="multipart/form-data",
            )
        assert resp.status_code == 200
        files = list((temp_dir / "2026-09-26").glob("*.jpg"))
        assert len(files) == 1
        assert files[0].name.startswith("01.")

    def test_no_file_with_reason_creates_txt(self, app_client, temp_db_all, temp_dir):
        """Без файла, но с причиной: txt с причинами появляется в папке даты,
        пронумерован, содержимое = введённая причина; запись в БД хранит причину."""
        from utils.database import get_all_materials

        with patch("routes.materials.MATERIALS_DIR", temp_dir):
            resp = app_client.post(
                "/api/materials/add",
                data={
                    "doc_name": "Сертификат качества",
                    "material_name": "Арматура А400",
                    "number": "77",
                    "reason": "документация уйдет с поставкой завтра",
                    "arrival_date": "2026-09-26",
                },
                content_type="multipart/form-data",
            )
            assert resp.status_code == 200
            folder = temp_dir / "2026-09-26"
            assert folder.is_dir()
            txts = list(folder.glob("*.txt"))
            assert len(txts) == 1
            assert txts[0].name.startswith("01.")
            assert txts[0].read_text(encoding="utf-8").strip() == (
                "документация уйдет с поставкой завтра"
            )
            mats = get_all_materials()
            assert len(mats) == 1
            assert mats[0]["reason"] == "документация уйдет с поставкой завтра"

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


class TestUnits:
    def test_units_empty(self, app_client, temp_db_all):
        resp = app_client.get("/api/materials/units")
        assert resp.status_code == 200
        assert resp.get_json()["units"] == []

    def test_units_collect_previously_entered(self, app_client, temp_db_all, temp_dir):
        """Ранее введённые единицы попадают в выпадающий список (уникальные)."""
        with patch("routes.materials.MATERIALS_DIR", temp_dir):
            for unit in ("шт", "т", "шт"):
                resp = app_client.post(
                    "/api/materials/add",
                    data={
                        "doc_name": "Сертификат",
                        "material_name": "Сваи",
                        "unit": unit,
                        "arrival_date": "2026-09-26",
                        "file": (io.BytesIO(b"%PDF-1.4 fake"), "x.pdf"),
                    },
                    content_type="multipart/form-data",
                )
                assert resp.status_code == 200
        data = app_client.get("/api/materials/units").get_json()
        assert data["success"] is True
        assert data["units"] == ["т", "шт"]  # отсортировано, без повторов

    def test_add_saves_unit(self, app_client, temp_db_all, temp_dir):
        from utils.database import get_all_materials

        with patch("routes.materials.MATERIALS_DIR", temp_dir):
            resp = app_client.post(
                "/api/materials/add",
                data={
                    "doc_name": "Сертификат",
                    "material_name": "Сваи",
                    "unit": "шт",
                    "arrival_date": "2026-09-26",
                    "file": (io.BytesIO(b"%PDF-1.4 fake"), "x.pdf"),
                },
                content_type="multipart/form-data",
            )
            assert resp.status_code == 200
        mats = get_all_materials()
        assert len(mats) == 1
        assert mats[0]["unit"] == "шт"


class TestPassports:
    def test_passport_label_has_unit(self, app_client, temp_db_all, temp_dir):
        """Единица измерения видна в подписи паспорта."""
        with patch("routes.materials.MATERIALS_DIR", temp_dir):
            app_client.post(
                "/api/materials/add",
                data={
                    "doc_name": "Сертификат",
                    "material_name": "Сваи",
                    "unit": "шт",
                    "number": "255",
                    "arrival_date": "2026-09-26",
                    "file": (io.BytesIO(b"%PDF-1.4 fake"), "svai.pdf"),
                },
                content_type="multipart/form-data",
            )
        data = app_client.get("/api/materials/passports").get_json()
        assert data["success"] is True
        assert "· шт" in data["passports"][0]["label"]

    def test_passport_without_date_label(self, app_client, temp_db_all, temp_dir):
        """Паспорт без даты в выпадающем списке показывается как «от без даты»."""
        with patch("routes.materials.MATERIALS_DIR", temp_dir):
            app_client.post(
                "/api/materials/add",
                data={
                    "doc_name": "Сертификат",
                    "material_name": "Сваи",
                    "number": "255",
                    "arrival_date": "2026-09-26",
                    "file": (io.BytesIO(b"%PDF-1.4 fake"), "svai.pdf"),
                },
                content_type="multipart/form-data",
            )
        data = app_client.get("/api/materials/passports").get_json()
        assert data["success"] is True
        assert len(data["passports"]) == 1
        assert "без даты" in data["passports"][0]["label"]

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
