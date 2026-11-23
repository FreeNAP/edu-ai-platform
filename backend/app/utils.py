"""通用小工具：统一成功响应、时间序列化、分页、字符串清洗。"""
import re
from datetime import datetime

from fastapi import HTTPException

# 分页单页上限，防止一次拉取过多数据
MAX_PAGE_SIZE = 50


def ok(data=None):
    """契约统一成功格式 {code:0, data:...}。"""
    return {"code": 0, "data": data}


def iso(dt):
    return dt.isoformat(sep=" ", timespec="seconds") if isinstance(dt, datetime) else dt


def paginate(query, page: int, size: int, out) -> dict:
    """统一分页：page 最小 1，size 限制在 1..MAX_PAGE_SIZE，返回契约分页结构。"""
    page = max(1, page or 1)
    size = max(1, min(MAX_PAGE_SIZE, size or 10))
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return {"total": total, "page": page, "size": size, "items": [out(x) for x in items]}


def require_text(value: str | None, message: str) -> str:
    """去首尾空白后不能为空，否则 400。"""
    text = (value or "").strip()
    if not text:
        raise HTTPException(400, message)
    return text


_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u2300-\u23FF\uFE0F\u200D]"
)


def clean_cover(value: str | None) -> str:
    """课程封面只保留 URL/路径；emoji 等非链接内容一律置空（前端不再使用 emoji 封面）。"""
    text = _EMOJI_RE.sub("", (value or "")).strip()
    if not text or not ("/" in text or "." in text):
        return ""
    return text
