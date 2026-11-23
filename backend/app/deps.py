"""鉴权依赖：当前用户、可选用户、管理员。"""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .security import decode_token

_bearer = HTTPBearer(auto_error=False)


def _user_from_token(token: str, db: Session) -> User | None:
    try:
        user_id, version = decode_token(token)
    except Exception:
        return None
    user = db.get(User, user_id)
    if user is None or user.status != "active" or (user.token_version or 0) != version:
        return None
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="未登录或登录已过期")
    user = _user_from_token(credentials.credentials, db)
    if user is None:
        raise HTTPException(status_code=401, detail="无效或过期的登录凭证")
    return user


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    return _user_from_token(credentials.credentials, db)


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


def require_teacher(user: User = Depends(get_current_user)) -> User:
    """教师或管理员。"""
    if user.role not in ("teacher", "admin"):
        raise HTTPException(status_code=403, detail="需要教师权限")
    return user
