import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Header, Query
from sqlalchemy import select

from app.core.api import AppError
from app.core.config import settings
from app.core.security import create_token, hash_secret, make_access_code
from app.modules.assessments.models import Assessment
from app.modules.assignments.models import AssignmentItem, AssignmentPackage, Response
from app.modules.assignments.schemas import AssignmentCreate, DraftPayload, SubmitPayload, VerifyRequest
from app.modules.assignments.service import (
    create_assignment,
    refresh_package_status,
    serialize_package,
    serialize_task,
    validate_answers,
    verify_assignment,
)
from app.modules.audit.models import AuditLog
from app.modules.auth.dependencies import CurrentUser, DbDep, PatientClaims
from app.modules.patients.models import Patient
from app.modules.questionnaires.models import Question, QuestionnaireVersion
from app.modules.scoring.service import score_response


router = APIRouter(tags=["问卷派发与填写"])


def assignment_scope(user: CurrentUser):
    query = select(AssignmentPackage)
    if user.role == "doctor":
        query = query.where(AssignmentPackage.doctor_id == user.id)
    return query


@router.get("/assignments")
def list_assignments(
    user: CurrentUser,
    db: DbDep,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    query = assignment_scope(user)
    if status:
        query = query.where(AssignmentPackage.status == status)
    rows = db.scalars(query.order_by(AssignmentPackage.created_at.desc())).all()
    for row in rows:
        refresh_package_status(db, row)
    db.commit()
    sliced = rows[(page - 1) * page_size : page * page_size]
    return {"items": [serialize_package(db, row) for row in sliced], "total": len(rows), "page": page, "page_size": page_size}


@router.post("/assignments", status_code=201)
def create(payload: AssignmentCreate, user: CurrentUser, db: DbDep):
    row, token, code = create_assignment(db, payload, user)
    db.add(AuditLog(user_id=user.id, action="assignment.create", target_type="assignment", target_id=str(row.id)))
    db.commit()
    result = serialize_package(db, row, detailed=True)
    result.update(
        {
            "patient_url": f"{settings.frontend_url}/p/fill/{token}",
            "patient_token": token,
            "access_code": code,
        }
    )
    return result


@router.get("/assignments/{assignment_id}")
def get_assignment(assignment_id: int, user: CurrentUser, db: DbDep):
    row = db.scalar(assignment_scope(user).where(AssignmentPackage.id == assignment_id))
    if not row:
        raise AppError(404, "ASSIGNMENT_NOT_FOUND", "派发任务不存在或无权查看")
    refresh_package_status(db, row)
    db.commit()
    result = serialize_package(db, row, detailed=True)
    assessments = db.scalars(
        select(Assessment)
        .join(Response, Response.id == Assessment.response_id)
        .join(AssignmentItem, AssignmentItem.id == Response.assignment_item_id)
        .where(AssignmentItem.package_id == row.id)
    ).all()
    result["assessments"] = [
        {
            "id": item.id,
            "total_score": item.total_score,
            "dimension_scores": item.dimension_scores,
            "risk_level": item.risk_level,
            "review_status": item.review_status,
            "assessed_at": item.assessed_at,
        }
        for item in assessments
    ]
    return result


@router.post("/assignments/{assignment_id}/revoke")
def revoke(assignment_id: int, user: CurrentUser, db: DbDep):
    row = db.scalar(assignment_scope(user).where(AssignmentPackage.id == assignment_id))
    if not row:
        raise AppError(404, "ASSIGNMENT_NOT_FOUND", "派发任务不存在")
    if row.status in {"submitted", "reviewed"}:
        raise AppError(422, "ALREADY_SUBMITTED", "已提交任务不能撤销")
    row.status = "revoked"
    db.commit()
    return {"id": row.id, "status": row.status}


@router.post("/assignments/{assignment_id}/regenerate-code")
def regenerate_code(assignment_id: int, user: CurrentUser, db: DbDep):
    row = db.scalar(assignment_scope(user).where(AssignmentPackage.id == assignment_id))
    if not row:
        raise AppError(404, "ASSIGNMENT_NOT_FOUND", "派发任务不存在")
    if row.status in {"submitted", "reviewed", "revoked", "expired"}:
        raise AppError(422, "INVALID_ASSIGNMENT_STATUS", "当前任务状态不能重新生成访问码")
    code = make_access_code()
    row.access_code_hash = hash_secret(code)
    db.commit()
    return {"id": row.id, "access_code": code}


@router.post("/assignments/{assignment_id}/review")
def review(assignment_id: int, user: CurrentUser, db: DbDep):
    row = db.scalar(assignment_scope(user).where(AssignmentPackage.id == assignment_id))
    if not row:
        raise AppError(404, "ASSIGNMENT_NOT_FOUND", "派发任务不存在")
    if row.status != "submitted":
        raise AppError(422, "NOT_SUBMITTED", "只有已提交任务可以复核")
    row.status = "reviewed"
    row.reviewed_at = datetime.now(UTC)
    assessments = db.scalars(
        select(Assessment)
        .join(Response, Response.id == Assessment.response_id)
        .join(AssignmentItem, AssignmentItem.id == Response.assignment_item_id)
        .where(AssignmentItem.package_id == row.id)
    ).all()
    for assessment in assessments:
        assessment.reviewed_by_id = user.id
        if assessment.review_status == "pending_review":
            assessment.review_status = "reviewed"
    db.add(AuditLog(user_id=user.id, action="assignment.review", target_type="assignment", target_id=str(row.id)))
    db.commit()
    return {"id": row.id, "status": row.status, "reviewed_at": row.reviewed_at}


@router.post("/patient-session/verify")
def patient_verify(payload: VerifyRequest, db: DbDep):
    row = verify_assignment(db, payload.token, payload.access_code)
    session = create_token(
        str(row.id),
        "patient-link",
        minutes=settings.patient_session_minutes,
        assignment_id=row.id,
    )
    return {"session_token": session, "assignment": serialize_package(db, row, detailed=True)}


def patient_package(db: DbDep, claims: PatientClaims) -> AssignmentPackage:
    row = db.get(AssignmentPackage, int(claims["assignment_id"]))
    if not row:
        raise AppError(404, "ASSIGNMENT_NOT_FOUND", "填写任务不存在")
    refresh_package_status(db, row)
    if row.status in {"expired", "revoked"}:
        db.commit()
        raise AppError(410, f"ASSIGNMENT_{row.status.upper()}", "填写任务已失效")
    return row


@router.get("/patient-session/tasks")
def patient_tasks(claims: PatientClaims, db: DbDep):
    row = patient_package(db, claims)
    return serialize_package(db, row, detailed=True)


def scoped_item(db: DbDep, claims: PatientClaims, item_id: int) -> tuple[AssignmentPackage, AssignmentItem]:
    package = patient_package(db, claims)
    item = db.scalar(
        select(AssignmentItem).where(AssignmentItem.id == item_id, AssignmentItem.package_id == package.id)
    )
    if not item:
        raise AppError(404, "TASK_NOT_FOUND", "问卷任务不存在")
    return package, item


@router.get("/patient-session/tasks/{item_id}")
def patient_task(item_id: int, claims: PatientClaims, db: DbDep):
    _, item = scoped_item(db, claims, item_id)
    return serialize_task(db, item, include_questions=True)


@router.put("/patient-session/tasks/{item_id}/draft")
def save_draft(item_id: int, payload: DraftPayload, claims: PatientClaims, db: DbDep):
    package, item = scoped_item(db, claims, item_id)
    if item.status == "submitted":
        raise AppError(409, "ALREADY_SUBMITTED", "问卷已提交，不能修改")
    response = db.scalar(select(Response).where(Response.assignment_item_id == item.id))
    if not response:
        if payload.revision != 0:
            raise AppError(409, "REVISION_CONFLICT", "草稿版本已变化，请刷新页面")
        response = Response(assignment_item_id=item.id, answers=payload.answers, revision=1)
        db.add(response)
        item.started_at = datetime.now(UTC)
    else:
        if response.revision != payload.revision:
            raise AppError(409, "REVISION_CONFLICT", "草稿版本已变化，请刷新页面")
        response.answers = payload.answers
        response.revision += 1
        response.updated_at = datetime.now(UTC)
    item.status = "draft"
    package.status = "in_progress"
    db.commit()
    db.refresh(response)
    return {"saved": True, "revision": response.revision, "saved_at": response.updated_at}


@router.post("/patient-session/tasks/{item_id}/submit")
def submit_task(
    item_id: int,
    payload: SubmitPayload,
    claims: PatientClaims,
    db: DbDep,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    package, item = scoped_item(db, claims, item_id)
    key = idempotency_key or payload.idempotency_key
    existing_by_key = db.scalar(select(Response).where(Response.idempotency_key == key))
    if existing_by_key:
        assessment = db.scalar(select(Assessment).where(Assessment.response_id == existing_by_key.id))
        return submission_result(existing_by_key, assessment)
    if item.status == "submitted":
        response = db.scalar(select(Response).where(Response.assignment_item_id == item.id))
        assessment = db.scalar(select(Assessment).where(Assessment.response_id == response.id)) if response else None
        return submission_result(response, assessment)
    version = db.get(QuestionnaireVersion, item.questionnaire_version_id)
    questions = db.scalars(
        select(Question).where(Question.version_id == item.questionnaire_version_id).order_by(Question.sort_order)
    ).all()
    validate_answers(questions, payload.answers)
    response = db.scalar(select(Response).where(Response.assignment_item_id == item.id))
    now = datetime.now(UTC)
    if not response:
        response = Response(assignment_item_id=item.id, answers=payload.answers, revision=1)
        db.add(response)
        db.flush()
    response.answers = payload.answers
    response.status = "submitted"
    response.idempotency_key = key
    response.submitted_at = now
    response.updated_at = now
    item.status = "submitted"
    item.submitted_at = now
    score = score_response(version, questions, payload.answers)
    patient = db.get(Patient, package.patient_id)
    assessment = Assessment(
        assessment_code=f"SELF-{uuid.uuid4().hex[:16].upper()}",
        patient_id=package.patient_id,
        doctor_id=package.doctor_id,
        department_id=patient.department_id,
        questionnaire_version_id=item.questionnaire_version_id,
        response_id=response.id,
        **score,
    )
    db.add(assessment)
    db.flush()
    refresh_package_status(db, package)
    db.add(AuditLog(user_id=None, action="response.submit", target_type="assignment_item", target_id=str(item.id)))
    db.commit()
    db.refresh(response)
    db.refresh(assessment)
    return submission_result(response, assessment)


def submission_result(response: Response | None, assessment: Assessment | None) -> dict:
    return {
        "submitted": bool(response and response.status == "submitted"),
        "response_id": response.id if response else None,
        "assessment_id": assessment.id if assessment else None,
        "review_status": assessment.review_status if assessment else None,
        "message": "提交成功，请等待医生查看",
    }

