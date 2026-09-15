from datetime import datetime, timezone
from math import ceil
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.dependencies import PatientIdentity, patient_identity
from ..models import Assessment, LlmMessage, LlmSession, Response
from ..services.assignment import refresh_assignment_status
from ..services.audit import audit
from ..services.deepseek import DeepSeekUnavailable, analyze_moca_with_deepseek, generate_scd_reply, summarize_scd_interview
from ..services.moca_open import MOCA_OPEN_TASKS, analyze_moca_open_answers
from ..services.stt_scale import STT_AGE_BANDS, expected_sequence, threshold_for
from .patient_session import item_for_identity

router = APIRouter(prefix="/patient-session/tasks", tags=["C/B 辅助任务"])
B_CODES = {"BOSTON_NAMING", "STT_SHAPE_TRAIL_MAKING"}
C_CODES = {"SCD_INTERVIEW", "MOCA_OPEN_ANSWER", "SCD_STRUCTURED_INTERVIEW"}
MOCK_REPLIES = [
    ("这种变化大约从什么时候开始？请按实际感受回答。", .4, False),
    ("这种变化是否影响过日常安排？可以简单举一个例子。", .7, False),
    ("感谢您的回答，本次访谈记录已完成，后续由专业人员查看。", 1.0, True),
]


class AssistedSubmitInput(BaseModel):
    answers: dict[str, Any]
    revision: int
    metrics: dict[str, Any] = Field(default_factory=dict)


class MessageInput(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


def task_code(item) -> str:
    return item.questionnaire_version.template.code


def _validate_trail(payload: AssistedSubmitInput, item) -> dict[str, Any]:
    """校验 STT 连线提交：练习 + 正式两阶段，按 A/B 卷的完整序列核对，并按年龄阈值判读。

    前端提交格式（answers）：
      form: "A" | "B"；ageBand: "50-59" | "60-69" | "70-79"
      stages: { "<form>-practice": 阶段结果, "<form>-test": 阶段结果 }
      阶段结果：{ events: [{nodeId, timestampMs, x, y}], sequence: 已完成节点, errorCount }
    """
    answers = payload.answers
    form = answers.get("form")
    age_band = answers.get("ageBand")
    stages = answers.get("stages")
    if form not in ("A", "B"):
        raise HTTPException(422, "连线任务缺少有效的试卷标识（A/B 卷）")
    if age_band not in STT_AGE_BANDS:
        raise HTTPException(422, "连线任务缺少有效的年龄组信息")
    if not isinstance(stages, dict):
        raise HTTPException(422, "连线任务缺少分阶段结果")
    if age_band and threshold_for(form, age_band) is None:
        raise HTTPException(422, "连线任务年龄组不在阈值表范围内")

    stage_results: dict[str, Any] = {}
    for phase in ("practice", "test"):
        stage_key = f"{form}-{phase}"
        stage_data = stages.get(stage_key)
        if not isinstance(stage_data, dict):
            raise HTTPException(422, f"连线任务缺少{phase}阶段结果")
        expected = expected_sequence(form, phase)
        assert expected is not None
        stage_results[stage_key] = _validate_trail_stage(stage_data, expected, phase)
        if phase == "test":
            test_result = stage_results[stage_key]
            threshold = threshold_for(form, age_band)
            assert threshold is not None
            duration_ms = test_result["duration_ms"]
            duration_seconds = duration_ms / 1000
            test_result["age_band"] = age_band
            test_result["threshold_seconds"] = threshold
            test_result["duration_seconds"] = round(duration_seconds, 1)
            test_result["threshold_interpretation"] = (
                "达到异常阈值" if duration_seconds >= threshold else "未达到异常阈值")
    return {"completed": True, "form": form, "age_band": age_band, "stages": stage_results,
            "error_count": sum(stage["error_count"] for stage in stage_results.values()),
            "correction_count": sum(stage["correction_count"] for stage in stage_results.values()),
            "duration_ms": stage_results[f"{form}-test"]["duration_ms"]}


def _validate_trail_stage(stage_data: dict[str, Any], expected: tuple[str, ...], phase: str) -> dict[str, Any]:
    events = stage_data.get("events")
    if not isinstance(events, list) or not events:
        raise HTTPException(422, f"{phase}阶段连线事件格式不正确")
    progress = errors = corrections = 0
    previous_timestamp = -1
    error_since_progress = False
    normalized_events = []
    for event in events:
        node = event.get("nodeId") if isinstance(event, dict) else None
        timestamp = event.get("timestampMs") if isinstance(event, dict) else None
        if not isinstance(timestamp, (int, float)) or timestamp < previous_timestamp or timestamp < 0:
            raise HTTPException(422, "连线任务点击时间必须按顺序记录")
        x, y = event.get("x"), event.get("y")
        if (x is not None or y is not None) and (not isinstance(x, (int, float)) or not isinstance(y, (int, float)) or not 0 <= x <= 100 or not 0 <= y <= 100):
            raise HTTPException(422, "连线任务节点坐标不正确")
        expected_node = expected[progress] if progress < len(expected) else None
        correct = node == expected_node
        if correct:
            if error_since_progress:
                corrections += 1
                error_since_progress = False
            progress += 1
        else:
            errors += 1
            error_since_progress = True
        normalized_events.append({"node_id": node, "timestamp_ms": timestamp, "correct": correct,
                                  "expected_node": expected_node, "x": x, "y": y})
        previous_timestamp = timestamp
    if progress != len(expected):
        raise HTTPException(422, f"{phase}阶段连线尚未完成")
    elapsed_ms = stage_data.get("elapsedMs")
    duration = elapsed_ms if isinstance(elapsed_ms, (int, float)) else events[-1]["timestampMs"]
    if duration < previous_timestamp:
        raise HTTPException(422, "连线任务总用时不正确")
    return {"completed": True, "error_count": errors, "correction_count": corrections,
            "sequence": list(expected), "first_click_ms": events[0]["timestampMs"],
            "duration_ms": duration, "events": normalized_events}


def submit_record(db: Session, item, payload: AssistedSubmitInput, key: str,
                  auto_result: dict | None = None, candidate_result: dict | None = None) -> Assessment:
    response = item.response
    if response and response.status == "submitted":
        if response.idempotency_key == key:
            return db.scalar(select(Assessment).where(Assessment.assignment_item_id == item.id))
        raise HTTPException(409, "任务已经提交")
    if response and response.revision != payload.revision:
        raise HTTPException(409, "答案版本冲突，请刷新后提交")
    now = datetime.now(timezone.utc)
    if response is None:
        response = Response(assignment_item_id=item.id, answers_json={}, revision=0)
        db.add(response)
        db.flush()
    response.answers_json = {**payload.answers, "_metrics": payload.metrics}
    response.status, response.idempotency_key, response.submitted_at = "submitted", key, now
    started = response.started_at if response.started_at.tzinfo else response.started_at.replace(tzinfo=timezone.utc)
    response.duration_seconds = max(1, ceil((now - started).total_seconds()))
    response.revision += 1
    assessment = Assessment(
        assignment_item_id=item.id, patient_id=item.assignment.patient_id, doctor_id=item.assignment.doctor_id,
        questionnaire_code=task_code(item), total_score=None, dimension_scores={}, risk_level="unknown",
        review_status="pending", auto_result_json=auto_result or {},
        candidate_result_json=candidate_result or {}, final_result_json={},
    )
    db.add(assessment)
    item.status = "submitted"
    db.flush()
    refresh_assignment_status(db, item.assignment)
    audit(db, "patient-link", item.assignment_id, "assisted_task.submit", "assignment_item", item.id)
    db.commit()
    db.refresh(assessment)
    return assessment


def acknowledgement(assessment: Assessment) -> dict:
    return {"submission_id": assessment.id, "status": "awaiting_clinician", "message": "记录已保存，将由专业人员复核。"}


@router.post("/{item_id}/assisted-submit")
def assisted_submit(payload: AssistedSubmitInput, item_id: int,
                     idempotency_key: str = Header(..., alias="Idempotency-Key"),
                     identity: PatientIdentity = Depends(patient_identity), db: Session = Depends(get_db)):
    item = item_for_identity(item_id, identity, db)
    code = task_code(item)
    if code not in B_CODES | C_CODES:
        raise HTTPException(422, "该任务不是 C/B 辅助任务")
    auto_result: dict[str, Any] = {}
    candidate_result: dict[str, Any] = {}
    if code == "BOSTON_NAMING":
        rows = payload.answers.get("items")
        if not isinstance(rows, list) or not rows:
            raise HTTPException(422, "Boston 任务答案不能为空")
        expected = item.questionnaire_version.scoring_json.get("expected_answers", {})
        scores = [{"question_id": row.get("questionId"), "score": int(str(row.get("answer", "")).strip() == str(expected.get(row.get("questionId"), "")))} for row in rows]
        if any(not row.get("questionId") or not str(row.get("answer", "")).strip() for row in rows):
            raise HTTPException(422, "Boston 答案格式不正确")
        auto_result = {"item_scores": scores, "provisional_total": sum(row["score"] for row in scores)}
    elif code == "STT_SHAPE_TRAIL_MAKING":
        auto_result = _validate_trail(payload, item)
    elif code == "MOCA_OPEN_ANSWER":
        answers = payload.answers.get("answers")
        if not isinstance(answers, dict):
            raise HTTPException(422, "MoCA-B 开放题答案格式不正确")
        missing = [task["id"] for task in MOCA_OPEN_TASKS if not str(answers.get(task["id"], "")).strip()]
        if missing:
            raise HTTPException(422, "MoCA-B 开放题答案不能为空")
        try:
            candidate_result = analyze_moca_with_deepseek(db, answers)
        except DeepSeekUnavailable as exc:
            candidate_result = {**analyze_moca_open_answers(answers), "fallback_reason": str(exc)}
    elif code == "SCD_INTERVIEW":
        messages = payload.answers.get("messages", [])
        if isinstance(messages, list) and messages:
            try:
                candidate_result = summarize_scd_interview(db, messages)
            except DeepSeekUnavailable as exc:
                candidate_result = {"status": "candidate_generated", "requires_clinician_review": True,
                                    "source": "local_fallback", "fallback_reason": str(exc)}
        else:
            candidate_result = {"status": "candidate_generated", "requires_clinician_review": True,
                                "source": "local_fallback"}
    elif code == "SCD_STRUCTURED_INTERVIEW":
        answers = payload.answers
        selected_domains = answers.get("selectedDomains", [])
        main_answers = answers.get("mainAnswers", {})
        follow_up_answers = answers.get("followUpAnswers", {})
        informant_data = answers.get("informant", )
        additional_info = answers.get("additionalInformation", {})

        if not isinstance(selected_domains, list) or not selected_domains:
            raise HTTPException(422, "SCD 结构性问卷必须至少选择一个认知域")
        if not isinstance(main_answers, dict):
            raise HTTPException(422, "SCD 结构性问卷主要答案格式不正确")

        # 计算基础统计
        positive_domains = [domain for domain in selected_domains if main_answers.get(domain) is True]
        has_concern = any(follow_up_answers.get(domain, {}).get("A") == 1 for domain in positive_domains)
        has_recent_onset = any(follow_up_answers.get(domain, {}).get("B") in [1, 2] for domain in positive_domains)
        worse_than_peers = any(follow_up_answers.get(domain, {}).get("C") == 1 for domain in positive_domains)
        sought_medical = any(follow_up_answers.get(domain, {}).get("D") == 1 for domain in positive_domains)

        auto_result = {
            "completed": True,
            "selected_domains": selected_domains,
            "positive_domains": positive_domains,
            "has_concern": has_concern,
            "has_recent_onset": has_recent_onset,
            "worse_than_peers": worse_than_peers,
            "sought_medical_help": sought_medical,
            "informant_available": informant_data.get("available", False),
            "informant_relation": informant_data.get("relation"),
        }

        candidate_result = {
            "status": "candidate_generated",
            "requires_clinician_review": True,
            "source": "structured_questionnaire",
            "summary": f"受访者报告 {len(positive_domains)}/{len(selected_domains)} 个认知域存在问题",
        }
    else:
        candidate_result = {"status": "candidate_generated", "requires_clinician_review": True,
                            "source": "local_fallback"}
    return acknowledgement(submit_record(db, item, payload, idempotency_key, auto_result, candidate_result))


@router.post("/{item_id}/llm/sessions/{session_id}/messages")
def interview_message(item_id: int, session_id: str, payload: MessageInput,
                      identity: PatientIdentity = Depends(patient_identity), db: Session = Depends(get_db)):
    item = item_for_identity(item_id, identity, db)
    if task_code(item) != "SCD_INTERVIEW":
        raise HTTPException(422, "该任务不是 C 类访谈任务")
    session = db.scalar(select(LlmSession).where(
        LlmSession.assignment_item_id == item.id, LlmSession.external_session_id == session_id))
    if session is None:
        session = LlmSession(assignment_item_id=item.id, external_session_id=session_id)
        db.add(session)
        db.flush()
    turns = db.scalar(select(func.count()).select_from(LlmMessage).where(
        LlmMessage.session_id == session.id, LlmMessage.role == "user")) or 0
    previous_messages = db.scalars(select(LlmMessage).where(LlmMessage.session_id == session.id).order_by(LlmMessage.id)).all()
    try:
        generated = generate_scd_reply(db, previous_messages, payload.message.strip())
        reply, progress, completed = generated["reply"], generated["progress"], generated["completed"]
    except DeepSeekUnavailable:
        reply, progress, completed = MOCK_REPLIES[min(turns, len(MOCK_REPLIES) - 1)]
    db.add_all([LlmMessage(session_id=session.id, role="user", content=payload.message.strip()),
                LlmMessage(session_id=session.id, role="assistant", content=reply)])
    session.progress, session.completed = round(progress * 100), completed
    item.status, item.assignment.status = "draft", "in_progress"
    db.commit()
    return {"reply": reply, "progress": progress, "completed": completed}
