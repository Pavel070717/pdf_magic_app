"""
Tests for utils/database.py — SQLite materials CRUD.
"""

from utils.database import (
    add_material,
    delete_material,
    get_all_materials,
    get_material,
    init_db,
    search_materials,
)


def test_init_db_creates_table(temp_db):
    """init_db() creates the materials table without errors."""
    result = init_db()
    assert result is None  # No explicit return, just side effect
    assert temp_db.exists()


def test_init_db_is_idempotent(temp_db):
    """Calling init_db multiple times is safe."""
    init_db()
    init_db()
    init_db()
    # Should not raise


def test_add_and_get_material(temp_db):
    """Add a material and retrieve it."""
    mid = add_material(
        doc_name="Сертификат №123",
        material_name="Сталь 09Г2С",
        number="ТУ-123-2025",
        date="2025-03-15",
        producer="ООО МеталлПром",
        filename="cert_123.pdf",
        original_filename="Сертификат №123.pdf",
    )
    assert mid > 0

    material = get_material(mid)
    assert material is not None
    assert material["doc_name"] == "Сертификат №123"
    assert material["material_name"] == "Сталь 09Г2С"
    assert material["number"] == "ТУ-123-2025"


def test_get_material_not_found(temp_db):
    """Non-existent ID returns None."""
    result = get_material(99999)
    assert result is None


def test_get_all_materials(temp_db):
    """get_all_materials returns all records ordered by created_at DESC."""
    add_material("Doc A", "Mat A", "", "", "", "a.pdf", "a.pdf")
    add_material("Doc B", "Mat B", "", "", "", "b.pdf", "b.pdf")
    add_material("Doc C", "Mat C", "", "", "", "c.pdf", "c.pdf")

    all_mats = get_all_materials()
    assert len(all_mats) == 3
    # All three should be present (order within same second is non-deterministic)
    names = {m["doc_name"] for m in all_mats}
    assert names == {"Doc A", "Doc B", "Doc C"}


def test_get_all_materials_empty(temp_db):
    """Empty database returns empty list."""
    result = get_all_materials()
    assert result == []


def test_delete_material(temp_db):
    """Delete removes the record and returns True."""
    mid = add_material("Doc", "Mat", "", "", "", "f.pdf", "f.pdf")
    assert delete_material(mid) is True
    assert get_material(mid) is None
    assert get_all_materials() == []


def test_delete_nonexistent(temp_db):
    """Deleting non-existent ID returns False."""
    assert delete_material(99999) is False


def test_search_materials(temp_db):
    """Search finds matching materials by doc_name, material_name, number, producer."""
    add_material(
        "Сертификат А", "Сталь 20", "001", "2025-01-01", "Завод А", "a.pdf", "a.pdf"
    )
    add_material(
        "Паспорт Б", "Бетон М300", "002", "2025-02-01", "Завод Б", "b.pdf", "b.pdf"
    )
    add_material(
        "Декларация В", "Сталь 45", "003", "2025-03-01", "Комбинат В", "c.pdf", "c.pdf"
    )

    # Search by material_name
    results = search_materials("Сталь")
    assert len(results) == 2

    # Search by doc_name
    results = search_materials("Паспорт")
    assert len(results) == 1
    assert results[0]["doc_name"] == "Паспорт Б"

    # Search by number
    results = search_materials("003")
    assert len(results) == 1

    # Search by producer
    results = search_materials("Завод А")
    assert len(results) == 1

    # No match
    results = search_materials("НетТакого")
    assert results == []


def test_add_material_empty_optional_fields(temp_db):
    """Empty strings for optional fields are stored correctly."""
    mid = add_material("Doc", "Mat", "", "", "", "f.pdf", "f.pdf")
    mat = get_material(mid)
    assert mat["number"] == ""
    assert mat["date"] == ""
    assert mat["producer"] == ""


def test_material_has_all_fields(temp_db):
    """Material dict contains all expected fields."""
    mid = add_material(
        "Doc X", "Mat Y", "N123", "2026-01-01", "Producer Z", "x.pdf", "x_orig.pdf"
    )
    mat = get_material(mid)
    expected_keys = {
        "id",
        "doc_name",
        "material_name",
        "number",
        "date",
        "producer",
        "filename",
        "original_filename",
        "created_at",
    }
    assert expected_keys.issubset(mat.keys())
