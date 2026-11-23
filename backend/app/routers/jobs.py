"""实习就业模块（契约第3节）：筛选/搜索/详情/收藏/申请/AI面试。"""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, get_current_user_optional
from ..models import Application, Interview, Job, JobFavorite, User
from ..schemas import ApplyIn
from ..serializers import application_out, job_out
from ..services import llm
from ..utils import ok, paginate

router = APIRouter(prefix="/api/jobs", tags=["职位"])


@router.get("")
def list_jobs(
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    city: Optional[str] = None,
    page: int = 1,
    size: int = 12,
    db: Session = Depends(get_db),
):
    q = db.query(Job).filter(Job.status == "on")
    if category:
        q = q.filter(Job.category == category)
    if city:
        q = q.filter(Job.city == city)
    if keyword:
        kw = f"%{keyword.strip()}%"
        q = q.filter(or_(Job.title.ilike(kw), Job.company.ilike(kw)))
    q = q.order_by(Job.created_at.desc(), Job.id.desc())
    return ok(paginate(q, page, size, job_out))


@router.get("/meta/filters")
def job_filters(db: Session = Depends(get_db)):
    categories = [
        r[0]
        for r in db.query(Job.category).filter(Job.status == "on").distinct().all()
        if r[0]
    ]
    cities = [
        r[0]
        for r in db.query(Job.city).filter(Job.status == "on").distinct().all()
        if r[0]
    ]
    return ok({"categories": sorted(categories), "cities": sorted(cities)})


def _get_job_or_404(db: Session, job_id: int, allow_off: bool = False) -> Job:
    """前台访问：下架职位视为不存在；allow_off 仅用于管理员预览详情。"""
    job = db.get(Job, job_id)
    if job is None or (job.status != "on" and not allow_off):
        raise HTTPException(404, "职位不存在或已下架")
    return job


@router.get("/{job_id}")
def job_detail(
    job_id: int,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    job = _get_job_or_404(db, job_id, allow_off=user is not None and user.role == "admin")
    is_fav = has_applied = False
    if user is not None:
        is_fav = (
            db.query(JobFavorite)
            .filter(JobFavorite.user_id == user.id, JobFavorite.job_id == job.id)
            .first()
            is not None
        )
        has_applied = (
            db.query(Application)
            .filter(Application.user_id == user.id, Application.job_id == job.id)
            .first()
            is not None
        )
    data = job_out(job)
    data["is_favorited"] = is_fav
    data["has_applied"] = has_applied
    return ok(data)


@router.post("/{job_id}/favorite")
def toggle_job_favorite(
    job_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_job_or_404(db, job_id)
    fav = (
        db.query(JobFavorite)
        .filter(JobFavorite.user_id == user.id, JobFavorite.job_id == job_id)
        .first()
    )
    if fav:
        db.delete(fav)
        db.commit()
        return ok({"favorited": False})
    db.add(JobFavorite(user_id=user.id, job_id=job_id))
    try:
        db.commit()
    except IntegrityError:  # 并发重复点击：已被另一请求收藏
        db.rollback()
    return ok({"favorited": True})


@router.post("/{job_id}/apply")
def apply_job(
    job_id: int,
    body: ApplyIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_job_or_404(db, job_id)
    app = (
        db.query(Application)
        .filter(Application.user_id == user.id, Application.job_id == job_id)
        .first()
    )
    if app:
        return ok(application_out(app, db.get(Job, app.job_id)))
    app = Application(
        user_id=user.id, job_id=job_id, message=(body.message or "").strip(), status="pending"
    )
    db.add(app)
    try:
        db.commit()
    except IntegrityError:  # 并发重复申请：返回已存在的申请
        db.rollback()
        app = (
            db.query(Application)
            .filter(Application.user_id == user.id, Application.job_id == job_id)
            .first()
        )
        return ok(application_out(app, db.get(Job, job_id)))
    db.refresh(app)
    return ok(application_out(app, db.get(Job, job_id)))


@router.post("/{job_id}/ai-interview")
def create_ai_interview(
    job_id: int,
    body: Optional[ApplyIn] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = _get_job_or_404(db, job_id)
    questions = llm.gen_interview_questions(job)
    interview = Interview(
        user_id=user.id,
        job_id=job.id,
        questions=json.dumps(questions, ensure_ascii=False),
        status="pending",
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return ok({"interview_id": interview.id, "questions": questions})
