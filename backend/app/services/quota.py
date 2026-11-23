"""AI 每日调用配额：学生受 AI_DAILY_QUOTA 限制，教师与管理员不限。"""
from __future__ import annotations

from datetime import date

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import get_current_user
from ..models import AiUsage, User


def usage_today(db: Session, user: User) -> dict:
    row = db.query(AiUsage).filter(AiUsage.user_id == user.id, AiUsage.day == date.today().isoformat()).first()
    used = row.count if row else 0
    unlimited = settings.ai_daily_quota <= 0 or user.role in ("teacher", "admin")
    return {"used": used, "limit": 0 if unlimited else settings.ai_daily_quota, "unlimited": unlimited,
            "remaining": None if unlimited else max(0, settings.ai_daily_quota - used)}


def consume_ai_quota(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
    """FastAPI 依赖：检查并计一次 AI 调用。"""
    info = usage_today(db, user)
    if not info["unlimited"] and info["remaining"] <= 0:
        raise HTTPException(429, f"今天的 AI 使用次数（{info['limit']} 次）已用完，明天再来")
    day = date.today().isoformat()
    row = db.query(AiUsage).filter(AiUsage.user_id == user.id, AiUsage.day == day).first()
    if row is None:
        db.add(AiUsage(user_id=user.id, day=day, count=1))
    else:
        row.count += 1
    db.commit()
    return user
