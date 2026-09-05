"""
Integration tests for Flask routes via test_client.
"""

import json


class TestHealthCheck:
    def test_health_returns_ok(self, app_client):
        resp = app_client.get("/api/health")
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "ok"


class TestStateRoutes:
    def test_clear_state(self, app_client):
        resp = app_client.post("/api/state/clear")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True


class TestFilesRoutes:
    def test_list_files_empty(self, app_client):
        resp = app_client.get("/api/files")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "files" in data
        assert isinstance(data["files"], list)

    def test_add_file_no_upload(self, app_client):
        resp = app_client.post("/api/files/add")
        assert resp.status_code == 400


class TestRulesRoutes:
    def test_get_replace_rules_empty(self, app_client):
        resp = app_client.get("/api/replace-rules")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert isinstance(data["rules"], list)

    def test_add_replace_rule(self, app_client):
        rule = {"type": "text", "from": "abc", "to": "xyz"}
        resp = app_client.post(
            "/api/replace-rules",
            data=json.dumps(rule),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_add_replace_rule_empty_from(self, app_client):
        rule = {"type": "text", "from": "", "to": "xyz"}
        resp = app_client.post(
            "/api/replace-rules",
            data=json.dumps(rule),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_delete_replace_rule(self, app_client):
        rule = {"type": "text", "from": "test", "to": "result"}
        resp = app_client.post(
            "/api/replace-rules",
            data=json.dumps(rule),
            content_type="application/json",
        )
        rule_id = resp.get_json()["rules"][-1]["id"]
        resp = app_client.delete(f"/api/replace-rules/{rule_id}")
        assert resp.status_code == 200

    def test_clear_replace_rules(self, app_client):
        resp = app_client.post("/api/replace-rules/clear")
        assert resp.status_code == 200
        assert resp.get_json()["rules"] == []

    def test_get_accompanying_prefixes(self, app_client):
        resp = app_client.get("/api/accompanying-prefixes")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_save_accompanying_prefixes(self, app_client):
        resp = app_client.post(
            "/api/accompanying-prefixes",
            data=json.dumps({"prefixes": ["Сертификат", "Паспорт"]}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "Сертификат" in data["prefixes"]


class TestMaterialsRoutes:
    def test_list_materials_empty(self, app_client):
        resp = app_client.get("/api/materials")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert isinstance(data["materials"], list)

    def test_add_material_missing_doc_name(self, app_client):
        resp = app_client.post(
            "/api/materials/add",
            data={"material_name": "Сталь"},
        )
        assert resp.status_code == 400

    def test_add_material_missing_material_name(self, app_client):
        resp = app_client.post(
            "/api/materials/add",
            data={"doc_name": "Сертификат"},
        )
        assert resp.status_code == 400

    def test_delete_nonexistent_material(self, app_client):
        resp = app_client.delete("/api/materials/99999")
        assert resp.status_code == 404


class TestDashboardRoutes:
    def test_get_stats(self, app_client):
        resp = app_client.get("/api/dashboard/stats")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, dict)


class TestRegistryRoutes:
    def test_get_registry_form(self, app_client):
        resp = app_client.get("/api/registry/form")
        assert resp.status_code == 200

    def test_get_registry_data(self, app_client):
        resp = app_client.get("/api/registry/data")
        assert resp.status_code == 200


class TestRequisitesRoutes:
    def test_get_objects_empty(self, app_client):
        resp = app_client.get("/api/requisites/objects")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert isinstance(data["objects"], list)

    def test_add_object(self, app_client):
        resp = app_client.post(
            "/api/requisites/objects",
            data=json.dumps({"name": "Объект Тест"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_add_object_empty_name(self, app_client):
        resp = app_client.post(
            "/api/requisites/objects",
            data=json.dumps({"name": ""}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_get_requisites_nonexistent(self, app_client):
        resp = app_client.get("/api/requisites/99999")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["requisites"] == {}

    def test_delete_nonexistent_object(self, app_client):
        resp = app_client.delete("/api/requisites/objects/99999")
        assert resp.status_code == 404


class TestConverterRoutes:
    def test_get_history_empty(self, app_client):
        resp = app_client.get("/api/converter/history")
        assert resp.status_code == 200


class TestDirectoriesRoutes:
    def test_list_directories(self, app_client):
        resp = app_client.get("/api/directories/list")
        assert resp.status_code == 200


class TestPageRoutes:
    def test_index_page(self, app_client):
        resp = app_client.get("/")
        assert resp.status_code == 200

    def test_directories_page(self, app_client):
        resp = app_client.get("/directories/create")
        assert resp.status_code == 200

    def test_converter_page(self, app_client):
        resp = app_client.get("/converter")
        assert resp.status_code == 200

    def test_aocr_page(self, app_client):
        resp = app_client.get("/aocr")
        assert resp.status_code == 200

    def test_requisites_page(self, app_client):
        resp = app_client.get("/requisites")
        assert resp.status_code == 200

    def test_rules_page(self, app_client):
        resp = app_client.get("/rules")
        assert resp.status_code == 200

    def test_materials_page(self, app_client):
        resp = app_client.get("/materials")
        assert resp.status_code == 200
