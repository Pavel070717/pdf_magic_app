"""
Blueprint: /api/directory/* + /api/directories/* — directory CRUD and listing.
"""

import shutil
from datetime import datetime, timezone
from pathlib import Path

import send2trash
from flask import Blueprint, jsonify, request

from routes.core import (
    DESKTOP_PATH,
    build_tree_from_created,
    create_subfolders,
    get_app_dir,
    logger,
    sanitize_folder_name,
    scan_filesystem_for_dirs,
    set_app_dir,
    sync_tree_from_fs,
    update_tree_paths,
)

dir_bp = Blueprint("directories", __name__)


@dir_bp.route("/api/directory/create", methods=["POST"])
def create_directory():
    from utils.state import load_state, save_state

    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Нет данных"}), 400

        project_code = data.get("project_code", "").strip()
        if not project_code:
            return jsonify({"success": False, "error": "Не указан шифр проекта"}), 400
        project_code = sanitize_folder_name(project_code)
        if project_code == "unnamed_folder":
            return (
                jsonify({"success": False, "error": "Некорректный шифр проекта"}),
                400,
            )

        subfolders_tree = data.get("subfolders_tree", [])
        if not isinstance(subfolders_tree, list):
            subfolders_tree = []

        state = load_state()
        if state.get("is_creating", False):
            return (
                jsonify(
                    {"success": False, "error": "Операция создания уже выполняется"}
                ),
                429,
            )
        state["is_creating"] = True
        save_state(state)

        try:
            today_str = datetime.now().strftime("%d.%m.%Y")
            date_dir = DESKTOP_PATH / today_str
            project_dir = date_dir / project_code
            project_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Создана корневая папка: {project_dir}")

            subfolder_result = create_subfolders(project_dir, subfolders_tree)
            created_subfolders = subfolder_result["created"]
            creation_errors = subfolder_result["errors"]

            set_app_dir(project_dir)
            state["current_directory"] = {
                "desktop_dir": str(DESKTOP_PATH),
                "date_dir": str(date_dir),
                "project_dir": str(project_dir),
                "project_code": project_code,
                "subfolders_tree": subfolders_tree,
                "subfolders": created_subfolders,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            if "created_directories" not in state:
                state["created_directories"] = []

            dir_entry = {
                "path": str(project_dir),
                "project_code": project_code,
                "date": today_str,
                "subfolders_tree": subfolders_tree,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            found = False
            for i, d in enumerate(state["created_directories"]):
                if d.get("path") == str(project_dir):
                    state["created_directories"][i] = dir_entry
                    found = True
                    break
            if not found:
                state["created_directories"].append(dir_entry)

            state["is_creating"] = False
            save_state(state)

            response = {
                "success": True,
                "path": str(project_dir),
                "date": today_str,
                "project_code": project_code,
                "subfolders_tree": subfolders_tree,
                "subfolders": created_subfolders,
            }
            if creation_errors:
                response["warnings"] = creation_errors
            return jsonify(response)
        except Exception:
            state["is_creating"] = False
            save_state(state)
            raise

    except Exception as e:
        logger.exception("Ошибка создания директории")
        return jsonify({"success": False, "error": str(e)}), 500


@dir_bp.route("/api/directory/delete", methods=["POST"])
def delete_directory():
    from utils.state import load_state, save_state

    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Нет данных"}), 400
        full_path = data.get("full_path", "").strip()
        if not full_path:
            return jsonify({"success": False, "error": "Не указан путь"}), 400

        dir_path = Path(full_path)
        try:
            dir_path_resolved = dir_path.resolve()
            desktop_resolved = DESKTOP_PATH.resolve()
            if not str(dir_path_resolved).startswith(str(desktop_resolved)):
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Можно удалять только на рабочем столе",
                        }
                    ),
                    400,
                )
        except Exception:
            return jsonify({"success": False, "error": "Некорректный путь"}), 400

        if dir_path.exists():
            send2trash.send2trash(str(dir_path))
            logger.info(f"Директория удалена в корзину: {dir_path}")

        state = load_state()
        created = state.get("created_directories", [])
        state["created_directories"] = [
            d for d in created if d.get("path") != full_path
        ]
        save_state(state)

        tree = build_tree_from_created(state["created_directories"])
        return jsonify({"success": True, "message": "Директория удалена", "tree": tree})
    except Exception as e:
        logger.exception("Ошибка удаления директории")
        return jsonify({"success": False, "error": str(e)}), 500


@dir_bp.route("/api/directory/add-folder", methods=["POST"])
def add_subfolder():
    from utils.state import load_state, save_state

    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Нет данных"}), 400
        parent_path = data.get("parent_path", "").strip()
        folder_name = data.get("folder_name", "").strip()
        if not parent_path or not folder_name:
            return jsonify({"success": False, "error": "Не указан путь или имя"}), 400

        folder_name = sanitize_folder_name(folder_name)
        if folder_name == "unnamed_folder":
            return jsonify({"success": False, "error": "Некорректное имя"}), 400

        parent_dir = Path(parent_path)
        new_folder = parent_dir / folder_name
        if not parent_dir.exists():
            return (
                jsonify({"success": False, "error": "Родительская папка не найдена"}),
                404,
            )
        if new_folder.exists():
            return jsonify({"success": False, "error": "Папка уже существует"}), 409

        new_folder.mkdir(parents=True, exist_ok=False)
        logger.info(f"Создана подпапка: {new_folder}")

        state = load_state()
        created = state.get("created_directories", [])
        for entry in created:
            entry_path = entry.get("path", "")
            if parent_path == entry_path or parent_path.startswith(entry_path):
                sync_tree_from_fs(entry, entry_path)
        save_state(state)

        tree = build_tree_from_created(state["created_directories"])
        return jsonify({"success": True, "path": str(new_folder), "tree": tree})
    except Exception as e:
        logger.exception("Ошибка создания подпапки")
        return jsonify({"success": False, "error": str(e)}), 500


@dir_bp.route("/api/directory/rename", methods=["POST"])
def rename_directory():
    from utils.state import load_state, save_state

    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Нет данных"}), 400
        old_path = data.get("old_path", "").strip()
        new_name = data.get("new_name", "").strip()
        if not old_path or not new_name:
            return jsonify({"success": False, "error": "Не указан путь или имя"}), 400

        new_name = sanitize_folder_name(new_name)
        if new_name == "unnamed_folder":
            return jsonify({"success": False, "error": "Некорректное имя"}), 400

        old_dir = Path(old_path)
        new_dir = old_dir.parent / new_name
        if not old_dir.exists():
            return jsonify({"success": False, "error": "Папка не найдена"}), 404
        if new_dir.exists():
            return jsonify({"success": False, "error": "Папка уже существует"}), 409

        old_dir.rename(new_dir)
        old_str, new_str = str(old_dir), str(new_dir)
        logger.info(f"Папка переименована: {old_str} → {new_str}")

        state = load_state()
        created = state.get("created_directories", [])
        for entry in created:
            entry_path = entry.get("path", "")
            if entry_path == old_str:
                entry["path"] = new_str
                entry["project_code"] = new_name
            elif old_str.startswith(entry_path):
                if "subfolders_tree" in entry:
                    update_tree_paths(entry["subfolders_tree"], old_str, new_str)
        if state.get("current_directory", {}).get("project_dir") == old_str:
            state["current_directory"]["project_dir"] = new_str
        save_state(state)

        tree = build_tree_from_created(state["created_directories"])
        return jsonify(
            {"success": True, "old_path": old_str, "new_path": new_str, "tree": tree}
        )
    except Exception as e:
        logger.exception("Ошибка переименования")
        return jsonify({"success": False, "error": str(e)}), 500


@dir_bp.route("/api/directory/recreate", methods=["POST"])
def recreate_directory():
    from utils.state import load_state

    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Нет данных"}), 400
        full_path = data.get("full_path", "").strip()
        if not full_path:
            return jsonify({"success": False, "error": "Не указан путь"}), 400

        state = load_state()
        created = state.get("created_directories", [])
        dir_entry = next((d for d in created if d.get("path") == full_path), None)
        if not dir_entry:
            return jsonify({"success": False, "error": "Директория не найдена"}), 404

        dir_path = Path(full_path)
        if dir_path.exists():
            shutil.rmtree(dir_path)
        dir_path.mkdir(parents=True, exist_ok=True)

        subfolders_tree = dir_entry.get("subfolders_tree", [])
        subfolder_result = create_subfolders(dir_path, subfolders_tree)

        return jsonify(
            {
                "success": True,
                "message": "Директория пересоздана",
                "path": full_path,
                "subfolders": subfolder_result["created"],
            }
        )
    except Exception as e:
        logger.exception("Ошибка пересоздания")
        return jsonify({"success": False, "error": str(e)}), 500


@dir_bp.route("/api/directory/scan", methods=["POST"])
def scan_directories():
    from utils.state import load_state, save_state

    try:
        scan_filesystem_for_dirs()
        state = load_state()
        created = state.get("created_directories", [])
        existing_dirs = [
            d
            for d in created
            if Path(d if isinstance(d, str) else d.get("path", "")).exists()
        ]
        if len(existing_dirs) != len(created):
            state["created_directories"] = existing_dirs
            save_state(state)
        tree = build_tree_from_created(existing_dirs)
        return jsonify({"success": True, "tree": tree, "count": len(existing_dirs)})
    except Exception as e:
        logger.exception("Ошибка сканирования")
        return jsonify({"success": False, "error": str(e)}), 500


@dir_bp.route("/api/directory/current", methods=["GET"])
def get_current_directory():
    from utils.state import load_state

    current_dir = get_app_dir()
    state = load_state()
    dir_info = state.get("current_directory", {})
    return jsonify(
        {
            "success": True,
            "current_dir": str(current_dir),
            "exists": current_dir.exists(),
            "info": dir_info,
        }
    )


@dir_bp.route("/api/directories/list", methods=["GET"])
def list_directories():
    from utils.state import load_state, save_state

    try:
        scan_filesystem_for_dirs()
        state = load_state()
        created = state.get("created_directories", [])
        existing_dirs = [
            d
            for d in created
            if Path(d if isinstance(d, str) else d.get("path", "")).exists()
        ]
        if len(existing_dirs) != len(created):
            state["created_directories"] = existing_dirs
            save_state(state)
        tree = build_tree_from_created(existing_dirs)
        return jsonify({"success": True, "tree": tree, "count": len(existing_dirs)})
    except Exception as e:
        logger.exception("Ошибка списка директорий")
        return jsonify({"success": False, "error": str(e)}), 500
