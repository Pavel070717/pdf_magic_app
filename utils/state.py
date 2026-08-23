"""
Thread-safe atomic state.json persistence — with type hints.
"""

import json
import logging
import os
import tempfile
import threading
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

STATE_FILE = Path(__file__).resolve().parent.parent / "state.json"
_state_lock = threading.Lock()


def load_state() -> dict[str, Any]:
    with _state_lock:
        try:
            if STATE_FILE.exists():
                with open(STATE_FILE, encoding="utf-8") as f:
                    data: dict[str, Any] = json.load(f)
                    return data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Ошибка загрузки state.json: {e}")
        return {"version": "1.0", "files": [], "last_magic_run": None}


def save_state(state: dict[str, Any]) -> None:
    with _state_lock:
        _atomic_save(state)


def _atomic_save(state: dict[str, Any]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        suffix=".json", prefix="state_tmp_", dir=str(STATE_FILE.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        Path(tmp_path).replace(STATE_FILE)
    except Exception:
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass
        raise
