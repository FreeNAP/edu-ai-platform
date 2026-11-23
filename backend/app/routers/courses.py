"""课程模块（契约第2节）：列表/筛选/详情/收藏/报名/评论/课时进度。"""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, get_current_user_optional
from ..models import (
    Chapter,
    Comment,
    Course,
    Enrollment,
    Favorite,
    Lecturer,
    Lesson,
    LessonProgress,
    Order,
    User,
)
from ..schemas import CommentIn, LessonCompleteIn
from ..serializers import comment_out, course_out, lecturer_out, order_out
from ..utils import ok, paginate

router = APIRouter(prefix="/api/courses", tags=["课程"])
lessons_router = APIRouter(prefix="/api/lessons", tags=["课时"])

_CATEGORY_LABELS = [
    {"key": "theory", "label": "理论课程"},
    {"key": "practice", "label": "实训课程"},
    {"key": "certification", "label": "认证课程"},
]
_DIFFICULTIES = ["入门", "初级", "中级", "高级"]


@router.get("")
def list_courses(
    category: Optional[str] = None,
    tech_domain: Optional[str] = None,
    difficulty: Optional[str] = None,
    is_free: Optional[bool] = None,
    sort: Optional[str] = "newest",
    keyword: Optional[str] = None,
    page: int = 1,
    size: int = 12,
    db: Session = Depends(get_db),
):
    q = db.query(Course).filter(Course.status == "on")
    if category:
        q = q.filter(Course.category == category)
    if tech_domain:
        q = q.filter(Course.tech_domain == tech_domain)
    if difficulty:
        q = q.filter(Course.difficulty == difficulty)
    if is_free is not None:
        q = q.filter(Course.is_free == is_free)
    if keyword:
        kw = f"%{keyword.strip()}%"
        q = q.outerjoin(Lecturer, Course.lecturer_id == Lecturer.id).filter(
            or_(Course.title.ilike(kw), Lecturer.name.ilike(kw))
        )
    if sort == "students":
        q = q.order_by(Course.students_count.desc())
    elif sort == "rating":
        q = q.order_by(Course.rating.desc())
    else:  # newest
        q = q.order_by(Course.created_at.desc(), Course.id.desc())
    return ok(paginate(q, page, size, course_out))


@router.get("/meta/filters")
def course_filters(db: Session = Depends(get_db)):
    domains = [
        r[0]
        for r in db.query(Course.tech_domain)
        .filter(Course.status == "on")
        .distinct()
        .order_by(Course.tech_domain)
        .all()
        if r[0]
    ]
    return ok(
        {
            "categories": _CATEGORY_LABELS,
            "tech_domains": domains,
            "difficulties": _DIFFICULTIES,
        }
    )


def _get_course_or_404(db: Session, course_id: int, allow_off: bool = False) -> Course:
    """前台访问：下架课程视为不存在；allow_off 仅用于管理员预览详情。"""
    course = db.get(Course, course_id)
    if course is None or (course.status != "on" and not allow_off):
        raise HTTPException(404, "课程不存在或已下架")
    return course


def _lesson_status(db: Session, user_id: int, course_id: int) -> list[int]:
    return [
        r[0]
        for r in db.query(LessonProgress.lesson_id)
        .filter(
            LessonProgress.user_id == user_id,
            LessonProgress.course_id == course_id,
        )
        .all()
    ]


@router.get("/{course_id}")
def course_detail(
    course_id: int,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    course = _get_course_or_404(
        db, course_id, allow_off=user is not None and user.role == "admin"
    )
    enroll = None
    if user is not None:
        enroll = (
            db.query(Enrollment)
            .filter(
                Enrollment.user_id == user.id, Enrollment.course_id == course.id
            )
            .first()
        )
    chapters = (
        db.query(Chapter)
        .filter(Chapter.course_id == course.id)
        .order_by(Chapter.order_index, Chapter.id)
        .all()
    )
    chapter_data = []
    for ch in chapters:
        lessons = (
            db.query(Lesson)
            .filter(Lesson.chapter_id == ch.id)
            .order_by(Lesson.order_index, Lesson.id)
            .all()
        )
        chapter_data.append(
            {
                "id": ch.id,
                "title": ch.title,
                "lessons": [
                    {
                        "id": ls.id,
                        "title": ls.title,
                        "duration": ls.duration,
                        "kind": ls.kind,
                        # 附加字段：课时正文仅对已报名用户下发，避免付费内容泄露
                        "content": (ls.content or "") if enroll else "",
                        "video_url": (ls.video_url or "") if enroll else "",
                    }
                    for ls in lessons
                ],
            }
        )
    comments = (
        db.query(Comment)
        .filter(Comment.course_id == course.id)
        .order_by(Comment.created_at.desc())
        .all()
    )
    is_fav = is_enrolled = False
    progress = 0
    lesson_status: list[int] = []
    if user is not None:
        is_fav = (
            db.query(Favorite)
            .filter(Favorite.user_id == user.id, Favorite.course_id == course.id)
            .first()
            is not None
        )
        is_enrolled = enroll is not None
        progress = enroll.progress if enroll else 0
        lesson_status = _lesson_status(db, user.id, course.id)
    return ok(
        {
            "course": course_out(course),
            "chapters": chapter_data,
            "lecturer": lecturer_out(course.lecturer) if course.lecturer else None,
            "comments": [comment_out(cm) for cm in comments],
            "is_favorited": is_fav,
            "is_enrolled": is_enrolled,
            "progress": progress,
            "lesson_status": lesson_status,
        }
    )


@router.post("/{course_id}/favorite")
def toggle_favorite(
    course_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_course_or_404(db, course_id)
    fav = (
        db.query(Favorite)
        .filter(Favorite.user_id == user.id, Favorite.course_id == course_id)
        .first()
    )
    if fav:
        db.delete(fav)
        db.commit()
        return ok({"favorited": False})
    db.add(Favorite(user_id=user.id, course_id=course_id))
    try:
        db.commit()
    except IntegrityError:  # 并发重复点击：已被另一请求收藏
        db.rollback()
    return ok({"favorited": True})


@router.post("/{course_id}/enroll")
def enroll(
    course_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = _get_course_or_404(db, course_id)
    exists = (
        db.query(Enrollment)
        .filter(Enrollment.user_id == user.id, Enrollment.course_id == course.id)
        .first()
    )
    if exists:
        return ok({"enrolled": True, "order": None})
    if course.is_free or not course.price:
        db.add(Enrollment(user_id=user.id, course_id=course.id))
        course.students_count = (course.students_count or 0) + 1
        try:
            db.commit()
        except IntegrityError:  # 并发重复报名：视为已报名
            db.rollback()
        return ok({"enrolled": True, "order": None})
    # 付费课程：已有待支付订单则直接返回，避免重复下单
    order = (
        db.query(Order)
        .filter(
            Order.user_id == user.id,
            Order.course_id == course.id,
            Order.status == "pending",
        )
        .first()
    )
    if order is None:
        order = Order(
            user_id=user.id,
            course_id=course.id,
            order_no="EDU" + uuid.uuid4().hex[:16].upper(),
            amount=course.price,
            status="pending",
        )
        db.add(order)
        db.commit()
        db.refresh(order)
    return ok({"enrolled": False, "order": order_out(order)})


@router.get("/{course_id}/comments")
def list_comments(course_id: int, db: Session = Depends(get_db)):
    _get_course_or_404(db, course_id)
    comments = (
        db.query(Comment)
        .filter(Comment.course_id == course_id)
        .order_by(Comment.created_at.desc())
        .all()
    )
    return ok([comment_out(c) for c in comments])


@router.post("/{course_id}/comments")
def create_comment(
    course_id: int,
    body: CommentIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = _get_course_or_404(db, course_id)
    enrolled = (
        db.query(Enrollment)
        .filter(Enrollment.user_id == user.id, Enrollment.course_id == course.id)
        .first()
    )
    if not enrolled:
        raise HTTPException(403, "请先报名课程后再评论")
    if not (1 <= body.rating <= 5):
        raise HTTPException(400, "评分需在 1-5 之间")
    if not (body.content or "").strip():
        raise HTTPException(400, "评论内容不能为空")
    comment = Comment(
        user_id=user.id,
        course_id=course.id,
        rating=body.rating,
        content=body.content.strip(),
    )
    db.add(comment)
    # 课程评分取评论平均值
    avg = (
        db.query(Comment)
        .filter(Comment.course_id == course.id)
        .with_entities(Comment.rating)
        .all()
    )
    ratings = [r[0] for r in avg] + [body.rating]
    course.rating = round(sum(ratings) / len(ratings), 1)
    db.commit()
    db.refresh(comment)
    return ok(comment_out(comment))


@lessons_router.post("/{lesson_id}/complete")
def complete_lesson(
    lesson_id: int,
    body: LessonCompleteIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lesson = db.get(Lesson, lesson_id)
    chapter = db.get(Chapter, lesson.chapter_id) if lesson else None
    if lesson is None or chapter is None:
        raise HTTPException(404, "课时不存在")
    course_id = chapter.course_id
    enrollment = (
        db.query(Enrollment)
        .filter(Enrollment.user_id == user.id, Enrollment.course_id == course_id)
        .first()
    )
    if enrollment is None:
        raise HTTPException(403, "请先报名课程")
    # 单次上报最多 4 小时，防止异常值污染学习时长统计
    seconds = max(0, min(4 * 3600, int(body.study_seconds or 0)))
    lp = (
        db.query(LessonProgress)
        .filter(
            LessonProgress.user_id == user.id,
            LessonProgress.lesson_id == lesson_id,
        )
        .first()
    )
    if lp is None:
        lp = LessonProgress(
            user_id=user.id,
            lesson_id=lesson_id,
            course_id=course_id,
            study_seconds=seconds,
            completed_at=datetime.now(),
        )
        db.add(lp)
    else:
        lp.study_seconds += seconds
        lp.completed_at = datetime.now()
    # 重算课程进度
    total = (
        db.query(Lesson)
        .join(Chapter, Lesson.chapter_id == Chapter.id)
        .filter(Chapter.course_id == course_id)
        .count()
    )
    done = (
        db.query(LessonProgress)
        .filter(
            LessonProgress.user_id == user.id,
            LessonProgress.course_id == course_id,
        )
        .count()
    ) + (0 if lp.id else 1)
    progress = min(100, round(done * 100 / total)) if total else 0
    enrollment.progress = progress
    enrollment.study_seconds += seconds
    db.commit()
    return ok({"progress": progress})
