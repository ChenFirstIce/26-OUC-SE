from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import get_db
from ..core.dependencies import PatientIdentity, patient_identity
from ..core.security import create_token, token_digest, verify_password
from ..models import Assessment, AssignmentItem, AssignmentPackage, Response
from ..services.assignment import is_expired, refresh_assignment_status
from ..services.audit import audit
from ..services.questionnaire import validate_answers
from ..services.scoring import score_questionnaire


router = APIRouter(prefix="/patient-session", tags=["患者填写"])


class VerifyInput(BaseModel):
    token: str
    access_code: str


class DraftInput(BaseModel):
    answers: dict[str, Any]
    revision: int


class SubmitInput(BaseModel):
    answers: dict[str, Any]
    revision: int


def get_assignment(identity: PatientIdentity, db: Session) -> AssignmentPackage:
    assignment = db.get(AssignmentPackage, identity.assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="派发任务不存在")
    if assignment.status == "revoked":
        raise HTTPException(status_code=410, detail="该任务已撤销")
    if is_expired(assignment) and assignment.status not in {"submitted", "reviewed"}:
        assignment.status = "expired"
        db.commit()
        raise HTTPException(status_code=410, detail="该任务已过期")
    return assignment


def item_for_identity(item_id: int, identity: PatientIdentity, db: Session) -> AssignmentItem:
    item = db.get(AssignmentItem, item_id)
    if not item or item.assignment_id != identity.assignment_id:
        raise HTTPException(status_code=404, detail="问卷任务不存在")
    get_assignment(identity, db)
    return item


@router.post("/verify")
def verify(payload: VerifyInput, db: Session = Depends(get_db)):
    assignment = db.scalar(select(AssignmentPackage).where(AssignmentPackage.token_hash == token_digest(payload.token)))
    if not assignment or not verify_password(payload.access_code, assignment.access_code_hash):
        raise HTTPException(status_code=401, detail="填写链接或访问码错误")
    if assignment.status == "revoked":
        raise HTTPException(status_code=410, detail="该任务已撤销")
    if is_expired(assignment) and assignment.status not in {"submitted", "reviewed"}:
        assignment.status = "expired"
        db.commit()
        raise HTTPException(status_code=410, detail="该任务已过期")
    audit(db, "patient-link", assignment.id, "assignment.verify", "assignment", assignment.id)
    db.commit()
    token = create_token(str(assignment.id), "patient-link", settings.patient_session_minutes, assignment_id=assignment.id)
    return {"access_token": token, "token_type": "bearer", "assignment": assignment_summary(assignment)}


def assignment_summary(assignment: AssignmentPackage) -> dict:
    return {
        "id": assignment.id, "title": assignment.title, "note": assignment.note,
        "status": assignment.status, "deadline": assignment.deadline,
        "patient_code": assignment.patient.patient_code,
        "doctor_name": assignment.doctor.display_name,
    }


@router.get("/tasks")
def tasks(identity: PatientIdentity = Depends(patient_identity), db: Session = Depends(get_db)):
    assignment = get_assignment(identity, db)
    return {
        "assignment": assignment_summary(assignment),
        "items": [{
            "id": item.id, "status": item.status,
            "name": item.questionnaire_version.template.name,
            "code": item.questionnaire_version.template.code,
            "description": item.questionnaire_version.template.description,
            "version": item.questionnaire_version.version,
        } for item in assignment.items],
    }


@router.get("/tasks/{item_id}")
def task(item_id: int, identity: PatientIdentity = Depends(patient_identity), db: Session = Depends(get_db)):
    item = item_for_identity(item_id, identity, db)
    response = item.response
    return {
        "id": item.id, "status": item.status,
        "name": item.questionnaire_version.template.name,
        "description": item.questionnaire_version.template.description,
        "schema": item.questionnaire_version.schema_json,
        "answers": response.answers_json if response else {},
        "revision": response.revision if response else 0,
    }


@router.put("/tasks/{item_id}/draft")
def save_draft(payload: DraftInput, item_id: int, identity: PatientIdentity = Depends(patient_identity), db: Session = Depends(get_db)):
    item = item_for_identity(item_id, identity, db)
    if item.status in {"submitted", "reviewed"}:
        raise HTTPException(status_code=409, detail="问卷已提交，不能修改")
    response = item.response
    if response and response.revision != payload.revision:
        raise HTTPException(status_code=409, detail="答案已在其他页面更新，请刷新后继续")
    if not response:
        response = Response(assignment_item_id=item.id, answers_json=payload.answers, revision=1)
        db.add(response)
    else:
        response.answers_json = payload.answers
        response.revision += 1
    item.status = "draft"
    item.assignment.status = "in_progress"
    db.commit()
    return {"saved": True, "revision": response.revision}


@router.post("/tasks/{item_id}/submit")
def submit(
    payload: SubmitInput, item_id: int,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    identity: PatientIdentity = Depends(patient_identity), db: Session = Depends(get_db),
):
    item = item_for_identity(item_id, identity, db)
    response = item.response
    if response and response.status == "submitted":
        if response.idempotency_key == idempotency_key:
            assessment = db.scalar(select(Assessment).where(Assessment.assignment_item_id == item.id))
            return assessment_view(assessment)
        raise HTTPException(status_code=409, detail="问卷已经提交")
    if response and response.revision != payload.revision:
        raise HTTPException(status_code=409, detail="答案版本冲突，请刷新后提交")
    errors = validate_answers(item.questionnaire_version.schema_json, payload.answers)
    if errors:
        raise HTTPException(status_code=422, detail={"message": "问卷校验失败", "errors": errors})
    now = datetime.now(timezone.utc)
    if not response:
        response = Response(assignment_item_id=item.id, answers_json=payload.answers, revision=1)
        db.add(response)
    response.answers_json = payload.answers
    response.status = "submitted"
    response.idempotency_key = idempotency_key
    response.submitted_at = now
    start = response.started_at
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    response.duration_seconds = max(0, int((now - start).total_seconds()))
    response.revision += 1
    total, dimensions, risk, review_status = score_questionnaire(
        item.questionnaire_version.schema_json, item.questionnaire_version.scoring_json, payload.answers
    )
    assessment = Assessment(
        assignment_item_id=item.id, patient_id=item.assignment.patient_id, doctor_id=item.assignment.doctor_id,
        questionnaire_code=item.questionnaire_version.template.code, total_score=total,
        dimension_scores=dimensions, risk_level=risk, review_status=review_status,
    )
    db.add(assessment)
    item.status = "submitted"
    db.flush()
    refresh_assignment_status(db, item.assignment)
    audit(db, "patient-link", item.assignment_id, "response.submit", "assignment_item", item.id)
    db.commit()
    db.refresh(assessment)
    return assessment_view(assessment)


def assessment_view(assessment: Assessment) -> dict:
    return {
        "id": assessment.id, "questionnaire_code": assessment.questionnaire_code,
        "total_score": assessment.total_score, "dimension_scores": assessment.dimension_scores,
        "risk_level": assessment.risk_level, "review_status": assessment.review_status,
        "assessed_at": assessment.assessed_at,
    }

