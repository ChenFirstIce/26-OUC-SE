from fastapi import APIRouter
from sqlalchemy import select

from app.core.api import AppError
from app.modules.auth.dependencies import AdminUser, CurrentUser, DbDep
from app.modules.questionnaires.models import QuestionnaireTemplate
from app.modules.questionnaires.schemas import QuestionnaireCreate
from app.modules.questionnaires.service import create_template, publish_template, serialize_template


router = APIRouter(prefix="/questionnaires", tags=["问卷模板"])


@router.get("")
def list_questionnaires(user: CurrentUser, db: DbDep):
    query = select(QuestionnaireTemplate).order_by(QuestionnaireTemplate.name)
    if user.role == "doctor":
        query = query.where(QuestionnaireTemplate.status == "published")
    return [serialize_template(db, item) for item in db.scalars(query).all()]


@router.post("", status_code=201)
def create_questionnaire(payload: QuestionnaireCreate, user: AdminUser, db: DbDep):
    row = create_template(db, payload, user.id)
    return serialize_template(db, row, include_questions=True)


@router.get("/{template_id}")
def get_questionnaire(template_id: int, _: CurrentUser, db: DbDep):
    row = db.get(QuestionnaireTemplate, template_id)
    if not row:
        raise AppError(404, "QUESTIONNAIRE_NOT_FOUND", "问卷不存在")
    return serialize_template(db, row, include_questions=True)


@router.post("/{template_id}/publish")
def publish_questionnaire(template_id: int, _: AdminUser, db: DbDep):
    version = publish_template(db, template_id)
    return {"template_id": template_id, "version_id": version.id, "version": version.version, "status": "published"}


@router.post("/{template_id}/archive")
def archive_questionnaire(template_id: int, _: AdminUser, db: DbDep):
    row = db.get(QuestionnaireTemplate, template_id)
    if not row:
        raise AppError(404, "QUESTIONNAIRE_NOT_FOUND", "问卷不存在")
    row.status = "archived"
    db.commit()
    return {"id": row.id, "status": row.status}

