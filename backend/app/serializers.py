"""ORM 对象 -> 契约 JSON 结构。"""
import json

from .models import (
    Application,
    Comment,
    Course,
    Interview,
    Job,
    LearningPlan,
    Lecturer,
    Order,
    Question,
    User,
)
from .utils import clean_cover, iso


def _loads(text, default):
    try:
        value = json.loads(text) if text else default
    except (TypeError, ValueError):
        return default
    return value if value is not None else default


def user_out(u: User) -> dict:
    return {
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "nickname": u.nickname,
        "avatar": u.avatar,
        "major": u.major,
        "role": u.role,
        "status": u.status,
        "created_at": iso(u.created_at),
    }


def lecturer_brief(l: Lecturer | None) -> dict | None:
    if l is None:
        return None
    return {"id": l.id, "name": l.name, "title": l.title}


def lecturer_out(l: Lecturer) -> dict:
    return {
        "id": l.id,
        "name": l.name,
        "title": l.title,
        "bio": l.bio,
        "avatar": l.avatar,
    }


def course_out(c: Course) -> dict:
    """列表项课程对象。"""
    return {
        "id": c.id,
        "title": c.title,
        "cover": clean_cover(c.cover),
        "category": c.category,
        "tech_domain": c.tech_domain,
        "difficulty": c.difficulty,
        "is_free": c.is_free,
        "price": c.price,
        "students_count": c.students_count,
        "rating": c.rating,
        "lecturer": lecturer_brief(c.lecturer),
        "brief": c.brief,
        "status": c.status,
        "created_at": iso(c.created_at),
    }


def job_out(j: Job) -> dict:
    return {
        "id": j.id,
        "title": j.title,
        "company": j.company,
        "city": j.city,
        "category": j.category,
        "salary": j.salary,
        "tags": [t for t in (j.tags or "").split(",") if t],
        "description": j.description,
        "requirements": j.requirements,
        "headcount": j.headcount,
        "status": j.status,
        "created_at": iso(j.created_at),
    }


def comment_out(c: Comment) -> dict:
    u = c.user
    return {
        "id": c.id,
        "user": {"nickname": u.nickname or u.username, "avatar": u.avatar} if u else None,
        "rating": c.rating,
        "content": c.content,
        "created_at": iso(c.created_at),
    }


def order_out(o: Order) -> dict:
    c = o.course
    return {
        "id": o.id,
        "order_no": o.order_no,
        "course": {"id": c.id, "title": c.title}
        if c
        else {"id": o.course_id, "title": "(课程已删除)"},
        "amount": o.amount,
        "status": o.status,
        "created_at": iso(o.created_at),
        "paid_at": iso(o.paid_at),
    }


def application_out(a: Application, job: Job | None) -> dict:
    return {
        "id": a.id,
        "job": job_out(job) if job else {"id": a.job_id, "title": "(职位已删除)"},
        "message": a.message,
        "status": a.status,
        "created_at": iso(a.created_at),
    }


def user_brief(u: User | None) -> dict | None:
    if u is None:
        return None
    return {"id": u.id, "nickname": u.nickname or u.username, "avatar": u.avatar}


def question_out(q: Question) -> dict:
    return {
        "id": q.id,
        "title": q.title,
        "content": q.content,
        "user": user_brief(q.user),
        "answers_count": q.answers_count,
        "views": q.views,
        "created_at": iso(q.created_at),
    }


def interview_out(iv: Interview, job: Job | None) -> dict:
    """契约第 9 节面试结构；未作答时 answers/score/evaluation/per_question 为 null。"""
    done = iv.status == "done"
    result = _loads(iv.result, {}) if done else {}
    return {
        "id": iv.id,
        "job": {"id": job.id, "title": job.title, "company": job.company}
        if job
        else {"id": iv.job_id, "title": "(职位已删除)", "company": ""},
        "questions": _loads(iv.questions, []),
        "answers": _loads(iv.answers, []) if done else None,
        "score": result.get("score", iv.score) if done else None,
        "evaluation": result.get("evaluation", "") if done else None,
        "per_question": (_loads(iv.per_question, None) or result.get("per_question", []))
        if done
        else None,
        "status": "done" if done else "pending",
        "created_at": iso(iv.created_at),
    }


def normalize_per_question(items, answers: list[dict]) -> list[dict]:
    """per_question 统一为 [{question, answer, score(0-100 int), comment}]（LLM 输出可能不规范）。"""
    out = []
    items = items if isinstance(items, list) else []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        fallback = answers[i] if i < len(answers) else {}
        try:
            score = int(round(float(item.get("score", 0) or 0)))
        except (TypeError, ValueError):
            score = 0
        out.append({
            "question": str(item.get("question") or fallback.get("question", "")),
            "answer": str(item.get("answer") or fallback.get("answer", "")),
            "score": max(0, min(100, score)),
            "comment": str(item.get("comment") or ""),
        })
    return out


def learning_plan_out(p: LearningPlan) -> dict:
    return {
        "id": p.id,
        "goal": p.goal,
        "hours_per_week": p.hours_per_week,
        "plan": _loads(p.plan_json, {}),
        "created_at": iso(p.created_at),
        "due_date": iso(p.due_date),
    }
