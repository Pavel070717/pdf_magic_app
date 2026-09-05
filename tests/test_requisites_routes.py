"""
Tests for routes/requisites.py — construction objects and requisites CRUD.
"""

import json


class TestRequisitesObjects:
    def test_list_empty(self, app_client, temp_db_all):
        resp = app_client.get("/api/requisites/objects")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["objects"] == []

    def test_create_object(self, app_client, temp_db_all):
        resp = app_client.post(
            "/api/requisites/objects",
            data=json.dumps({"name": "Building A"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True
        assert "id" in resp.get_json()

    def test_create_object_empty_name(self, app_client, temp_db_all):
        resp = app_client.post(
            "/api/requisites/objects",
            data=json.dumps({"name": ""}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_create_object_whitespace_name(self, app_client, temp_db_all):
        resp = app_client.post(
            "/api/requisites/objects",
            data=json.dumps({"name": "   "}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_create_object_no_body(self, app_client, temp_db_all):
        resp = app_client.post(
            "/api/requisites/objects",
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_delete_nonexistent_object(self, app_client, temp_db_all):
        resp = app_client.delete("/api/requisites/objects/99999")
        assert resp.status_code == 404

    def test_delete_existing_object(self, app_client, temp_db_all):
        resp = app_client.post(
            "/api/requisites/objects",
            data=json.dumps({"name": "To Delete"}),
            content_type="application/json",
        )
        obj_id = resp.get_json()["id"]
        resp = app_client.delete(f"/api/requisites/objects/{obj_id}")
        assert resp.status_code == 200

    def test_create_multiple_objects(self, app_client, temp_db_all):
        for name in ["Object A", "Object B", "Object C"]:
            resp = app_client.post(
                "/api/requisites/objects",
                data=json.dumps({"name": name}),
                content_type="application/json",
            )
            assert resp.status_code == 200
        resp = app_client.get("/api/requisites/objects")
        assert len(resp.get_json()["objects"]) == 3


class TestRequisitesCRUD:
    def test_get_requisites_empty(self, app_client, temp_db_all):
        resp = app_client.get("/api/requisites/99999")
        assert resp.status_code == 200
        assert resp.get_json()["requisites"] == {}

    def test_save_and_get_requisites(self, app_client, temp_db_all):
        resp = app_client.post(
            "/api/requisites/objects",
            data=json.dumps({"name": "Building"}),
            content_type="application/json",
        )
        obj_id = resp.get_json()["id"]
        reqs_data = {
            "developer_name": "Dev LLC",
            "builder_name": "Builder Inc",
            "designer_name": "Design Co",
        }
        resp = app_client.post(
            f"/api/requisites/{obj_id}",
            data=json.dumps(reqs_data),
            content_type="application/json",
        )
        assert resp.status_code == 200

        resp = app_client.get(f"/api/requisites/{obj_id}")
        data = resp.get_json()
        assert data["success"] is True
        assert data["requisites"]["developer_name"] == "Dev LLC"

    def test_save_requisites_no_body(self, app_client, temp_db_all):
        resp = app_client.post(
            "/api/requisites/1",
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_update_requisites(self, app_client, temp_db_all):
        resp = app_client.post(
            "/api/requisites/objects",
            data=json.dumps({"name": "Updating"}),
            content_type="application/json",
        )
        obj_id = resp.get_json()["id"]
        app_client.post(
            f"/api/requisites/{obj_id}",
            data=json.dumps({"developer_name": "V1"}),
            content_type="application/json",
        )
        app_client.post(
            f"/api/requisites/{obj_id}",
            data=json.dumps({"developer_name": "V2"}),
            content_type="application/json",
        )
        resp = app_client.get(f"/api/requisites/{obj_id}")
        assert resp.get_json()["requisites"]["developer_name"] == "V2"


class TestAOCRData:
    def test_nonexistent_object(self, app_client, temp_db_all):
        resp = app_client.get("/api/requisites/99999/aocr")
        assert resp.status_code == 404

    def test_empty_requisites(self, app_client, temp_db_all):
        resp = app_client.post(
            "/api/requisites/objects",
            data=json.dumps({"name": "Empty Reqs"}),
            content_type="application/json",
        )
        obj_id = resp.get_json()["id"]
        resp = app_client.get(f"/api/requisites/{obj_id}/aocr")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["object_name"] == "Empty Reqs"
        assert data["developer_name"] == ""

    def test_filled_requisites(self, app_client, temp_db_all):
        resp = app_client.post(
            "/api/requisites/objects",
            data=json.dumps({"name": "Full"}),
            content_type="application/json",
        )
        obj_id = resp.get_json()["id"]
        reqs = {
            "developer_name": "Dev LLC",
            "developer_address": "123 Main St",
            "builder_name": "Builder Inc",
            "builder_address": "456 Oak Ave",
            "builder_phone": "+7 999 111 2233",
            "builder_sro_number": "SRO-001",
            "builder_sro_name": "SRO Union",
            "builder_sro_ogrn": "1234567890123",
            "builder_sro_inn": "1234567890",
            "designer_name": "Design Co",
            "designer_sro_number": "SRO-002",
            "designer_sro_name": "Design SRO",
            "designer_sro_ogrn": "9876543210987",
            "designer_sro_inn": "9876543210",
            "rep_developer_position": "Director",
            "rep_developer_name": "Ivanov I.I.",
            "rep_developer_doc": "Power of Attorney",
            "rep_builder_position": "Engineer",
            "rep_builder_name": "Petrov P.P.",
            "rep_builder_doc": "Order",
            "rep_builder_ctrl_position": "Inspector",
            "rep_builder_ctrl_name": "Sidorov S.S.",
            "rep_builder_ctrl_doc": "Certificate",
            "rep_designer_position": "Architect",
            "rep_designer_name": "Kozlov K.K.",
            "rep_designer_doc": "License",
            "rep_contractor_position": "Foreman",
            "rep_contractor_name": "Smirnov S.S.",
            "rep_contractor_doc": "Certificate",
            "rep_others_position": "Other",
            "rep_others_name": "Other Person",
            "rep_others_doc": "Other Doc",
            "rep_others_continued": "Additional info",
            "s2_work_name": "Welding work",
            "s2_project_docs": "Project doc",
            "s2_materials_used": "Steel",
            "s2_documents_submitted": "Certificate",
            "s2_start_day": "01",
            "s2_start_month": "January",
            "s2_start_year": "2026",
            "s2_end_day": "31",
            "s2_end_month": "December",
            "s2_end_year": "2026",
            "s2_standards_l1": "SP 70.13330",
            "s2_standards_l2": "GOST 33610",
            "s2_standards_l3": "SNiP 3.03.01",
            "s2_standards_l4": "",
            "s2_standards_l5": "",
            "s2_next_work": "Finishing",
            "s2_additional_info": "None",
            "s2_copies": "3",
            "s2_appendices": "Appendix A",
            "s2_rep_developer": "Dev Rep",
            "s2_rep_builder": "Builder Rep",
            "s2_rep_builder_ctrl": "Ctrl Rep",
            "s2_rep_designer": "Design Rep",
            "s2_rep_contractor": "Contractor Rep",
            "s2_rep_others": "Others Rep",
        }
        app_client.post(
            f"/api/requisites/{obj_id}",
            data=json.dumps(reqs),
            content_type="application/json",
        )
        resp = app_client.get(f"/api/requisites/{obj_id}/aocr")
        data = resp.get_json()
        assert data["success"] is True
        assert data["developer_name"] == "Dev LLC"
        assert data["builder_name"] == "Builder Inc"
        assert "456 Oak Ave" in data["builder_continued"]
        assert "SRO-001" in data["builder_continued2"]
        assert "SRO-002" in data["designer_continued"]
        assert "Director" in data["rep_developer"]
        assert "Ivanov I.I." in data["rep_developer"]
        assert data["success"] is True

    def test_sro_formatting(self, app_client, temp_db_all):
        resp = app_client.post(
            "/api/requisites/objects",
            data=json.dumps({"name": "SRO Test"}),
            content_type="application/json",
        )
        obj_id = resp.get_json()["id"]
        reqs = {
            "builder_sro_number": "SRO-123",
            "builder_sro_name": "Test SRO",
            "builder_sro_ogrn": "111222333",
            "builder_sro_inn": "444555666",
        }
        app_client.post(
            f"/api/requisites/{obj_id}",
            data=json.dumps(reqs),
            content_type="application/json",
        )
        resp = app_client.get(f"/api/requisites/{obj_id}/aocr")
        data = resp.get_json()
        assert "SRO-123" in data["builder_continued2"]
        assert "Test SRO" in data["builder_continued2"]
        assert "ОГРН 111222333" in data["builder_continued2"]
        assert "ИНН 444555666" in data["builder_continued2"]
