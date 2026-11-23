"""教师工作台：管理自己负责的课程、章节目录、测验/考试，查看学员学习情况。

管理员可以访问全部课程；教师只能访问 teacher_id 为自己的课程。
"""
from __future__ import annotations

import json
from typing import Union

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_teacher
from ..models import (
    Comment,
    Course,
    Enrollment,
    Lesson,
    Chapter,
    Quiz,
    QuizAttempt,
    QuizQuestion,
    User,
)
from ..schemas import AdminCourseIn, OutlineChapterIn, OutlineIn, QuizIn
from ..serializers import course_out
from ..utils import iso, ok
from . import admin as admin_api
from .quizzes import normalize_answer, quiz_out

router = APIRouter(prefix="/api/teacher", tags=["教师工作台"], dependencies=[Depends(require_teacher)])


def _own_course(db: Session, user: User, course_id: int) -> Course:
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(404, "课程不存在")
    if user.role != "admin" and course.teacher_id != user.id:
        raise HTTPException(403, "只能管理自己负责的课程")
    return course


def _lesson_count(db: Session, course_id: int) -> int:
    return db.query(func.count(Lesson.id)).join(Chapter, Lesson.chapter_id == Chapter.id).filter(Chapter.course_id == course_id).scalar() or 0


@router.get("/overview")
def overview(user: User = Depends(require_teacher), db: Session = Depends(get_db)):
    q = db.query(Course)
    if user.role != "admin":
        q = q.filter(Course.teacher_id == user.id)
    courses = q.all()
    ids = [c.id for c in courses]
    students = db.query(func.count(Enrollment.id)).filter(Enrollment.course_id.in_(ids)).scalar() if ids else 0
    avg_progress = db.query(func.avg(Enrollment.progress)).filter(Enrollment.course_id.in_(ids)).scalar() if ids else None
    comments = db.query(func.count(Comment.id)).filter(Comment.course_id.in_(ids)).scalar() if ids else 0
    return ok({
        "courses": len(courses),
        "on_sale": sum(1 for c in courses if c.status == "on"),
        "students": students or 0,
        "avg_progress": round(avg_progress or 0),
        "comments": comments or 0,
    })


@router.get("/courses")
def my_courses(user: User = Depends(require_teacher), db: Session = Depends(get_db)):
    q = db.query(Course)
    if user.role != "admin":
        q = q.filter(Course.teacher_id == user.id)
    out = []
    for c in q.order_by(Course.created_at.desc()).all():
        item = course_out(c)
        item["lesson_count"] = _lesson_count(db, c.id)
        item["enrolled"] = db.query(func.count(Enrollment.id)).filter(Enrollment.course_id == c.id).scalar() or 0
        item["quiz_count"] = db.query(func.count(Quiz.id)).filter(Quiz.course_id == c.id).scalar() or 0
        out.append(item)
    return ok(out)


@router.post("/courses")
def create_course(body: AdminCourseIn, user: User = Depends(require_teacher), db: Session = Depends(get_db)):
    if user.role != "admin":
        body.teacher_id = user.id
        body.status = "off"  # 教师新建课程默认下架，完善后再上架
    return admin_api.create_course(body, db)


@router.put("/courses/{course_id}")
def update_course(course_id: int, body: AdminCourseIn, user: User = Depends(require_teacher), db: Session = Depends(get_db)):
    course = _own_course(db, user, course_id)
    if user.role != "admin":
        body.teacher_id = course.teacher_id  # 教师不能把课程转给别人
    return admin_api.update_course(course_id, body, db)


@router.get("/courses/{course_id}/outline")
def get_outline(course_id: int, user: User = Depends(require_teacher), db: Session = Depends(get_db)):
    _own_course(db, user, course_id)
    return admin_api.get_course_outline(course_id, db)


@router.put("/courses/{course_id}/outline")
def put_outline(
    course_id: int,
    body: Union[list[OutlineChapterIn], OutlineIn] = Body(...),
    user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    _own_course(db, user, course_id)
    return admin_api.put_course_outline(course_id, body, db)


@router.get("/courses/{course_id}/students")
def students(course_id: int, user: User = Depends(require_teacher), db: Session = Depends(get_db)):
    _own_course(db, user, course_id)
    rows = (
        db.query(Enrollment, User)
        .join(User, User.id == Enrollment.user_id)
        .filter(Enrollment.course_id == course_id)
        .order_by(Enrollment.created_at.desc())
        .all()
    )
    quiz_ids = [q.id for q in db.query(Quiz.id).filter(Quiz.course_id == course_id).all()]
    out = []
    for e, u in rows:
        best = None
        if quiz_ids:
            best = db.query(func.max(QuizAttempt.score)).filter(QuizAttempt.user_id == u.id, QuizAttempt.quiz_id.in_(quiz_ids)).scalar()
        out.append({
            "user": {"id": u.id, "username": u.username, "nickname": u.nickname, "avatar": u.avatar, "major": u.major},
            "progress": e.progress,
            "study_minutes": round((e.study_seconds or 0) / 60),
            "best_quiz_score": best,
            "enrolled_at": iso(e.created_at),
        })
    return ok(out)


# ---------- 测验 / 考试 ----------

def _save_questions(db: Session, quiz: Quiz, body: QuizIn) -> None:
    for q in list(quiz.questions):
        db.delete(q)
    db.flush()
    for i, q in enumerate(body.questions):
        if q.kind != "judge" and len([o for o in q.options if o.strip()]) < 2:
            raise HTTPException(400, f"第 {i + 1} 题至少需要两个选项")
        answer = normalize_answer(q.kind, q.answer)
        letters = "".join(chr(65 + k) for k in range(len(q.options)))
        if q.kind == "judge" and answer not in ("T", "F"):
            raise HTTPException(400, f"第 {i + 1} 题判断题答案只能是 T 或 F")
        if q.kind != "judge" and (not answer or any(ch not in letters for ch in answer)):
            raise HTTPException(400, f"第 {i + 1} 题答案必须是选项字母")
        if q.kind == "single" and len(answer) != 1:
            raise HTTPException(400, f"第 {i + 1} 题是单选题，只能有一个答案")
        db.add(QuizQuestion(
            quiz_id=quiz.id, kind=q.kind, stem=q.stem.strip(),
            options=json.dumps([o.strip() for o in q.options] if q.kind != "judge" else ["正确", "错误"], ensure_ascii=False),
            answer=answer, explanation=(q.explanation or "").strip(), score=q.score, order_index=i,
        ))


def _check_lesson(db: Session, course_id: int, lesson_id: int | None) -> None:
    if lesson_id is None:
        return
    lesson = db.get(Lesson, lesson_id)
    chapter = db.get(Chapter, lesson.chapter_id) if lesson else None
    if chapter is None or chapter.course_id != course_id:
        raise HTTPException(400, "课时不属于该课程")


@router.get("/courses/{course_id}/quizzes")
def list_quizzes(course_id: int, user: User = Depends(require_teacher), db: Session = Depends(get_db)):
    _own_course(db, user, course_id)
    quizzes = db.query(Quiz).filter(Quiz.course_id == course_id).order_by(Quiz.kind.desc(), Quiz.id).all()
    return ok([quiz_out(q, with_answers=True) for q in quizzes])


@router.post("/courses/{course_id}/quizzes")
def create_quiz(course_id: int, body: QuizIn, user: User = Depends(require_teacher), db: Session = Depends(get_db)):
    _own_course(db, user, course_id)
    _check_lesson(db, course_id, body.lesson_id)
    if body.kind == "exam":
        body.lesson_id = None
        if db.query(Quiz).filter(Quiz.course_id == course_id, Quiz.kind == "exam").first():
            raise HTTPException(400, "每门课程只能有一份结业考试")
    quiz = Quiz(course_id=course_id, lesson_id=body.lesson_id, title=body.title.strip(), kind=body.kind,
                pass_score=body.pass_score, time_limit_minutes=body.time_limit_minutes, max_attempts=body.max_attempts)
    db.add(quiz)
    db.flush()
    _save_questions(db, quiz, body)
    db.commit()
    db.refresh(quiz)
    return ok(quiz_out(quiz, with_answers=True))


@router.put("/quizzes/{quiz_id}")
def update_quiz(quiz_id: int, body: QuizIn, user: User = Depends(require_teacher), db: Session = Depends(get_db)):
    quiz = db.get(Quiz, quiz_id)
    if quiz is None:
        raise HTTPException(404, "测验不存在")
    _own_course(db, user, quiz.course_id)
    _check_lesson(db, quiz.course_id, body.lesson_id)
    quiz.title, quiz.pass_score = body.title.strip(), body.pass_score
    quiz.time_limit_minutes, quiz.max_attempts = body.time_limit_minutes, body.max_attempts
    quiz.lesson_id = None if quiz.kind == "exam" else body.lesson_id
    _save_questions(db, quiz, body)
    db.commit()
    db.refresh(quiz)
    return ok(quiz_out(quiz, with_answers=True))


@router.delete("/quizzes/{quiz_id}")
def delete_quiz(quiz_id: int, user: User = Depends(require_teacher), db: Session = Depends(get_db)):
    quiz = db.get(Quiz, quiz_id)
    if quiz is None:
        raise HTTPException(404, "测验不存在")
    _own_course(db, user, quiz.course_id)
    db.query(QuizAttempt).filter(QuizAttempt.quiz_id == quiz.id).delete()
    db.delete(quiz)
    db.commit()
    return ok({"ok": True})
