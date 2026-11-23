"""进程内滑动窗口限流（单实例部署足够；多实例请在 Nginx 层限流）。"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

_lock = threading.Lock()
_hits: dict[str, deque] = defaultdict(deque)


def client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "-"


def hit(key: str, limit: int, window_seconds: int) -> None:
    """记录一次访问，超限抛 429。"""
    now = time.monotonic()
    with _lock:
        q = _hits[key]
        while q and now - q[0] > window_seconds:
            q.popleft()
        if len(q) >= limit:
            retry = int(window_seconds - (now - q[0])) + 1
            raise HTTPException(429, f"操作太频繁，请 {retry} 秒后再试", headers={"Retry-After": str(retry)})
        q.append(now)


def limiter(name: str, limit: int, window_seconds: int):
    """FastAPI 依赖：按 IP 限流。"""

    def _dep(request: Request):
        hit(f"{name}:{client_ip(request)}", limit, window_seconds)

    return _dep


def reset_all() -> None:
    with _lock:
        _hits.clear()
