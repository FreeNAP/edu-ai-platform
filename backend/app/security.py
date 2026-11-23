"""密码哈希、密码强度校验与 JWT（访问令牌 + 刷新令牌）。"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from .config import settings

_PBKDF2_ITERATIONS = 310_000
_LEGACY_ITERATIONS = 100_000


def hash_password(password: str) -> str:
    """格式: pbkdf2$迭代次数$salt$hash。"""
    salt = os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), _PBKDF2_ITERATIONS)
    return f"pbkdf2${_PBKDF2_ITERATIONS}${salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        parts = stored.split("$")
        if len(parts) == 4 and parts[0] == "pbkdf2":
            iterations, salt, hash_hex = int(parts[1]), parts[2], parts[3]
        else:  # 旧格式 salt$hash
            iterations, (salt, hash_hex) = _LEGACY_ITERATIONS, stored.split("$", 1)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
        return hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False


def needs_rehash(stored: str) -> bool:
    parts = stored.split("$")
    return not (len(parts) == 4 and parts[0] == "pbkdf2" and int(parts[1]) >= _PBKDF2_ITERATIONS)


def password_problem(password: str, username: str = "") -> str | None:
    """返回不符合要求的原因；None 表示通过。"""
    if len(password) < settings.password_min_length:
        return f"密码至少 {settings.password_min_length} 位"
    if len(password) > 128:
        return "密码不能超过 128 位"
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return "密码需要同时包含字母和数字"
    if username and username.lower() in password.lower():
        return "密码不能包含用户名"
    return None


def _encode(user_id: int, version: int, kind: str, ttl: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "ver": version, "typ": kind, "iat": now, "exp": now + ttl, "jti": secrets.token_hex(8)}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_token(user_id: int, version: int = 0) -> str:
    """访问令牌（短期）。"""
    return _encode(user_id, version, "access", timedelta(minutes=settings.access_token_expire_minutes))


def create_refresh_token(user_id: int, version: int = 0) -> str:
    return _encode(user_id, version, "refresh", timedelta(days=settings.refresh_token_expire_days))


def decode_token(token: str, kind: str = "access") -> tuple[int, int]:
    """返回 (user_id, token_version)；类型不符或过期抛异常。"""
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    if payload.get("typ", "access") != kind:
        raise jwt.InvalidTokenError("token type mismatch")
    return int(payload["sub"]), int(payload.get("ver", 0))


def hash_code(code: str) -> str:
    return hmac.new(settings.secret_key.encode(), code.encode(), hashlib.sha256).hexdigest()
