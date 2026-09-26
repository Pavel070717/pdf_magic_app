"""
Blueprint: /api/materials/* — materials CRUD with PDF storage.
"""

import re
from pathlib import Path

from flask import Blueprint, jsonify, request, send_file

from routes.core import MATERIALS_DIR, logger, sanitize_text

materials_bp = Blueprint("materials", __name__)


def _parse_iso_date(value: str) -> str:
    """Принимает 'ГГГГ-ММ-ДД' или 'ДД.ММ.ГГГГ', возвращает 'ГГГГ-ММ-ДД'."""
    value = (value or "").strip().replace(".", "-")
    parts = [p.strip() for p in value.split("-") if p.strip()]
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        return ""
    if len(parts[0]) == 4:  # ГГГГ-ММ-ДД
        y, m, d = parts
    elif len(parts[2]) == 4:  # ДД-ММ-ГГГГ
        d, m, y = parts
    else:
        return ""
    try:
        if not (1 <= int(m) <= 12 and 1 <= int(d) <= 31 and int(y) >= 1900):
            return ""
    except ValueError:
        return ""
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"


def _readable_date(iso: str) -> str:
    if not iso or not len(iso.split("-")) == 3:
        return iso or ""
    y, m, d = iso.split("-")
    return f"{d}.{m}.{y}"


def _safe_name(text: str) -> str:
    return re.sub(r'[\\/*?:"<>|;]', "_", text)


def _next_file_number(folder: Path) -> str:
    from utils.database import count_materials_in_folder

    count = count_materials_in_folder(folder.name)
    for n in range(count + 1, count + 50):
        candidate = f"{n:02d}_"
        if not any(p.name.startswith(candidate) for p in folder.iterdir()):
            return f"{n:02d}"
    return f"{count + 1:02d}"


@materials_bp.route("/api/materials", methods=["GET"])
def get_materials():
    from utils.database import delete_material, get_all_materials, search_materials

    try:
        query = request.args.get("q", "").strip()
        if query:
            materials = search_materials(query)
        else:
            materials = get_all_materials()

        valid_materials = []
        for mat in materials:
            filepath = MATERIALS_DIR / mat["filename"]
            if filepath.exists():
                valid_materials.append(mat)
            else:
                delete_material(mat["id"])
                logger.info(f"Материал #{mat['id']} удалён: PDF не найден")

        return jsonify({"success": True, "materials": valid_materials})
    except Exception as e:
        logger.exception("Ошибка получения материалов")
        return jsonify({"success": False, "error": str(e)}), 500


@materials_bp.route("/api/materials/add", methods=["POST"])
def add_material_endpoint():
    from utils.database import add_material

    try:
        doc_name = sanitize_text(request.form.get("doc_name", ""))
        material_name = sanitize_text(request.form.get("material_name", ""))
        number = sanitize_text(request.form.get("number", ""))
        date = sanitize_text(request.form.get("date", ""))
        producer = sanitize_text(request.form.get("producer", ""))
        arrival_input = sanitize_text(request.form.get("arrival_date", ""))
        quantity_raw = sanitize_text(request.form.get("quantity", "0"))
        file = request.files.get("file")

        if not doc_name:
            return (
                jsonify({"success": False, "error": "Введите наименование документа"}),
                400,
            )
        if not material_name:
            return (
                jsonify({"success": False, "error": "Введите наименование материала"}),
                400,
            )
        arrival_date = _parse_iso_date(arrival_input)
        if not arrival_date:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Укажите дату поступления (дд.мм.гггг или гггг-мм-дд)",
                    }
                ),
                400,
            )
        try:
            quantity = float(str(quantity_raw or "0").replace(",", "."))
        except ValueError:
            quantity = 0.0
        if not file or file.filename == "":
            return jsonify({"success": False, "error": "Загрузите PDF-файл"}), 400
        if file.content_type and not file.content_type.startswith("application/pdf"):
            return (
                jsonify(
                    {"success": False, "error": "Можно загружать только PDF-файлы"}
                ),
                400,
            )

        materials_dir = MATERIALS_DIR
        materials_dir.mkdir(parents=True, exist_ok=True)

        safe_doc = _safe_name(doc_name)
        safe_mat = _safe_name(material_name)
        safe_num = _safe_name(number or "—")
        # Пустая дата документа = «без даты» (б/д). Слэш из токена заменяется
        # на "_", как и в остальных частях имени (на Windows "/" запрещён).
        safe_date = _safe_name(date or "б/д")

        # Папка поступления: ISO-дата — проводник сортирует старые → новые
        folder_name = arrival_date
        folder_path = materials_dir / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)

        num = _next_file_number(folder_path)
        new_filename = f"{num}_{safe_doc};{safe_mat};{safe_num};{safe_date}.pdf"
        filepath = folder_path / new_filename

        counter = 1
        while filepath.exists():
            new_filename = (
                f"{num}_{counter}_{safe_doc};{safe_mat};{safe_num};{safe_date}.pdf"
            )
            filepath = folder_path / new_filename
            counter += 1

        file.save(str(filepath))
        logger.info(f"PDF материала сохранён: {filepath}")

        stored_filename = f"{folder_name}/{filepath.name}"
        material_id = add_material(
            doc_name=doc_name,
            material_name=material_name,
            number=number,
            date=date,
            producer=producer,
            filename=stored_filename,
            original_filename=file.filename or "unknown.pdf",
            arrival_date=arrival_date,
            quantity=quantity,
            folder=folder_name,
        )

        return jsonify(
            {
                "success": True,
                "material_id": material_id,
                "filename": stored_filename,
                "folder": folder_name,
                "path": str(filepath),
            }
        )
    except Exception as e:
        logger.exception("Ошибка добавления материала")
        return jsonify({"success": False, "error": str(e)}), 500


@materials_bp.route("/api/materials/passports")
def get_passports():
    from utils.database import get_material_passports

    try:
        rows = get_material_passports()
        for r in rows:
            r["label"] = (
                (
                    f"{r['doc_name']} {r['material_name']}"
                    f" (№ {r['number'] or '—'})"
                    f" от {_readable_date(r['date']) or 'б/д'} · {r['producer']}"
                )
                .replace("  ", " ")
                .strip(" ·")
            )
        return jsonify({"success": True, "passports": rows})
    except Exception as e:
        logger.exception("Ошибка получения паспортов")
        return jsonify({"success": False, "error": str(e)}), 500


@materials_bp.route("/api/materials/reset", methods=["POST"])
def reset_materials_endpoint():
    from utils.database import reset_materials

    try:
        reset_materials()
        materials_dir = MATERIALS_DIR
        if materials_dir.exists():
            for item in materials_dir.iterdir():
                if item.is_dir():
                    import shutil

                    shutil.rmtree(item, ignore_errors=True)
                else:
                    item.unlink(missing_ok=True)
            materials_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Раздел «База материалов» обнулён")
        return jsonify({"success": True})
    except Exception as e:
        logger.exception("Ошибка сброса материалов")
        return jsonify({"success": False, "error": str(e)}), 500


@materials_bp.route("/api/materials/pdf/<int:material_id>")
def get_material_pdf(material_id):
    from utils.database import get_material

    try:
        material = get_material(material_id)
        if not material:
            return jsonify({"success": False, "error": "Материал не найден"}), 404

        filepath = (MATERIALS_DIR / material["filename"]).resolve()
        materials_dir_resolved = MATERIALS_DIR.resolve()
        if not str(filepath).startswith(str(materials_dir_resolved)):
            return jsonify({"success": False, "error": "Недопустимый путь"}), 400
        if not filepath.exists():
            return jsonify({"success": False, "error": "PDF-файл не найден"}), 404

        return send_file(str(filepath), mimetype="application/pdf")
    except Exception as e:
        logger.exception("Ошибка получения PDF")
        return jsonify({"success": False, "error": str(e)}), 500


@materials_bp.route("/api/materials/<int:material_id>", methods=["DELETE"])
def delete_material_endpoint(material_id):
    from utils.database import delete_material, get_material

    try:
        material = get_material(material_id)
        if not material:
            return jsonify({"success": False, "error": "Материал не найден"}), 404

        filepath = (MATERIALS_DIR / material["filename"]).resolve()
        if not str(filepath).startswith(str(MATERIALS_DIR.resolve())):
            return jsonify({"success": False, "error": "Недопустимый путь"}), 400
        if filepath.exists():
            filepath.unlink()
            logger.info(f"PDF материала удалён: {filepath}")

        if delete_material(material_id):
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "Не удалось удалить запись"}), 500
    except Exception as e:
        logger.exception("Ошибка удаления материала")
        return jsonify({"success": False, "error": str(e)}), 500
