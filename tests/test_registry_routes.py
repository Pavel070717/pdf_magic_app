"""
Tests for routes/registry.py — registry data CRUD.
"""

import json


class TestRegistryForm:
    def test_get_form(self, app_client, clean_state):
        resp = app_client.get("/api/registry/form")
        assert resp.status_code == 200


class TestRegistryData:
    def test_get_data_empty(self, app_client, clean_state):
        resp = app_client.get("/api/registry/data")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert isinstance(data["data"], dict)
        assert isinstance(data["dicts"], dict)
        assert isinstance(data["history"], list)

    def test_save_data(self, app_client, clean_state):
        payload = {
            "org_name": "Test Org",
            "object_name": "Test Object",
            "customer": "Customer LLC",
            "sk_representative": "SK Rep",
            "general_contractor": "GC LLC",
            "work_executor": "Executor",
            "registry_number": "REG-001",
            "signature_sdal": "Person A",
            "signature_proveril": "Person B",
            "signature_prinyal": "Person C",
        }
        resp = app_client.post(
            "/api/registry/data",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 200

    def test_save_data_with_dicts(self, app_client, clean_state):
        payload = {
            "org_name": "Org",
            "dicts": {
                "work_types": ["Welding", "Painting"],
                "materials": ["Steel", "Concrete"],
            },
        }
        resp = app_client.post(
            "/api/registry/data",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 200

        resp2 = app_client.get("/api/registry/data")
        data = resp2.get_json()
        assert "Welding" in data["dicts"]["work_types"]
        assert "Steel" in data["dicts"]["materials"]

    def test_save_data_dedup_dicts(self, app_client, clean_state):
        payload1 = {"dicts": {"work_types": ["Welding"]}}
        app_client.post(
            "/api/registry/data",
            data=json.dumps(payload1),
            content_type="application/json",
        )
        payload2 = {"dicts": {"work_types": ["Welding", "Painting"]}}
        app_client.post(
            "/api/registry/data",
            data=json.dumps(payload2),
            content_type="application/json",
        )
        resp = app_client.get("/api/registry/data")
        work_types = resp.get_json()["dicts"]["work_types"]
        assert work_types.count("Welding") == 1

    def test_save_empty_dicts(self, app_client, clean_state):
        payload = {"dicts": {}}
        resp = app_client.post(
            "/api/registry/data",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 200

    def test_save_no_body(self, app_client, clean_state):
        resp = app_client.post(
            "/api/registry/data",
            content_type="application/json",
        )
        assert resp.status_code == 200
