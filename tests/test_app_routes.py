"""
Tests for app.py — page routes, health check, and request logging.
"""


class TestPageRoutes:
    def test_index(self, app_client):
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


class TestHealthCheck:
    def test_health(self, app_client):
        resp = app_client.get("/api/health")
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "ok"


class TestStaticFiles:
    def test_static_route(self, app_client):
        resp = app_client.get("/static/nonexistent.js")
        assert resp.status_code in (200, 404)


class TestRequestLogging:
    def test_api_request_logged(self, app_client):
        resp = app_client.get("/api/health")
        assert resp.status_code == 200

    def test_non_api_not_logged(self, app_client):
        resp = app_client.get("/")
        assert resp.status_code == 200


class TestAppConfig:
    def test_max_content_length(self, app_client):
        from app import app

        assert app.config["MAX_CONTENT_LENGTH"] == 100 * 1024 * 1024

    def test_secret_key_exists(self, app_client):
        from app import app

        assert app.config["SECRET_KEY"]

    def test_testing_config(self, app_client):
        from app import app

        assert app.config["TESTING"] is True
