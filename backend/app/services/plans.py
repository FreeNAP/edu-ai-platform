"""学习路径辅助：按各阶段时长估算到期日。"""
import re
from datetime import datetime, timedelta

DEFAULT_PLAN_DAYS = 28  # 解析不出时长时默认 4 周
MAX_PLAN_DAYS = 730

_DURATION_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:[-~～到至]\s*(\d+(?:\.\d+)?))?\s*(个月|月|周|星期|天|日)"
)
_UNIT_DAYS = {"个月": 30, "月": 30, "周": 7, "星期": 7, "天": 1, "日": 1}


def stage_days(duration) -> float:
    """'3周（每周约8小时）' -> 21；'2-3个月' 取上限 -> 90；解析失败 -> 0。"""
    if isinstance(duration, (int, float)):
        return float(duration) * 7  # 纯数字按周理解
    m = _DURATION_RE.search(str(duration or ""))
    if not m:
        return 0
    value = max(float(m.group(1)), float(m.group(2) or 0))
    return value * _UNIT_DAYS[m.group(3)]


def estimate_due_date(plan: dict, start: datetime | None = None) -> datetime:
    start = start or datetime.now()
    stages = plan.get("stages") if isinstance(plan, dict) else None
    total = 0.0
    if isinstance(stages, list):
        for st in stages:
            if isinstance(st, dict):
                total += stage_days(st.get("duration"))
    days = round(total) if total > 0 else DEFAULT_PLAN_DAYS
    return start + timedelta(days=min(days, MAX_PLAN_DAYS))
