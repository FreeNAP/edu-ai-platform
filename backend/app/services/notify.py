"""站内通知统一写入（自动通知规则见 API契约.md 第 9 节）。

只 add 不 commit，由调用方在业务事务里一并提交。
"""
from typing import Iterable

from sqlalchemy.orm import Session

from ..models import Favorite, JobFavorite, Notification


def notify(db: Session, user_ids: Iterable[int] | int, type_: str, title: str, content: str) -> int:
    """给一个或多个用户写通知，自动去重，返回写入条数。"""
    if isinstance(user_ids, int):
        user_ids = [user_ids]
    count = 0
    for uid in dict.fromkeys(u for u in user_ids if u):
        db.add(Notification(user_id=uid, type=type_, title=title, content=content))
        count += 1
    return count


def course_favoriter_ids(db: Session, course_id: int) -> list[int]:
    return [r[0] for r in db.query(Favorite.user_id).filter(Favorite.course_id == course_id).all()]


def job_favoriter_ids(db: Session, job_id: int) -> list[int]:
    return [r[0] for r in db.query(JobFavorite.user_id).filter(JobFavorite.job_id == job_id).all()]
