"""
Tests for utils/state.py — thread-safe atomic state.json persistence.
"""

import threading

from utils.state import load_state, save_state


def test_load_state_returns_default_when_file_missing(temp_state_file):
    """When state.json doesn't exist, load_state returns a default dict."""
    assert not temp_state_file.exists()
    result = load_state()
    assert result == {"version": "1.0", "files": [], "last_magic_run": None}


def test_save_and_load_state(temp_state_file):
    """Save state and load it back — round-trip integrity."""
    state = {
        "version": "1.0",
        "files": [{"name": "test.pdf", "path": "/tmp/test.pdf"}],
        "last_magic_run": "2026-01-01T00:00:00",
        "replace_rules": [{"id": "1", "from": "abc", "to": "xyz", "type": "text"}],
    }
    save_state(state)
    assert temp_state_file.exists()

    loaded = load_state()
    assert loaded == state
    assert loaded["files"][0]["name"] == "test.pdf"
    assert len(loaded["replace_rules"]) == 1


def test_save_state_is_atomic(temp_state_file):
    """Partial writes should not corrupt state.json (atomic replace)."""
    state = {"version": "1.0", "files": ["file1.pdf", "file2.pdf"]}
    save_state(state)

    # Load and verify
    loaded = load_state()
    assert loaded["files"] == ["file1.pdf", "file2.pdf"]

    # The temp file used during save should be gone (replaced)
    tmp_files = list(temp_state_file.parent.glob("state_tmp_*"))
    assert len(tmp_files) == 0, "Temporary files should be cleaned up"


def test_load_state_handles_corrupt_json(temp_state_file, monkeypatch):
    """Corrupt JSON falls back to default state."""
    from utils.state import load_state, save_state

    # First, save valid state
    save_state({"version": "1.0", "files": ["a.pdf"]})

    # Now corrupt the file
    temp_state_file.write_text("{this is not valid json", encoding="utf-8")
    result = load_state()
    assert result == {"version": "1.0", "files": [], "last_magic_run": None}


def test_concurrent_saves(clean_state):
    """Multiple threads writing state concurrently should not corrupt it."""
    errors = []

    def worker(n):
        try:
            import time

            time.sleep(0.01)  # Increase chance of overlap
            state = load_state()
            state[f"thread_{n}"] = n
            save_state(state)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Errors during concurrent saves: {errors}"

    # Final state should be loadable
    result = load_state()
    assert result is not None
    assert isinstance(result, dict)


def test_save_state_preserves_unicode(clean_state):
    """Russian characters are preserved correctly."""
    state = {
        "version": "1.0",
        "files": ["Сертификат.pdf", "Паспорт качества.pdf"],
        "replace_rules": [{"from": "ГОСТ", "to": "ГОСТ Р", "type": "text"}],
    }
    save_state(state)
    loaded = load_state()
    assert "Сертификат.pdf" in loaded["files"]
    assert loaded["replace_rules"][0]["to"] == "ГОСТ Р"
