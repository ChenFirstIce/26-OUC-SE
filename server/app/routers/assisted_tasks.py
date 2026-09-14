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
from .patient_session import item_for_identity

router = APIRouter(prefix="/patient-session/tasks", tags=["C/B 辅助任务"])
B_CODES = {"DEMO_BOSTON", "DEMO_TRAIL"}
C_CODES = {"DEMO_SCD_INTERVIEW", "DEMO_MOCA_OPEN"}
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
    if code == "DEMO_BOSTON":
        rows = payload.answers.get("items")
        if not isinstance(rows, list) or not rows:
            raise HTTPException(422, "Boston 任务答案不能为空")
        expected = item.questionnaire_version.scoring_json.get("expected_answers", {})
        scores = [{"question_id": row.get("questionId"), "score": int(str(row.get("answer", "")).strip() == str(expected.get(row.get("questionId"), "")))} for row in rows]
        if any(not row.get("questionId") or not str(row.get("answer", "")).strip() for row in rows):
            raise HTTPException(422, "Boston 答案格式不正确")
        auto_result = {"item_scores": scores, "provisional_total": sum(row["score"] for row in scores)}
    elif code == "DEMO_TRAIL":
        events = payload.answers.get("events")
        if not isinstance(events, list):
            raise HTTPException(422, "连线任务事件格式不正确")
        expected = item.questionnaire_version.scoring_json.get("sequence", [])
        progress = errors = 0
        for event in events:
            node = event.get("nodeId") if isinstance(event, dict) else None
            if progress < len(expected) and node == expected[progress]:
                progress += 1
            else:
                errors += 1
        if progress != len(expected):
            raise HTTPException(422, "连线任务尚未完成")
        auto_result = {"completed": True, "error_count": errors, "sequence": expected, "duration_ms": payload.metrics.get("durationMs")}
    else:
        candidate_result = {"status": "candidate_generated", "requires_clinician_review": True}
    return acknowledgement(submit_record(db, item, payload, idempotency_key, auto_result, candidate_result))


@router.post("/{item_id}/llm/sessions/{session_id}/messages")
def interview_message(item_id: int, session_id: str, payload: MessageInput,
                      identity: PatientIdentity = Depends(patient_identity), db: Session = Depends(get_db)):
    item = item_for_identity(item_id, identity, db)
    if task_code(item) != "DEMO_SCD_INTERVIEW":
        raise HTTPException(422, "该任务不是 C 类访谈任务")
    session = db.scalar(select(LlmSession).where(
        LlmSession.assignment_item_id == item.id, LlmSession.external_session_id == session_id))
    if session is None:
        session = LlmSession(assignment_item_id=item.id, external_session_id=session_id)
        db.add(session)
        db.flush()
    turns = db.scalar(select(func.count()).select_from(LlmMessage).where(
        LlmMessage.session_id == session.id, LlmMessage.role == "user")) or 0
    reply, progress, completed = MOCK_REPLIES[min(turns, len(MOCK_REPLIES) - 1)]
    db.add_all([LlmMessage(session_id=session.id, role="user", content=payload.message.strip()),
                LlmMessage(session_id=session.id, role="assistant", content=reply)])
    session.progress, session.completed = round(progress * 100), completed
    item.status, item.assignment.status = "draft", "in_progress"
    db.commit()
    return {"reply": reply, "progress": progress, "completed": completed}
