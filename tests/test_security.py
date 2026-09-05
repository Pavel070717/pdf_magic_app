"""
Security-focused tests — path traversal, injection, validation.
"""

import json
from pathlib import Path

from routes.core import sanitize_folder_name, sanitize_text

# ─── Path Traversal ─────────────────────────────────────────────


class TestPathTraversal:
    def test_sanitize_rejects_slash_traversal(self):
        result = sanitize_folder_name("folder/../../secret")
        assert "/" not in result

    def test_sanitize_rejects_backslash_traversal(self):
        result = sanitize_folder_name("folder\\..\\..\\secret")
        assert "\\" not in result

    def test_sanitize_rejects_colon(self):
        result = sanitize_folder_name("C:\\Windows\\System32")
        assert ":" not in result

    def test_materials_pdf_no_path_traversal(self, app_client):
        """Attempting to serve materials PDF with path traversal should fail."""
        resp = app_client.get("/api/materials/pdf/../../etc/passwd")
        assert resp.status_code in (400, 404, 500)


# ─── HTML/XSS Injection ────────────────────────────────────────


class TestHtmlInjection:
    def test_sanitize_strips_html_tags(self):
        result = sanitize_text("<b>bold</b><i>italic</i>")
        assert "<b>" not in result
        assert "<i>" not in result
        assert "bold" in result

    def test_sanitize_strips_event_handlers(self):
        result = sanitize_text("<img src=x onerror=alert(1)>")
        assert "onerror" not in result

    def test_sanitize_strips_script_tags(self):
        result = sanitize_text("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "</script>" not in result

    def test_sanitize_preserves_text_after_tags(self):
        result = sanitize_text("<p>Safe content</p>")
        assert "Safe content" in result


# ─── Input Validation ──────────────────────────────────────────


class TestInputValidation:
    def test_sanitize_text_none(self):
        assert sanitize_text(None) == ""

    def test_sanitize_text_integer(self):
        assert sanitize_text(12345) == ""

    def test_sanitize_text_list(self):
        assert sanitize_text(["a", "b"]) == ""

    def test_sanitize_text_boolean(self):
        assert sanitize_text(True) == ""

    def test_sanitize_folder_name_none(self):
        assert sanitize_folder_name(None) == "unnamed_folder"

    def test_sanitize_folder_name_integer(self):
        assert sanitize_folder_name(42) == "unnamed_folder"

    def test_sanitize_folder_name_boolean(self):
        assert sanitize_folder_name(False) == "unnamed_folder"

    def test_empty_materials_add(self, app_client):
        """Adding material with empty data should not crash."""
        resp = app_client.post(
            "/api/materials/add",
            data={},
        )
        assert resp.status_code == 400

    def test_add_rule_empty_from(self, app_client):
        """Saving rule with empty from should return 400."""
        resp = app_client.post(
            "/api/replace-rules",
            data=json.dumps({"type": "text", "from": "", "to": "xyz"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_objects_with_empty_name(self, app_client):
        """Adding object with empty name should return 400."""
        resp = app_client.post(
            "/api/requisites/objects",
            data=json.dumps({"name": ""}),
            content_type="application/json",
        )
        assert resp.status_code == 400


# ─── Large Payload ─────────────────────────────────────────────


class TestLargePayload:
    def test_large_text_sanitization(self):
        large_text = "<p>" + "A" * 100000 + "</p>"
        result = sanitize_text(large_text)
        assert "A" in result
        assert "<p>" not in result

    def test_large_folder_name(self):
        large_name = "a" * 10000
        result = sanitize_folder_name(large_name)
        assert len(result) <= 10000
        assert result == large_name

    def test_many_rules_on_state(self, clean_state):
        """State can handle many replace rules without issues."""
        from utils.rules import save_replace_rules

        rules = [
            {"id": str(i), "type": "text", "from": f"from_{i}", "to": f"to_{i}"}
            for i in range(200)
        ]
        save_replace_rules(rules)
        from utils.rules import get_replace_rules

        loaded = get_replace_rules()
        assert len(loaded) == 200
