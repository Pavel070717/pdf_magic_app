"""
Blueprint: /api/magic/* — file copy, numbering, and Excel registry generation.
"""

import os
import shutil
import threading
import time
from pathlib import Path

from flask import Blueprint, jsonify, request

from routes.core import _magic_lock, get_app_dir, logger, magic_progress
from utils.excel_registry import generate_excel_registry
from utils.state import load_state, save_state

magic_bp = Blueprint("magic", __name__)

_jobs: dict[str, dict] = {}  # аннотация типа добавлена


def _get_job_id():
    return threading.current_thread().ident


def generate_numbered_filename(start_number: int, name: str, ext: str) -> str:
    """Сквозная нумерация: '01.Имя.ext'"""
    num = str(start_number).zfill(2)
    return f"{num}.{name}{ext}"


@magic_bp.route("/api/magic/start", methods=["POST"])
def start_magic():
    """Start file copy/numbering worker in background thread."""
    data = request.get_json(silent=True) or {}
    target_dir = data.get("target_dir", "")
    if target_dir and Path(target_dir).exists():
        app_dir = Path(target_dir)
    else:
        app_dir = Path(get_app_dir())
        if target_dir and not Path(target_dir).exists():
            logger.warning(
                f"target_dir не существует: {target_dir}, fallback на {app_dir}"
            )

    if not app_dir.exists():
        return (
            jsonify(
                {"success": False, "error": f"Директория не существует: {app_dir}"}
            ),
            400,
        )

    state = load_state()
    files = state.get("files", [])

    if not files:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Нет файлов для обработки. Загрузите файлы.",
                }
            ),
            400,
        )

    # Check this directory doesn't already have numbered files
    existing = [
        f
        for f in app_dir.iterdir()
        if f.is_file()
        and f.name.split(".")[0].split(";")[0].strip().lstrip("0").isdigit()
    ]
    if existing:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "В директории уже есть пронумерованные файлы. Удалите их или выберите другую папку.",
                }
            ),
            400,
        )

    state["is_creating"] = False
    save_state(state)
    logger.info("Запрос на запуск магии (копирование файлов)")

    thread = threading.Thread(
        target=copy_files_worker,
        args=(files, app_dir),
        daemon=True,
        name="magic-worker",
    )
    thread.start()

    return jsonify(
        {
            "success": True,
            "message": "Магия запущена. Копирование и нумерация файлов...",
        }
    )


@magic_bp.route("/api/magic/cancel", methods=["POST"])
def cancel_magic():
    """Cancel running magic job."""
    with _magic_lock:
        magic_progress["cancelled"] = True
        magic_progress["status"] = "cancelled"
    logger.info("Магия отменена пользователем")
    return jsonify({"success": True, "message": "Операция отменена"})


@magic_bp.route("/api/magic/progress", methods=["GET"])
def get_magic_progress():
    """Poll magic progress."""
    with _magic_lock:
        data = dict(magic_progress)
    return jsonify({"success": True, "progress": data})


@magic_bp.route("/api/magic/result", methods=["GET"])
def get_magic_result():
    """Get magic result after completion."""
    state = load_state()
    return jsonify(
        {
            "success": True,
            "last_magic_run": state.get("last_magic_run"),
            "files": state.get("files", []),
            "created_directories": state.get("created_directories", []),
        }
    )


def copy_files_worker(files, app_dir):
    """Background worker: copy and number files, generate Excel registry."""
    from utils.rules import apply_rules_to_name, apply_symbol_rules

    with _magic_lock:
        magic_progress["status"] = "running"
        magic_progress["total"] = len(files)
        magic_progress["done"] = 0
        magic_progress["cancelled"] = False
        magic_progress["current_file"] = ""
        magic_progress["error"] = None

    try:
        start_number = 1
        copied = 0
        skipped = []
        copied_names = []

        for i, file_info in enumerate(files):
            with _magic_lock:
                if magic_progress["cancelled"]:
                    return

            src_path = Path(file_info.get("path", ""))
            if not src_path.exists():
                skipped.append(f"{src_path.name} (файл не найден)")
                with _magic_lock:
                    magic_progress["done"] += 1
                continue

            try:
                filename = src_path.name
                name_no_ext, ext = os.path.splitext(filename)

                # Apply replace rules
                new_name = apply_rules_to_name(name_no_ext)
                if new_name:
                    name_no_ext = new_name

                # Apply symbol rules
                name_no_ext = apply_symbol_rules(name_no_ext)

                # Generate numbered filename
                numbered_name = generate_numbered_filename(
                    start_number, name_no_ext, ext
                )

                dest_path = app_dir / numbered_name

                with _magic_lock:
                    magic_progress["current_file"] = str(src_path.name)

                shutil.copy2(str(src_path), str(dest_path))
                logger.info(f"Скопирован: {src_path.name} → {numbered_name}")
                copied += 1
                copied_names.append(numbered_name)
                start_number += 1
            except Exception as e:
                skipped.append(f"{src_path.name} ({e})")

            with _magic_lock:
                magic_progress["done"] += 1
                magic_progress["percent"] = int(
                    (magic_progress["done"] / magic_progress["total"]) * 100
                )

        # Generate Excel registry (only with copied files)
        try:
            state = load_state()
            registry_data = state.get("registry_data", {})
            saved_dicts = state.get("registry_dicts", {})

            logger.info(
                f"Копирование завершено: {copied} файлов, пропущено: {len(skipped)}"
            )
            logger.info("Генерация Excel реестра...")

            with _magic_lock:
                magic_progress["current_file"] = "Генерация Excel реестра..."
                magic_progress["percent"] = 95

            registry_path = generate_excel_registry(
                app_dir, registry_data, saved_dicts, set(copied_names)
            )
            logger.info(f"Excel-реестр создан: {registry_path}")

            state = load_state()
            state["last_magic_run"] = {
                "time": time.strftime("%d.%m.%Y %H:%M:%S"),
                "target_dir": str(app_dir),
                "files_processed": copied,
                "files_skipped": len(skipped),
            }
            # Update directory in created_directories
            app_dir_str = str(app_dir)
            existing_paths = [
                d if isinstance(d, str) else d.get("path", "")
                for d in state.get("created_directories", [])
            ]
            if app_dir_str not in existing_paths:
                state["created_directories"].append(
                    {
                        "path": app_dir_str,
                        "project_code": app_dir.name,
                        "date": time.strftime("%d.%m.%Y"),
                    }
                )
            save_state(state)
        except Exception as e:
            logger.exception("Ошибка при генерации реестра")
            with _magic_lock:
                magic_progress["error"] = str(e)

        with _magic_lock:
            magic_progress["status"] = "done"
            magic_progress["percent"] = 100
            magic_progress["current_file"] = f"Готово: {copied} файлов скопировано"
            magic_progress["copied"] = copied
            magic_progress["skipped"] = skipped

    except Exception as e:
        logger.exception("Ошибка в магии")
        with _magic_lock:
            magic_progress["status"] = "error"
            magic_progress["error"] = str(e)
