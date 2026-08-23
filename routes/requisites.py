"""
Blueprint: /api/requisites/* — Управление объектами строительства и их реквизитами
для автозаполнения формы АОСР.
"""

from flask import Blueprint, jsonify, request

from routes.core import logger
from utils.database import (
    add_object,
    delete_object,
    get_objects,
    get_requisites,
    save_requisites,
)

requisites_bp = Blueprint("requisites", __name__)


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _get_object_name(object_id: int) -> str | None:
    """Return the name of an object by its id, or None if not found."""
    objects = get_objects()
    for obj in objects:
        if obj["id"] == object_id:
            return obj["name"]
    return None


# ─── Objects CRUD ─────────────────────────────────────────────────────────────


@requisites_bp.route("/api/requisites/objects", methods=["GET"])
def list_objects():
    """GET /api/requisites/objects — list all construction objects."""
    try:
        objects = get_objects()
        return jsonify({"success": True, "objects": objects})
    except Exception as e:
        logger.exception("Ошибка получения списка объектов")
        return jsonify({"success": False, "error": str(e)}), 500


@requisites_bp.route("/api/requisites/objects", methods=["POST"])
def create_object():
    """POST /api/requisites/objects — create a new construction object.
    Expects JSON body: {"name": "..."}
    """
    try:
        data = request.get_json(silent=True)
        if not data or not data.get("name", "").strip():
            return jsonify({"success": False, "error": "Поле 'name' обязательно"}), 400

        obj_id = add_object(data["name"].strip())
        logger.info(f"Объект создан: id={obj_id}, name={data['name'].strip()}")
        return jsonify({"success": True, "id": obj_id})
    except Exception as e:
        logger.exception("Ошибка создания объекта")
        return jsonify({"success": False, "error": str(e)}), 500


@requisites_bp.route("/api/requisites/objects/<int:obj_id>", methods=["DELETE"])
def remove_object(obj_id: int):
    """DELETE /api/requisites/objects/<id> — delete a construction object."""
    try:
        deleted = delete_object(obj_id)
        if not deleted:
            return jsonify({"success": False, "error": "Объект не найден"}), 404

        logger.info(f"Объект удалён: id={obj_id}")
        return jsonify({"success": True})
    except Exception as e:
        logger.exception("Ошибка удаления объекта")
        return jsonify({"success": False, "error": str(e)}), 500


# ─── Requisites CRUD ──────────────────────────────────────────────────────────


@requisites_bp.route("/api/requisites/<int:object_id>", methods=["GET"])
def read_requisites(object_id: int):
    """GET /api/requisites/<object_id> — get requisites for an object."""
    try:
        reqs = get_requisites(object_id)
        if reqs is None:
            return jsonify({"success": True, "requisites": {}})

        return jsonify({"success": True, "requisites": reqs})
    except Exception as e:
        logger.exception(f"Ошибка получения реквизитов для object_id={object_id}")
        return jsonify({"success": False, "error": str(e)}), 500


@requisites_bp.route("/api/requisites/<int:object_id>", methods=["POST"])
def write_requisites(object_id: int):
    """POST /api/requisites/<object_id> — save/update requisites for an object.
    Expects JSON body with requisites fields.
    """
    try:
        data = request.get_json(silent=True)
        if not data:
            return (
                jsonify({"success": False, "error": "Тело запроса должно быть JSON"}),
                400,
            )

        save_requisites(object_id, data)
        logger.info(f"Реквизиты сохранены для object_id={object_id}")
        return jsonify({"success": True})
    except Exception as e:
        logger.exception(f"Ошибка сохранения реквизитов для object_id={object_id}")
        return jsonify({"success": False, "error": str(e)}), 500


# ─── AOCR autofill endpoint ───────────────────────────────────────────────────


@requisites_bp.route("/api/requisites/<int:object_id>/aocr", methods=["GET"])
def get_aocr_data(object_id: int):
    """GET /api/requisites/<object_id>/aocr — merged data ready for AOCP form autofill.

    Combines object name + requisites into the exact shape expected by
    POST /api/aocr/generate, with computed fields:
      - builder_continued   = builder_address + builder_phone
      - builder_continued2  = builder_sro
      - designer_continued  = designer_sro + designer_phone
    """
    try:
        # Object name
        object_name = _get_object_name(object_id)
        if object_name is None:
            return jsonify({"success": False, "error": "Объект не найден"}), 404

        # Requisites (may be empty dict if none saved yet)
        reqs = get_requisites(object_id) or {}

        # Computed fields — собираем СРО в читаемый текст как в акте
        def _fmt_sro(r: dict, prefix: str) -> str:
            num = r.get(f"{prefix}_sro_number", "").strip()
            name = r.get(f"{prefix}_sro_name", "").strip()
            ogrn = r.get(f"{prefix}_sro_ogrn", "").strip()
            inn = r.get(f"{prefix}_sro_inn", "").strip()
            parts = []
            if num:
                parts.append(num)
            if name:
                parts.append(name)
            if ogrn or inn:
                tail = []
                if ogrn:
                    tail.append(f"ОГРН {ogrn}")
                if inn:
                    tail.append(f"ИНН {inn}")
                parts.append(", ".join(tail))
            return ", ".join(parts) if parts else ""

        builder_continued = (reqs.get("builder_address", "") + " " + reqs.get("builder_phone", "")).strip()
        builder_continued2 = _fmt_sro(reqs, "builder")
        designer_continued = _fmt_sro(reqs, "designer")

        # Компоновка представителей: должность, ФИО, документ → одна строка
        def _fmt_rep(r: dict, prefix: str, default: str = "-") -> str:
            pos = r.get(f"{prefix}_position", "").strip()
            name = r.get(f"{prefix}_name", "").strip()
            doc = r.get(f"{prefix}_doc", "").strip()
            parts = [p for p in [pos, name, doc] if p]
            return ", ".join(parts) if parts else default

        # Sheet 1 fields
        result = {
            "success": True,
            "object_name": object_name,
            "developer_name": reqs.get("developer_name", ""),
            "developer_address": reqs.get("developer_address", ""),
            "builder_name": reqs.get("builder_name", ""),
            "builder_continued": builder_continued,
            "builder_continued2": builder_continued2,
            "designer_name": reqs.get("designer_name", ""),
            "designer_address": reqs.get("designer_address", ""),
            "designer_continued": designer_continued,
            "rep_developer": _fmt_rep(reqs, "rep_developer"),
            "rep_builder": _fmt_rep(reqs, "rep_builder"),
            "rep_builder_control": _fmt_rep(reqs, "rep_builder_ctrl"),
            "rep_designer": _fmt_rep(reqs, "rep_designer"),
            "rep_contractor": _fmt_rep(reqs, "rep_contractor"),
            "rep_others": _fmt_rep(reqs, "rep_others"),
            "rep_others_continued": reqs.get("rep_others_continued", ""),
        }

        # Sheet 2 fields (all pass-through from requisites, default empty)
        s2_fields = [
            "s2_work_name",
            "s2_project_docs",
            "s2_materials_used",
            "s2_documents_submitted",
            "s2_start_day",
            "s2_start_month",
            "s2_start_year",
            "s2_end_day",
            "s2_end_month",
            "s2_end_year",
            "s2_standards_l1",
            "s2_standards_l2",
            "s2_standards_l3",
            "s2_standards_l4",
            "s2_standards_l5",
            "s2_next_work",
            "s2_additional_info",
            "s2_copies",
            "s2_appendices",
            "s2_rep_developer",
            "s2_rep_builder",
            "s2_rep_builder_ctrl",
            "s2_rep_designer",
            "s2_rep_contractor",
            "s2_rep_others",
        ]
        for field in s2_fields:
            result[field] = reqs.get(field, "")

        return jsonify(result)
    except Exception as e:
        logger.exception(f"Ошибка сборки AOCR данных для object_id={object_id}")
        return jsonify({"success": False, "error": str(e)}), 500
