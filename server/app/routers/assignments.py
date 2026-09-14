from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import get_db
from ..core.dependencies import current_user, ensure_patient_scope
from ..core.security import hash_password, new_access_code, new_assignment_token, token_digest
from ..models import Assessment, AssessmentReviewEvent, AssignmentItem, AssignmentPackage, Patient, QuestionnaireVersion, User, utcnow
from ..services.questionnaire import all_questions
from ..services.assignment import refresh_assignment_status
from ..services.audit import audit
from ..services.permissions import require_permission
from ..services.review_rules import review_config, suggested_risk, validate_review_result


router = APIRouter(prefix="/assignments", tags=["问卷派发"])


class AssignmentInput(BaseModel):
    patient_id: int
    questionnaire_version_ids: list[int] = Field(min_length=1)
    title: str = Field(min_length=2, max_length=120)
    note: str = ""
    deadline: datetime | None = None
    doctor_id: int | None = None


class AssignmentUpdateInput(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=120)
    note: str | None = None
    deadline: datetime | None = None
    doctor_id: int | None = None


class ReviewInput(BaseModel):
    action: Literal["save", "confirm"]
    candidate_result: dict[str, Any] = Field(default_factory=dict)
    total_score: float | None = None
    dimension_scores: dict[str, float] = Field(default_factory=dict)
    risk_level: Literal["low", "medium", "high", "unknown"] = "unknown"
    note: str = Field(default="", max_length=2000)


class ReopenInput(BaseModel):
    reason: str = Field(min_length=2, max_length=500)


def review_snapshot(assessment: Assessment, response=None) -> dict:
    result = {
        "review_status": assessment.review_status, "total_score": assessment.total_score,
        "dimension_scores": assessment.dimension_scores or {}, "risk_level": assessment.risk_level,
        "auto_result": assessment.auto_result_json or {}, "candidate_result": assessment.candidate_result_json or {},
        "final_result": assessment.final_result_json or {}, "review_note": assessment.review_note,
    }
    if response:
        result["response"] = {"answers": response.answers_json or {}, "submitted_at": response.submitted_at.isoformat() if response.submitted_at else None}
    return result


def validate_final_review(payload: ReviewInput, item: AssignmentItem) -> None:
    if payload.action != "confirm":
        return
    validate_review_result(payload.total_score, payload.dimension_scores, payload.risk_level,
                           payload.note, item.questionnaire_version.scoring_json)


def assignment_view(assignment: AssignmentPackage, include_secret: dict | None = None) -> dict:
    result = {
        "id": assignment.id, "patient_id": assignment.patient_id,
        "patient_code": assignment.patient.patient_code,
        "patient_name": assignment.patient.profile.full_name if assignment.patient.profile else None,
        "doctor_id": assignment.doctor_id, "doctor_name": assignment.doctor.display_name,
        "title": assignment.title, "note": assignment.note, "status": assignment.status,
        "deadline": assignment.deadline, "created_at": assignment.created_at,
        "items": [{
            "id": item.id, "status": item.status,
            "questionnaire_version_id": item.questionnaire_version_id,
            "questionnaire_code": item.questionnaire_version.template.code,
            "questionnaire_name": item.questionnaire_version.name or item.questionnaire_version.template.name,
            "version": item.questionnaire_version.version,
        } for item in assignment.items],
    }
    if include_secret:
        result.update(include_secret)
    return result


@router.get("")
def list_assignments(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(AssignmentPackage).order_by(AssignmentPackage.created_at.desc())
    if user.role != "admin":
        query = query.where(AssignmentPackage.doctor_id == user.id)
    assignments = db.scalars(query).unique().all()
    for assignment in assignments:
        refresh_assignment_status(db, assignment)
    db.commit()
    return [assignment_view(a) for a in assignments]


@router.post("", status_code=201)
def create_assignment(payload: AssignmentInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_permission(db, user, "can_assign_questionnaires")
    patient = db.get(Patient, payload.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    ensure_patient_scope(user, patient.assigned_doctor_id)
    versions = db.scalars(select(QuestionnaireVersion).where(QuestionnaireVersion.id.in_(payload.questionnaire_version_ids))).all()
    if len(versions) != len(set(payload.questionnaire_version_ids)):
        raise HTTPException(status_code=422, detail="包含无效问卷版本")
    if any(v.status != "published" or not v.published_at for v in versions):
        raise HTTPException(status_code=422, detail="只能派发已发布问卷")
    if any(v.schema_json.get("administration_mode") == "clinician" for v in versions):
        raise HTTPException(status_code=422, detail="纯医生录入量表不能派发到患者端")
    raw_token = new_assignment_token()
    access_code = new_access_code()
    doctor_id = payload.doctor_id if user.role == "admin" and payload.doctor_id else patient.assigned_doctor_id
    doctor = db.get(User, doctor_id)
    if not doctor or doctor.role != "doctor" or not doctor.active:
        raise HTTPException(status_code=422, detail="负责医生不存在或不可用")
    assignment = AssignmentPackage(
        patient_id=patient.id, doctor_id=doctor_id, title=payload.title, note=payload.note,
        deadline=payload.deadline, token_hash=token_digest(raw_token), access_code_hash=hash_password(access_code),
    )
    db.add(assignment)
    db.flush()
    for version in versions:
        db.add(AssignmentItem(assignment_id=assignment.id, questionnaire_version_id=version.id))
    audit(db, "user", user.id, "assignment.create", "assignment", assignment.id)
    db.commit()
    db.refresh(assignment)
    link = f"{settings.frontend_origin}/p/fill/{raw_token}"
    return assignment_view(assignment, {"patient_link": link, "access_code": access_code, "token": raw_token})


@router.patch("/{assignment_id}")
def update_assignment(assignment_id: int, payload: AssignmentUpdateInput,
                      user: User = Depends(current_user), db: Session = Depends(get_db)):
    assignment = db.get(AssignmentPackage, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="派发任务不存在")
    ensure_patient_scope(user, assignment.doctor_id)
    require_permission(db, user, "can_assign_questionnaires")
    if assignment.status in {"submitted", "reviewed", "revoked"}:
        raise HTTPException(status_code=409, detail="已完成或撤销的任务不能修改")
    fields = payload.model_fields_set
    for field in ("title", "note", "deadline"):
        if field in fields:
            setattr(assignment, field, getattr(payload, field))
    if "doctor_id" in fields:
        if user.role != "admin":
            raise HTTPException(status_code=403, detail="只有管理员可以转交派发任务")
        doctor = db.get(User, payload.doctor_id) if payload.doctor_id else None
        if not doctor or doctor.role != "doctor" or not doctor.active:
            raise HTTPException(status_code=422, detail="负责医生不存在或不可用")
        assignment.doctor_id = doctor.id
    audit(db, "user", user.id, "assignment.update", "assignment", assignment.id)
    db.commit()
    return assignment_view(assignment)


@router.get("/{assignment_id}")
def get_assignment(assignment_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    assignment = db.get(AssignmentPackage, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="派发任务不存在")
    ensure_patient_scope(user, assignment.doctor_id)
    refresh_assignment_status(db, assignment)
    db.commit()
    return assignment_view(assignment)


@router.get("/{assignment_id}/items/{item_id}/result")
def get_item_result(
    assignment_id: int, item_id: int,
    user: User = Depends(current_user), db: Session = Depends(get_db),
):
    assignment = db.get(AssignmentPackage, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="派发任务不存在")
    ensure_patient_scope(user, assignment.doctor_id)
    item = db.get(AssignmentItem, item_id)
    if not item or item.assignment_id != assignment.id:
        raise HTTPException(status_code=404, detail="问卷任务不存在")
    if not item.response or item.response.status != "submitted":
        raise HTTPException(status_code=409, detail="患者尚未提交该问卷")
    assessment = db.scalar(select(Assessment).where(Assessment.assignment_item_id == item.id))
    if not assessment:
        raise HTTPException(status_code=404, detail="评估结果不存在")
    answers = item.response.answers_json or {}
    answer_items = []
    for question in all_questions(item.questionnaire_version.schema_json):
        raw_value = answers.get(question["key"])
        option_labels = {str(option["value"]): option["label"] for option in question.get("options", [])}
        if isinstance(raw_value, list):
            display_value = "、".join(option_labels.get(str(value), str(value)) for value in raw_value)
        elif raw_value is None or raw_value == "":
            display_value = "未填写"
        else:
            display_value = option_labels.get(str(raw_value), str(raw_value))
        answer_items.append({
            "question_key": question["key"], "label": question.get("label", question["key"]),
            "type": question.get("type"), "raw_value": raw_value, "display_value": display_value,
            "dimension": question.get("dimension"),
        })
    events = db.scalars(select(AssessmentReviewEvent).where(
        AssessmentReviewEvent.assignment_item_id == item.id
    ).order_by(AssessmentReviewEvent.created_at.desc())).all()
    reviewer_ids = {event.reviewer_id for event in events}
    if assessment.reviewed_by_id:
        reviewer_ids.add(assessment.reviewed_by_id)
    reviewers = {row.id: row.display_name for row in db.scalars(
        select(User).where(User.id.in_(reviewer_ids))
    ).all()} if reviewer_ids else {}
    audit(db, "user", user.id, "response.view", "assignment_item", item.id)
    db.commit()
    return {
        "assignment_id": assignment.id, "item_id": item.id,
        "patient_code": assignment.patient.patient_code,
        "patient_name": assignment.patient.profile.full_name if assignment.patient.profile else None,
        "questionnaire_code": item.questionnaire_version.template.code,
        "questionnaire_name": item.questionnaire_version.name or item.questionnaire_version.template.name,
        "questionnaire_version": item.questionnaire_version.version,
        "review_config": review_config(item.questionnaire_version.scoring_json),
        "suggested_risk": suggested_risk(assessment.total_score, review_config(item.questionnaire_version.scoring_json)),
        "submitted_at": item.response.submitted_at,
        "duration_seconds": item.response.duration_seconds,
        "assessment": {
            "total_score": assessment.total_score, "dimension_scores": assessment.dimension_scores,
            "risk_level": assessment.risk_level, "review_status": assessment.review_status,
            "assessed_at": assessment.assessed_at, "auto_result": assessment.auto_result_json,
            "candidate_result": assessment.candidate_result_json, "final_result": assessment.final_result_json,
            "review_note": assessment.review_note, "reviewed_by_id": assessment.reviewed_by_id,
            "reviewed_by_name": reviewers.get(assessment.reviewed_by_id), "reviewed_at": assessment.reviewed_at,
        },
        "answers": answer_items, "raw_answers": answers if not answer_items else None,
        "review_history": [{"id": event.id, "action": event.action, "note": event.note,
            "reviewer_id": event.reviewer_id, "reviewer_name": reviewers.get(event.reviewer_id),
            "snapshot": event.snapshot_json, "created_at": event.created_at} for event in events],
    }


@router.patch("/{assignment_id}/items/{item_id}/review")
def review_item(assignment_id: int, item_id: int, payload: ReviewInput,
                user: User = Depends(current_user), db: Session = Depends(get_db)):
    assignment = db.get(AssignmentPackage, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="派发任务不存在")
    ensure_patient_scope(user, assignment.doctor_id)
    require_permission(db, user, "can_review_results")
    item = db.get(AssignmentItem, item_id)
    if not item or item.assignment_id != assignment.id:
        raise HTTPException(status_code=404, detail="问卷任务不存在")
    assessment = db.scalar(select(Assessment).where(Assessment.assignment_item_id == item.id))
    if not assessment or not item.response or item.response.status != "submitted":
        raise HTTPException(status_code=409, detail="患者尚未提交该问卷")
    if assessment.review_status == "reviewed":
        raise HTTPException(status_code=409, detail="最终结果已经确认，请先退回后重新评估")
    if assessment.review_status != "pending":
        raise HTTPException(status_code=409, detail="该问卷为自动计分结果，无需人工复核")
    validate_final_review(payload, item)
    assessment.candidate_result_json = payload.candidate_result
    assessment.review_note = payload.note
    action = "save"
    if payload.action == "confirm":
        assessment.total_score = payload.total_score
        assessment.dimension_scores = payload.dimension_scores
        assessment.risk_level = payload.risk_level
        assessment.final_result_json = {
            "total_score": payload.total_score, "dimension_scores": payload.dimension_scores,
            "risk_level": payload.risk_level, "note": payload.note,
        }
        assessment.review_status = "reviewed"
        assessment.reviewed_by_id = user.id
        assessment.reviewed_at = utcnow()
        item.status = "reviewed"
        action = "confirm"
        refresh_assignment_status(db, assignment)
    db.add(AssessmentReviewEvent(assessment_id=assessment.id, assignment_item_id=item.id,
        reviewer_id=user.id, action=action, note=payload.note, snapshot_json=review_snapshot(assessment)))
    audit(db, "user", user.id, f"assessment.review.{action}", "assessment", assessment.id)
    db.commit()
    return {"status": assessment.review_status, "item_status": item.status, "reviewed_at": assessment.reviewed_at}


@router.post("/{assignment_id}/items/{item_id}/reopen")
def reopen_item(assignment_id: int, item_id: int, payload: ReopenInput,
                user: User = Depends(current_user), db: Session = Depends(get_db)):
    assignment = db.get(AssignmentPackage, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="派发任务不存在")
    ensure_patient_scope(user, assignment.doctor_id)
    require_permission(db, user, "can_review_results")
    item = db.get(AssignmentItem, item_id)
    if not item or item.assignment_id != assignment.id:
        raise HTTPException(status_code=404, detail="问卷任务不存在")
    assessment = db.scalar(select(Assessment).where(Assessment.assignment_item_id == item.id))
    if not assessment or not item.response or item.response.status != "submitted":
        raise HTTPException(status_code=409, detail="只有已提交结果可以退回重做")
    if assessment.review_status not in {"pending", "reviewed"}:
        raise HTTPException(status_code=409, detail="自动计分结果不能通过复核流程退回")
    db.add(AssessmentReviewEvent(assessment_id=assessment.id, assignment_item_id=item.id,
        reviewer_id=user.id, action="reopen", note=payload.reason,
        snapshot_json=review_snapshot(assessment, item.response)))
    assessment_id = assessment.id
    db.delete(assessment)
    item.response.status = "draft"
    item.response.answers_json = {}
    item.response.idempotency_key = None
    item.response.submitted_at = None
    item.response.duration_seconds = None
    item.response.revision += 1
    item.response.started_at = utcnow()
    item.status = "in_progress"
    assignment.status = "in_progress"
    audit(db, "user", user.id, "assessment.review.reopen", "assessment", assessment_id)
    db.commit()
    return {"status": "reopened", "item_status": item.status, "revision": item.response.revision}


@router.post("/{assignment_id}/revoke")
def revoke(assignment_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    assignment = db.get(AssignmentPackage, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="派发任务不存在")
    ensure_patient_scope(user, assignment.doctor_id)
    require_permission(db, user, "can_assign_questionnaires")
    if assignment.status in {"submitted", "reviewed"}:
        raise HTTPException(status_code=409, detail="已提交任务不能撤销")
    assignment.status = "revoked"
    audit(db, "user", user.id, "assignment.revoke", "assignment", assignment.id)
    db.commit()
    return {"status": assignment.status}
