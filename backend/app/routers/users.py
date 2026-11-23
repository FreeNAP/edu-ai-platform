"""个人信息、我的学习、我的收藏、我的申请（契约第1-3节）。"""
import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import (
    Application,
    Chapter,
    Course,
    Enrollment,
    Favorite,
    Interview,
    Job,
    JobFavorite,
    Lesson,
    LessonProgress,
    User,
)
from ..schemas import ChangePasswordIn, ProfileIn
from ..security import hash_password, password_problem, verify_password
from .auth import issue_tokens
from ..serializers import application_out, course_out, interview_out, job_out, user_out
from ..utils import iso, ok

router = APIRouter(prefix="/api/users", tags=["用户"])


def _valid_avatar(v: str) -> bool:
    return (
        v == ""
        or re.fullmatch(r"builtin:[1-8]", v) is not None
        or v.startswith("/uploads/avatar/")
        or re.fullmatch(r"https://[^\s\"'<>]+", v) is not None
    )


@router.put("/profile")
def update_profile(
    body: ProfileIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.nickname is not None:
        nickname = body.nickname.strip()
        if not nickname:
            raise HTTPException(400, "昵称不能为空")
        user.nickname = nickname
    if body.avatar is not None and not _valid_avatar(body.avatar.strip()):
        raise HTTPException(400, "头像只能使用内置图案、上传的图片或 https 图片地址")
    if body.resume_url is not None and body.resume_url.strip() and not body.resume_url.strip().startswith("/uploads/resume/"):
        raise HTTPException(400, "简历请通过上传功能提交")
    for field in ("avatar", "major", "bio", "resume_url"):
        value = getattr(body, field)
        if value is not None:
            setattr(user, field, value.strip())
    db.commit()
    return ok(user_out(user))


@router.put("/password")
def change_password(
    body: ChangePasswordIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(body.old_password or "", user.password_hash):
        raise HTTPException(400, "原密码错误")
    problem = password_problem(body.new_password or "", user.username)
    if problem:
        raise HTTPException(400, problem)
    if verify_password(body.new_password, user.password_hash):
        raise HTTPException(400, "新密码不能与原密码相同")
    user.password_hash = hash_password(body.new_password)
    user.token_version = (user.token_version or 0) + 1  # 其他设备上的登录随之失效
    db.commit()
    db.refresh(user)
    return ok(issue_tokens(user))


def _lesson_total(db: Session, course_id: int) -> int:
    return (
        db.query(Lesson)
        .join(Chapter, Lesson.chapter_id == Chapter.id)
        .filter(Chapter.course_id == course_id)
        .count()
    )


@router.get("/me/enrollments")
def my_enrollments(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    enrollments = (
        db.query(Enrollment)
        .filter(Enrollment.user_id == user.id)
        .order_by(Enrollment.created_at.desc())
        .all()
    )
    items = []
    for e in enrollments:
        course = db.get(Course, e.course_id)
        if course is None:
            continue
        done = (
            db.query(LessonProgress)
            .filter(
                LessonProgress.user_id == user.id,
                LessonProgress.course_id == e.course_id,
            )
            .count()
        )
        items.append(
            {
                "id": e.id,
                "course": course_out(course),
                "progress": e.progress,
                "study_seconds": e.study_seconds,
                "completed_lessons": done,
                "total_lessons": _lesson_total(db, e.course_id),
                "created_at": iso(e.created_at),
            }
        )
    return ok(items)


@router.get("/me/favorites")
def my_favorites(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    course_ids = [
        f.course_id
        for f in db.query(Favorite)
        .filter(Favorite.user_id == user.id)
        .order_by(Favorite.created_at.desc())
        .all()
    ]
    job_ids = [
        f.job_id
        for f in db.query(JobFavorite)
        .filter(JobFavorite.user_id == user.id)
        .order_by(JobFavorite.created_at.desc())
        .all()
    ]
    # 下架的课程/职位在前台收藏列表中隐藏
    courses = [course_out(c) for c in
               (db.get(Course, cid) for cid in course_ids)
               if c is not None and c.status == "on"]
    job_list = [job_out(j) for j in
                (db.get(Job, jid) for jid in job_ids)
                if j is not None and j.status == "on"]
    return ok({"courses": courses, "jobs": job_list})


@router.get("/me/applications")
def my_applications(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    apps = (
        db.query(Application)
        .filter(Application.user_id == user.id)
        .order_by(Application.created_at.desc())
        .all()
    )
    return ok([application_out(a, db.get(Job, a.job_id)) for a in apps])


@router.get("/me/interviews")
def my_interviews(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    interviews = (
        db.query(Interview)
        .filter(Interview.user_id == user.id)
        .order_by(Interview.created_at.desc(), Interview.id.desc())
        .all()
    )
    return ok([interview_out(iv, db.get(Job, iv.job_id)) for iv in interviews])
