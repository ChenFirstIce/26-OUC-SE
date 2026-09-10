from typing import Any

from fastapi import HTTPException


SUPPORTED_TYPES = {
    "short_text", "long_text", "integer", "number", "date", "time", "duration",
    "yes_no", "single_choice", "multi_choice", "scale",
}


def all_questions(schema: dict[str, Any]) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    for section in schema.get("sections", []):
        questions.extend(section.get("questions", []))
    return questions


def visible(question: dict[str, Any], answers: dict[str, Any]) -> bool:
    condition = question.get("show_if")
    if not condition:
        return True
    return answers.get(condition.get("question_key")) == condition.get("equals")


def validate_schema(schema: dict[str, Any]) -> None:
    seen: set[str] = set()
    if not schema.get("sections"):
        raise HTTPException(status_code=422, detail="问卷至少需要一个分区")
    for question in all_questions(schema):
        key = question.get("key")
        if not key or key in seen:
            raise HTTPException(status_code=422, detail="题目 key 缺失或重复")
        if question.get("type") not in SUPPORTED_TYPES:
            raise HTTPException(status_code=422, detail=f"不支持的题型：{question.get('type')}")
        seen.add(key)


def validate_answers(schema: dict[str, Any], answers: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for question in all_questions(schema):
        if not visible(question, answers):
            continue
        key = question["key"]
        value = answers.get(key)
        if question.get("required") and (value is None or value == "" or value == []):
            errors.append(f"{question.get('label', key)}为必填项")
            continue
        if value is None or value == "":
            continue
        qtype = question["type"]
        if qtype in {"integer", "number", "duration"}:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                errors.append(f"{question.get('label', key)}必须是数字")
                continue
            if "min" in question and value < question["min"]:
                errors.append(f"{question.get('label', key)}不能小于{question['min']}")
            if "max" in question and value > question["max"]:
                errors.append(f"{question.get('label', key)}不能大于{question['max']}")
        if qtype == "multi_choice" and not isinstance(value, list):
            errors.append(f"{question.get('label', key)}必须是多选数组")
        if qtype in {"yes_no", "single_choice", "scale"}:
            allowed = {option["value"] for option in question.get("options", [])}
            if allowed and value not in allowed:
                errors.append(f"{question.get('label', key)}选项无效")
    return errors

