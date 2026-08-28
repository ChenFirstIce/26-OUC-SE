from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AssignmentCreate(BaseModel):
    patient_id: int
    title: str = Field(min_length=2, max_length=160)
    questionnaire_version_ids: list[int] = Field(min_length=1)
    due_at: datetime
    note: str | None = Field(default=None, max_length=500)


class VerifyRequest(BaseModel):
    token: str = Field(min_length=20)
    access_code: str = Field(pattern=r"^\d{6}$")


class DraftPayload(BaseModel):
    answers: dict[str, Any]
    revision: int = Field(ge=0)


class SubmitPayload(BaseModel):
    answers: dict[str, Any]
    idempotency_key: str = Field(min_length=8, max_length=100)

