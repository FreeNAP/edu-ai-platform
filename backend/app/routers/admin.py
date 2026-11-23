"""后台管理（契约第8节）：看板/用户/课程/讲师/职位/订单/申请。"""
from datetime import datetime, timedelta
import re
from typing import Optional, Union

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_admin
from ..models import (
    Answer,
    Application,
    Chapter,
    ChatMessage,
    ChatSession,
    Comment,
    Course,
    Enrollment,
    Favorite,
    Interview,
    Job,
    JobFavorite,
    LearningPlan,
    Lecturer,
    Lesson,
    LessonProgress,
    Notification,
    Order,
    Question,
    User,
)
from ..schemas import (
    AdminApplicationIn,
    AdminCourseIn,
    AdminJobIn,
    AdminLecturerIn,
    AdminOrderIn,
    AdminUserCreateIn,
    AdminUserIn,
    OutlineChapterIn,
    OutlineIn,
)
from ..serializers import (
    application_out,
    course_out,
    job_out,
    lecturer_out,
    order_out,
    question_out,
    user_out,
)
from ..services.notify import course_favoriter_ids, job_favoriter_ids, notify
from ..utils import clean_cover, ok, paginate, require_text
from .auth import create_user_account
from .community import delete_question_cascade, search_questions
from .orders import mark_order_paid

_CATEGORIES = ("theory", "practice", "certification")
_DIFFICULTIES = ("入门", "初级", "中级", "高级")
_ON_OFF = ("on", "off")
_LESSON_KINDS = ("video", "article", "lab")
_APPLICATION_LABELS = {
    "pending": "待处理", "viewed": "已查看", "accepted": "已通过", "rejected": "未通过",
}

router = APIRouter(
    prefix="/api/admin", tags=["后台"], dependencies=[Depends(require_admin)]
)


# ---------- 数据看板 ----------
@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    paid_orders = db.query(Order).filter(Order.status == "paid").all()
    paid_amount = sum(o.amount for o in paid_orders)
    total_study_seconds = (
        db.query(LessonProgress).with_entities(LessonProgress.study_seconds).all()
    )
    total_study_minutes = round(sum(r[0] for r in total_study_seconds) / 60)
    week_ago = datetime.now() - timedelta(days=7)
    recent_users = db.query(User).filter(User.created_at >= week_ago).count()
    # 近7日新增用户趋势
    trend = []
    for i in range(6, -1, -1):
        day_start = (datetime.now() - timedelta(days=i)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        day_end = day_start + timedelta(days=1)
        count = (
            db.query(User)
            .filter(User.created_at >= day_start, User.created_at < day_end)
            .count()
        )
        trend.append({"date": day_start.strftime("%m-%d"), "value": count})
    return ok(
        {
            "users": db.query(User).count(),
            "courses": db.query(Course).count(),
            "jobs": db.query(Job).count(),
            "orders": db.query(Order).count(),
            "paid_amount": paid_amount,
            "total_study_minutes": total_study_minutes,
            "recent_users": recent_users,
            "trend": trend,
        }
    )


# ---------- 用户管理 ----------
@router.get("/users")
def list_users(
    keyword: Optional[str] = None,
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_db),
):
    q = db.query(User)
    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        q = q.filter(
            or_(
                User.username.ilike(kw),
                User.email.ilike(kw),
                User.nickname.ilike(kw),
            )
        )
    q = q.order_by(User.created_at.desc(), User.id.desc())
    return ok(paginate(q, page, size, user_out))


@router.post("/users")
def create_user(body: AdminUserCreateIn, db: Session = Depends(get_db)):
    user = create_user_account(
        db, body.username, body.email, body.password, body.nickname, body.role
    )
    db.commit()
    db.refresh(user)
    return ok(user_out(user))


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    body: AdminUserIn,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "用户不存在")
    if body.role is not None:
        if body.role not in ("student", "teacher", "admin"):
            raise HTTPException(400, "非法角色")
        if user.id == admin.id and body.role != "admin":
            raise HTTPException(400, "不能修改自己的管理员角色")
        user.role = body.role
    if body.status is not None:
        if body.status not in ("active", "disabled"):
            raise HTTPException(400, "非法状态")
        if user.id == admin.id and body.status != "active":
            raise HTTPException(400, "不能禁用自己的账号")
        user.status = body.status
    db.commit()
    return ok(user_out(user))


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "用户不存在")
    if user.id == admin.id:
        raise HTTPException(400, "不能删除自己的账号")
    _delete_user_data(db, user_id)
    db.delete(user)
    db.commit()
    return ok({"ok": True})


def _recalc_course_rating(db: Session, course_id: int) -> None:
    course = db.get(Course, course_id)
    if course is None:
        return
    ratings = [r[0] for r in db.query(Comment.rating).filter(Comment.course_id == course_id).all()]
    if ratings:
        course.rating = round(sum(ratings) / len(ratings), 1)


def _delete_user_data(db: Session, user_id: int) -> None:
    """删除用户的全部关联数据，避免孤儿记录（SQLite 默认不强制外键）。"""
    # 报名人数回退
    for (cid,) in db.query(Enrollment.course_id).filter(Enrollment.user_id == user_id).all():
        c = db.get(Course, cid)
        if c is not None and c.students_count:
            c.students_count -= 1
    # 他人问题下的回答数回退
    for (qid,) in db.query(Answer.question_id).filter(Answer.user_id == user_id).all():
        q = db.get(Question, qid)
        if q is not None and q.user_id != user_id:
            q.answers_count = max(0, (q.answers_count or 0) - 1)
    commented = {r[0] for r in db.query(Comment.course_id).filter(Comment.user_id == user_id).all()}
    # 本人提问（含他人在其下的回答）
    own_qids = [r[0] for r in db.query(Question.id).filter(Question.user_id == user_id).all()]
    if own_qids:
        db.query(Answer).filter(Answer.question_id.in_(own_qids)).delete(synchronize_session=False)
    session_ids = [r[0] for r in db.query(ChatSession.id).filter(ChatSession.user_id == user_id).all()]
    if session_ids:
        db.query(ChatMessage).filter(ChatMessage.session_id.in_(session_ids)).delete(synchronize_session=False)
    for model in (
        Enrollment, LessonProgress, Favorite, JobFavorite, Application, Order,
        Comment, Answer, Question, ChatSession, LearningPlan, Interview, Notification,
    ):
        db.query(model).filter(model.user_id == user_id).delete(synchronize_session=False)
    db.flush()
    for cid in commented:
        _recalc_course_rating(db, cid)


# ---------- 课程管理 ----------
@router.get("/courses")
def admin_courses(db: Session = Depends(get_db)):
    courses = db.query(Course).order_by(Course.created_at.desc()).all()
    return ok([course_out(c) for c in courses])


def _validate_course_body(db: Session, body: AdminCourseIn) -> None:
    if body.title is not None and not body.title.strip():
        raise HTTPException(400, "课程标题不能为空")
    if body.category is not None and body.category not in _CATEGORIES:
        raise HTTPException(400, "非法课程分类")
    if body.difficulty is not None and body.difficulty not in _DIFFICULTIES:
        raise HTTPException(400, "非法难度")
    if body.status is not None and body.status not in _ON_OFF:
        raise HTTPException(400, "状态只能是 on/off")
    if body.lecturer_id is not None and db.get(Lecturer, body.lecturer_id) is None:
        raise HTTPException(400, "讲师不存在")


def _notify_course_favoriters(db: Session, course: Course, what: str) -> None:
    notify(
        db, course_favoriter_ids(db, course.id), "course", "收藏的课程有更新",
        f"你收藏的课程《{course.title}》{what}，快去看看吧。",
    )


@router.post("/courses")
def create_course(body: AdminCourseIn, db: Session = Depends(get_db)):
    if not (body.title or "").strip():
        raise HTTPException(400, "课程标题不能为空")
    _validate_course_body(db, body)
    course = Course(
        title=body.title.strip(),
        cover=clean_cover(body.cover),
        category=body.category or "theory",
        tech_domain=body.tech_domain or "",
        difficulty=body.difficulty or "入门",
        is_free=body.is_free if body.is_free is not None else True,
        price=body.price or 0,
        lecturer_id=body.lecturer_id,
        brief=body.brief or "",
        status=body.status or "on",
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return ok(course_out(course))


@router.put("/courses/{course_id}")
def update_course(
    course_id: int, body: AdminCourseIn, db: Session = Depends(get_db)
):
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(404, "课程不存在")
    _validate_course_body(db, body)
    if body.title is not None:
        body.title = body.title.strip()
    if body.cover is not None:
        body.cover = clean_cover(body.cover)
    changes = []
    old_status = course.status
    for field in (
        "title", "cover", "category", "tech_domain", "difficulty",
        "is_free", "price", "lecturer_id", "brief", "status",
    ):
        value = getattr(body, field)
        if value is not None and getattr(course, field) != value:
            setattr(course, field, value)
            changes.append(field)
    # 按契约：标题/简介/价格/上架变化通知收藏者（下架、封面等不通知）
    labels = {"title": "标题", "brief": "简介", "price": "价格", "is_free": "价格"}
    what = list(dict.fromkeys(labels[f] for f in changes if f in labels))
    relisted = old_status != "on" and course.status == "on"
    if course.status == "on" and (what or relisted):
        parts = []
        if relisted:
            parts.append("已重新上架")
        if what:
            parts.append("更新了" + "、".join(what))
        _notify_course_favoriters(db, course, "，".join(parts))
    db.commit()
    return ok(course_out(course))


# ---------- 课程目录（章节/课时）----------
_MINUTES_RE = re.compile(r"(\d+)")


def _parse_minutes(duration: str) -> int:
    m = _MINUTES_RE.search(duration or "")
    return max(1, min(600, int(m.group(1)))) if m else 10


def _course_outline(db: Session, course_id: int) -> list[dict]:
    chapters = (
        db.query(Chapter)
        .filter(Chapter.course_id == course_id)
        .order_by(Chapter.order_index, Chapter.id)
        .all()
    )
    data = []
    for ch in chapters:
        lessons = (
            db.query(Lesson)
            .filter(Lesson.chapter_id == ch.id)
            .order_by(Lesson.order_index, Lesson.id)
            .all()
        )
        data.append({
            "id": ch.id,
            "title": ch.title,
            "lessons": [
                {
                    "id": ls.id,
                    "title": ls.title,
                    "duration": ls.duration,
                    "kind": ls.kind,
                    "content": ls.content or "",
                }
                for ls in lessons
            ],
        })
    return data


def recalc_course_progress(db: Session, course_id: int) -> None:
    """课时总数变化后重算该课程所有报名记录的进度（不 commit）。"""
    lesson_ids = [
        r[0]
        for r in db.query(Lesson.id)
        .join(Chapter, Lesson.chapter_id == Chapter.id)
        .filter(Chapter.course_id == course_id)
        .all()
    ]
    total = len(lesson_ids)
    for e in db.query(Enrollment).filter(Enrollment.course_id == course_id).all():
        done = (
            db.query(LessonProgress)
            .filter(
                LessonProgress.user_id == e.user_id,
                LessonProgress.lesson_id.in_(lesson_ids),
            )
            .count()
            if lesson_ids
            else 0
        )
        e.progress = min(100, round(done * 100 / total)) if total else 0


@router.get("/courses/{course_id}/outline")
def get_course_outline(course_id: int, db: Session = Depends(get_db)):
    if db.get(Course, course_id) is None:
        raise HTTPException(404, "课程不存在")
    return ok(_course_outline(db, course_id))


@router.put("/courses/{course_id}/outline")
def put_course_outline(
    course_id: int,
    body: Union[list[OutlineChapterIn], OutlineIn] = Body(...),
    db: Session = Depends(get_db),
):
    """整体替换目录：带 id 的章节/课时就地更新，无 id 新增，未出现的删除。

    契约主写法是直接传数组，也兼容 {chapters:[...]}。
    """
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(404, "课程不存在")
    chapters_in = body.chapters if isinstance(body, OutlineIn) else body
    if len(chapters_in) > 50:
        raise HTTPException(400, "章节数量不能超过 50")

    old_chapters = {
        c.id: c for c in db.query(Chapter).filter(Chapter.course_id == course_id).all()
    }
    old_lessons = (
        {
            ls.id: ls
            for ls in db.query(Lesson).filter(Lesson.chapter_id.in_(list(old_chapters))).all()
        }
        if old_chapters
        else {}
    )

    # 先完整校验，避免改到一半报错留下半成品
    seen_ch, seen_ls = set(), set()
    for ch in chapters_in:
        require_text(ch.title, "章节标题不能为空")
        if ch.id is not None:
            if ch.id not in old_chapters:
                raise HTTPException(400, f"章节 {ch.id} 不属于该课程")
            if ch.id in seen_ch:
                raise HTTPException(400, f"章节 {ch.id} 重复")
            seen_ch.add(ch.id)
        for ls in ch.lessons:
            require_text(ls.title, "课时标题不能为空")
            if ls.kind == "text":
                ls.kind = "article"
            if (ls.kind or "video") not in _LESSON_KINDS:
                raise HTTPException(400, "课时类型只能是 video/article/lab")
            if ls.id is not None:
                if ls.id not in old_lessons:
                    raise HTTPException(400, f"课时 {ls.id} 不属于该课程")
                if ls.id in seen_ls:
                    raise HTTPException(400, f"课时 {ls.id} 重复")
                seen_ls.add(ls.id)

    # 删除不再出现的课时：先清学习进度，避免外键孤儿
    removed_lessons = [lid for lid in old_lessons if lid not in seen_ls]
    if removed_lessons:
        db.query(LessonProgress).filter(
            LessonProgress.lesson_id.in_(removed_lessons)
        ).delete(synchronize_session=False)
        db.query(Lesson).filter(Lesson.id.in_(removed_lessons)).delete(
            synchronize_session=False
        )

    for ci, ch_in in enumerate(chapters_in):
        if ch_in.id is not None:
            chapter = old_chapters[ch_in.id]
        else:
            chapter = Chapter(course_id=course_id)
            db.add(chapter)
        chapter.title = ch_in.title.strip()
        chapter.order_index = ci
        db.flush()
        for li, ls_in in enumerate(ch_in.lessons):
            if ls_in.id is not None:
                lesson = old_lessons[ls_in.id]
            else:
                lesson = Lesson()
                db.add(lesson)
            duration = (ls_in.duration or "").strip() or "10分钟"
            lesson.chapter_id = chapter.id
            lesson.title = ls_in.title.strip()
            lesson.duration = duration
            lesson.duration_minutes = _parse_minutes(duration)
            lesson.kind = ls_in.kind or "video"
            lesson.content = (ls_in.content or "").strip()
            lesson.order_index = li
    db.flush()

    # 保留课时已全部挂到保留/新章节，此时未出现的章节已为空，可安全删除
    removed_chapters = [cid for cid in old_chapters if cid not in seen_ch]
    if removed_chapters:
        db.query(Chapter).filter(Chapter.id.in_(removed_chapters)).delete(
            synchronize_session=False
        )
    db.flush()
    recalc_course_progress(db, course_id)
    if course.status == "on":
        _notify_course_favoriters(db, course, "更新了课程目录")
    db.commit()
    return ok(_course_outline(db, course_id))


@router.delete("/courses/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(404, "课程不存在")
    chapter_ids = [
        r[0] for r in db.query(Chapter.id).filter(Chapter.course_id == course_id).all()
    ]
    lesson_ids = [
        r[0]
        for r in db.query(Lesson.id).filter(Lesson.chapter_id.in_(chapter_ids)).all()
    ] if chapter_ids else []
    if lesson_ids:
        db.query(LessonProgress).filter(LessonProgress.lesson_id.in_(lesson_ids)).delete()
        db.query(Lesson).filter(Lesson.id.in_(lesson_ids)).delete()
    db.query(LessonProgress).filter(LessonProgress.course_id == course_id).delete()
    db.query(Chapter).filter(Chapter.course_id == course_id).delete()
    db.query(Enrollment).filter(Enrollment.course_id == course_id).delete()
    db.query(Favorite).filter(Favorite.course_id == course_id).delete()
    db.query(Comment).filter(Comment.course_id == course_id).delete()
    db.query(Order).filter(Order.course_id == course_id).delete()
    db.query(ChatSession).filter(ChatSession.course_id == course_id).update(
        {"course_id": None}, synchronize_session=False
    )
    db.delete(course)
    db.commit()
    return ok({"ok": True})


# ---------- 讲师管理 ----------
@router.get("/lecturers")
def list_lecturers(db: Session = Depends(get_db)):
    return ok([lecturer_out(l) for l in db.query(Lecturer).order_by(Lecturer.id).all()])


@router.post("/lecturers")
def create_lecturer(body: AdminLecturerIn, db: Session = Depends(get_db)):
    if not (body.name or "").strip():
        raise HTTPException(400, "讲师姓名不能为空")
    lecturer = Lecturer(
        name=body.name.strip(),
        title=body.title or "",
        bio=body.bio or "",
        avatar=body.avatar or "",
    )
    db.add(lecturer)
    db.commit()
    db.refresh(lecturer)
    return ok(lecturer_out(lecturer))


@router.put("/lecturers/{lecturer_id}")
def update_lecturer(
    lecturer_id: int, body: AdminLecturerIn, db: Session = Depends(get_db)
):
    lecturer = db.get(Lecturer, lecturer_id)
    if lecturer is None:
        raise HTTPException(404, "讲师不存在")
    if body.name is not None:
        body.name = require_text(body.name, "讲师姓名不能为空")
    for field in ("name", "title", "bio", "avatar"):
        value = getattr(body, field)
        if value is not None:
            setattr(lecturer, field, value)
    db.commit()
    return ok(lecturer_out(lecturer))


@router.delete("/lecturers/{lecturer_id}")
def delete_lecturer(lecturer_id: int, db: Session = Depends(get_db)):
    lecturer = db.get(Lecturer, lecturer_id)
    if lecturer is None:
        raise HTTPException(404, "讲师不存在")
    # 解除课程关联
    db.query(Course).filter(Course.lecturer_id == lecturer_id).update(
        {"lecturer_id": None}
    )
    db.delete(lecturer)
    db.commit()
    return ok({"ok": True})


# ---------- 职位管理 ----------
@router.get("/jobs")
def admin_jobs(db: Session = Depends(get_db)):
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    return ok([job_out(j) for j in jobs])


_JOB_FIELDS = (
    "title", "company", "city", "category", "salary",
    "description", "requirements", "headcount", "status",
)


def _validate_job_body(body: AdminJobIn) -> None:
    if body.title is not None:
        body.title = require_text(body.title, "职位名称不能为空")
    if body.company is not None:
        body.company = require_text(body.company, "公司名称不能为空")
    if body.status is not None and body.status not in _ON_OFF:
        raise HTTPException(400, "状态只能是 on/off")


def _apply_job_fields(job: Job, body: AdminJobIn) -> list[str]:
    """写入非空字段，返回实际发生变化的字段名。"""
    changed = []
    for field in _JOB_FIELDS:
        value = getattr(body, field)
        if isinstance(value, str) and field not in ("description", "requirements"):
            value = value.strip()
        if value is not None and getattr(job, field) != value:
            setattr(job, field, value)
            changed.append(field)
    if body.tags is not None:
        tags = ",".join(t.strip().replace(",", " ") for t in body.tags if t and t.strip())
        if (job.tags or "") != tags:
            job.tags = tags
            changed.append("tags")
    return changed


@router.post("/jobs")
def create_job(body: AdminJobIn, db: Session = Depends(get_db)):
    if not (body.title or "").strip() or not (body.company or "").strip():
        raise HTTPException(400, "职位名称与公司不能为空")
    _validate_job_body(body)
    job = Job(title=body.title, company=body.company, status="on")
    _apply_job_fields(job, body)
    db.add(job)
    db.commit()
    db.refresh(job)
    return ok(job_out(job))


@router.put("/jobs/{job_id}")
def update_job(job_id: int, body: AdminJobIn, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(404, "职位不存在")
    _validate_job_body(body)
    old_status = job.status
    changed = _apply_job_fields(job, body)
    # 契约：修改职位或重新上架通知收藏者；仅下架、或下架状态下的修改不通知
    relisted = old_status != "on" and job.status == "on"
    content_changed = [f for f in changed if f != "status"]
    if job.status == "on" and (relisted or content_changed):
        what = "已重新上架" if relisted else "信息有更新"
        notify(
            db, job_favoriter_ids(db, job.id), "job", "收藏的职位有更新",
            f"你收藏的职位「{job.title}·{job.company}」{what}，快去看看吧。",
        )
    db.commit()
    return ok(job_out(job))


@router.delete("/jobs/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(404, "职位不存在")
    db.query(JobFavorite).filter(JobFavorite.job_id == job_id).delete()
    db.query(Application).filter(Application.job_id == job_id).delete()
    db.query(Interview).filter(Interview.job_id == job_id).delete()
    db.delete(job)
    db.commit()
    return ok({"ok": True})


# ---------- 订单管理 ----------
@router.get("/orders")
def admin_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    items = []
    for o in orders:
        data = order_out(o)
        u = db.get(User, o.user_id)
        data["user"] = {"id": u.id, "username": u.username, "nickname": u.nickname} if u else None
        items.append(data)
    return ok(items)


@router.put("/orders/{order_id}")
def update_order(
    order_id: int, body: AdminOrderIn, db: Session = Depends(get_db)
):
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(404, "订单不存在")
    if body.status is not None:
        if body.status not in ("pending", "paid", "cancelled"):
            raise HTTPException(400, "非法订单状态")
        if body.status == "paid" and order.status != "paid":
            mark_order_paid(db, order)
        else:
            order.status = body.status
    db.commit()
    return ok(order_out(order))


# ---------- 申请管理 ----------
@router.get("/applications")
def admin_applications(db: Session = Depends(get_db)):
    apps = db.query(Application).order_by(Application.created_at.desc()).all()
    items = []
    for a in apps:
        data = application_out(a, db.get(Job, a.job_id))
        u = db.get(User, a.user_id)
        data["user"] = {"id": u.id, "username": u.username, "nickname": u.nickname} if u else None
        items.append(data)
    return ok(items)


@router.put("/applications/{application_id}")
def update_application(
    application_id: int, body: AdminApplicationIn, db: Session = Depends(get_db)
):
    app = db.get(Application, application_id)
    if app is None:
        raise HTTPException(404, "申请不存在")
    if body.status is not None:
        if body.status not in ("pending", "viewed", "accepted", "rejected"):
            raise HTTPException(400, "非法申请状态")
        if app.status != body.status:
            app.status = body.status
            job = db.get(Job, app.job_id)
            label = _APPLICATION_LABELS[body.status]
            notify(
                db, app.user_id, "application", "你的职位申请状态已更新",
                f"你申请的职位「{job.title if job else '已删除职位'}」状态变更为：{label}。",
            )
    db.commit()
    return ok(application_out(app, db.get(Job, app.job_id)))


# ---------- 社区问题管理 ----------
@router.get("/questions")
def admin_questions(
    keyword: Optional[str] = None,
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_db),
):
    return ok(paginate(search_questions(db, keyword), page, size, question_out))


@router.delete("/questions/{question_id}")
def admin_delete_question(question_id: int, db: Session = Depends(get_db)):
    q = db.get(Question, question_id)
    if q is None:
        raise HTTPException(404, "问题不存在")
    delete_question_cascade(db, q)
    db.commit()
    return ok({"ok": True})
