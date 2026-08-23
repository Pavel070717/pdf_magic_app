"""
Blueprint: /api/files/* — file upload, list, reorder, delete.
"""

import uuid
from pathlib import Path

from flask import Blueprint, jsonify, request

from routes.core import PROJECT_DIR, logger

files_bp = Blueprint("files", __name__)

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".dwg",
    ".dxf",
}
ALLOWED_MIME_PREFIXES = {
    ".pdf": ["application/pdf"],
    ".jpg": ["image/jpeg"],
    ".jpeg": ["image/jpeg"],
    ".png": ["image/png"],
    ".doc": ["application/msword"],
    ".docx": [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ],
    ".xls": ["application/vnd.ms-excel"],
    ".xlsx": ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
    ".dwg": ["application/acad", "application/x-autocad", "image/vnd.dwg"],
    ".dxf": ["image/vnd.dxf", "application/x-dxf"],
}


@files_bp.route("/api/files", methods=["GET"])
def get_files():
    from utils.state import load_state

    state = load_state()
    files = state.get("files", [])
    for i, f in enumerate(files, 1):
        f["display_order"] = i
    return jsonify({"files": files})


@files_bp.route("/api/files/add", methods=["POST"])
def add_files():
    from utils.state import load_state, save_state

    if "files" not in request.files:
        return jsonify({"success": False, "error": "No files uploaded"}), 400

    temp_uploads_dir = PROJECT_DIR / "temp_uploads"
    temp_uploads_dir.mkdir(parents=True, exist_ok=True)

    uploaded_files = request.files.getlist("files")
    valid_paths = []
    rejected = []

    for uploaded_file in uploaded_files:
        filename = uploaded_file.filename
        if not filename or filename == "":
            rejected.append(
                {"name": filename or "(пусто)", "reason": "Отсутствует имя файла"}
            )
            continue
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            rejected.append(
                {
                    "name": filename,
                    "reason": f"Недопустимое расширение: {ext or '(нет)'}",
                }
            )
            continue

        # Validate MIME type if available
        allowed_mimes = ALLOWED_MIME_PREFIXES.get(ext, [])
        if allowed_mimes and getattr(uploaded_file, "content_type", None):
            if uploaded_file.content_type not in allowed_mimes:
                rejected.append(
                    {
                        "name": filename,
                        "reason": f"Недопустимый тип файла: {uploaded_file.content_type}",
                    }
                )
                continue

        safe_name = "".join(c for c in filename if c.isalnum() or c in "._- ();№")
        if not safe_name:
            safe_name = filename

        dest_path = temp_uploads_dir / safe_name
        counter = 1
        while dest_path.exists():
            dest_path = temp_uploads_dir / f"{Path(safe_name).stem}_{counter}{ext}"
            counter += 1

        uploaded_file.seek(0)
        uploaded_file.save(str(dest_path))
        logger.info(f"Файл загружен: {dest_path}")

        valid_paths.append(
            {
                "id": str(uuid.uuid4()),
                "name": filename,
                "path": str(dest_path),
                "original_path": str(dest_path),
            }
        )

    if not valid_paths:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Нет допустимых файлов для загрузки",
                    "rejected": rejected,
                }
            ),
            400,
        )

    state = load_state()
    state["files"].extend(valid_paths)
    save_state(state)

    return jsonify(
        {
            "success": True,
            "files": state["files"],
            "rejected": rejected,
        }
    )


@files_bp.route("/api/files/remove", methods=["POST"])
def remove_file():
    from utils.state import load_state, save_state

    data = request.get_json(silent=True) or {}
    file_id = data.get("id", "").strip()
    if not file_id:
        return jsonify({"success": False, "error": "No file id provided"}), 400

    state = load_state()
    files = state["files"]
    file_to_remove = next((f for f in files if f["id"] == file_id), None)

    if file_to_remove:
        try:
            Path(file_to_remove["original_path"]).unlink(missing_ok=True)
        except Exception:
            pass
        files.remove(file_to_remove)
        state["files"] = files
        save_state(state)

    return jsonify({"success": True, "files": files})


@files_bp.route("/api/files/reorder", methods=["POST"])
def reorder_files():
    from utils.state import load_state, save_state

    data = request.get_json(silent=True) or {}
    ordered_ids = data.get("order", [])
    if not isinstance(ordered_ids, list):
        return jsonify({"success": False, "error": "order must be a list"}), 400

    state = load_state()
    files = state["files"]
    file_map = {f["id"]: f for f in files}
    new_files = [file_map[fid] for fid in ordered_ids if fid in file_map]
    new_files.extend([f for f in files if f["id"] not in ordered_ids])
    state["files"] = new_files
    save_state(state)

    return jsonify({"success": True, "files": new_files})
