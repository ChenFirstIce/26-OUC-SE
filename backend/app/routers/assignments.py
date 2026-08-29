from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import get_db
from ..core.dependencies import current_user, ensure_patient_scope
from ..core.security import hash_password, new_access_code, new_assignment_token, token_digest
from ..models import Assessment, AssignmentItem, AssignmentPackage, Patient, QuestionnaireVersion, User
from ..services.questionnaire import all_questions
from ..services.assignment import refresh_assignment_status
from ..services.audit import audit
from ..services.permissions import require_permission


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


def assignment_view(assignment: AssignmentPackage, include_secret: dict | None = None) -> dict:
    result = {
        "id": assignment.id, "patient_id": assignment.patient_id,
        "patient_code": assignment.patient.patient_code,
        "doctor_id": assignment.doctor_id, "doctor_name": assignment.doctor.display_name,
        "title": assignment.title, "note": assignment.note, "status": assignment.status,
        "deadline": assignment.deadline, "created_at": assignment.created_at,
        "items": [{
            "id": item.id, "status": item.status,
            "questionnaire_version_id": item.questionnaire_version_id,
            "questionnaire_code": item.questionnaire_version.template.code,
            "questionnaire_name": item.questionnaire_version.template.name,
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
    if any(v.template.status != "published" or not v.published_at for v in versions):
        raise HTTPException(status_code=422, detail="只能派发已发布问卷")
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
    audit(db, "user", user.id, "response.view", "assignment_item", item.id)
    db.commit()
    return {
        "assignment_id": assignment.id, "item_id": item.id,
        "patient_code": assignment.patient.patient_code,
        "questionnaire_code": item.questionnaire_version.template.code,
        "questionnaire_name": item.questionnaire_version.template.name,
        "questionnaire_version": item.questionnaire_version.version,
        "submitted_at": item.response.submitted_at,
        "duration_seconds": item.response.duration_seconds,
        "assessment": {
            "total_score": assessment.total_score, "dimension_scores": assessment.dimension_scores,
            "risk_level": assessment.risk_level, "review_status": assessment.review_status,
            "assessed_at": assessment.assessed_at,
        },
        "answers": answer_items,
    }


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
