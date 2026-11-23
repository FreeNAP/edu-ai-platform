"""认证：注册/登录/重置/me（契约第1节）。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import LoginIn, RegisterIn, ResetPasswordIn
from ..security import create_token, hash_password, verify_password
from ..serializers import user_out
from ..utils import ok

router = APIRouter(prefix="/api/auth", tags=["认证"])


def create_user_account(
    db: Session,
    username: str | None,
    email: str | None,
    password: str | None,
    nickname: str | None = None,
    role: str = "student",
) -> User:
    """注册与管理员建号共用的校验 + 创建（不 commit）。"""
    username = (username or "").strip()
    email = (email or "").strip()
    if not username or not email or not password:
        raise HTTPException(400, "用户名、邮箱、密码不能为空")
    if len(username) < 3:
        raise HTTPException(400, "用户名至少 3 个字符")
    if any(ch.isspace() for ch in username) or "@" in username:
        raise HTTPException(400, "用户名不能包含空白字符或 @")
    if len(password) < 6:
        raise HTTPException(400, "密码长度至少 6 位")
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise HTTPException(400, "邮箱格式不正确")
    if role not in ("student", "teacher", "admin"):
        raise HTTPException(400, "非法角色")
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(400, "用户名已存在")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(400, "邮箱已被注册")
    user = User(
        username=username,
        email=email,
        nickname=(nickname or "").strip() or username,
        avatar="",
        major="",
        role=role,
        status="active",
        password_hash=hash_password(password),
    )
    db.add(user)
    return user


@router.post("/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    user = create_user_account(db, body.username, body.email, body.password, body.nickname)
    db.commit()
    db.refresh(user)
    return ok({"user": user_out(user), "token": create_token(user.id)})


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    name = (body.username or "").strip()
    user = (
        db.query(User)
        .filter(or_(User.username == name, User.email == name))
        .first()
    )
    if user is None or not verify_password(body.password or "", user.password_hash):
        raise HTTPException(400, "用户名或密码错误")
    if user.status != "active":
        raise HTTPException(403, "账号已被禁用，请联系管理员")
    return ok({"user": user_out(user), "token": create_token(user.id)})


@router.post("/reset-password")
def reset_password(body: ResetPasswordIn, db: Session = Depends(get_db)):
    if not body.new_password or len(body.new_password) < 6:
        raise HTTPException(400, "新密码长度至少 6 位")
    user = (
        db.query(User)
        .filter(
            User.username == (body.username or "").strip(),
            User.email == (body.email or "").strip(),
        )
        .first()
    )
    if user is None:
        raise HTTPException(400, "用户名与邮箱不匹配")
    user.password_hash = hash_password(body.new_password)
    db.commit()
    return ok({"ok": True})


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return ok(user_out(user))
