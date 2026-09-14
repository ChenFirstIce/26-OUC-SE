from math import isfinite
from typing import Any

from fastapi import HTTPException


def review_config(scoring: dict[str, Any]) -> dict[str, Any]:
    configured = scoring.get("review") or {}
    score = configured.get("score") or {}
    return {
        "score": {"required": score.get("required", True), "min": score.get("min", 0), "max": score.get("max")},
        "dimensions": configured.get("dimensions", []),
        "risk": {"required": (configured.get("risk") or {}).get("required", True),
                 "levels": (configured.get("risk") or {}).get("levels", ["low", "medium", "high"]),
                 "thresholds": (configured.get("risk") or {}).get("thresholds", [])},
        "note_required": configured.get("note_required", True),
    }


def suggested_risk(total_score: float | None, config: dict[str, Any]) -> str | None:
    if total_score is None:
        return None
    suggestion = None
    for threshold in sorted(config["risk"]["thresholds"], key=lambda row: row["min"]):
        if total_score >= threshold["min"] and (threshold.get("max") is None or total_score <= threshold["max"]):
            suggestion = threshold["level"]
    return suggestion


def validate_review_result(total_score: float | None, dimensions: dict[str, float], risk_level: str,
                           note: str, scoring: dict[str, Any]) -> dict[str, Any]:
    config = review_config(scoring)
    score_rule = config["score"]
    if score_rule["required"] and total_score is None:
        raise HTTPException(status_code=422, detail="确认最终结果前必须填写总分")
    if total_score is not None:
        if not isfinite(total_score) or total_score < score_rule["min"]:
            raise HTTPException(status_code=422, detail=f"总分不能低于 {score_rule['min']}")
        if score_rule["max"] is not None and total_score > score_rule["max"]:
            raise HTTPException(status_code=422, detail=f"总分不能超过 {score_rule['max']}")
    risk_rule = config["risk"]
    if risk_rule["required"] and risk_level == "unknown":
        raise HTTPException(status_code=422, detail="确认最终结果前必须选择风险等级")
    if risk_level != "unknown" and risk_level not in risk_rule["levels"]:
        raise HTTPException(status_code=422, detail="风险等级不在当前问卷版本允许范围内")
    if config["note_required"] and len(note.strip()) < 2:
        raise HTTPException(status_code=422, detail="确认最终结果前必须填写复核意见")
    dimension_rules = {row["key"]: row for row in config["dimensions"]}
    for name, score in dimensions.items():
        if not name.strip() or not isfinite(score) or score < 0:
            raise HTTPException(status_code=422, detail="维度名称不能为空，维度得分必须是有效的非负数")
        rule = dimension_rules.get(name)
        if not rule:
            raise HTTPException(status_code=422, detail=f"维度 {name} 不在当前问卷版本允许范围内")
        if score < rule.get("min", 0) or (rule.get("max") is not None and score > rule["max"]):
            raise HTTPException(status_code=422, detail=f"{rule.get('label', name)}得分超出允许范围")
    return config
