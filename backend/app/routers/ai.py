"""AI 学习助手（契约第5节）：多轮答疑/学习路径/作业批改/学习报告/AI面试评估。"""
import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import (
    ChatMessage,
    ChatSession,
    Course,
    Enrollment,
    Interview,
    Job,
    LearningPlan,
    LessonProgress,
    User,
)
from ..schemas import ChatIn, GradeIn, InterviewAnswerIn, LearningPathIn
from ..serializers import interview_out, learning_plan_out, normalize_per_question
from ..services import llm
from ..services.plans import estimate_due_date
from ..utils import iso, ok

router = APIRouter(prefix="/api/ai", tags=["AI助手"])


@router.post("/chat")
def ai_chat(
    body: ChatIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    message = (body.message or "").strip()
    if not message:
        raise HTTPException(400, "消息不能为空")
    if body.course_id:
        c = db.get(Course, body.course_id)
        if c is None or c.status != "on":
            raise HTTPException(404, "课程不存在或已下架")
    if body.session_id:
        session = db.get(ChatSession, body.session_id)
        if session is None or session.user_id != user.id:
            raise HTTPException(404, "会话不存在")
    else:
        session = ChatSession(
            user_id=user.id,
            course_id=body.course_id,
            title=message[:20],
        )
        db.add(session)
        db.flush()
    if body.course_id:
        session.course_id = body.course_id

    # 历史消息（不含本条）
    history = [
        {"role": m.role, "content": m.content}
        for m in db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at)
        .all()
    ]
    db.add(ChatMessage(session_id=session.id, role="user", content=message))

    course = db.get(Course, session.course_id) if session.course_id else None
    reply = llm.chat_reply(message, course=course, history=history)
    db.add(ChatMessage(session_id=session.id, role="assistant", content=reply))
    session.updated_at = datetime.now()
    db.commit()
    return ok({"session_id": session.id, "reply": reply})


@router.get("/chat/sessions")
def chat_sessions(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user.id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )
    items = []
    for s in sessions:
        count = (
            db.query(ChatMessage).filter(ChatMessage.session_id == s.id).count()
        )
        items.append(
            {
                "id": s.id,
                "title": s.title,
                "updated_at": iso(s.updated_at),
                "message_count": count,
            }
        )
    return ok(items)


@router.get("/chat/sessions/{session_id}")
def chat_session_detail(
    session_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.get(ChatSession, session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(404, "会话不存在")
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    return ok(
        {
            "id": session.id,
            "title": session.title,
            "messages": [
                {"role": m.role, "content": m.content, "created_at": iso(m.created_at)}
                for m in messages
            ],
        }
    )


@router.delete("/chat/sessions/{session_id}")
def delete_chat_session(
    session_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.get(ChatSession, session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(404, "会话不存在")
    db.query(ChatMessage).filter(ChatMessage.session_id == session.id).delete()
    db.delete(session)
    db.commit()
    return ok({"ok": True})


@router.post("/learning-path")
def learning_path(
    body: LearningPathIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goal = (body.goal or "").strip()
    if not goal:
        raise HTTPException(400, "请填写目标岗位或方向")
    courses = db.query(Course).filter(Course.status == "on").all()
    plan = llm.gen_learning_path(goal, body.hours_per_week, courses)
    now = datetime.now()
    record = LearningPlan(
        user_id=user.id,
        goal=goal,
        hours_per_week=body.hours_per_week,
        plan_json=json.dumps(plan, ensure_ascii=False),
        created_at=now,
        due_date=estimate_due_date(plan, now),
        reminded=False,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    # 契约字段为 plan；id/due_date 为附加字段，便于前端跳转历史记录
    return ok({"plan": plan, "id": record.id, "due_date": iso(record.due_date)})


@router.get("/learning-plans")
def list_learning_plans(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    plans = (
        db.query(LearningPlan)
        .filter(LearningPlan.user_id == user.id)
        .order_by(LearningPlan.created_at.desc(), LearningPlan.id.desc())
        .all()
    )
    return ok([learning_plan_out(p) for p in plans])


@router.delete("/learning-plans/{plan_id}")
def delete_learning_plan(
    plan_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = db.get(LearningPlan, plan_id)
    if plan is None or plan.user_id != user.id:
        raise HTTPException(404, "学习路径不存在")
    db.delete(plan)
    db.commit()
    return ok({"ok": True})


@router.post("/grade")
def grade(body: GradeIn, user: User = Depends(get_current_user)):
    if not (body.question or "").strip():
        raise HTTPException(400, "请提供题目描述")
    result = llm.grade_code(body.question, body.code or "", body.language)
    return ok(result)


@router.get("/report")
def report(
    period: str = "week",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if period not in ("week", "month"):
        period = "week"
    days = 7 if period == "week" else 30
    since = datetime.now() - timedelta(days=days)
    progresses = (
        db.query(LessonProgress)
        .filter(
            LessonProgress.user_id == user.id,
            LessonProgress.completed_at >= since,
        )
        .all()
    )
    total_seconds = sum(p.study_seconds for p in progresses)
    completed_lessons = len(progresses)
    courses_progress = []
    enrollments = (
        db.query(Enrollment).filter(Enrollment.user_id == user.id).all()
    )
    for e in enrollments:
        course = db.get(Course, e.course_id)
        courses_progress.append(
            {
                "course_id": e.course_id,
                "title": course.title if course else "(已删除)",
                "progress": e.progress,
            }
        )
    stats = {
        "total_minutes": round(total_seconds / 60),
        "completed_lessons": completed_lessons,
        "courses_progress": courses_progress,
    }
    fields = llm.gen_report(period, stats)
    return ok(
        {
            "period": period,
            "total_minutes": stats["total_minutes"],
            "courses_progress": courses_progress,
            "completed_lessons": completed_lessons,
            "strengths": fields["strengths"],
            "weaknesses": fields["weaknesses"],
            "suggestions": fields["suggestions"],
            "summary": fields["summary"],
        }
    )


def _my_interview(db: Session, user: User, interview_id: int) -> Interview:
    interview = db.get(Interview, interview_id)
    if interview is None or interview.user_id != user.id:
        raise HTTPException(404, "面试不存在")
    return interview


@router.get("/interview/{interview_id}")
def interview_detail(
    interview_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    interview = _my_interview(db, user, interview_id)
    return ok(interview_out(interview, db.get(Job, interview.job_id)))


@router.post("/interview/{interview_id}/answer")
def answer_interview(
    interview_id: int,
    body: InterviewAnswerIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    interview = _my_interview(db, user, interview_id)
    if interview.status == "done":
        # 已评估过的面试幂等返回原结果，避免重复刷分
        data = interview_out(interview, db.get(Job, interview.job_id))
        return ok({k: data[k] for k in ("score", "evaluation", "per_question")})
    answers = [a.model_dump() for a in (body.answers or [])]
    if not answers or not any(a["answer"].strip() for a in answers):
        raise HTTPException(400, "请提交作答内容")
    job = db.get(Job, interview.job_id)
    if job is None:
        raise HTTPException(404, "职位已删除，无法评估")
    raw = llm.evaluate_interview(job, answers)
    try:
        score = max(0.0, min(100.0, float(raw.get("score", 0) or 0)))
    except (TypeError, ValueError):
        score = 0.0
    per_question = normalize_per_question(raw.get("per_question"), answers)
    result = {
        "score": score,
        "evaluation": str(raw.get("evaluation") or ""),
        "per_question": per_question,
    }
    interview.answers = json.dumps(answers, ensure_ascii=False)
    interview.per_question = json.dumps(per_question, ensure_ascii=False)
    interview.result = json.dumps(result, ensure_ascii=False)
    interview.score = score
    interview.status = "done"
    db.commit()
    return ok(result)
