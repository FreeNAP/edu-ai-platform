"""密码哈希（PBKDF2）与 JWT 编解码。"""
import hashlib
import os
from datetime import datetime, timedelta, timezone

import jwt

from . import config

_PBKDF2_ITERATIONS = 100_000


def hash_password(password: str) -> str:
    """格式: salt$hash（十六进制）。"""
    salt = os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), _PBKDF2_ITERATIONS
    )
    return f"{salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, hash_hex = stored.split("$", 1)
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), _PBKDF2_ITERATIONS
        )
        return dk.hex() == hash_hex
    except Exception:
        return False


def create_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc)
        + timedelta(days=config.ACCESS_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def decode_token(token: str) -> int:
    """解码成功返回 user_id，失败抛 jwt 异常。"""
    payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
    return int(payload["sub"])
