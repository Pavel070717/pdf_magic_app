"""
Blueprint: /api/materials/* — materials CRUD with PDF storage.
"""

import os
import re
import shutil
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
        candidate = f"{n:02d}."
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
        producer = sanitize_text(request.form.get("producer", ""))
        unit = sanitize_text(request.form.get("unit", ""))
        reason = sanitize_text(request.form.get("reason", "")).strip()
        copy_from = sanitize_text(request.form.get("copy_from", "")).strip()
        arrival_input = sanitize_text(request.form.get("arrival_date", ""))
        quantity_raw = sanitize_text(request.form.get("quantity", "0"))

        # Паспортов может быть несколько: у каждого свой номер, дата и файл(ы).
        number_rows = [sanitize_text(n) for n in request.form.getlist("number")]
        date_rows = [sanitize_text(d) for d in request.form.getlist("date")]
        if not number_rows:
            number_rows = [""]
        if not date_rows:
            date_rows = [""]
        while len(date_rows) < len(number_rows):
            date_rows.append("")

        def _row_files(i: int):
            fs = [f for f in request.files.getlist(f"file_{i}") if f and f.filename]
            if i == 0:
                fs += [f for f in request.files.getlist("file") if f and f.filename]
            return fs

        uploaded = [(i, f) for i in range(len(number_rows)) for f in _row_files(i)]
        has_file = bool(uploaded)

        # Файл можно не прикреплять, если выбран паспорт из ранее добавленных:
        # его сопроводительный документ копируется в новую папку даты поступления.
        copy_source_path = None
        if not has_file and copy_from.isdigit():
            from utils.database import get_material

            src = get_material(int(copy_from))
            if src and src.get("filename"):
                src_path = MATERIALS_DIR / src["filename"]
                if src_path.exists() and not src_path.name.lower().endswith(".txt"):
                    copy_source_path = src_path
        has_file = has_file or copy_source_path is not None

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
        if not has_file and not reason:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": (
                            "Прикрепите сопроводительный документ или укажите "
                            "причину его отсутствия"
                        ),
                    }
                ),
                400,
            )

        materials_dir = MATERIALS_DIR
        materials_dir.mkdir(parents=True, exist_ok=True)

        # Имя файла начинается с «Документ Материал» (через пробел), далее
        # ;№ Номер;Дата — материал входит в имя, как просит пользователь.
        safe_doc = _safe_name(f"{doc_name} {material_name}".strip())

        def _safe_tokens(num_text: str, date_text: str):
            # Уже введённый «№» не дублируется; пустой номер = «—».
            number_clean = num_text.strip()
            if number_clean and not number_clean.startswith("№"):
                number_clean = "№ " + number_clean
            safe_num = _safe_name(number_clean or "—")
            # Дата документа в имени файла — в читаемом виде «ДД.ММ.ГГГГ»,
            # пустая дата = «без даты».
            date_iso = _parse_iso_date(date_text)
            safe_date = _safe_name(_readable_date(date_iso) if date_iso else "без даты")
            return safe_num, safe_date

        def _save_one(ext: str, num_text: str, date_text: str) -> int:
            safe_num, safe_date = _safe_tokens(num_text, date_text)
            folder_path = materials_dir / arrival_date
            folder_path.mkdir(parents=True, exist_ok=True)
            num = _next_file_number(folder_path)
            base = f"{num}.{safe_doc};{safe_num};{safe_date}"
            new_filename = f"{base}{ext}"
            filepath = folder_path / new_filename
            counter = 1
            while filepath.exists():
                new_filename = f"{num}.{counter}.{safe_doc};{safe_num};{safe_date}{ext}"
                filepath = folder_path / new_filename
                counter += 1
            stored_filename = f"{arrival_date}/{filepath.name}"
            material_id = add_material(
                doc_name=doc_name,
                material_name=material_name,
                number=num_text,
                date=date_text,
                producer=producer,
                filename=stored_filename,
                original_filename=f"{base}{ext}",
                arrival_date=arrival_date,
                quantity=quantity,
                folder=arrival_date,
                unit=unit,
                reason=reason,
            )
            return filepath, stored_filename, material_id

        created_ids = []
        saved_paths = []
        if uploaded:
            for i, f in uploaded:
                ext = os.path.splitext(f.filename or "")[1].lower() or ".pdf"
                filepath, stored_filename, material_id = _save_one(
                    ext, number_rows[i], date_rows[i]
                )
                f.save(str(filepath))
                logger.info(f"Файл материала сохранён: {filepath}")
                created_ids.append(material_id)
                saved_paths.append(stored_filename)
        elif copy_source_path is not None:
            ext = os.path.splitext(copy_source_path.name)[1].lower() or ".pdf"
            filepath, stored_filename, material_id = _save_one(
                ext, number_rows[0], date_rows[0]
            )
            shutil.copyfile(copy_source_path, filepath)
            logger.info(f"Файл скопирован из ранее добавленного: {filepath}")
            created_ids.append(material_id)
            saved_paths.append(stored_filename)
        else:
            filepath, stored_filename, material_id = _save_one(
                ".txt", number_rows[0], date_rows[0]
            )
            filepath.write_text(reason, encoding="utf-8")
            logger.info(f"txt причины отсутствия сохранён: {filepath}")
            created_ids.append(material_id)
            saved_paths.append(stored_filename)

        return jsonify(
            {
                "success": True,
                "material_id": created_ids[0] if created_ids else 0,
                "count": len(created_ids),
                "filenames": saved_paths,
                "folder": arrival_date,
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
            unit_part = f" · {r['unit']}" if r.get("unit") else ""
            r["label"] = (
                (
                    f"{r['doc_name']} {r['material_name']}{unit_part}"
                    f" (№ {r['number'] or '—'})"
                    f" от {_readable_date(r['date']) or 'без даты'} · {r['producer']}"
                )
                .replace("  ", " ")
                .strip(" ·")
            )
        return jsonify({"success": True, "passports": rows})
    except Exception as e:
        logger.exception("Ошибка получения паспортов")
        return jsonify({"success": False, "error": str(e)}), 500


@materials_bp.route("/api/materials/units")
def get_units():
    from utils.database import get_material_units

    try:
        return jsonify({"success": True, "units": get_material_units()})
    except Exception as e:
        logger.exception("Ошибка получения единиц измерения")
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
            return jsonify({"success": False, "error": "Файл не найден"}), 404

        return send_file(str(filepath))
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
