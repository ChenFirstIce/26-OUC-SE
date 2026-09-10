from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.api import AppError
from app.core.config import settings
from app.core.security import hash_secret, make_access_code, make_public_token
from app.modules.assignments.models import AssignmentItem, AssignmentPackage, Response
from app.modules.assignments.schemas import AssignmentCreate
from app.modules.patients.models import Patient
from app.modules.questionnaires.models import Question, QuestionnaireTemplate, QuestionnaireVersion
from app.modules.questionnaires.service import serialize_question
from app.modules.users.models import User


def utc_now() -> datetime:
    return datetime.now(UTC)


def aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def create_assignment(db: Session, payload: AssignmentCreate, user: User) -> tuple[AssignmentPackage, str, str]:
    patient = db.get(Patient, payload.patient_id)
    if not patient or not patient.is_active:
        raise AppError(404, "PATIENT_NOT_FOUND", "患者不存在")
    if user.role == "doctor" and patient.assigned_doctor_id != user.id:
        raise AppError(403, "FORBIDDEN", "只能向本人负责的患者派发问卷")
    if aware(payload.due_at) <= utc_now():
        raise AppError(422, "INVALID_DUE_AT", "截止时间必须晚于当前时间")
    version_ids = list(dict.fromkeys(payload.questionnaire_version_ids))
    versions = db.scalars(
        select(QuestionnaireVersion).where(
            QuestionnaireVersion.id.in_(version_ids), QuestionnaireVersion.is_published.is_(True)
        )
    ).all()
    if len(versions) != len(version_ids):
        raise AppError(422, "QUESTIONNAIRE_NOT_PUBLISHED", "包含不存在或未发布的问卷版本")
    token = make_public_token()
    code = make_access_code()
    row = AssignmentPackage(
        patient_id=patient.id,
        doctor_id=user.id,
        title=payload.title,
        note=payload.note,
        token_hash=hash_secret(token),
        access_code_hash=hash_secret(code),
        due_at=payload.due_at,
    )
    db.add(row)
    db.flush()
    for order, version_id in enumerate(version_ids):
        db.add(AssignmentItem(package_id=row.id, questionnaire_version_id=version_id, sort_order=order))
    db.commit()
    db.refresh(row)
    return row, token, code


def refresh_package_status(db: Session, package: AssignmentPackage) -> None:
    items = db.scalars(select(AssignmentItem).where(AssignmentItem.package_id == package.id)).all()
    if package.status in {"revoked", "reviewed"}:
        return
    if aware(package.due_at) < utc_now() and not all(item.status == "submitted" for item in items):
        package.status = "expired"
    elif items and all(item.status in {"submitted", "reviewed"} for item in items):
        package.status = "submitted"
        package.submitted_at = max((item.submitted_at for item in items if item.submitted_at), default=utc_now())
    elif any(item.status == "draft" for item in items):
        package.status = "in_progress"


def verify_assignment(db: Session, token: str, code: str) -> AssignmentPackage:
    row = db.scalar(select(AssignmentPackage).where(AssignmentPackage.token_hash == hash_secret(token)))
    if not row or row.access_code_hash != hash_secret(code):
        raise AppError(401, "INVALID_ACCESS", "填写链接或访问码错误")
    refresh_package_status(db, row)
    if row.status == "expired":
        db.commit()
        raise AppError(410, "ASSIGNMENT_EXPIRED", "该填写任务已过期")
    if row.status == "revoked":
        raise AppError(410, "ASSIGNMENT_REVOKED", "该填写任务已撤销")
    if not row.opened_at:
        row.opened_at = utc_now()
    db.commit()
    return row


def serialize_package(db: Session, package: AssignmentPackage, detailed: bool = False) -> dict:
    patient = db.get(Patient, package.patient_id)
    items = db.scalars(
        select(AssignmentItem).where(AssignmentItem.package_id == package.id).order_by(AssignmentItem.sort_order)
    ).all()
    result = {
        "id": package.id,
        "patient_id": package.patient_id,
        "patient_code": patient.patient_code if patient else "-",
        "doctor_id": package.doctor_id,
        "title": package.title,
        "note": package.note,
        "status": package.status,
        "due_at": package.due_at,
        "created_at": package.created_at,
        "opened_at": package.opened_at,
        "submitted_at": package.submitted_at,
        "reviewed_at": package.reviewed_at,
        "total_items": len(items),
        "completed_items": sum(item.status in {"submitted", "reviewed"} for item in items),
    }
    if detailed:
        result["items"] = [serialize_task(db, item, include_questions=False) for item in items]
    return result


def serialize_task(db: Session, item: AssignmentItem, include_questions: bool = True) -> dict:
    version = db.get(QuestionnaireVersion, item.questionnaire_version_id)
    template = db.get(QuestionnaireTemplate, version.template_id) if version else None
    response = db.scalar(select(Response).where(Response.assignment_item_id == item.id))
    data: dict[str, Any] = {
        "id": item.id,
        "status": item.status,
        "questionnaire_version_id": item.questionnaire_version_id,
        "questionnaire_code": template.code if template else "",
        "title": version.title if version else "未知问卷",
        "instructions": version.instructions if version else None,
        "estimated_minutes": version.estimated_minutes if version else 0,
        "answers": response.answers if response else {},
        "revision": response.revision if response else 0,
    }
    if include_questions and version:
        questions = db.scalars(
            select(Question).where(Question.version_id == version.id).order_by(Question.sort_order, Question.id)
        ).all()
        data["questions"] = [serialize_question(question) for question in questions]
    return data


def is_visible(question: Question, answers: dict[str, Any]) -> bool:
    condition = question.condition or {}
    if not condition:
        return True
    source = condition.get("question_key")
    operator = condition.get("operator", "equals")
    expected = condition.get("value")
    actual = answers.get(source)
    if operator == "equals":
        return actual == expected
    if operator == "not_equals":
        return actual != expected
    if operator == "contains":
        return isinstance(actual, list) and expected in actual
    return True


def validate_answers(questions: list[Question], answers: dict[str, Any]) -> None:
    known_keys = {item.question_key for item in questions}
    unknown = set(answers) - known_keys
    if unknown:
        raise AppError(422, "UNKNOWN_QUESTION", f"包含未知题目：{', '.join(sorted(unknown))}")
    errors: list[str] = []
    for question in questions:
        if not is_visible(question, answers):
            continue
        value = answers.get(question.question_key)
        if question.required and (value is None or value == "" or value == []):
            errors.append(f"{question.question_key} 为必填项")
            continue
        if value is None or value == "":
            continue
        validation = question.validation or {}
        if question.question_type in {"integer", "number", "scale"}:
            try:
                number = float(value)
            except (TypeError, ValueError):
                errors.append(f"{question.question_key} 必须是数字")
                continue
            if "min" in validation and number < float(validation["min"]):
                errors.append(f"{question.question_key} 不能小于 {validation['min']}")
            if "max" in validation and number > float(validation["max"]):
                errors.append(f"{question.question_key} 不能大于 {validation['max']}")
        if question.options:
            allowed = {str(option.get("value")) for option in question.options}
            selected = value if isinstance(value, list) else [value]
            if any(str(item) not in allowed for item in selected):
                errors.append(f"{question.question_key} 包含非法选项")
    if errors:
        raise AppError(422, "ANSWER_VALIDATION_FAILED", "；".join(errors[:5]))

