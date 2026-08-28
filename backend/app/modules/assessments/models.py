from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), index=True)
    questionnaire_version_id: Mapped[int] = mapped_column(ForeignKey("questionnaire_versions.id"), index=True)
    response_id: Mapped[int | None] = mapped_column(ForeignKey("responses.id"), unique=True, nullable=True)
    total_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    dimension_scores: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    risk_level: Mapped[str] = mapped_column(String(20), default="unknown", index=True)
    source: Mapped[str] = mapped_column(String(30), default="patient_self_fill")
    review_status: Mapped[str] = mapped_column(String(30), default="auto_scored", index=True)
    reviewed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)

