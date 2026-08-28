from typing import Any

from .questionnaire import all_questions, visible


def score_questionnaire(
    schema: dict[str, Any], scoring: dict[str, Any], answers: dict[str, Any]
) -> tuple[float | None, dict[str, float], str, str]:
    strategy = scoring.get("strategy", "manual_review")
    if strategy == "manual_review":
        return None, {}, "unknown", "pending"
    scores: dict[str, float] = {}
    dimensions: dict[str, float] = {}
    for question in all_questions(schema):
        if not visible(question, answers):
            continue
        value = answers.get(question["key"])
        option_scores = {str(o["value"]): float(o.get("score", 0)) for o in question.get("options", [])}
        if isinstance(value, list):
            question_score = sum(option_scores.get(str(v), 0) for v in value)
        elif option_scores:
            question_score = option_scores.get(str(value), 0)
        elif isinstance(value, (int, float)) and question.get("score_numeric"):
            question_score = float(value)
        else:
            question_score = 0
        scores[question["key"]] = question_score
        dimension = question.get("dimension", "总分")
        dimensions[dimension] = dimensions.get(dimension, 0) + question_score
    total = sum(scores.values())
    risk = "unknown"
    for threshold in sorted(scoring.get("risk_thresholds", []), key=lambda item: item["min"]):
        if total >= threshold["min"]:
            risk = threshold["level"]
    return total, dimensions, risk, "auto"

