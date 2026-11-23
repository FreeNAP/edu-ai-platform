"""审计日志：记录管理员 / 教师的所有写操作。"""
from __future__ import annotations

import logging
import re

from starlette.middleware.base import BaseHTTPMiddleware

from ..database import SessionLocal
from ..models import AuditLog, User
from ..ratelimit import client_ip
from ..security import decode_token

logger = logging.getLogger("edu.audit")

_AUDITED = re.compile(r"^/api/(admin|teacher)/")
_ID = re.compile(r"/(\d+)(?:/|$)")


def _action(method: str, path: str) -> tuple[str, str, str]:
    parts = [p for p in path.split("/") if p and not p.isdigit()][1:]  # 去掉 api 前缀
    verb = {"POST": "create", "PUT": "update", "PATCH": "update", "DELETE": "delete"}.get(method, method.lower())
    action = ".".join(parts + [verb])[:64]
    target_type = parts[1] if len(parts) > 1 else parts[0] if parts else ""
    m = _ID.search(path)
    return action, target_type, m.group(1) if m else ""


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.method in ("POST", "PUT", "PATCH", "DELETE") and _AUDITED.match(request.url.path) and response.status_code < 400:
            try:
                self._record(request, response.status_code)
            except Exception:
                logger.exception("写入审计日志失败")
        return response

    @staticmethod
    def _record(request, status: int) -> None:
        auth = request.headers.get("authorization", "")
        actor_id = None
        if auth.lower().startswith("bearer "):
            try:
                actor_id, _ = decode_token(auth[7:])
            except Exception:
                actor_id = None
        action, target_type, target_id = _action(request.method, request.url.path)
        with SessionLocal() as db:
            actor = db.get(User, actor_id) if actor_id else None
            db.add(AuditLog(
                actor_id=actor.id if actor else None,
                actor_name=actor.username if actor else "",
                action=action,
                target_type=target_type,
                target_id=target_id,
                detail=f"{request.method} {request.url.path} -> {status}",
                ip=client_ip(request),
            ))
            db.commit()
