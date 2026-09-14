from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.dependencies import admin_user, current_user
from ..models import QuestionnaireTemplate, QuestionnaireVersion, User
from ..services.audit import audit
from ..services.questionnaire import validate_schema
from ..services.questionnaire_governance import content_hash, governance_review, version_diff
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
    preview_hashes: dict[str, str] = Field(default_factory=dict)
    preview_versions: dict[str, int | None] = Field(default_factory=dict)


class CatalogImportInput(BaseModel):
    codes: list[str] = Field(min_length=1, max_length=30)
    publish: bool = False
    preview_hashes: dict[str, str] = Field(default_factory=dict)
    preview_versions: dict[str, int | None] = Field(default_factory=dict)


class PublishInput(BaseModel):
    expected_content_hash: str = Field(min_length=64, max_length=64)
    confirmation_code: str
    change_summary: str = Field(min_length=2, max_length=1000)
    acknowledge_warnings: bool = False


class RetireInput(BaseModel):
    confirmation_code: str
    reason: str = Field(min_length=2, max_length=1000)


def version_name(version: QuestionnaireVersion) -> str:
    return version.name or version.template.name


def version_description(version: QuestionnaireVersion) -> str:
    return version.description if version.description is not None else version.template.description


def version_content_hash(version: QuestionnaireVersion) -> str:
    return version.content_hash or content_hash(
        version.template.code, version_name(version), version_description(version),
        version.schema_json, version.scoring_json,
    )


def version_view(version: QuestionnaireVersion) -> dict[str, Any]:
    errors, warnings = governance_review(version.schema_json, version.scoring_json)
    return {
        "id": version.id, "template_id": version.template_id, "version": version.version,
        "name": version_name(version), "description": version_description(version),
        "status": version.status, "schema_json": version.schema_json, "scoring_json": version.scoring_json,
        "content_hash": version_content_hash(version), "change_summary": version.change_summary,
        "created_at": version.created_at, "published_at": version.published_at,
        "retired_at": version.retired_at, "retirement_reason": version.retirement_reason,
        "errors": errors, "warnings": warnings,
    }


def sync_template_status(template: QuestionnaireTemplate) -> None:
    statuses = {version.status for version in template.versions}
    template.status = "published" if "published" in statuses else "draft" if "draft" in statuses else "retired"


def template_view(template: QuestionnaireTemplate, prefer_published: bool = False) -> dict[str, Any]:
    versions = sorted(template.versions, key=lambda item: item.version, reverse=True)
    active = next((version for version in versions if version.status == "published"), None)
    latest = versions[0] if versions else None
    selected = active if prefer_published and active else latest
    return {
        "id": template.id, "code": template.code,
        "name": version_name(selected) if selected else template.name,
        "description": version_description(selected) if selected else template.description,
        "status": template.status,
        "latest_version_id": selected.id if selected else None,
        "latest_version": selected.version if selected else None,
        "latest_version_status": selected.status if selected else None,
        "active_version_id": active.id if active else None,
        "active_version": active.version if active else None,
        "total_versions": len(versions),
        "schema_json": selected.schema_json if selected else None,
        "scoring_json": selected.scoring_json if selected else None,
    }


def preview_items(items: list[TemplateInput], db: Session) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    counts = {item.code: sum(candidate.code == item.code for candidate in items) for item in items}
    for item in items:
        template = db.scalar(select(QuestionnaireTemplate).where(QuestionnaireTemplate.code == item.code))
        latest = max(template.versions, key=lambda row: row.version) if template and template.versions else None
        errors, warnings = governance_review(item.questionnaire_schema, item.scoring_json)
        if counts[item.code] > 1:
            errors.append("同一导入包中问卷编码重复")
        digest = content_hash(item.code, item.name, item.description, item.questionnaire_schema, item.scoring_json)
        results.append({
            "code": item.code, "name": item.name, "valid": not errors,
            "action": "new_version" if template else "create",
            "current_version": latest.version if latest else None,
            "proposed_version": latest.version + 1 if latest else 1,
            "content_hash": digest, "errors": errors, "warnings": warnings,
            "diff": version_diff(
                latest.schema_json if latest else None, latest.scoring_json if latest else None,
                item.questionnaire_schema, item.scoring_json,
            ),
        })
    return results


def catalog_templates(codes: list[str]) -> list[TemplateInput]:
    catalog = {item["code"]: item for item in catalog_items()}
    missing = [code for code in codes if code not in catalog]
    if missing:
        raise HTTPException(status_code=422, detail=f"未知目录量表：{', '.join(missing)}")
    return [TemplateInput(**catalog[code]) for code in codes]


def import_templates(payload: ImportPackageInput, user: User, db: Session, require_preview: bool) -> list[dict[str, Any]]:
    if payload.publish:
        raise HTTPException(status_code=422, detail="导入只能生成草稿，必须通过版本发布接口审核发布")
    previews = preview_items(payload.templates, db)
    invalid = [message for item in previews for message in item["errors"]]
    if invalid:
        raise HTTPException(status_code=422, detail={"message": "问卷治理校验未通过", "errors": invalid})
    if require_preview:
        stale = [
            item["code"] for item in previews
            if payload.preview_hashes.get(item["code"]) != item["content_hash"]
            or item["code"] not in payload.preview_versions
            or payload.preview_versions[item["code"]] != item["current_version"]
        ]
        if stale:
            raise HTTPException(status_code=409, detail=f"以下问卷尚未预览或预览内容已变化：{', '.join(stale)}")

    results: list[dict[str, Any]] = []
    for item, preview in zip(payload.templates, previews, strict=True):
        template = db.scalar(select(QuestionnaireTemplate).where(QuestionnaireTemplate.code == item.code))
        if template and payload.conflict_strategy == "error":
            raise HTTPException(status_code=409, detail=f"问卷编码已存在：{item.code}")
        if template and payload.conflict_strategy == "skip":
            results.append({"code": item.code, "action": "skipped", "version": max(row.version for row in template.versions)})
            continue
        if template:
            version_number = max(row.version for row in template.versions) + 1
            template.name, template.description = item.name, item.description
        else:
            template = QuestionnaireTemplate(code=item.code, name=item.name, description=item.description, created_by_id=user.id)
            db.add(template)
            db.flush()
            version_number = 1

        version = QuestionnaireVersion(
            template_id=template.id, version=version_number, name=item.name, description=item.description,
            schema_json=item.questionnaire_schema, scoring_json=item.scoring_json,
            status="draft", content_hash=preview["content_hash"], created_by_id=user.id,
        )
        template.versions.append(version)
        db.flush()
        sync_template_status(template)
        results.append({"code": item.code, "action": "versioned" if version_number > 1 else "created", "version": version_number})
    audit(db, "user", user.id, "questionnaire.import", "questionnaire_package", len(results))
    db.commit()
    return results


@router.get("")
def list_templates(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(QuestionnaireTemplate).order_by(QuestionnaireTemplate.name)
    if user.role != "admin":
        query = query.where(QuestionnaireTemplate.versions.any(QuestionnaireVersion.status == "published"))
    return [template_view(template, prefer_published=user.role != "admin") for template in db.scalars(query).unique().all()]


@router.get("/catalog")
def scale_catalog(_: User = Depends(admin_user)):
    return [{
        "code": item["code"], "name": item["name"], "description": item["description"],
        "administration_mode": item["questionnaire_schema"].get("administration_mode"),
        "source": item["questionnaire_schema"].get("source"),
        "question_count": sum(len(section.get("questions", [])) for section in item["questionnaire_schema"].get("sections", [])),
    } for item in catalog_items()]


@router.post("/import-preview")
def import_preview(payload: ImportPackageInput, _: User = Depends(admin_user), db: Session = Depends(get_db)):
    return {"items": preview_items(payload.templates, db)}


@router.post("/import-preview/catalog")
def import_catalog_preview(payload: CatalogImportInput, _: User = Depends(admin_user), db: Session = Depends(get_db)):
    return {"items": preview_items(catalog_templates(payload.codes), db)}


@router.post("/import-package")
def import_package(payload: ImportPackageInput, user: User = Depends(admin_user), db: Session = Depends(get_db)):
    return {"items": import_templates(payload, user, db, require_preview=True)}


@router.post("/import-catalog")
def import_catalog(payload: CatalogImportInput, user: User = Depends(admin_user), db: Session = Depends(get_db)):
    templates = catalog_templates(payload.codes)
    package = ImportPackageInput(
        templates=templates, conflict_strategy="new_version", publish=payload.publish,
        preview_hashes=payload.preview_hashes, preview_versions=payload.preview_versions,
    )
    return {"items": import_templates(package, user, db, require_preview=True)}


@router.post("", status_code=201)
def create_template(payload: TemplateInput, user: User = Depends(admin_user), db: Session = Depends(get_db)):
    validate_schema(payload.questionnaire_schema)
    errors, _ = governance_review(payload.questionnaire_schema, payload.scoring_json)
    if errors:
        raise HTTPException(status_code=422, detail={"message": "问卷治理校验未通过", "errors": errors})
    if db.scalar(select(QuestionnaireTemplate).where(QuestionnaireTemplate.code == payload.code)):
        raise HTTPException(status_code=409, detail="问卷编码已存在")
    template = QuestionnaireTemplate(code=payload.code, name=payload.name, description=payload.description, created_by_id=user.id)
    db.add(template)
    db.flush()
    template.versions.append(QuestionnaireVersion(
        template_id=template.id, version=1, name=payload.name, description=payload.description,
        schema_json=payload.questionnaire_schema, scoring_json=payload.scoring_json, created_by_id=user.id,
        content_hash=content_hash(payload.code, payload.name, payload.description, payload.questionnaire_schema, payload.scoring_json),
    ))
    audit(db, "user", user.id, "questionnaire.create", "questionnaire", template.id)
    db.commit()
    db.refresh(template)
    return template_view(template)


@router.get("/{template_id}/versions")
def list_versions(template_id: int, _: User = Depends(admin_user), db: Session = Depends(get_db)):
    template = db.get(QuestionnaireTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="问卷不存在")
    return [version_view(version) for version in sorted(template.versions, key=lambda item: item.version, reverse=True)]


@router.get("/versions/{version_id}/diff")
def compare_version(version_id: int, base_version_id: int, _: User = Depends(admin_user), db: Session = Depends(get_db)):
    target, base = db.get(QuestionnaireVersion, version_id), db.get(QuestionnaireVersion, base_version_id)
    if not target or not base:
        raise HTTPException(status_code=404, detail="问卷版本不存在")
    if target.template_id != base.template_id:
        raise HTTPException(status_code=422, detail="只能比较同一问卷的版本")
    return version_diff(base.schema_json, base.scoring_json, target.schema_json, target.scoring_json)


@router.post("/versions/{version_id}/publish")
def publish_version(version_id: int, payload: PublishInput, user: User = Depends(admin_user), db: Session = Depends(get_db)):
    version = db.get(QuestionnaireVersion, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="问卷版本不存在")
    if version.status != "draft":
        raise HTTPException(status_code=409, detail="只有草稿版本可以发布")
    if payload.confirmation_code != version.template.code:
        raise HTTPException(status_code=422, detail="确认编号与问卷编号不一致")
    digest = version_content_hash(version)
    if payload.expected_content_hash != digest:
        raise HTTPException(status_code=409, detail="问卷内容已变化，请重新预览")
    errors, warnings = governance_review(version.schema_json, version.scoring_json)
    if errors:
        raise HTTPException(status_code=422, detail={"message": "问卷治理校验未通过", "errors": errors})
    if warnings and not payload.acknowledge_warnings:
        raise HTTPException(status_code=409, detail={"message": "存在待确认警告", "errors": warnings})

    now = datetime.now(timezone.utc)
    for previous in version.template.versions:
        if previous.status == "published":
            previous.status, previous.retired_at = "retired", now
            previous.retired_by_id, previous.retirement_reason = user.id, f"由 v{version.version} 自动替代"
    version.status, version.content_hash = "published", digest
    version.change_summary, version.published_at, version.published_by_id = payload.change_summary, now, user.id
    version.template.name, version.template.description = version_name(version), version_description(version)
    sync_template_status(version.template)
    audit(db, "user", user.id, "questionnaire.publish", "questionnaire_version", version.id)
    db.commit()
    return version_view(version)


@router.post("/versions/{version_id}/retire")
def retire_version(version_id: int, payload: RetireInput, user: User = Depends(admin_user), db: Session = Depends(get_db)):
    version = db.get(QuestionnaireVersion, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="问卷版本不存在")
    if version.status != "published":
        raise HTTPException(status_code=409, detail="只有当前已发布版本可以停用")
    if payload.confirmation_code != version.template.code:
        raise HTTPException(status_code=422, detail="确认编号与问卷编号不一致")
    version.status, version.retired_at = "retired", datetime.now(timezone.utc)
    version.retired_by_id, version.retirement_reason = user.id, payload.reason
    sync_template_status(version.template)
    audit(db, "user", user.id, "questionnaire.retire", "questionnaire_version", version.id)
    db.commit()
    return version_view(version)
