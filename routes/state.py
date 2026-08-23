"""
Blueprint: /api/state/clear
"""

import shutil

from flask import Blueprint, jsonify

from routes.core import PROJECT_DIR, logger

state_bp = Blueprint("state", __name__)


@state_bp.route("/api/state/clear", methods=["POST"])
def clear_state():
    from utils.state import load_state, save_state

    try:
        current_state = load_state()
        created_dirs = current_state.get("created_directories", [])

        empty_state = {
            "version": current_state.get("version", "1.0"),
            "app_dir": current_state.get("app_dir", ""),
            "files": [],
            "last_magic_run": None,
            "created_directories": created_dirs,
            "replace_rules": [],
            "accompanying_prefixes": [],
            "registry_data": {},
            "registry_dicts": {},
            "registry_history": [],
        }
        save_state(empty_state)

        temp_uploads_dir = PROJECT_DIR / "temp_uploads"
        if temp_uploads_dir.exists():
            try:
                shutil.rmtree(temp_uploads_dir)
                logger.info(f"Очищена временная папка: {temp_uploads_dir}")
            except Exception as e:
                logger.warning(f"Не удалось очистить временную папку: {e}")

        logger.info("Состояние приложения очищено")
        return jsonify({"success": True, "message": "Состояние приложения очищено"})
    except Exception as e:
        logger.exception("Ошибка очистки состояния")
        return jsonify({"success": False, "error": str(e)}), 500
