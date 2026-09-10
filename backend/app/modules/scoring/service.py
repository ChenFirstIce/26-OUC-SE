from collections import defaultdict
from typing import Any

from app.modules.questionnaires.models import Question, QuestionnaireVersion


def score_response(version: QuestionnaireVersion, questions: list[Question], answers: dict[str, Any]) -> dict:
    if version.scoring_strategy == "manual_review":
        return {"total_score": None, "dimension_scores": {}, "risk_level": "unknown", "review_status": "pending_review"}
    if version.scoring_strategy == "registered_calculator":
        # Complex calculators are registered by code when authorized source rules are available.
        return {"total_score": None, "dimension_scores": {}, "risk_level": "unknown", "review_status": "pending_review"}

    total = 0.0
    scored = False
    dimensions: dict[str, float] = defaultdict(float)
    for question in questions:
        answer = answers.get(question.question_key)
        score = option_score(question, answer)
        if score is None:
            continue
        scored = True
        total += score
        if question.dimension:
            dimensions[question.dimension] += score
    if not scored:
        return {"total_score": None, "dimension_scores": {}, "risk_level": "unknown", "review_status": "auto_scored"}
    risk = "unknown"
    for threshold in sorted(version.risk_config or [], key=lambda item: float(item.get("min", 0))):
        minimum = float(threshold.get("min", float("-inf")))
        maximum = float(threshold.get("max", float("inf")))
        if minimum <= total <= maximum:
            risk = str(threshold.get("level", "unknown"))
            break
    return {
        "total_score": total,
        "dimension_scores": dict(dimensions),
        "risk_level": risk,
        "review_status": "auto_scored",
    }


def option_score(question: Question, answer: Any) -> float | None:
    if answer is None or answer == "":
        return None
    score_by_value = {str(item.get("value")): item.get("score") for item in question.options or []}
    if question.question_type == "multi_choice" and isinstance(answer, list):
        values = [score_by_value.get(str(item)) for item in answer]
        values = [float(item) for item in values if item is not None]
        return sum(values) if values else None
    mapped = score_by_value.get(str(answer))
    if mapped is not None:
        return float(mapped)
    if question.question_type in {"number", "integer", "scale"} and not question.options:
        try:
            return float(answer)
        except (TypeError, ValueError):
            return None
    return None

