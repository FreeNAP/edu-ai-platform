"""社区问答（契约第7节 + 第9节删除接口）。"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, get_current_user_optional
from ..models import Answer, Question, User
from ..schemas import AnswerIn, QuestionIn
from ..serializers import question_out, user_brief
from ..services.notify import notify
from ..utils import iso, ok, paginate, require_text

router = APIRouter(prefix="/api/community", tags=["社区"])
answers_router = APIRouter(prefix="/api/community/answers", tags=["社区"])


def _answer_out(a: Answer) -> dict:
    return {
        "id": a.id,
        "user": user_brief(a.user),
        "content": a.content,
        "created_at": iso(a.created_at),
    }


def search_questions(db: Session, keyword: Optional[str]):
    q = db.query(Question)
    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        q = q.filter(or_(Question.title.ilike(kw), Question.content.ilike(kw)))
    return q.order_by(Question.created_at.desc(), Question.id.desc())


def delete_question_cascade(db: Session, q: Question) -> None:
    """删除问题及其全部回答（不 commit）。"""
    db.query(Answer).filter(Answer.question_id == q.id).delete(synchronize_session=False)
    db.delete(q)


def _can_manage(user: User, owner_id: int) -> bool:
    return user.role == "admin" or user.id == owner_id


@router.get("/questions")
def list_questions(
    keyword: Optional[str] = None,
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_db),
):
    return ok(paginate(search_questions(db, keyword), page, size, question_out))


@router.post("/questions")
def create_question(
    body: QuestionIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    title = require_text(body.title, "标题和内容不能为空")
    content = require_text(body.content, "标题和内容不能为空")
    q = Question(user_id=user.id, title=title, content=content)
    db.add(q)
    db.commit()
    db.refresh(q)
    return ok(question_out(q))


@router.get("/questions/{question_id}")
def question_detail(
    question_id: int,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    q = db.get(Question, question_id)
    if q is None:
        raise HTTPException(404, "问题不存在")
    q.views = (q.views or 0) + 1
    answers = (
        db.query(Answer)
        .filter(Answer.question_id == q.id)
        .order_by(Answer.created_at, Answer.id)
        .all()
    )
    db.commit()
    data = question_out(q)
    data["answers"] = [_answer_out(a) for a in answers]
    # 附加字段：当前用户能否删除（作者或管理员），便于前端显示删除按钮
    data["can_delete"] = bool(user and _can_manage(user, q.user_id))
    return ok(data)


@router.delete("/questions/{question_id}")
def delete_question(
    question_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.get(Question, question_id)
    if q is None:
        raise HTTPException(404, "问题不存在")
    if not _can_manage(user, q.user_id):
        raise HTTPException(403, "只能删除自己发布的问题")
    delete_question_cascade(db, q)
    db.commit()
    return ok({"ok": True})


@router.post("/questions/{question_id}/answers")
def create_answer(
    question_id: int,
    body: AnswerIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.get(Question, question_id)
    if q is None:
        raise HTTPException(404, "问题不存在")
    content = require_text(body.content, "回答内容不能为空")
    a = Answer(question_id=q.id, user_id=user.id, content=content)
    db.add(a)
    q.answers_count = (q.answers_count or 0) + 1
    if q.user_id != user.id:
        notify(
            db, q.user_id, "community", "你的问题有了新回答",
            f"{user.nickname or user.username} 回答了你的问题「{q.title[:40]}」。",
        )
    db.commit()
    db.refresh(a)
    return ok(_answer_out(a))


@answers_router.delete("/{answer_id}")
def delete_answer(
    answer_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    a = db.get(Answer, answer_id)
    if a is None:
        raise HTTPException(404, "回答不存在")
    if not _can_manage(user, a.user_id):
        raise HTTPException(403, "只能删除自己发布的回答")
    q = db.get(Question, a.question_id)
    if q is not None:
        q.answers_count = max(0, (q.answers_count or 0) - 1)
    db.delete(a)
    db.commit()
    return ok({"ok": True})
