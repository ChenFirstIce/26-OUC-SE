from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


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
        created = client.post("/api/v1/patients", headers=doctor, json={"patient_code": code})
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

        verified = client.post("/api/v1/patient-session/verify", json={
            "token": secret["token"], "access_code": secret["access_code"],
        })
        assert verified.status_code == 200, verified.text
        patient_headers = {"Authorization": f"Bearer {verified.json()['access_token']}"}
        tasks = client.get("/api/v1/patient-session/tasks", headers=patient_headers).json()
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

