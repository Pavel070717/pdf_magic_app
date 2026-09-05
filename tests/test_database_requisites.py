"""
Tests for utils/database.py — requisites and objects subsystem.
"""

from utils.database import (
    add_object,
    delete_object,
    get_objects,
    get_requisites,
    init_requisites_db,
    save_requisites,
)


# ─── Objects CRUD ────────────────────────────────────────────────


class TestObjects:
    def test_init_requisites_db_creates_tables(self, temp_db):
        """init_requisites_db creates objects and requisites tables."""
        init_requisites_db()

    def test_init_requisites_db_idempotent(self, temp_db):
        """Multiple calls to init_requisites_db are safe."""
        init_requisites_db()
        init_requisites_db()
        init_requisites_db()

    def test_add_object(self, temp_db):
        """Add an object and verify it exists."""
        init_requisites_db()
        oid = add_object("Объект Тест")
        assert oid > 0

    def test_get_objects(self, temp_db):
        """get_objects returns all objects."""
        init_requisites_db()
        add_object("Объект А")
        add_object("Объект Б")
        objs = get_objects()
        assert len(objs) == 2
        names = {o["name"] for o in objs}
        assert names == {"Объект А", "Объект Б"}

    def test_get_objects_empty(self, temp_db):
        """Empty table returns empty list."""
        init_requisites_db()
        assert get_objects() == []

    def test_delete_object(self, temp_db):
        """Delete removes an object."""
        init_requisites_db()
        oid = add_object("Test")
        assert delete_object(oid) is True
        assert get_objects() == []

    def test_delete_nonexistent_object(self, temp_db):
        """Deleting non-existent ID returns False."""
        init_requisites_db()
        assert delete_object(99999) is False

    def test_object_has_id_and_name(self, temp_db):
        """Object dict contains expected fields."""
        init_requisites_db()
        oid = add_object("Объект")
        objs = get_objects()
        assert "id" in objs[0]
        assert "name" in objs[0]
        assert "created_at" in objs[0]


# ─── Requisites CRUD ─────────────────────────────────────────────


class TestRequisites:
    def _setup(self, temp_db):
        init_requisites_db()
        return add_object("Объект Тест")

    def test_save_and_get_requisites(self, temp_db):
        """Save requisites and retrieve them."""
        oid = self._setup(temp_db)
        data = {
            "developer_name": "Застройщик ООО",
            "developer_ogrn": "1234567890123",
            "developer_inn": "7701234567",
            "builder_name": "Подрядчик АО",
        }
        save_requisites(oid, data)
        req = get_requisites(oid)
        assert req is not None
        assert req["developer_name"] == "Застройщик ООО"
        assert req["developer_ogrn"] == "1234567890123"
        assert req["builder_name"] == "Подрядчик АО"

    def test_get_requisites_nonexistent(self, temp_db):
        """Non-existent object returns None."""
        init_requisites_db()
        assert get_requisites(99999) is None

    def test_save_requisites_upsert_update(self, temp_db):
        """Saving requisites for existing object updates (upsert)."""
        oid = self._setup(temp_db)
        save_requisites(oid, {"developer_name": "V1"})
        save_requisites(oid, {"developer_name": "V2"})
        req = get_requisites(oid)
        assert req["developer_name"] == "V2"

    def test_save_requisites_partial_data(self, temp_db):
        """Saving with partial data preserves defaults for missing fields."""
        oid = self._setup(temp_db)
        save_requisites(oid, {"developer_name": "Test"})
        req = get_requisites(oid)
        assert req["developer_name"] == "Test"
        assert req["builder_name"] == ""
        assert req["designer_name"] == ""

    def test_save_requisites_empty_data(self, temp_db):
        """Saving with empty data uses all defaults."""
        oid = self._setup(temp_db)
        save_requisites(oid, {})
        req = get_requisites(oid)
        assert req is not None
        assert req["developer_name"] == ""

    def test_requisites_has_all_fields(self, temp_db):
        """Requisites dict contains all expected fields."""
        oid = self._setup(temp_db)
        save_requisites(oid, {})
        req = get_requisites(oid)
        expected_keys = {
            "id", "object_id",
            "developer_name", "developer_ogrn", "developer_inn",
            "developer_address", "developer_phone",
            "builder_name", "builder_ogrn", "builder_inn",
            "builder_address", "builder_phone",
            "builder_sro_number", "builder_sro_name",
            "builder_sro_ogrn", "builder_sro_inn",
            "designer_name", "designer_ogrn", "designer_inn",
            "designer_sro_number", "designer_sro_name",
            "designer_sro_ogrn", "designer_sro_inn",
            "designer_address", "designer_phone",
            "control_name", "control_ogrn", "control_inn",
            "control_address", "control_phone",
            "control_sro_number", "control_sro_name",
            "control_sro_ogrn", "control_sro_inn",
            "rep_developer_position", "rep_developer_name", "rep_developer_doc",
            "rep_builder_position", "rep_builder_name", "rep_builder_doc",
            "rep_builder_ctrl_position", "rep_builder_ctrl_name", "rep_builder_ctrl_doc",
            "rep_designer_position", "rep_designer_name", "rep_designer_doc",
            "rep_contractor_position", "rep_contractor_name", "rep_contractor_doc",
            "rep_others_org", "rep_others_position", "rep_others_name",
            "rep_others_doc", "rep_others_continued",
            "created_at",
        }
        assert expected_keys.issubset(req.keys())

    def test_cascade_delete_object_removes_requisites(self, temp_db):
        """Deleting an object cascades to requisites."""
        oid = self._setup(temp_db)
        save_requisites(oid, {"developer_name": "Test"})
        assert get_requisites(oid) is not None
        delete_object(oid)
        assert get_requisites(oid) is None

    def test_save_requisites_all_fields(self, temp_db):
        """Save and verify all 51 fields round-trip correctly."""
        oid = self._setup(temp_db)
        data = {}
        for i, key in enumerate([
            "developer_name", "developer_ogrn", "developer_inn",
            "developer_address", "developer_phone",
            "builder_name", "builder_ogrn", "builder_inn",
            "builder_address", "builder_phone",
            "builder_sro_number", "builder_sro_name",
            "builder_sro_ogrn", "builder_sro_inn",
            "designer_name", "designer_ogrn", "designer_inn",
            "designer_sro_number", "designer_sro_name",
            "designer_sro_ogrn", "designer_sro_inn",
            "designer_address", "designer_phone",
            "control_name", "control_ogrn", "control_inn",
            "control_address", "control_phone",
            "control_sro_number", "control_sro_name",
            "control_sro_ogrn", "control_sro_inn",
            "rep_developer_position", "rep_developer_name", "rep_developer_doc",
            "rep_builder_position", "rep_builder_name", "rep_builder_doc",
            "rep_builder_ctrl_position", "rep_builder_ctrl_name", "rep_builder_ctrl_doc",
            "rep_designer_position", "rep_designer_name", "rep_designer_doc",
            "rep_contractor_position", "rep_contractor_name", "rep_contractor_doc",
            "rep_others_org", "rep_others_position", "rep_others_name",
            "rep_others_doc", "rep_others_continued",
        ]):
            data[key] = f"value_{i}"
        save_requisites(oid, data)
        req = get_requisites(oid)
        for key, val in data.items():
            assert req[key] == val, f"Field {key} mismatch"
