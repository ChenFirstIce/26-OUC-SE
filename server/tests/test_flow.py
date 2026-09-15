import os
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

_test_directory = tempfile.TemporaryDirectory(prefix="ad-questionnaire-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{(Path(_test_directory.name) / 'test.db').as_posix()}"

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.core.database import SessionLocal, engine
from app.models import Assessment, AssessmentReviewEvent, LlmMessage, LlmProviderConfig, Response


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
        assert task["revision"] == 0
        with SessionLocal() as db:
            response = db.get(Response, item_id)
            assert response is not None
            response.started_at = datetime.now(timezone.utc) - timedelta(seconds=75)
            db.commit()
        answers = valid_answers(task["schema"])

        draft = client.put(f"/api/v1/patient-session/tasks/{item_id}/draft", headers=patient_headers,
                           json={"answers": answers, "revision": 0})
        assert draft.status_code == 200, draft.text
        submit_headers = {**patient_headers, "Idempotency-Key": uuid4().hex}
        submitted = client.post(f"/api/v1/patient-session/tasks/{item_id}/submit", headers=submit_headers,
                                json={"answers": answers, "revision": draft.json()["revision"]})
        assert submitted.status_code == 200, submitted.text
        assert submitted.json()["risk_level"] in {"low", "medium", "high", "unknown"}
        result = client.get(f"/api/v1/assignments/{secret['id']}/items/{item_id}/result", headers=doctor)
        assert result.status_code == 200, result.text
        assert 75 <= result.json()["duration_seconds"] <= 76
        assert result.json()["submitted_at"].endswith("+00:00")
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
        assert len(tasks.json()["items"]) == 6


def test_cb_tasks_are_in_formal_patient_workflow_and_require_review():
    with TestClient(app) as client:
        verified = client.post("/api/v1/patient-session/verify", json={
            "token": "demo-patient-token", "access_code": "123456",
        }).json()
        headers = {"Authorization": f"Bearer {verified['access_token']}"}
        tasks = client.get("/api/v1/patient-session/tasks", headers=headers).json()["items"]
        by_code = {item["code"]: item for item in tasks}
        assert {"SCD_INTERVIEW", "MOCA_OPEN_ANSWER", "BOSTON_NAMING", "STT_SHAPE_TRAIL_MAKING"} <= set(by_code)

        scd_id = by_code["SCD_INTERVIEW"]["id"]
        detail = client.get(f"/api/v1/patient-session/tasks/{scd_id}", headers=headers).json()
        message = client.post(f"/api/v1/patient-session/tasks/{scd_id}/llm/sessions/test-session/messages",
                              headers=headers, json={"message": "最近半年开始有变化。"})
        assert message.status_code == 200 and message.json()["progress"] == .4
        draft = client.put(f"/api/v1/patient-session/tasks/{scd_id}/draft", headers=headers,
                           json={"answers": {"messages": [{"role": "user", "content": "最近半年"}]}, "revision": detail["revision"]})
        submitted = client.post(f"/api/v1/patient-session/tasks/{scd_id}/assisted-submit",
            headers={**headers, "Idempotency-Key": "cb-scd-submit"},
            json={"answers": {"messages": []}, "revision": draft.json()["revision"], "metrics": {"durationMs": 1000}})
        assert submitted.status_code == 200
        assert "candidate" not in submitted.text and "score" not in submitted.text

        moca_id = by_code["MOCA_OPEN_ANSWER"]["id"]
        moca_detail = client.get(f"/api/v1/patient-session/tasks/{moca_id}", headers=headers).json()
        empty_moca = client.post(f"/api/v1/patient-session/tasks/{moca_id}/assisted-submit",
            headers={**headers, "Idempotency-Key": "cb-moca-empty"}, json={
                "answers": {"answers": {"moca_payment_13": "", "moca_abstraction": ""}},
                "revision": moca_detail["revision"], "metrics": {"durationMs": 1000},
            })
        assert empty_moca.status_code == 422
        moca = client.post(f"/api/v1/patient-session/tasks/{moca_id}/assisted-submit",
            headers={**headers, "Idempotency-Key": "cb-moca-submit"}, json={
                "answers": {"answers": {
                    "moca_payment_13": "10元+2元+1元；5元+5元+2元+1元；13张1元",
                    "moca_abstraction": "火车和轮船都是交通工具；锣鼓和笛子都是乐器；南方和北方都是方位。",
                }, "completedAt": "2026-09-14T00:00:00+00:00"},
                "revision": moca_detail["revision"], "metrics": {"durationMs": 1200},
            })
        assert moca.status_code == 200 and "score" not in moca.text

        boston_id = by_code["BOSTON_NAMING"]["id"]
        boston_detail = client.get(f"/api/v1/patient-session/tasks/{boston_id}", headers=headers).json()
        boston = client.post(f"/api/v1/patient-session/tasks/{boston_id}/assisted-submit",
            headers={**headers, "Idempotency-Key": "cb-boston-submit"}, json={
                "answers": {"items": [{"questionId": "demo_boston_01", "answer": "雨伞"}]},
                "revision": boston_detail["revision"], "metrics": {"durationMs": 900},
            })
        assert boston.status_code == 200 and "score" not in boston.text
        trail_id = by_code["STT_SHAPE_TRAIL_MAKING"]["id"]
        trail_detail = client.get(f"/api/v1/patient-session/tasks/{trail_id}", headers=headers).json()
        from app.services.stt_scale import expected_sequence
        practice_seq = expected_sequence("A", "practice")
        test_seq = expected_sequence("A", "test")
        assert practice_seq and test_seq

        def trail_stage_events(sequence: tuple[str, ...]) -> list[dict]:
            # 在序列第 2 位插入一次错误点击，随后点回正确目标，验证错误/纠正统计。
            clicks = [sequence[0], sequence[2], *sequence[1:]]
            return [{"nodeId": node, "timestampMs": (index + 1) * 100,
                     "x": (index % 90) + 5, "y": (index % 80) + 5}
                    for index, node in enumerate(clicks)]

        trail = client.post(f"/api/v1/patient-session/tasks/{trail_id}/assisted-submit",
            headers={**headers, "Idempotency-Key": "cb-trail-submit"}, json={
                "answers": {"form": "A", "ageBand": "60-69", "stages": {
                    "A-practice": {"events": trail_stage_events(practice_seq), "errorCount": 1,
                                   "sequence": list(practice_seq)},
                    "A-test": {"events": trail_stage_events(test_seq), "errorCount": 1,
                               "sequence": list(test_seq), "elapsedMs": 60000}}},
                "revision": trail_detail["revision"], "metrics": {"durationMs": 80000},
            })
        assert trail.status_code == 200, trail.text
        with SessionLocal() as db:
            scd_assessment = db.query(Assessment).filter_by(assignment_item_id=scd_id).one()
            moca_assessment = db.query(Assessment).filter_by(assignment_item_id=moca_id).one()
            boston_assessment = db.query(Assessment).filter_by(assignment_item_id=boston_id).one()
            trail_assessment = db.query(Assessment).filter_by(assignment_item_id=trail_id).one()
            assert scd_assessment.candidate_result_json["requires_clinician_review"] is True
            assert not scd_assessment.final_result_json
            assert moca_assessment.candidate_result_json["candidate_total"] == 6
            assert moca_assessment.candidate_result_json["max_score"] == 6
            assert {item["question_id"] for item in moca_assessment.candidate_result_json["items"]} == {"moca_payment_13", "moca_abstraction"}
            assert boston_assessment.auto_result_json["provisional_total"] == 1
            trail_auto = trail_assessment.auto_result_json
            assert trail_auto["form"] == "A" and trail_auto["age_band"] == "60-69"
            assert trail_auto["error_count"] == 2 and trail_auto["correction_count"] == 2
            assert trail_auto["stages"]["A-practice"]["error_count"] == 1
            assert trail_auto["stages"]["A-test"]["threshold_seconds"] == 80
            assert trail_auto["stages"]["A-test"]["duration_seconds"] == 60.0
            assert trail_auto["stages"]["A-test"]["threshold_interpretation"] == "未达到异常阈值"
            assert trail_auto["stages"]["A-test"]["events"][0]["expected_node"] == test_seq[0]
            assert db.query(LlmMessage).count() >= 2

        doctor = auth(client, "doctor1", "Doctor123!")
        assignment_id = verified["assignment"]["id"]
        pending = client.get("/api/v1/statistics/pending-reviews", headers=doctor)
        assert pending.status_code == 200
        assert {row["item_id"] for row in pending.json()} >= {scd_id, boston_id}
        invalid = client.patch(f"/api/v1/assignments/{assignment_id}/items/{boston_id}/review", headers=doctor, json={
            "action": "confirm", "candidate_result": {}, "total_score": 4,
            "dimension_scores": {}, "risk_level": "unknown", "note": "",
        })
        assert invalid.status_code == 422
        invalid_max = client.patch(f"/api/v1/assignments/{assignment_id}/items/{boston_id}/review", headers=doctor, json={
            "action": "confirm", "candidate_result": {}, "total_score": 4,
            "dimension_scores": {"命名": 3}, "risk_level": "low", "note": "已核对",
        })
        assert invalid_max.status_code == 422 and "3" in invalid_max.text
        invalid_dimension = client.patch(f"/api/v1/assignments/{assignment_id}/items/{boston_id}/review", headers=doctor, json={
            "action": "confirm", "candidate_result": {}, "total_score": 1,
            "dimension_scores": {"自定义维度": 1}, "risk_level": "low", "note": "已核对",
        })
        assert invalid_dimension.status_code == 422 and "不在当前问卷版本" in invalid_dimension.text
        saved = client.patch(f"/api/v1/assignments/{assignment_id}/items/{boston_id}/review", headers=doctor, json={
            "action": "save", "candidate_result": {"accepted_items": 1}, "total_score": 1,
            "dimension_scores": {"命名": 1}, "risk_level": "unknown", "note": "候选结果待确认",
        })
        assert saved.status_code == 200 and saved.json()["status"] == "pending"
        confirmed = client.patch(f"/api/v1/assignments/{assignment_id}/items/{boston_id}/review", headers=doctor, json={
            "action": "confirm", "candidate_result": {"accepted_items": 1}, "total_score": 1,
            "dimension_scores": {"命名": 1}, "risk_level": "low", "note": "已核对原始回答",
        })
        assert confirmed.status_code == 200 and confirmed.json()["status"] == "reviewed"
        result = client.get(f"/api/v1/assignments/{assignment_id}/items/{boston_id}/result", headers=doctor).json()
        assert result["review_config"]["score"] == {"required": True, "min": 0, "max": 3}
        assert result["assessment"]["final_result"]["total_score"] == 1
        assert result["assessment"]["reviewed_by_name"] == "演示医生1"
        assert [event["action"] for event in result["review_history"]][:2] == ["confirm", "save"]

        reopened = client.post(f"/api/v1/assignments/{assignment_id}/items/{boston_id}/reopen", headers=doctor,
                               json={"reason": "请患者重新确认答案"})
        assert reopened.status_code == 200 and reopened.json()["item_status"] == "in_progress"
        reopened_detail = client.get(f"/api/v1/patient-session/tasks/{boston_id}", headers=headers).json()
        assert reopened_detail["status"] == "in_progress" and reopened_detail["revision"] == reopened.json()["revision"]
        assert reopened_detail["answers"] == {}
        with SessionLocal() as db:
            assert db.query(Assessment).filter_by(assignment_item_id=boston_id).count() == 0
            history = db.query(AssessmentReviewEvent).filter_by(assignment_item_id=boston_id).all()
            assert [event.action for event in history] == ["save", "confirm", "reopen"]
            assert history[-1].snapshot_json["response"]["answers"]["items"][0]["answer"] == "雨伞"


def test_admin_stores_deepseek_key_encrypted_and_hides_plaintext(monkeypatch):
    from app.core.config import settings

    with TestClient(app) as client:
        admin = auth(client, "admin", "Admin123!")
        doctor = auth(client, "doctor1", "Doctor123!")
        forbidden = client.get("/api/v1/admin/llm-config", headers=doctor)
        assert forbidden.status_code == 403
        object.__setattr__(settings, "llm_secret_key", "")
        missing_secret = client.put("/api/v1/admin/llm-config", headers=admin, json={
            "api_key": "sk-test-secret-1234", "enabled": True,
        })
        assert missing_secret.status_code == 422

        object.__setattr__(settings, "llm_secret_key", "unit-test-master-key")
        saved = client.put("/api/v1/admin/llm-config", headers=admin, json={
            "api_key": "sk-test-secret-1234", "enabled": True,
            "model": "deepseek-flash", "base_url": "https://api.deepseek.com",
        })
        assert saved.status_code == 200, saved.text
        body = saved.json()
        assert body["configured"] is True and body["enabled"] is True
        assert body["key_hint"].endswith("1234")
        assert "sk-test-secret-1234" not in saved.text
        loaded = client.get("/api/v1/admin/llm-config", headers=admin)
        assert loaded.status_code == 200 and "sk-test-secret-1234" not in loaded.text
        with SessionLocal() as db:
            row = db.query(LlmProviderConfig).filter_by(provider="deepseek").one()
            assert row.encrypted_api_key and "sk-test-secret-1234" not in row.encrypted_api_key


def test_deepseek_success_and_failure_paths(monkeypatch):
    from app.core.config import settings
    import app.services.deepseek as deepseek

    object.__setattr__(settings, "llm_secret_key", "unit-test-master-key")

    def fake_chat_json(_db, messages, *, max_tokens=None):
        system = messages[0]["content"]
        if "结构化访谈助手" in system:
            return {"reply": "这种变化是否影响日常安排？", "progress": 0.66, "completed": False}
        if "MoCA-B 开放题候选计分助手" in system:
            return {"items": [
                {"question_id": "moca_payment_13", "task_type": "payment", "candidate_score": 2, "explanation": "识别到两种付款方式。"},
                {"question_id": "moca_abstraction", "task_type": "abstraction", "candidate_score": 3, "explanation": "三组抽象分类均正确。"},
            ], "candidate_total": 5, "max_score": 6, "explanation": "候选总分 5/6。"}
        return {"ok": True, "message": "connected"}

    monkeypatch.setattr(deepseek, "_chat_json", fake_chat_json)

    def create_cb_assignment(client, doctor_headers):
        patient = client.post("/api/v1/patients", headers=doctor_headers, json={
            "patient_code": f"DS{uuid4().hex[:8].upper()}", "full_name": "DeepSeek 测试患者",
        })
        assert patient.status_code == 201, patient.text
        templates = client.get("/api/v1/questionnaires", headers=doctor_headers).json()
        versions = [next(item["latest_version_id"] for item in templates if item["code"] == code)
                    for code in ("SCD_INTERVIEW", "MOCA_OPEN_ANSWER")]
        assignment = client.post("/api/v1/assignments", headers=doctor_headers, json={
            "patient_id": patient.json()["id"], "questionnaire_version_ids": versions, "title": "DeepSeek C 类测试",
        })
        assert assignment.status_code == 201, assignment.text
        verified = client.post("/api/v1/patient-session/verify", json={
            "token": assignment.json()["token"], "access_code": assignment.json()["access_code"],
        })
        assert verified.status_code == 200, verified.text
        return {"Authorization": f"Bearer {verified.json()['access_token']}"}

    with TestClient(app) as client:
        admin = auth(client, "admin", "Admin123!")
        doctor = auth(client, "doctor1", "Doctor123!")
        assert client.put("/api/v1/admin/llm-config", headers=admin, json={
            "api_key": "sk-deepseek-unit-5678", "enabled": True,
        }).status_code == 200
        assert client.post("/api/v1/admin/llm-config/test", headers=admin).json()["ok"] is True

        headers = create_cb_assignment(client, doctor)
        tasks = client.get("/api/v1/patient-session/tasks", headers=headers).json()["items"]
        by_code = {item["code"]: item for item in tasks}
        scd_id = by_code["SCD_INTERVIEW"]["id"]
        moca_id = by_code["MOCA_OPEN_ANSWER"]["id"]

        scd_reply = client.post(f"/api/v1/patient-session/tasks/{scd_id}/llm/sessions/deepseek-test/messages",
            headers=headers, json={"message": "最近半年开始有变化。"})
        assert scd_reply.status_code == 200, scd_reply.text
        assert scd_reply.json()["reply"] == "这种变化是否影响日常安排？"
        assert scd_reply.json()["progress"] == 0.66

        moca_detail = client.get(f"/api/v1/patient-session/tasks/{moca_id}", headers=headers).json()
        moca = client.post(f"/api/v1/patient-session/tasks/{moca_id}/assisted-submit",
            headers={**headers, "Idempotency-Key": "deepseek-moca-submit"}, json={
                "answers": {"answers": {
                    "moca_payment_13": "10元+2元+1元；5元+5元+2元+1元",
                    "moca_abstraction": "交通工具、乐器、方位",
                }},
                "revision": moca_detail["revision"], "metrics": {"durationMs": 1200},
            })
        assert moca.status_code == 200 and "score" not in moca.text
        with SessionLocal() as db:
            assessment = db.query(Assessment).filter_by(assignment_item_id=moca_id).one()
            assert assessment.candidate_result_json["source"] == "deepseek"
            assert assessment.candidate_result_json["candidate_total"] == 5

    def failing_chat_json(*_args, **_kwargs):
        raise deepseek.DeepSeekUnavailable("unit_failure")

    monkeypatch.setattr(deepseek, "_chat_json", failing_chat_json)
    with TestClient(app) as client:
        doctor = auth(client, "doctor1", "Doctor123!")
        headers = create_cb_assignment(client, doctor)
        tasks = client.get("/api/v1/patient-session/tasks", headers=headers).json()["items"]
        by_code = {item["code"]: item for item in tasks}
        scd_id = by_code["SCD_INTERVIEW"]["id"]
        reply = client.post(f"/api/v1/patient-session/tasks/{scd_id}/llm/sessions/fallback-test/messages",
            headers=headers, json={"message": "最近半年开始有变化。"})
        assert reply.status_code == 200
        assert reply.json()["reply"] == "这种变化大约从什么时候开始？请按实际感受回答。"


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
        first_preview = client.post("/api/v1/questionnaires/import-preview/catalog", headers=admin,
                                    json={"codes": ["OUC_SCD_Q9", "OUC_CDR"]}).json()["items"]
        imported = client.post("/api/v1/questionnaires/import-catalog", headers=admin, json={
            "codes": ["OUC_SCD_Q9", "OUC_CDR"], "publish": False,
            "preview_hashes": {item["code"]: item["content_hash"] for item in first_preview},
            "preview_versions": {item["code"]: item["current_version"] for item in first_preview},
        })
        assert imported.status_code == 200, imported.text
        assert all(item["version"] == 1 for item in imported.json()["items"])
        repeat_preview = client.post("/api/v1/questionnaires/import-preview/catalog", headers=admin,
                                     json={"codes": ["OUC_SCD_Q9"]}).json()["items"]
        repeated = client.post("/api/v1/questionnaires/import-catalog", headers=admin, json={
            "codes": ["OUC_SCD_Q9"], "publish": False,
            "preview_hashes": {item["code"]: item["content_hash"] for item in repeat_preview},
            "preview_versions": {item["code"]: item["current_version"] for item in repeat_preview},
        })
        assert repeated.status_code == 200 and repeated.json()["items"][0]["version"] == 2
        templates = client.get("/api/v1/questionnaires", headers=admin).json()
        scd = next(item for item in templates if item["code"] == "OUC_SCD_Q9")
        assert scd["status"] == "draft" and scd["latest_version"] == 2
        assert sum(len(section["questions"]) for section in scd["schema_json"]["sections"]) == 9


def test_questionnaire_preview_publish_diff_and_retire_governance():
    with TestClient(app) as client:
        admin = auth(client, "admin", "Admin123!")
        doctor = auth(client, "doctor1", "Doctor123!")
        code = f"GOV_{uuid4().hex[:8].upper()}"
        template = {
            "code": code, "name": "治理流程测试问卷", "description": "验证预览、发布与停用",
            "questionnaire_schema": {
                "title": "治理流程测试问卷", "administration_mode": "patient_self",
                "source": {"file_name": "自动化测试", "review_note": "仅测试"},
                "sections": [{"key": "basic", "title": "基本题", "questions": [{
                    "key": "q1", "type": "yes_no", "label": "测试问题", "required": True,
                    "options": [{"value": "yes", "label": "是", "score": 1}, {"value": "no", "label": "否", "score": 0}],
                }]}],
            },
            "scoring_json": {"strategy": "metadata_sum", "risk_thresholds": []},
        }
        package = {"templates": [template], "conflict_strategy": "new_version", "publish": False}
        preview = client.post("/api/v1/questionnaires/import-preview", headers=admin, json=package)
        assert preview.status_code == 200, preview.text
        preview_item = preview.json()["items"][0]
        assert preview_item["valid"] is True and preview_item["action"] == "create"

        missing_preview = client.post("/api/v1/questionnaires/import-package", headers=admin, json=package)
        assert missing_preview.status_code == 409
        package["preview_hashes"] = {code: preview_item["content_hash"]}
        package["preview_versions"] = {code: preview_item["current_version"]}
        imported = client.post("/api/v1/questionnaires/import-package", headers=admin, json=package)
        assert imported.status_code == 200, imported.text
        row = next(item for item in client.get("/api/v1/questionnaires", headers=admin).json() if item["code"] == code)
        versions = client.get(f"/api/v1/questionnaires/{row['id']}/versions", headers=admin).json()
        version = versions[0]
        assert version["status"] == "draft" and not version["errors"] and not version["warnings"]

        published = client.post(f"/api/v1/questionnaires/versions/{version['id']}/publish", headers=admin, json={
            "expected_content_hash": version["content_hash"], "confirmation_code": code,
            "change_summary": "首次审核发布", "acknowledge_warnings": False,
        })
        assert published.status_code == 200, published.text
        assert published.json()["status"] == "published"
        doctor_row = next(item for item in client.get("/api/v1/questionnaires", headers=doctor).json() if item["code"] == code)
        assert doctor_row["latest_version_id"] == version["id"]

        patient = client.get("/api/v1/patients", headers=doctor).json()["items"][0]
        assignment = client.post("/api/v1/assignments", headers=doctor, json={
            "patient_id": patient["id"], "questionnaire_version_ids": [version["id"]], "title": "治理历史任务",
        })
        assert assignment.status_code == 201, assignment.text

        retired = client.post(f"/api/v1/questionnaires/versions/{version['id']}/retire", headers=admin, json={
            "confirmation_code": code, "reason": "自动化测试停用",
        })
        assert retired.status_code == 200 and retired.json()["status"] == "retired"
        assert all(item["code"] != code for item in client.get("/api/v1/questionnaires", headers=doctor).json())
        denied = client.post("/api/v1/assignments", headers=doctor, json={
            "patient_id": patient["id"], "questionnaire_version_ids": [version["id"]], "title": "不应创建",
        })
        assert denied.status_code == 422
        verified = client.post("/api/v1/patient-session/verify", json={
            "token": assignment.json()["token"], "access_code": assignment.json()["access_code"],
        })
        assert verified.status_code == 200

        # Retiring a version must not break the already-pinned patient task.
        patient_headers = {"Authorization": f"Bearer {verified.json()['access_token']}"}
        item_id = assignment.json()["items"][0]["id"]
        old_task = client.get(f"/api/v1/patient-session/tasks/{item_id}", headers=patient_headers)
        assert old_task.status_code == 200
        submitted = client.post(
            f"/api/v1/patient-session/tasks/{item_id}/submit",
            headers={**patient_headers, "Idempotency-Key": uuid4().hex},
            json={"answers": valid_answers(old_task.json()["schema"]), "revision": old_task.json()["revision"]},
        )
        assert submitted.status_code == 200, submitted.text

        updated_template = {**template, "questionnaire_schema": {
            **template["questionnaire_schema"],
            "sections": [{"key": "basic", "title": "基本题", "questions": [
                *template["questionnaire_schema"]["sections"][0]["questions"],
                {"key": "q2", "type": "short_text", "label": "新增问题", "required": False},
            ]}],
        }}
        next_package = {"templates": [updated_template], "conflict_strategy": "new_version", "publish": False}
        next_preview = client.post("/api/v1/questionnaires/import-preview", headers=admin, json=next_package).json()["items"][0]
        next_package["preview_hashes"] = {code: next_preview["content_hash"]}
        next_package["preview_versions"] = {code: next_preview["current_version"]}
        assert client.post("/api/v1/questionnaires/import-package", headers=admin, json=next_package).status_code == 200
        updated_versions = client.get(f"/api/v1/questionnaires/{row['id']}/versions", headers=admin).json()
        compared = client.get(
            f"/api/v1/questionnaires/versions/{updated_versions[0]['id']}/diff",
            headers=admin, params={"base_version_id": updated_versions[1]["id"]},
        )
        assert compared.status_code == 200 and compared.json()["added_questions"] == ["q2"]


def test_questionnaire_governance_migration_upgrades_legacy_sqlite():
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine
    from sqlalchemy.pool import NullPool

    # Alembic/SQLite may keep a transient Windows file handle until interpreter teardown.
    with tempfile.TemporaryDirectory(prefix="ad-governance-migration-", ignore_cleanup_errors=True) as directory:
        database_path = Path(directory) / "legacy.db"
        with sqlite3.connect(database_path) as connection:
            connection.executescript("""
                CREATE TABLE questionnaire_templates (
                    id INTEGER PRIMARY KEY, name VARCHAR(120), description TEXT, status VARCHAR(20)
                );
                CREATE TABLE questionnaire_versions (
                    id INTEGER PRIMARY KEY, template_id INTEGER, version INTEGER,
                    schema_json JSON, scoring_json JSON, published_at DATETIME
                );
                INSERT INTO questionnaire_templates VALUES (1, '旧问卷', '旧说明', 'draft');
                INSERT INTO questionnaire_versions VALUES (1, 1, 1, '{}', '{}', '2026-01-01 00:00:00');
                INSERT INTO questionnaire_versions VALUES (2, 1, 2, '{}', '{}', NULL);
            """)
        backend_root = Path(__file__).resolve().parents[1]
        config = Config(str(backend_root / "alembic.ini"))
        config.set_main_option("script_location", str(backend_root / "alembic"))
        config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path.as_posix()}")
        migration_engine = create_engine(config.get_main_option("sqlalchemy.url"), poolclass=NullPool)
        try:
            with migration_engine.begin() as connection:
                config.attributes["connection"] = connection
                command.upgrade(config, "head")
        finally:
            migration_engine.dispose()
        with sqlite3.connect(database_path) as connection:
            columns = {row[1] for row in connection.execute("PRAGMA table_info(questionnaire_versions)")}
            statuses = connection.execute("SELECT version, status FROM questionnaire_versions ORDER BY version").fetchall()
            template_status = connection.execute("SELECT status FROM questionnaire_templates WHERE id = 1").fetchone()[0]
        assert {"status", "content_hash", "retired_at", "retirement_reason"} <= columns
        assert statuses == [(1, "published"), (2, "draft")]
        assert template_status == "published"


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
