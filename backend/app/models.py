from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Department(Base):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(80))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(80))
    role: Mapped[str] = mapped_column(String(20), index=True)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    department: Mapped[Department | None] = relationship()


class UserPermission(Base):
    """可独立调整的业务权限，避免把所有能力硬编码在角色中。"""

    __tablename__ = "user_permissions"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    can_create_patients: Mapped[bool] = mapped_column(Boolean, default=True)
    can_assign_questionnaires: Mapped[bool] = mapped_column(Boolean, default=True)
    can_review_results: Mapped[bool] = mapped_column(Boolean, default=True)
    can_manage_templates: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    user: Mapped[User] = relationship()


class Patient(Base):
    __tablename__ = "patients"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    sex: Mapped[str | None] = mapped_column(String(20), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    education_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    residence_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), index=True)
    assigned_doctor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    department: Mapped[Department] = relationship()
    assigned_doctor: Mapped[User] = relationship()
    profile: Mapped[PatientProfile | None] = relationship(back_populates="patient", uselist=False, cascade="all, delete-orphan")


class PatientProfile(Base):
    """可扩展的患者临床主档，与任务/问卷数据解耦并兼容既有数据库。"""

    __tablename__ = "patient_profiles"
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), primary_key=True)
    full_name: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    marital_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(80), nullable=True)
    chief_concern: Mapped[str | None] = mapped_column(Text, nullable=True)
    past_medical_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    family_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_medications: Mapped[str | None] = mapped_column(Text, nullable=True)
    allergy_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    emergency_contact: Mapped[str | None] = mapped_column(String(80), nullable=True)
    emergency_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    patient: Mapped[Patient] = relationship(back_populates="profile")


class QuestionnaireTemplate(Base):
    __tablename__ = "questionnaire_templates"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    versions: Mapped[list[QuestionnaireVersion]] = relationship(back_populates="template")


class QuestionnaireVersion(Base):
    __tablename__ = "questionnaire_versions"
    __table_args__ = (UniqueConstraint("template_id", "version", name="uq_template_version"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("questionnaire_templates.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    schema_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    scoring_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    template: Mapped[QuestionnaireTemplate] = relationship(back_populates="versions")


class AssignmentPackage(Base):
    __tablename__ = "assignment_packages"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(120))
    note: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    access_code_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    patient: Mapped[Patient] = relationship()
    doctor: Mapped[User] = relationship()
    items: Mapped[list[AssignmentItem]] = relationship(back_populates="assignment", cascade="all, delete-orphan")


class AssignmentItem(Base):
    __tablename__ = "assignment_items"
    __table_args__ = (UniqueConstraint("assignment_id", "questionnaire_version_id", name="uq_assignment_version"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignment_packages.id"), index=True)
    questionnaire_version_id: Mapped[int] = mapped_column(ForeignKey("questionnaire_versions.id"))
    status: Mapped[str] = mapped_column(String(20), default="not_started", index=True)
    assignment: Mapped[AssignmentPackage] = relationship(back_populates="items")
    questionnaire_version: Mapped[QuestionnaireVersion] = relationship()
    response: Mapped[Response | None] = relationship(back_populates="assignment_item", uselist=False)


class Response(Base):
    __tablename__ = "responses"
    assignment_item_id: Mapped[int] = mapped_column(ForeignKey("assignment_items.id"), primary_key=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    answers_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    revision: Mapped[int] = mapped_column(Integer, default=0)
    idempotency_key: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    assignment_item: Mapped[AssignmentItem] = relationship(back_populates="response")


class Assessment(Base):
    __tablename__ = "assessments"
    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_item_id: Mapped[int] = mapped_column(ForeignKey("assignment_items.id"), unique=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    questionnaire_code: Mapped[str] = mapped_column(String(50), index=True)
    total_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    dimension_scores: Mapped[dict[str, float]] = mapped_column(JSON, default=dict)
    risk_level: Mapped[str] = mapped_column(String(20), default="unknown", index=True)
    review_status: Mapped[str] = mapped_column(String(20), default="auto", index=True)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class ClinicalRecord(Base):
    """医生人工记录的诊断、随访和处置意见；与自动问卷评分明确分离。"""

    __tablename__ = "clinical_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    record_type: Mapped[str] = mapped_column(String(30), index=True)
    title: Mapped[str] = mapped_column(String(120))
    diagnosis_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    patient: Mapped[Patient] = relationship()
    doctor: Mapped[User] = relationship()


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_type: Mapped[str] = mapped_column(String(20))
    actor_id: Mapped[str] = mapped_column(String(50))
    action: Mapped[str] = mapped_column(String(60), index=True)
    target_type: Mapped[str] = mapped_column(String(40))
    target_id: Mapped[str] = mapped_column(String(50))
    result: Mapped[str] = mapped_column(String(20), default="success")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
