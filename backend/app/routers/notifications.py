"""站内通知（契约第6节）+ 学习路径到期提醒惰性补发（第9节）。"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import LearningPlan, Notification, User
from ..services.notify import notify
from ..utils import iso, ok

router = APIRouter(prefix="/api/notifications", tags=["通知"])


def remind_due_plans(db: Session, user_id: int) -> int:
    """已到期且未提醒的学习路径补发一次 study 通知，返回补发条数。"""
    not_reminded = or_(LearningPlan.reminded.is_(None), LearningPlan.reminded == False)  # noqa: E712
    plans = (
        db.query(LearningPlan)
        .filter(
            LearningPlan.user_id == user_id,
            LearningPlan.due_date.isnot(None),
            LearningPlan.due_date <= datetime.now(),
            not_reminded,
        )
        .all()
    )
    sent = 0
    for p in plans:
        # 条件更新抢占标记，并发拉取时保证每条计划只提醒一次
        claimed = (
            db.query(LearningPlan)
            .filter(LearningPlan.id == p.id, not_reminded)
            .update({"reminded": True}, synchronize_session=False)
        )
        if not claimed:
            continue
        notify(
            db, user_id, "study", "学习计划到期提醒",
            f"你的学习计划「{p.goal}」已于 {p.due_date:%Y-%m-%d} 到期，"
            "回顾一下完成情况，也可以重新生成新的学习路径。",
        )
        sent += 1
    if sent:
        db.commit()
    return sent


@router.get("")
def list_notifications(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    remind_due_plans(db, user.id)
    items = (
        db.query(Notification)
        .filter(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .all()
    )
    unread = sum(1 for n in items if not n.is_read)
    return ok(
        {
            "items": [
                {
                    "id": n.id,
                    "type": n.type,
                    "title": n.title,
                    "content": n.content,
                    "is_read": n.is_read,
                    "created_at": iso(n.created_at),
                }
                for n in items
            ],
            "unread_count": unread,
        }
    )


@router.post("/{notification_id}/read")
def read_notification(
    notification_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    n = db.get(Notification, notification_id)
    if n is None or n.user_id != user.id:
        raise HTTPException(404, "通知不存在")
    n.is_read = True
    db.commit()
    return ok({"ok": True})


@router.post("/read-all")
def read_all_notifications(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    db.query(Notification).filter(
        Notification.user_id == user.id, Notification.is_read == False  # noqa: E712
    ).update({"is_read": True})
    db.commit()
    return ok({"ok": True})
