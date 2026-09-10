import os
import tempfile
from pathlib import Path
from uuid import uuid4

_test_directory = tempfile.TemporaryDirectory(prefix="ad-questionnaire-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{(Path(_test_directory.name) / 'test.db').as_posix()}"

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.core.database import engine


@pytest.fixture(scope="session", autouse=True)
def close_test_database():
    yield
    engine.dispose()
    _test_directory.cleanup()


def auth(client: TestClient, username: str, password: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def valid_answers(schema: dict) -> dict:
    answers = {}
    for section in schema["sections"]:
        for question in section["questions"]:
            if not question.get("required"):
                continue
            if question.get("options"):
                answers[question["key"]] = question["options"][0]["value"]
            elif question["type"] in {"integer", "number", "duration"}:
                answers[question["key"]] = question.get("min", 1)
            elif question["type"] == "date":
                answers[question["key"]] = "2026-08-27"
            elif question["type"] == "time":
                answers[question["key"]] = "09:00"
            else:
                answers[question["key"]] = "演示答案"
    return answers


def test_staff_patient_assignment_submission_statistics_flow():
    with TestClient(app) as client:
        doctor = auth(client, "doctor1", "Doctor123!")
        before = client.get("/api/v1/statistics/overview", headers=doctor).json()["assessment_count"]
        code = f"T{uuid4().hex[:10].upper()}"
        created = client.post("/api/v1/patients", headers=doctor, json={"patient_code": code, "full_name": "闭环测试患者"})
        assert created.status_code == 201, created.text
        patient_id = created.json()["id"]

        questionnaires = client.get("/api/v1/questionnaires", headers=doctor)
        assert questionnaires.status_code == 200
        version_id = questionnaires.json()[0]["latest_version_id"]
        assigned = client.post("/api/v1/assignments", headers=doctor, json={
            "patient_id": patient_id,
            "questionnaire_version_ids": [version_id],
            "title": "自动化闭环测试",
        })
        assert assigned.status_code == 201, assigned.text
        secret = assigned.json()
        assert secret["patient_code"] == code
        assert secret["patient_name"] == "闭环测试患者"

        verified = client.post("/api/v1/patient-session/verify", json={
            "token": secret["token"], "access_code": secret["access_code"],
        })
        assert verified.status_code == 200, verified.text
        patient_headers = {"Authorization": f"Bearer {verified.json()['access_token']}"}
        tasks = client.get("/api/v1/patient-session/tasks", headers=patient_headers).json()
        assert tasks["assignment"]["patient_name"] == "闭环测试患者"
        item_id = tasks["items"][0]["id"]
        task = client.get(f"/api/v1/patient-session/tasks/{item_id}", headers=patient_headers).json()
        answers = valid_answers(task["schema"])

        draft = client.put(f"/api/v1/patient-session/tasks/{item_id}/draft", headers=patient_headers,
                           json={"answers": answers, "revision": 0})
        assert draft.status_code == 200, draft.text
        submit_headers = {**patient_headers, "Idempotency-Key": uuid4().hex}
        submitted = client.post(f"/api/v1/patient-session/tasks/{item_id}/submit", headers=submit_headers,
                                json={"answers": answers, "revision": draft.json()["revision"]})
        assert submitted.status_code == 200, submitted.text
        assert submitted.json()["risk_level"] in {"low", "medium", "high", "unknown"}
        repeated = client.post(f"/api/v1/patient-session/tasks/{item_id}/submit", headers=submit_headers,
                               json={"answers": answers, "revision": draft.json()["revision"]})
        assert repeated.status_code == 200

        after = client.get("/api/v1/statistics/overview", headers=doctor).json()["assessment_count"]
        assert after == before + 1


def test_doctor_cannot_read_another_doctors_patient():
    with TestClient(app) as client:
        doctor1 = auth(client, "doctor1", "Doctor123!")
        doctor2 = auth(client, "doctor2", "Doctor123!")
        patient_id = client.get("/api/v1/patients", headers=doctor1).json()["items"][0]["id"]
        response = client.get(f"/api/v1/patients/{patient_id}", headers=doctor2)
        assert response.status_code == 403


def test_demo_patient_link_is_available():
    with TestClient(app) as client:
        verified = client.post("/api/v1/patient-session/verify", json={
            "token": "demo-patient-token", "access_code": "123456",
        })
        assert verified.status_code == 200, verified.text
        headers = {"Authorization": f"Bearer {verified.json()['access_token']}"}
        tasks = client.get("/api/v1/patient-session/tasks", headers=headers)
        assert tasks.status_code == 200
        assert len(tasks.json()["items"]) == 2


def test_admin_can_manage_doctor_permissions_and_backend_enforces_them():
    with TestClient(app) as client:
        admin = auth(client, "admin", "Admin123!")
        suffix = uuid4().hex[:8]
        departments = client.get("/api/v1/admin/departments", headers=admin).json()
        created = client.post("/api/v1/admin/users", headers=admin, json={
            "username": f"limited_{suffix}", "password": "Limited123!",
            "display_name": "受限医生", "role": "doctor", "department_id": departments[0]["id"],
            "permissions": {"can_create_patients": False, "can_assign_questionnaires": False,
                            "can_review_results": False, "can_manage_templates": False},
        })
        assert created.status_code == 201, created.text
        limited = auth(client, f"limited_{suffix}", "Limited123!")
        denied = client.post("/api/v1/patients", headers=limited, json={"patient_code": f"L{suffix}", "full_name": "受限测试患者"})
        assert denied.status_code == 403
        updated = client.patch(f"/api/v1/admin/users/{created.json()['id']}", headers=admin,
                               json={"permissions": {"can_create_patients": True}})
        assert updated.status_code == 200, updated.text
        allowed = client.post("/api/v1/patients", headers=limited, json={"patient_code": f"L{suffix}", "full_name": "受限测试患者"})
        assert allowed.status_code == 201, allowed.text


def test_patient_longitudinal_analysis_and_clinical_record_flow():
    with TestClient(app) as client:
        doctor = auth(client, "doctor1", "Doctor123!")
        code = f"C{uuid4().hex[:9].upper()}"
        patient = client.post("/api/v1/patients", headers=doctor, json={"patient_code": code, "full_name": "纵向档案测试患者"}).json()
        updated = client.patch(f"/api/v1/patients/{patient['id']}", headers=doctor, json={
            "sex": "female", "birth_date": "1958-06-18",
            "education_level": "高中", "residence_type": "与家人同住",
        })
        assert updated.status_code == 200, updated.text
        assert updated.json()["education_level"] == "高中"
        record = client.post(f"/api/v1/patients/{patient['id']}/clinical-records", headers=doctor, json={
            "record_type": "follow_up", "title": "自动化随访记录", "content": "情况稳定，计划下月复评。",
        })
        assert record.status_code == 201, record.text
        records = client.get(f"/api/v1/patients/{patient['id']}/clinical-records", headers=doctor)
        assert records.status_code == 200 and records.json()[0]["title"] == "自动化随访记录"
        analysis = client.get(f"/api/v1/patients/{patient['id']}/analysis", headers=doctor)
        assert analysis.status_code == 200, analysis.text
        assert analysis.json()["recent_records"][0]["record_type"] == "follow_up"
        assert analysis.json()["assessment_count"] == 0


def test_admin_can_modify_and_reassign_pending_assignment():
    with TestClient(app) as client:
        doctor1 = auth(client, "doctor1", "Doctor123!")
        doctor2 = auth(client, "doctor2", "Doctor123!")
        admin = auth(client, "admin", "Admin123!")
        code = f"R{uuid4().hex[:9].upper()}"
        patient = client.post("/api/v1/patients", headers=doctor1, json={"patient_code": code, "full_name": "归档权限测试患者"}).json()
        version_id = client.get("/api/v1/questionnaires", headers=doctor1).json()[0]["latest_version_id"]
        assignment = client.post("/api/v1/assignments", headers=doctor1, json={
            "patient_id": patient["id"], "questionnaire_version_ids": [version_id], "title": "待转交任务",
        }).json()
        doctor2_id = client.get("/api/v1/auth/me", headers=doctor2).json()["id"]
        changed = client.patch(f"/api/v1/assignments/{assignment['id']}", headers=admin,
                               json={"title": "管理员已转交", "doctor_id": doctor2_id})
        assert changed.status_code == 200, changed.text
        assert changed.json()["doctor_id"] == doctor2_id
        assert any(row["id"] == assignment["id"] for row in client.get("/api/v1/assignments", headers=doctor2).json())
        assert client.delete(f"/api/v1/patients/{patient['id']}", headers=doctor1).status_code == 403
        archived = client.delete(f"/api/v1/patients/{patient['id']}", headers=admin)
        assert archived.status_code == 200 and archived.json()["status"] == "archived"


def test_admin_can_import_catalog_scales_and_create_new_versions():
    with TestClient(app) as client:
        admin = auth(client, "admin", "Admin123!")
        catalog = client.get("/api/v1/questionnaires/catalog", headers=admin)
        assert catalog.status_code == 200, catalog.text
        codes = {item["code"] for item in catalog.json()}
        assert {
            "OUC_SCD_Q9", "OUC_MMSE", "OUC_FAQ", "OUC_MOCA_B", "OUC_CDR", "OUC_ADAS_COG",
            "OUC_GDS_15", "OUC_ESS", "OUC_EDINBURGH",
        } <= codes
        imported = client.post("/api/v1/questionnaires/import-catalog", headers=admin,
                               json={"codes": ["OUC_SCD_Q9", "OUC_CDR"], "publish": False})
        assert imported.status_code == 200, imported.text
        assert all(item["version"] == 1 for item in imported.json()["items"])
        repeated = client.post("/api/v1/questionnaires/import-catalog", headers=admin,
                               json={"codes": ["OUC_SCD_Q9"], "publish": False})
        assert repeated.status_code == 200 and repeated.json()["items"][0]["version"] == 2
        templates = client.get("/api/v1/questionnaires", headers=admin).json()
        scd = next(item for item in templates if item["code"] == "OUC_SCD_Q9")
        assert scd["status"] == "draft" and scd["latest_version"] == 2
        assert sum(len(section["questions"]) for section in scd["schema_json"]["sections"]) == 9


def test_migrated_patient_scales_keep_authoritative_backend_scoring():
    from app.services.scale_catalog import catalog_items
    from app.services.scoring import score_questionnaire

    catalog = {item["code"]: item for item in catalog_items()}

    gds = catalog["OUC_GDS_15"]
    gds_answers = {f"gds_{index}": "yes" for index in range(1, 16)}
    total, dimensions, risk, review = score_questionnaire(
        gds["questionnaire_schema"], gds["scoring_json"], gds_answers
    )
    assert total == 10
    assert dimensions == {"情绪状态": 10}
    assert risk == "unknown" and review == "auto"

    ess = catalog["OUC_ESS"]
    ess_answers = {f"ess_{index}": 3 for index in range(1, 9)}
    total, dimensions, _, review = score_questionnaire(
        ess["questionnaire_schema"], ess["scoring_json"], ess_answers
    )
    assert total == 24
    assert dimensions == {"日间嗜睡": 24}
    assert review == "auto"

    handedness = catalog["OUC_EDINBURGH"]
    right_answers = {f"hand_{index}": "right" for index in range(1, 11)}
    left_answers = {f"hand_{index}": "left" for index in range(1, 11)}
    right_total, right_dimensions, _, _ = score_questionnaire(
        handedness["questionnaire_schema"], handedness["scoring_json"], right_answers
    )
    left_total, left_dimensions, _, _ = score_questionnaire(
        handedness["questionnaire_schema"], handedness["scoring_json"], left_answers
    )
    assert right_total == 100 and right_dimensions == {"左手累计": 0, "右手累计": 20}
    assert left_total == -100 and left_dimensions == {"左手累计": 20, "右手累计": 0}
