import re
from typing import Any


MOCA_OPEN_TASKS = [
    {
        "id": "moca_payment_13",
        "type": "payment",
        "title": "付款方式",
        "prompt": "如果买东西需要付 13 元，请写出 3 种不同的付款方式。",
        "max_score": 3,
    },
    {
        "id": "moca_abstraction",
        "type": "abstraction",
        "title": "抽象分类",
        "prompt": "请分别说明以下三组词语的共同类别：火车/轮船、锣鼓/笛子、南方/北方。",
        "max_score": 3,
    },
]

CHINESE_NUMBERS = {"一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7,
                   "八": 8, "九": 9, "十": 10, "十一": 11, "十二": 12, "十三": 13}
COUNT_PATTERN = r"\d+|十三|十二|十一|十|一|二|两|三|四|五|六|七|八|九"


def _normalize(value: str) -> str:
    return re.sub(r"\s+", "", value.lower())


def _count(value: str) -> int:
    return int(value) if value.isdigit() else CHINESE_NUMBERS.get(value, 1)


def _payment_segment_total(segment: str) -> int:
    total = 0
    quantified = rf"({COUNT_PATTERN})(?:张|个|枚)?([125]|10)(?:元|块)"
    for match in re.finditer(quantified, segment):
        total += _count(match.group(1)) * int(match.group(2))
    counted = re.sub(quantified, "", segment)
    total += sum(int(match.group(1)) for match in re.finditer(r"([125]|10)(?:元|块)", counted))
    return total


def _score_payment(answer: str) -> tuple[int, str]:
    segments = [segment for segment in re.split(r"[;；。,，、\n]", _normalize(answer)) if segment]
    valid = {segment for segment in segments if _payment_segment_total(segment) == 13}
    score = min(3, len(valid))
    return score, f"识别到 {score} 种不同且总额为 13 元的付款方式，候选计 {score}/3 分。"


ABSTRACTION_RULES = [
    ("火车/轮船", ("交通", "运输", "交通工具", "运输工具", "工具", "出行", "车船")),
    ("锣鼓/笛子", ("乐器", "音乐", "器乐", "演奏", "奏乐")),
    ("南方/北方", ("方向", "方位", "位置", "地理方位", "地域")),
]


def _score_abstraction(answer: str) -> tuple[int, str]:
    normalized = _normalize(answer)
    hits = [label for label, words in ABSTRACTION_RULES if any(word in normalized for word in words)]
    score = len(hits)
    if hits:
        return score, f"识别到 {'、'.join(hits)} 的类别概括，候选计 {score}/3 分。"
    return 0, "未识别到可计分的共同类别概括，候选计 0/3 分。"


def analyze_moca_open_answers(answers: dict[str, Any]) -> dict[str, Any]:
    items = []
    for task in MOCA_OPEN_TASKS:
        answer = str(answers.get(task["id"], "")).strip()
        score, explanation = _score_payment(answer) if task["type"] == "payment" else _score_abstraction(answer)
        items.append({
            "question_id": task["id"],
            "task_type": task["type"],
            "prompt": task["prompt"],
            "answer": answer,
            "candidate_score": score,
            "explanation": explanation,
        })
    candidate_total = sum(item["candidate_score"] for item in items)
    max_score = sum(task["max_score"] for task in MOCA_OPEN_TASKS)
    return {
        "status": "candidate_generated",
        "requires_clinician_review": True,
        "source": "local_fallback",
        "items": items,
        "candidate_total": candidate_total,
        "max_score": max_score,
        "explanation": f"MoCA-B 开放题候选总分 {candidate_total}/{max_score}，需由专业人员结合原始回答复核。",
    }
