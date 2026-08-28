from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.api import AppError
from app.modules.questionnaires.models import Question, QuestionnaireTemplate, QuestionnaireVersion
from app.modules.questionnaires.schemas import QuestionnaireCreate


def create_template(db: Session, payload: QuestionnaireCreate, user_id: int) -> QuestionnaireTemplate:
    if db.scalar(select(QuestionnaireTemplate).where(QuestionnaireTemplate.code == payload.code)):
        raise AppError(409, "QUESTIONNAIRE_EXISTS", "问卷编码已存在")
    keys = [item.question_key for item in payload.questions]
    if len(keys) != len(set(keys)):
        raise AppError(422, "DUPLICATE_QUESTION_KEY", "同一版本内题目键不能重复")
    template = QuestionnaireTemplate(
        code=payload.code,
        name=payload.name,
        description=payload.description,
        category=payload.category,
        audience=payload.audience,
        created_by_id=user_id,
    )
    db.add(template)
    db.flush()
    version = QuestionnaireVersion(
        template_id=template.id,
        version=1,
        title=payload.name,
        instructions=payload.instructions,
        estimated_minutes=payload.estimated_minutes,
        scoring_strategy=payload.scoring_strategy,
        scoring_config=payload.scoring_config,
        risk_config=payload.risk_config,
    )
    db.add(version)
    db.flush()
    for item in payload.questions:
        db.add(Question(version_id=version.id, **item.model_dump()))
    db.commit()
    db.refresh(template)
    return template


def publish_template(db: Session, template_id: int) -> QuestionnaireVersion:
    template = db.get(QuestionnaireTemplate, template_id)
    if not template or template.status == "archived":
        raise AppError(404, "QUESTIONNAIRE_NOT_FOUND", "问卷不存在或已归档")
    version = db.scalar(
        select(QuestionnaireVersion)
        .where(QuestionnaireVersion.template_id == template.id)
        .order_by(QuestionnaireVersion.version.desc())
    )
    if not version:
        raise AppError(422, "VERSION_NOT_FOUND", "问卷没有可发布版本")
    question_count = db.scalar(select(func.count(Question.id)).where(Question.version_id == version.id)) or 0
    if question_count == 0:
        raise AppError(422, "EMPTY_QUESTIONNAIRE", "空问卷不能发布")
    from datetime import UTC, datetime

    version.is_published = True
    version.published_at = datetime.now(UTC)
    template.status = "published"
    db.commit()
    db.refresh(version)
    return version


def serialize_template(db: Session, template: QuestionnaireTemplate, include_questions: bool = False) -> dict:
    version = db.scalar(
        select(QuestionnaireVersion)
        .where(QuestionnaireVersion.template_id == template.id)
        .order_by(QuestionnaireVersion.version.desc())
    )
    data = {
        "id": template.id,
        "code": template.code,
        "name": template.name,
        "description": template.description,
        "category": template.category,
        "audience": template.audience,
        "status": template.status,
        "version": version.version if version else None,
        "version_id": version.id if version else None,
        "estimated_minutes": version.estimated_minutes if version else None,
        "scoring_strategy": version.scoring_strategy if version else None,
        "is_published": version.is_published if version else False,
    }
    if include_questions and version:
        questions = db.scalars(
            select(Question).where(Question.version_id == version.id).order_by(Question.sort_order, Question.id)
        ).all()
        data.update(
            {
                "instructions": version.instructions,
                "scoring_config": version.scoring_config,
                "risk_config": version.risk_config,
                "questions": [serialize_question(item) for item in questions],
            }
        )
    return data


def serialize_question(item: Question) -> dict:
    return {
        "id": item.id,
        "question_key": item.question_key,
        "title": item.title,
        "help_text": item.help_text,
        "question_type": item.question_type,
        "required": item.required,
        "section": item.section,
        "sort_order": item.sort_order,
        "options": item.options,
        "validation": item.validation,
        "condition": item.condition,
        "dimension": item.dimension,
    }

