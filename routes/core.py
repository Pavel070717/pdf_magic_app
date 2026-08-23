"""
Shared state, utilities, and helpers — with type hints for mypy.
"""

import logging
import os
import re
import threading
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ─── Logging ─────────────────────────────────────────────────────────────────
PROJECT_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_DIR / "logs"
LOG_FILE = LOG_DIR / "app.log"


def setup_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    from logging.handlers import RotatingFileHandler

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))

    error_handler = RotatingFileHandler(
        LOG_DIR / "errors.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(log_format, date_format))

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)

    return root_logger


logger = setup_logging()

# ─── App directory ───────────────────────────────────────────────────────────
DESKTOP_PATH = Path.home() / "Desktop"
USER_DESIRED_PATH: str | None = os.environ.get("PDF_MAGIC_APP_DIR", None)
APP_DIR: Path = Path(USER_DESIRED_PATH) if USER_DESIRED_PATH else DESKTOP_PATH
_APP_DIR_OVERRIDE: Path | None = None


def get_app_dir() -> Path:
    # Убрано global _APP_DIR_OVERRIDE – здесь только чтение, не присвоение
    if _APP_DIR_OVERRIDE is not None:
        return _APP_DIR_OVERRIDE
    return APP_DIR


def set_app_dir(path: Path) -> None:
    global _APP_DIR_OVERRIDE
    _APP_DIR_OVERRIDE = Path(path)
    _APP_DIR_OVERRIDE.mkdir(parents=True, exist_ok=True)
    logger.info(f"Рабочая директория установлена: {_APP_DIR_OVERRIDE}")


# ─── Magic progress ──────────────────────────────────────────────────────────
_magic_lock = threading.Lock()

magic_progress: dict[str, Any] = {
    "running": False,
    "progress": 0,
    "current_file": "",
    "total_files": 0,
    "files_copied": 0,
    "error": None,
    "cancel_requested": False,
}


# ─── Directories ─────────────────────────────────────────────────────────────
TEMP_UPLOADS_DIR = PROJECT_DIR / "temp_uploads"
MATERIALS_DIR = Path.home() / "Desktop" / "база материалов"
STATE_FILE = PROJECT_DIR / "state.json"
REACT_DIST = PROJECT_DIR / "frontend" / "dist"


def ensure_app_dirs() -> None:
    TEMP_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    from utils.state import load_state, save_state

    if not STATE_FILE.exists():
        initial_state: dict[str, Any] = {
            "version": "1.0",
            "app_dir": str(APP_DIR),
            "files": [],
            "last_magic_run": None,
            "created_directories": [],
            "replace_rules": [],
            "accompanying_prefixes": [],
        }
        save_state(initial_state)

    # Сбрасываем флаг is_creating, если процесс был убит во время создания директории
    state = load_state()
    if state.get("is_creating"):
        state["is_creating"] = False
        save_state(state)
        logger.warning("Сброшен флаг is_creating после некорректного завершения")


# ─── Sanitization helpers ───────────────────────────────────────────────────
def sanitize_text(text: str | None) -> str:
    if not text or not isinstance(text, str):
        return ""
    text = re.sub(r"<[^>]*>", "", text)
    text = re.sub(r"[<>]", "", text)
    return text.strip()


def sanitize_folder_name(name: str | None) -> str:
    if not name or not isinstance(name, str):
        return "unnamed_folder"
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    name = name.strip(". ")
    if not name:
        name = "unnamed_folder"
    return name


# ─── Subfolder / tree helpers ────────────────────────────────────────────────
def create_subfolders(
    base_path: Path, tree: list[dict[str, Any]]
) -> dict[str, list[Any]]:
    result: dict[str, list[Any]] = {"created": [], "errors": []}
    for node in tree:
        raw_name = node.get("name", "")
        name = sanitize_folder_name(raw_name)
        if not name:
            continue
        children: list[dict[str, Any]] = node.get("children", [])
        folder_path = base_path / name
        try:
            folder_path.mkdir(parents=True, exist_ok=True)
            result["created"].append(name)
        except Exception as e:
            result["errors"].append({"name": name, "error": str(e)})
            continue
        child_result = create_subfolders(folder_path, children)
        for cp in child_result["created"]:
            result["created"].append(f"{name}/{cp}")
        for err in child_result["errors"]:
            result["errors"].append(
                {"name": f"{name}/{err['name']}", "error": err["error"]}
            )
    return result


def build_tree_from_fs(directory: Path) -> list[dict[str, Any]]:
    tree: list[dict[str, Any]] = []
    try:
        for item in sorted(directory.iterdir()):
            if item.is_dir():
                tree.append({"name": item.name, "children": build_tree_from_fs(item)})
    except (PermissionError, Exception) as e:
        logger.warning(f"Ошибка чтения папки {directory}: {e}")
    return tree


def sync_tree_from_fs(entry: dict[str, Any], base_path: str) -> None:
    base = Path(base_path)
    if base.exists():
        entry["subfolders_tree"] = build_tree_from_fs(base)


def update_tree_paths(
    tree_nodes: list[dict[str, Any]], old_base: str, new_base: str
) -> None:
    if not tree_nodes:
        return
    for node in tree_nodes:
        children: list[dict[str, Any]] = node.get("children", [])
        if children:
            update_tree_paths(children, old_base, new_base)
        # Update path references in this node
        node_path = node.get("path", "")
        if node_path and node_path.startswith(old_base):
            node["path"] = new_base + node_path[len(old_base) :]


def build_tree_from_created(created_dirs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in created_dirs:
        date = entry.get("date", "unknown")
        by_date[date].append(entry)

    tree: list[dict[str, Any]] = []
    for date in sorted(by_date.keys(), reverse=True):
        date_entry: dict[str, Any] = {
            "name": date,
            "path": "",
            "type": "date",
            "children": [],
        }
        for proj in sorted(by_date[date], key=lambda x: str(x.get("project_code", ""))):
            proj_path = proj.get("path", "")
            proj_entry: dict[str, Any] = {
                "name": proj.get("project_code", ""),
                "path": proj_path,
                "type": "project",
                "children": tree_from_subfolders(
                    proj.get("subfolders_tree", []), proj_path
                ),
            }
            date_entry["children"].append(proj_entry)
        if date_entry["children"]:
            tree.append(date_entry)
    return tree


def tree_from_subfolders(
    tree_nodes: list[dict[str, Any]], base_path: str
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for node in tree_nodes:
        name = node.get("name", "")
        children: list[dict[str, Any]] = node.get("children", [])
        entry: dict[str, Any] = {
            "name": name,
            "path": str(Path(base_path) / name),
            "type": "folder",
            "children": tree_from_subfolders(children, str(Path(base_path) / name)),
        }
        result.append(entry)
    return result


def scan_filesystem_for_dirs() -> list[dict[str, Any]]:
    from utils.state import load_state, save_state

    state = load_state()
    try:
        created: list[dict[str, Any]] = state.get("created_directories", [])
        existing_paths = {d.get("path", "") for d in created if d.get("path")}
        new_entries: list[dict[str, Any]] = []

        for item in DESKTOP_PATH.iterdir():
            if not item.is_dir():
                continue
            date_match = re.match(r"^\d{2}\.\d{2}\.\d{4}$", item.name) or re.match(
                r"^\d{4}-\d{2}-\d{2}$", item.name
            )
            if not date_match:
                continue
            date_str = item.name
            for proj_item in item.iterdir():
                if not proj_item.is_dir():
                    continue
                proj_path_str = str(proj_item)
                if proj_path_str in existing_paths:
                    continue
                entry: dict[str, Any] = {
                    "path": proj_path_str,
                    "project_code": proj_item.name,
                    "date": date_str,
                    "subfolders_tree": build_tree_from_fs(proj_item),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                new_entries.append(entry)
                existing_paths.add(proj_path_str)

        if new_entries:
            created.extend(new_entries)
            state["created_directories"] = created
            save_state(state)

        return created
    except Exception as e:
        logger.error(f"Ошибка сканирования ФС: {e}")
        result: list[dict[str, Any]] = state.get("created_directories", [])
        return result
