"""
Fixtures for pdf_magic_app tests.
"""

import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def temp_state_file(monkeypatch):
    """Mock STATE_FILE to a temporary path, isolated per test."""
    tmp_dir = Path(tempfile.mkdtemp())
    tmp_state = tmp_dir / "state.json"
    monkeypatch.setattr("utils.state.STATE_FILE", tmp_state)
    yield tmp_state
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture
def clean_state(temp_state_file):
    """Return a clean default state, saved to temp file."""
    from utils.state import save_state

    state = {
        "version": "1.0",
        "files": [],
        "last_magic_run": None,
        "created_directories": [],
        "replace_rules": [],
        "accompanying_prefixes": [],
    }
    save_state(state)
    return state


@pytest.fixture
def temp_db(monkeypatch):
    """Mock DB_PATH to a temporary database, isolated per test."""
    import utils.database

    tmp_dir = Path(tempfile.mkdtemp())
    tmp_db = tmp_dir / "test_materials.db"
    monkeypatch.setattr(utils.database, "DB_PATH", tmp_db)
    utils.database.init_db()
    yield tmp_db
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture
def temp_db_all(monkeypatch):
    """Mock DB_PATH to a temporary database with all tables initialized."""
    import utils.database

    tmp_dir = Path(tempfile.mkdtemp())
    tmp_db = tmp_dir / "test_all.db"
    monkeypatch.setattr(utils.database, "DB_PATH", tmp_db)
    utils.database.init_db()
    utils.database.init_converter_db()
    utils.database.init_requisites_db()
    yield tmp_db
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture
def temp_dir():
    """Provide a temporary directory, cleaned up after test."""
    tmp_dir = Path(tempfile.mkdtemp())
    yield tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture
def app_client(temp_state_file, temp_db_all, monkeypatch):
    """Flask test client with isolated state and database."""
    monkeypatch.setattr("routes.core._APP_DIR_OVERRIDE", None)

    from app import app

    app.config["TESTING"] = True
    app.config["SERVER_NAME"] = "localhost"
    with app.test_client() as client:
        yield client
