from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.dependencies import admin_user, current_user
from ..models import QuestionnaireTemplate, QuestionnaireVersion, User
from ..services.audit import audit
from ..services.questionnaire import validate_schema
from ..services.scale_catalog import catalog_items


router = APIRouter(prefix="/questionnaires", tags=["问卷模板"])


class TemplateInput(BaseModel):
    code: str = Field(pattern=r"^[A-Z0-9_]+$")
    name: str = Field(min_length=2, max_length=120)
    description: str = ""
    questionnaire_schema: dict[str, Any]
    scoring_json: dict[str, Any] = Field(default_factory=lambda: {"strategy": "manual_review"})


class ImportPackageInput(BaseModel):
    templates: list[TemplateInput] = Field(min_length=1, max_length=100)
    conflict_strategy: Literal["new_version", "skip", "error"] = "new_version"
    publish: bool = False


class CatalogImportInput(BaseModel):
    codes: list[str] = Field(min_length=1, max_length=30)
    publish: bool = False


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


def import_templates(payload: ImportPackageInput, user: User, db: Session) -> list[dict]:
    if len({item.code for item in payload.templates}) != len(payload.templates):
        raise HTTPException(status_code=422, detail="导入包中存在重复问卷编码")
    for item in payload.templates:
        validate_schema(item.questionnaire_schema)
    results = []
    now = datetime.now(timezone.utc)
    for item in payload.templates:
        template = db.scalar(select(QuestionnaireTemplate).where(QuestionnaireTemplate.code == item.code))
        if template and payload.conflict_strategy == "error":
            raise HTTPException(status_code=409, detail=f"问卷编码已存在：{item.code}")
        if template and payload.conflict_strategy == "skip":
            results.append({"code": item.code, "action": "skipped", "version": max(v.version for v in template.versions)})
            continue
        if template:
            version_number = max(v.version for v in template.versions) + 1
            template.name, template.description = item.name, item.description
        else:
            template = QuestionnaireTemplate(code=item.code, name=item.name, description=item.description, created_by_id=user.id)
            db.add(template); db.flush(); version_number = 1
        version = QuestionnaireVersion(template_id=template.id, version=version_number,
                                       schema_json=item.questionnaire_schema, scoring_json=item.scoring_json,
                                       published_at=now if payload.publish else None)
        db.add(version)
        template.status = "published" if payload.publish else "draft"
        results.append({"code": item.code, "action": "versioned" if version_number > 1 else "created", "version": version_number})
    audit(db, "user", user.id, "questionnaire.import", "questionnaire_package", len(results))
    db.commit()
    return results


@router.get("")
def list_templates(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(QuestionnaireTemplate).order_by(QuestionnaireTemplate.name)
    if user.role != "admin":
        query = query.where(QuestionnaireTemplate.status == "published")
    return [template_view(t) for t in db.scalars(query).unique().all()]


@router.get("/catalog")
def scale_catalog(_: User = Depends(admin_user)):
    return [{
        "code": item["code"], "name": item["name"], "description": item["description"],
        "administration_mode": item["questionnaire_schema"].get("administration_mode"),
        "source": item["questionnaire_schema"].get("source"),
        "question_count": sum(len(section.get("questions", [])) for section in item["questionnaire_schema"].get("sections", [])),
    } for item in catalog_items()]


@router.post("/import-package")
def import_package(payload: ImportPackageInput, user: User = Depends(admin_user), db: Session = Depends(get_db)):
    return {"items": import_templates(payload, user, db)}


@router.post("/import-catalog")
def import_catalog(payload: CatalogImportInput, user: User = Depends(admin_user), db: Session = Depends(get_db)):
    catalog = {item["code"]: item for item in catalog_items()}
    missing = [code for code in payload.codes if code not in catalog]
    if missing:
        raise HTTPException(status_code=422, detail=f"未知目录量表：{', '.join(missing)}")
    package = ImportPackageInput(templates=[TemplateInput(**catalog[code]) for code in payload.codes],
                                 conflict_strategy="new_version", publish=payload.publish)
    return {"items": import_templates(package, user, db)}


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
