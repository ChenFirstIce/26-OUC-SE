from __future__ import annotations

import json
from typing import Any

import httpx
from sqlalchemy.orm import Session

from ..core.config import settings
from ..models import LlmMessage
from .llm_config import LlmConfigError, deepseek_credentials
from .moca_open import MOCA_OPEN_TASKS


class DeepSeekUnavailable(RuntimeError):
    pass


def _chat_json(db: Session, messages: list[dict[str, str]], *, max_tokens: int | None = None) -> dict[str, Any]:
    try:
        credentials = deepseek_credentials(db)
    except LlmConfigError as exc:
        raise DeepSeekUnavailable(str(exc)) from exc
    if credentials is None:
        raise DeepSeekUnavailable("deepseek_not_configured")
    payload = {
        "model": credentials.model,
        "messages": messages,
        "stream": False,
        "temperature": 0.2,
        "max_tokens": max_tokens or settings.deepseek_max_tokens,
        "response_format": {"type": "json_object"},
        "thinking": {"type": "disabled"},
        "reasoning_effort": "none",
    }
    try:
        with httpx.Client(timeout=settings.deepseek_timeout_seconds) as client:
            response = client.post(
                f"{credentials.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {credentials.api_key}", "Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise DeepSeekUnavailable("deepseek_request_failed") from exc
    try:
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise DeepSeekUnavailable("deepseek_invalid_json") from exc
    if not isinstance(parsed, dict):
        raise DeepSeekUnavailable("deepseek_invalid_shape")
    return parsed


def generate_scd_reply(db: Session, previous_messages: list[LlmMessage], user_message: str) -> dict[str, Any]:
    history = [{"role": row.role, "content": row.content[:1000]} for row in previous_messages[-8:] if row.role in {"assistant", "user"}]
    result = _chat_json(db, [
        {"role": "system", "content": (
            "你是认知筛查系统中的结构化访谈助手。请只输出 JSON，字段为 "
            "reply:string, progress:number(0到1), completed:boolean。"
            "目标是温和追问主观认知变化、开始时间、日常影响和例子；不要诊断，不要给分。"
        )},
        {"role": "user", "content": json.dumps({"history": history, "new_answer": user_message}, ensure_ascii=False)},
    ], max_tokens=500)
    reply = str(result.get("reply", "")).strip()
    progress = float(result.get("progress", 0))
    completed = bool(result.get("completed", False))
    if not reply:
        raise DeepSeekUnavailable("deepseek_empty_reply")
    return {"reply": reply[:1000], "progress": max(0.0, min(1.0, progress)), "completed": completed}


def summarize_scd_interview(db: Session, messages: list[dict[str, Any]]) -> dict[str, Any]:
    result = _chat_json(db, [
        {"role": "system", "content": (
            "你是医生复核前的访谈整理助手。请只输出 JSON，字段为 summary:string, "
            "subjective_changes:string, daily_impact:string, concerns:string[], explanation:string。"
            "只整理患者原话证据，不要诊断，不要给风险等级。"
        )},
        {"role": "user", "content": json.dumps({"messages": messages[-20:]}, ensure_ascii=False)},
    ], max_tokens=700)
    return {
        "status": "candidate_generated",
        "requires_clinician_review": True,
        "source": "deepseek",
        "summary": str(result.get("summary", "")).strip(),
        "subjective_changes": str(result.get("subjective_changes", "")).strip(),
        "daily_impact": str(result.get("daily_impact", "")).strip(),
        "concerns": [str(item) for item in result.get("concerns", []) if str(item).strip()][:5],
        "explanation": str(result.get("explanation", "")).strip() or "DeepSeek 已整理访谈候选摘要，需医生复核。",
    }


def analyze_moca_with_deepseek(db: Session, answers: dict[str, Any]) -> dict[str, Any]:
    result = _chat_json(db, [
        {"role": "system", "content": (
            "你是 MoCA-B 开放题候选计分助手。请只输出 JSON。"
            "字段：items 为数组，每项含 question_id, task_type, candidate_score, explanation；"
            "candidate_total:number, max_score:number, explanation:string。"
            "付款方式题 0-3 分，抽象分类题 0-3 分，总分 0-6。只给候选分，最终由医生复核。"
        )},
        {"role": "user", "content": json.dumps({"tasks": MOCA_OPEN_TASKS, "answers": answers}, ensure_ascii=False)},
    ], max_tokens=700)
    raw_items = result.get("items", [])
    items = []
    task_by_id = {task["id"]: task for task in MOCA_OPEN_TASKS}
    iterable_items = raw_items if isinstance(raw_items, list) else []
    for raw in iterable_items:
        question_id = str(raw.get("question_id", ""))
        task = task_by_id.get(question_id)
        if not task:
            continue
        score = max(0, min(int(raw.get("candidate_score", 0)), int(task["max_score"])))
        items.append({
            "question_id": question_id,
            "task_type": task["type"],
            "prompt": task["prompt"],
            "answer": str(answers.get(question_id, "")).strip(),
            "candidate_score": score,
            "explanation": str(raw.get("explanation", "")).strip() or f"候选计 {score}/{task['max_score']} 分。",
        })
    if {item["question_id"] for item in items} != set(task_by_id):
        raise DeepSeekUnavailable("deepseek_incomplete_moca_items")
    candidate_total = sum(item["candidate_score"] for item in items)
    max_score = sum(int(task["max_score"]) for task in MOCA_OPEN_TASKS)
    return {
        "status": "candidate_generated",
        "requires_clinician_review": True,
        "source": "deepseek",
        "items": items,
        "candidate_total": candidate_total,
        "max_score": max_score,
        "explanation": str(result.get("explanation", "")).strip() or f"DeepSeek 候选总分 {candidate_total}/{max_score}，需医生复核。",
    }


def test_deepseek_connection(db: Session) -> dict[str, Any]:
    result = _chat_json(db, [
        {"role": "system", "content": "只输出 JSON，字段 ok:boolean, message:string。"},
        {"role": "user", "content": "请返回 {\"ok\": true, \"message\": \"connected\"}。"},
    ], max_tokens=80)
    return {"ok": bool(result.get("ok")), "message": str(result.get("message", ""))[:200]}
