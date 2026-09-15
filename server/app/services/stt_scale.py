"""STT 形状连线任务的服务端数据：A/B 卷正确点击序列与年龄阈值。

坐标数据来自仓库 stt_sequences_with_coordinates.json（main 分支 STT 补全工作），
节点键与前端 admin-web/src/data/stt-scale.ts 的 coordinateKey 保持一致：
`形状-标签-x-y`。本模块只保留服务端校验和判读所需的最小信息。
"""
import json
from functools import lru_cache
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parents[3]
_STT_FORMS = {
    "A": {"practice": "STT_A_practice", "test": "STT_A_test"},
    "B": {"practice": "STT_B_practice", "test": "STT_B_test"},
}
STT_AGE_BANDS = ("50-59", "60-69", "70-79")
STT_PHASES = ("practice", "test")


@lru_cache
def stt_sequences() -> dict[str, tuple[str, ...]]:
    """按 `{form}-{phase}` 返回正确点击序列（coordinateKey 元组）。"""
    data = json.loads((_DATA_DIR / "stt_sequences_with_coordinates.json").read_text(encoding="utf-8"))
    sequences: dict[str, tuple[str, ...]] = {}
    for form, phases in _STT_FORMS.items():
        for phase, key in phases.items():
            sequences[f"{form}-{phase}"] = tuple(
                f"{node['shape']}-{node['label']}-{node['x']}-{node['y']}" for node in data[key])
    return sequences


@lru_cache
def stt_thresholds() -> dict[str, dict[str, int]]:
    """按卷返回年龄阈值（秒），与 stt_age_thresholds.json 同步。"""
    data = json.loads((_DATA_DIR / "stt_age_thresholds.json").read_text(encoding="utf-8"))
    return {"A": data["STT_A_thresholds"], "B": data["STT_B_thresholds"]}


def expected_sequence(form: str, phase: str) -> tuple[str, ...] | None:
    if form not in _STT_FORMS or phase not in STT_PHASES:
        return None
    return stt_sequences().get(f"{form}-{phase}")


def threshold_for(form: str, age_band: str) -> int | None:
    thresholds = stt_thresholds().get(form)
    if thresholds is None or age_band not in STT_AGE_BANDS:
        return None
    return thresholds[age_band]
