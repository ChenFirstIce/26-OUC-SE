from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class QuestionnaireTemplate(Base):
    __tablename__ = "questionnaire_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(60), default="screening")
    audience: Mapped[str] = mapped_column(String(30), default="patient")
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class QuestionnaireVersion(Base):
    __tablename__ = "questionnaire_versions"
    __table_args__ = (UniqueConstraint("template_id", "version", name="uq_template_version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("questionnaire_templates.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(160))
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=5)
    scoring_strategy: Mapped[str] = mapped_column(String(40), default="metadata_sum")
    scoring_config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    risk_config: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (UniqueConstraint("version_id", "question_key", name="uq_version_question"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("questionnaire_versions.id"), index=True)
    section: Mapped[str] = mapped_column(String(120), default="问卷内容")
    question_key: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(Text)
    help_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    question_type: Mapped[str] = mapped_column(String(30))
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    options: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    validation: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    condition: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    dimension: Mapped[str | None] = mapped_column(String(80), nullable=True)
    reverse_score: Mapped[bool] = mapped_column(Boolean, default=False)

