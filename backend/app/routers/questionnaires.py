from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.dependencies import admin_user, current_user
from ..models import QuestionnaireTemplate, QuestionnaireVersion, User
from ..services.audit import audit
from ..services.questionnaire import validate_schema


router = APIRouter(prefix="/questionnaires", tags=["问卷模板"])


class TemplateInput(BaseModel):
    code: str = Field(pattern=r"^[A-Z0-9_]+$")
    name: str = Field(min_length=2, max_length=120)
    description: str = ""
    questionnaire_schema: dict[str, Any]
    scoring_json: dict[str, Any] = {"strategy": "manual_review"}


def template_view(template: QuestionnaireTemplate) -> dict:
    versions = sorted(template.versions, key=lambda v: v.version, reverse=True)
    latest = versions[0] if versions else None
    return {
        "id": template.id, "code": template.code, "name": template.name,
        "description": template.description, "status": template.status,
        "latest_version_id": latest.id if latest else None,
        "latest_version": latest.version if latest else None,
        "schema_json": latest.schema_json if latest else None,
        "scoring_json": latest.scoring_json if latest else None,
    }


@router.get("")
def list_templates(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(QuestionnaireTemplate).order_by(QuestionnaireTemplate.name)
    if user.role != "admin":
        query = query.where(QuestionnaireTemplate.status == "published")
    return [template_view(t) for t in db.scalars(query).unique().all()]


@router.post("", status_code=201)
def create_template(payload: TemplateInput, user: User = Depends(admin_user), db: Session = Depends(get_db)):
    validate_schema(payload.questionnaire_schema)
    if db.scalar(select(QuestionnaireTemplate).where(QuestionnaireTemplate.code == payload.code)):
        raise HTTPException(status_code=409, detail="问卷编码已存在")
    template = QuestionnaireTemplate(code=payload.code, name=payload.name, description=payload.description, created_by_id=user.id)
    db.add(template)
    db.flush()
    db.add(QuestionnaireVersion(template_id=template.id, version=1, schema_json=payload.questionnaire_schema, scoring_json=payload.scoring_json))
    audit(db, "user", user.id, "questionnaire.create", "questionnaire", template.id)
    db.commit()
    db.refresh(template)
    return template_view(template)


@router.post("/{template_id}/publish")
def publish(template_id: int, user: User = Depends(admin_user), db: Session = Depends(get_db)):
    template = db.get(QuestionnaireTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="问卷不存在")
    latest = max(template.versions, key=lambda v: v.version)
    validate_schema(latest.schema_json)
    latest.published_at = datetime.now(timezone.utc)
    template.status = "published"
    audit(db, "user", user.id, "questionnaire.publish", "questionnaire", template.id)
    db.commit()
    return template_view(template)
