"""
Tests for utils/database.py — converter subsystem.
"""

from utils.database import (
    add_conversion,
    delete_conversion,
    get_conversions,
    init_converter_db,
)


def test_init_converter_db_creates_table(temp_db):
    """init_converter_db() creates the conversions table."""
    init_converter_db()
    result = temp_db.exists()
    assert result


def test_init_converter_db_idempotent(temp_db):
    """Calling init_converter_db multiple times is safe."""
    init_converter_db()
    init_converter_db()
    init_converter_db()


def test_add_and_get_conversion(temp_db):
    """Add a conversion and retrieve it."""
    init_converter_db()
    cid = add_conversion("test.pdf", "markdown", "/path/to/test.pdf")
    assert cid > 0

    convs = get_conversions()
    assert len(convs) == 1
    assert convs[0]["filename"] == "test.pdf"
    assert convs[0]["output_format"] == "markdown"
    assert convs[0]["source_path"] == "/path/to/test.pdf"
    assert convs[0]["status"] == "pending"


def test_get_conversions_empty(temp_db):
    """Empty table returns empty list."""
    init_converter_db()
    assert get_conversions() == []


def test_get_conversions_ordered_by_created_at_desc(temp_db):
    """Conversions ordered by created_at DESC."""
    init_converter_db()
    add_conversion("a.pdf", "markdown", "/a")
    add_conversion("b.pdf", "html", "/b")
    add_conversion("c.pdf", "json", "/c")

    convs = get_conversions()
    assert len(convs) == 3
    # All should be present
    filenames = {c["filename"] for c in convs}
    assert filenames == {"a.pdf", "b.pdf", "c.pdf"}


def test_get_conversions_limit_50(temp_db):
    """Conversions limited to 50 entries."""
    init_converter_db()
    for i in range(55):
        add_conversion(f"file_{i}.pdf", "markdown", f"/path/{i}")
    convs = get_conversions()
    assert len(convs) == 50


def test_delete_conversion(temp_db):
    """Delete removes a conversion record."""
    init_converter_db()
    cid = add_conversion("test.pdf", "markdown", "/path")
    assert delete_conversion(cid) is True

    convs = get_conversions()
    assert len(convs) == 0


def test_delete_nonexistent_conversion(temp_db):
    """Deleting non-existent ID returns False."""
    init_converter_db()
    assert delete_conversion(99999) is False


def test_conversion_has_all_fields(temp_db):
    """Conversion dict contains all expected fields."""
    init_converter_db()
    add_conversion("doc.pdf", "html", "/some/path")
    convs = get_conversions()
    expected_keys = {
        "id",
        "filename",
        "output_format",
        "source_path",
        "status",
        "created_at",
    }
    assert expected_keys.issubset(convs[0].keys())


def test_multiple_format_types(temp_db):
    """Different output formats are stored correctly."""
    init_converter_db()
    for fmt in ("markdown", "html", "json", "text", "pdf"):
        add_conversion(f"doc_{fmt}.pdf", fmt, f"/path/{fmt}")

    convs = get_conversions()
    formats = {c["output_format"] for c in convs}
    assert formats == {"markdown", "html", "json", "text", "pdf"}
