"""
Blueprint: /api/files/* — file upload, list, reorder, delete.
"""

import shutil
import uuid
from pathlib import Path

from flask import Blueprint, jsonify, request
from natsort import natsorted

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


def _collect_dir_files(folder: Path) -> tuple[list[Path], list[dict[str, str]]]:
    """Рекурсивно собирает файлы папки в естественном порядке.

    Внутри каждой папки сначала файлы (по имени), затем подпапки (по имени).
    Файлы с недопустимым расширением попадают в rejected.
    """
    found: list[Path] = []
    rejected: list[dict[str, str]] = []

    def walk(directory: Path) -> None:
        try:
            entries = list(directory.iterdir())
        except (PermissionError, OSError) as e:
            logger.warning(f"Ошибка чтения папки {directory}: {e}")
            return
        file_entries = [e for e in entries if e.is_file()]
        dir_entries = [e for e in entries if e.is_dir()]
        for entry in natsorted(file_entries, key=lambda p: p.name):
            if entry.suffix.lower() in ALLOWED_EXTENSIONS:
                found.append(entry)
            else:
                rejected.append(
                    {
                        "name": entry.name,
                        "reason": f"Недопустимое расширение: {entry.suffix or '(нет)'}",
                    }
                )
        for entry in natsorted(dir_entries, key=lambda p: p.name):
            walk(entry)

    walk(folder)
    return found, rejected


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


@files_bp.route("/api/files/add-from-dir", methods=["POST"])
def add_files_from_dir():
    """Импорт всех допустимых файлов из указанной папки (рекурсивно).

    Файлы копируются в temp_uploads и добавляются в state["files"] в
    естественном порядке имён, чтобы нумерация при магии шла по порядку.
    """
    from utils.state import load_state, save_state

    data = request.get_json(silent=True) or {}
    folder_path = (data.get("path") or "").strip()
    if not folder_path:
        return jsonify({"success": False, "error": "Не указан путь к папке"}), 400

    folder = Path(folder_path)
    if not folder.exists():
        return jsonify({"success": False, "error": "Папка не найдена"}), 404
    if not folder.is_dir():
        return jsonify({"success": False, "error": "Указанный путь — не папка"}), 400

    temp_uploads_dir = PROJECT_DIR / "temp_uploads"
    temp_uploads_dir.mkdir(parents=True, exist_ok=True)

    found, rejected = _collect_dir_files(folder)
    valid_paths = []

    for src_path in found:
        try:
            safe_name = "".join(
                c for c in src_path.name if c.isalnum() or c in "._- ();№"
            )
            if not safe_name:
                safe_name = src_path.name

            dest_path = temp_uploads_dir / safe_name
            counter = 1
            ext = src_path.suffix.lower()
            while dest_path.exists():
                dest_path = temp_uploads_dir / f"{Path(safe_name).stem}_{counter}{ext}"
                counter += 1

            shutil.copy2(str(src_path), str(dest_path))
            logger.info(f"Файл импортирован из папки: {src_path}")

            valid_paths.append(
                {
                    "id": str(uuid.uuid4()),
                    "name": src_path.name,
                    "path": str(dest_path),
                    "original_path": str(dest_path),
                    "size": src_path.stat().st_size,
                }
            )
        except Exception as e:
            rejected.append({"name": src_path.name, "reason": str(e)})

    if not valid_paths:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Нет допустимых файлов в папке",
                    "rejected": rejected,
                }
            ),
            400,
        )

    state = load_state()
    state["files"].extend(valid_paths)
    save_state(state)

    logger.info(f"Импортировано из папки {folder}: {len(valid_paths)} файлов")
    return jsonify(
        {
            "success": True,
            "added": len(valid_paths),
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


@files_bp.route("/api/files/clear", methods=["POST"])
def clear_files():
    """Полностью очистить список загруженных файлов."""
    from utils.state import load_state, save_state

    state = load_state()

    for f in state.get("files", []):
        try:
            Path(f.get("original_path", "")).unlink(missing_ok=True)
        except Exception:
            pass

    state["files"] = []
    save_state(state)

    # Зачищаем temp_uploads на случай рассинхрона
    try:
        temp_uploads_dir = PROJECT_DIR / "temp_uploads"
        if temp_uploads_dir.exists():
            for item in temp_uploads_dir.iterdir():
                try:
                    if item.is_file():
                        item.unlink(missing_ok=True)
                    elif item.is_dir():
                        shutil.rmtree(item)
                except Exception:
                    pass
    except Exception:
        pass

    logger.info("Список загруженных файлов полностью очищен")
    return jsonify({"success": True, "files": []})


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
