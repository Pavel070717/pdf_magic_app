"""
Blueprint: /api/materials/* — materials CRUD with PDF storage.
"""

import re

from flask import Blueprint, jsonify, request, send_file

from routes.core import MATERIALS_DIR, logger, sanitize_text

materials_bp = Blueprint("materials", __name__)


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
        if not file or file.filename == "":
            return jsonify({"success": False, "error": "Загрузите PDF-файл"}), 400
        if file.content_type and not file.content_type.startswith("application/pdf"):
            return (
                jsonify({"success": False, "error": "Можно загружать только PDF-файлы"}),
                400,
            )

        materials_dir = MATERIALS_DIR
        materials_dir.mkdir(parents=True, exist_ok=True)

        def safe_name(text: str) -> str:
            return re.sub(r'[\\/*?:"<>|;]', "_", text)

        safe_doc = safe_name(doc_name)
        safe_mat = safe_name(material_name)
        safe_num = safe_name(number or "—")
        safe_date = safe_name(date or "—")
        new_filename = f"{safe_doc};{safe_mat};{safe_num};{safe_date}.pdf"
        filepath = materials_dir / new_filename

        counter = 1
        while filepath.exists():
            new_filename = f"{safe_doc};{safe_mat};{safe_num};{safe_date}_{counter}.pdf"
            filepath = materials_dir / new_filename
            counter += 1

        file.save(str(filepath))
        logger.info(f"PDF материала сохранён: {filepath}")

        material_id = add_material(
            doc_name=doc_name,
            material_name=material_name,
            number=number,
            date=date,
            producer=producer,
            filename=new_filename,
            original_filename=file.filename or "unknown.pdf",
        )

        return jsonify(
            {
                "success": True,
                "material_id": material_id,
                "filename": new_filename,
                "path": str(filepath),
            }
        )
    except Exception as e:
        logger.exception("Ошибка добавления материала")
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
