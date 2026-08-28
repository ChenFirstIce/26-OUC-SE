from typing import Any, Literal

from pydantic import BaseModel, Field


QuestionType = Literal[
    "short_text", "long_text", "integer", "number", "date", "time", "duration",
    "yes_no", "single_choice", "multi_choice", "scale",
]


class QuestionInput(BaseModel):
    question_key: str = Field(pattern=r"^[A-Za-z0-9_\-]+$", max_length=80)
    title: str = Field(min_length=1)
    help_text: str | None = None
    question_type: QuestionType
    required: bool = True
    section: str = "问卷内容"
    sort_order: int = 0
    options: list[dict[str, Any]] = Field(default_factory=list)
    validation: dict[str, Any] = Field(default_factory=dict)
    condition: dict[str, Any] = Field(default_factory=dict)
    dimension: str | None = None
    reverse_score: bool = False


class QuestionnaireCreate(BaseModel):
    code: str = Field(pattern=r"^[A-Z0-9_\-]+$", max_length=60)
    name: str = Field(min_length=2, max_length=160)
    description: str | None = None
    category: str = "screening"
    audience: str = "patient"
    estimated_minutes: int = Field(default=5, ge=1, le=120)
    instructions: str | None = None
    scoring_strategy: Literal["metadata_sum", "registered_calculator", "manual_review"] = "metadata_sum"
    scoring_config: dict[str, Any] = Field(default_factory=dict)
    risk_config: list[dict[str, Any]] = Field(default_factory=list)
    questions: list[QuestionInput] = Field(min_length=1)

