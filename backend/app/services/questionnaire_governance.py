import hashlib
import json
from typing import Any

from fastapi import HTTPException

from .questionnaire import all_questions, validate_schema


SUPPORTED_SCORING = {"metadata_sum", "manual_review", "laterality_index"}


def content_hash(code: str, name: str, description: str, schema: dict[str, Any], scoring: dict[str, Any]) -> str:
    payload = {"code": code, "name": name, "description": description, "schema": schema, "scoring": scoring}
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def governance_review(schema: dict[str, Any], scoring: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        validate_schema(schema)
    except HTTPException as exc:
        errors.append(str(exc.detail))
        return errors, warnings

    questions = all_questions(schema)
    keys = {question["key"] for question in questions}
    choice_types = {"yes_no", "single_choice", "multi_choice", "scale"}
    for question in questions:
        key = question["key"]
        if not question.get("label"):
            warnings.append(f"题目 {key} 缺少显示标题")
        if question["type"] in choice_types:
            options = question.get("options", [])
            if not options:
                errors.append(f"题目 {key} 缺少可选项")
            values = [json.dumps(option.get("value"), ensure_ascii=False, sort_keys=True) for option in options]
            if len(values) != len(set(values)):
                errors.append(f"题目 {key} 存在重复选项值")
        condition = question.get("show_if")
        if condition and condition.get("question_key") not in keys:
            errors.append(f"题目 {key} 的显示条件引用了不存在的题目")

    mode = schema.get("administration_mode")
    if mode not in {"patient_self", "informant", "clinician"}:
        warnings.append("未明确填写/施测方式")
    if not schema.get("source"):
        warnings.append("未记录量表来源与授权审核说明")

    strategy = scoring.get("strategy", "manual_review")
    if strategy not in SUPPORTED_SCORING:
        errors.append(f"不支持的计分策略：{strategy}")
    thresholds = scoring.get("risk_thresholds", [])
    previous_max: float | None = None
    for index, threshold in enumerate(sorted(thresholds, key=lambda item: item.get("min", 0))):
        minimum = threshold.get("min", 0)
        maximum = threshold.get("max")
        if maximum is not None and maximum < minimum:
            errors.append(f"第 {index + 1} 个风险阈值最大值小于最小值")
        if previous_max is not None and minimum <= previous_max:
            errors.append("风险阈值存在重叠")
        previous_max = maximum
    return list(dict.fromkeys(errors)), list(dict.fromkeys(warnings))


def version_diff(
    old_schema: dict[str, Any] | None,
    old_scoring: dict[str, Any] | None,
    new_schema: dict[str, Any],
    new_scoring: dict[str, Any],
) -> dict[str, Any]:
    if old_schema is None:
        return {
            "added_questions": [question["key"] for question in all_questions(new_schema)],
            "removed_questions": [], "changed_questions": [],
            "schema_fields_changed": [], "scoring_changed": bool(new_scoring), "risk_level": "normal",
        }
    old_questions = {question["key"]: question for question in all_questions(old_schema)}
    new_questions = {question["key"]: question for question in all_questions(new_schema)}
    added = sorted(new_questions.keys() - old_questions.keys())
    removed = sorted(old_questions.keys() - new_questions.keys())
    changed = sorted(key for key in old_questions.keys() & new_questions.keys() if old_questions[key] != new_questions[key])
    schema_fields = sorted(
        key for key in set(old_schema) | set(new_schema)
        if key != "sections" and old_schema.get(key) != new_schema.get(key)
    )
    scoring_changed = (old_scoring or {}) != new_scoring
    risk = "high" if removed or scoring_changed else "normal"
    return {
        "added_questions": added, "removed_questions": removed, "changed_questions": changed,
        "schema_fields_changed": schema_fields, "scoring_changed": scoring_changed, "risk_level": risk,
    }
