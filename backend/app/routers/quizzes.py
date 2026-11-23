"""课时测验、结业/认证考试与证书。

学员：查看题目（不含答案）→ 提交作答 → 自动判分、显示解析；通过结业考试颁发证书。
证书编号可公开查验。
"""
from __future__ import annotations

import json
import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Certificate, Course, Enrollment, Quiz, QuizAttempt, User
from ..services.notify import notify
from ..utils import iso, ok

router = APIRouter(prefix="/api", tags=["测验与证书"])


class SubmitIn(BaseModel):
    answers: dict[str, str] = Field(default_factory=dict)


def _options(q) -> list[str]:
    try:
        v = json.loads(q.options or "[]")
        return v if isinstance(v, list) else []
    except ValueError:
        return []


def normalize_answer(kind: str, value: str) -> str:
    v = (value or "").strip().upper()
    if kind == "multiple":
        return "".join(sorted(set(ch for ch in v if ch.isalpha())))
    if kind == "judge":
        return {"TRUE": "T", "FALSE": "F", "对": "T", "错": "F"}.get(v, v[:1])
    return v[:1]


def quiz_out(quiz: Quiz, with_answers: bool = False) -> dict:
    data = {
        "id": quiz.id,
        "course_id": quiz.course_id,
        "lesson_id": quiz.lesson_id,
        "title": quiz.title,
        "kind": quiz.kind,
        "pass_score": quiz.pass_score,
        "time_limit_minutes": quiz.time_limit_minutes,
        "max_attempts": quiz.max_attempts,
        "total_score": sum(q.score for q in quiz.questions),
        "question_count": len(quiz.questions),
    }
    data["questions"] = [
        {
            "id": q.id,
            "kind": q.kind,
            "stem": q.stem,
            "options": _options(q),
            "score": q.score,
            **({"answer": q.answer, "explanation": q.explanation} if with_answers else {}),
        }
        for q in quiz.questions
    ]
    return data


def attempt_out(a: QuizAttempt) -> dict:
    return {
        "id": a.id,
        "quiz_id": a.quiz_id,
        "score": a.score,
        "total": a.total,
        "passed": a.passed,
        "started_at": iso(a.started_at),
        "submitted_at": iso(a.submitted_at),
    }


def cert_out(c: Certificate, db: Session) -> dict:
    course = db.get(Course, c.course_id)
    user = db.get(User, c.user_id)
    return {
        "cert_no": c.cert_no,
        "course": {"id": course.id, "title": course.title, "category": course.category} if course else None,
        "holder": (user.nickname or user.username) if user else "",
        "score": c.score,
        "issued_at": iso(c.issued_at),
    }


def _require_enrolled(db: Session, user: User, course_id: int) -> None:
    if user.role in ("admin", "teacher"):
        return
    if not db.query(Enrollment).filter(Enrollment.user_id == user.id, Enrollment.course_id == course_id).first():
        raise HTTPException(403, "报名课程后才能参加测验")


@router.get("/courses/{course_id}/quizzes")
def course_quizzes(course_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if course is None or (course.status != "on" and user.role != "admin"):
        raise HTTPException(404, "课程不存在或已下架")
    quizzes = db.query(Quiz).filter(Quiz.course_id == course_id).order_by(Quiz.kind.desc(), Quiz.id).all()
    out = []
    for q in quizzes:
        attempts = db.query(QuizAttempt).filter(QuizAttempt.quiz_id == q.id, QuizAttempt.user_id == user.id, QuizAttempt.submitted_at.isnot(None)).all()
        best = max((a.score for a in attempts), default=None)
        item = quiz_out(q)
        item.pop("questions")
        item.update({"attempts": len(attempts), "best_score": best, "passed": any(a.passed for a in attempts)})
        out.append(item)
    return ok(out)


@router.get("/quizzes/{quiz_id}")
def get_quiz(quiz_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    quiz = db.get(Quiz, quiz_id)
    if quiz is None:
        raise HTTPException(404, "测验不存在")
    _require_enrolled(db, user, quiz.course_id)
    data = quiz_out(quiz)
    data["attempts"] = [attempt_out(a) for a in db.query(QuizAttempt).filter(
        QuizAttempt.quiz_id == quiz.id, QuizAttempt.user_id == user.id, QuizAttempt.submitted_at.isnot(None)
    ).order_by(QuizAttempt.id.desc()).all()]
    return ok(data)


@router.post("/quizzes/{quiz_id}/submit")
def submit_quiz(quiz_id: int, body: SubmitIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    quiz = db.get(Quiz, quiz_id)
    if quiz is None:
        raise HTTPException(404, "测验不存在")
    _require_enrolled(db, user, quiz.course_id)
    if not quiz.questions:
        raise HTTPException(400, "这份测验还没有题目")
    done = db.query(QuizAttempt).filter(QuizAttempt.quiz_id == quiz.id, QuizAttempt.user_id == user.id, QuizAttempt.submitted_at.isnot(None)).count()
    if quiz.max_attempts and done >= quiz.max_attempts:
        raise HTTPException(400, f"最多可以作答 {quiz.max_attempts} 次，已用完")

    score, total, results = 0, 0, []
    for q in quiz.questions:
        given = normalize_answer(q.kind, body.answers.get(str(q.id), ""))
        correct = normalize_answer(q.kind, q.answer)
        right = bool(given) and given == correct
        total += q.score
        score += q.score if right else 0
        results.append({"question_id": q.id, "given": given, "answer": correct, "correct": right, "explanation": q.explanation})
    percent = round(score * 100 / total) if total else 0
    passed = percent >= quiz.pass_score
    attempt = QuizAttempt(
        quiz_id=quiz.id, user_id=user.id, answers=json.dumps(body.answers, ensure_ascii=False),
        score=percent, total=100, passed=passed, submitted_at=datetime.now(),
    )
    db.add(attempt)

    certificate = None
    if quiz.kind == "exam" and passed:
        cert = db.query(Certificate).filter(Certificate.user_id == user.id, Certificate.course_id == quiz.course_id).first()
        if cert is None:
            cert = Certificate(cert_no=f"EDU{datetime.now():%Y%m}{secrets.token_hex(4).upper()}", user_id=user.id, course_id=quiz.course_id, score=percent)
            db.add(cert)
            course = db.get(Course, quiz.course_id)
            notify(db, user.id, "study", "获得课程证书", f"你通过了《{course.title if course else ''}》的结业考试，证书已发放到个人中心。")
        elif percent > cert.score:
            cert.score = percent
        certificate = cert
    db.commit()
    data = {"attempt": attempt_out(attempt), "results": results, "pass_score": quiz.pass_score}
    if certificate is not None:
        db.refresh(certificate)
        data["certificate"] = cert_out(certificate, db)
    return ok(data)


@router.get("/users/me/certificates")
def my_certificates(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    certs = db.query(Certificate).filter(Certificate.user_id == user.id).order_by(Certificate.issued_at.desc()).all()
    return ok([cert_out(c, db) for c in certs])


@router.get("/certificates/{cert_no}")
def verify_certificate(cert_no: str, db: Session = Depends(get_db)):
    """公开查验证书真伪（无需登录）。"""
    cert = db.query(Certificate).filter(Certificate.cert_no == cert_no.strip().upper()).first()
    if cert is None:
        raise HTTPException(404, "证书不存在")
    return ok(cert_out(cert, db))
