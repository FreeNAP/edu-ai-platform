"""认证：注册、登录（失败锁定）、刷新令牌、退出、邮件验证码找回密码、当前用户。"""
import logging
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import get_current_user
from ..models import PasswordResetCode, User
from ..ratelimit import limiter
from ..schemas import ForgotPasswordIn, LoginIn, RefreshIn, RegisterIn, ResetPasswordIn
from ..security import (
    create_refresh_token,
    create_token,
    decode_token,
    hash_code,
    hash_password,
    needs_rehash,
    password_problem,
    verify_password,
)
from ..serializers import user_out
from ..services.mailer import send_mail
from ..utils import ok

router = APIRouter(prefix="/api/auth", tags=["认证"])
logger = logging.getLogger("edu.auth")

_MAX_CODE_ATTEMPTS = 5


def issue_tokens(user: User) -> dict:
    version = user.token_version or 0
    return {
        "user": user_out(user),
        "token": create_token(user.id, version),
        "refresh_token": create_refresh_token(user.id, version),
        "expires_in": settings.access_token_expire_minutes * 60,
    }


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
    email = (email or "").strip().lower()
    if not username or not email or not password:
        raise HTTPException(400, "用户名、邮箱、密码不能为空")
    if len(username) < 3:
        raise HTTPException(400, "用户名至少 3 个字符")
    if any(ch.isspace() for ch in username) or "@" in username:
        raise HTTPException(400, "用户名不能包含空白字符或 @")
    problem = password_problem(password, username)
    if problem:
        raise HTTPException(400, problem)
    if "@" not in email or email.startswith("@") or email.endswith("@") or "." not in email.split("@")[-1]:
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
        role=role,
        status="active",
        password_hash=hash_password(password),
    )
    db.add(user)
    return user


@router.post("/register", dependencies=[Depends(limiter("register", 10, 3600))])
def register(body: RegisterIn, db: Session = Depends(get_db)):
    user = create_user_account(db, body.username, body.email, body.password, body.nickname)
    db.commit()
    db.refresh(user)
    return ok(issue_tokens(user))


@router.post("/login", dependencies=[Depends(limiter("login", 30, 300))])
def login(body: LoginIn, db: Session = Depends(get_db)):
    name = (body.username or "").strip()
    user = db.query(User).filter(or_(User.username == name, User.email == name.lower())).first()
    now = datetime.now()
    if user is not None and user.locked_until and user.locked_until > now:
        minutes = int((user.locked_until - now).total_seconds() // 60) + 1
        raise HTTPException(423, f"密码错误次数过多，账号已锁定，请 {minutes} 分钟后再试或找回密码")
    if user is None or not verify_password(body.password or "", user.password_hash):
        if user is not None:
            user.failed_logins = (user.failed_logins or 0) + 1
            if user.failed_logins >= settings.login_max_attempts:
                user.locked_until = now + timedelta(minutes=settings.login_lock_minutes)
                user.failed_logins = 0
                logger.warning("账号 %s 因连续登录失败被锁定", user.username)
            db.commit()
        raise HTTPException(400, "用户名或密码错误")
    if user.status != "active":
        raise HTTPException(403, "账号已被禁用，请联系管理员")
    user.failed_logins = 0
    user.locked_until = None
    user.last_login_at = now
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(body.password)
    db.commit()
    return ok(issue_tokens(user))


@router.post("/refresh", dependencies=[Depends(limiter("refresh", 60, 60))])
def refresh(body: RefreshIn, db: Session = Depends(get_db)):
    try:
        user_id, version = decode_token(body.refresh_token, "refresh")
    except Exception:
        raise HTTPException(401, "登录已过期，请重新登录")
    user = db.get(User, user_id)
    if user is None or user.status != "active" or (user.token_version or 0) != version:
        raise HTTPException(401, "登录已过期，请重新登录")
    return ok(issue_tokens(user))


@router.post("/logout-all")
def logout_all(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """让该账号所有设备上的令牌失效。"""
    user.token_version = (user.token_version or 0) + 1
    db.commit()
    return ok({"ok": True})


@router.post("/forgot-password", dependencies=[Depends(limiter("forgot", 5, 600))])
def forgot_password(body: ForgotPasswordIn, db: Session = Depends(get_db)):
    """向注册邮箱发送 6 位验证码。无论邮箱是否存在都返回相同结果，避免枚举账号。"""
    email = (body.email or "").strip().lower()
    user = db.query(User).filter(User.email == email).first()
    data = {"sent": True, "expires_in": settings.reset_code_expire_minutes * 60}
    if user is None or user.status != "active":
        return ok(data)
    db.query(PasswordResetCode).filter(PasswordResetCode.user_id == user.id, PasswordResetCode.used.is_(False)).update({"used": True})
    code = f"{secrets.randbelow(1_000_000):06d}"
    db.add(PasswordResetCode(
        user_id=user.id,
        code_hash=hash_code(code),
        expires_at=datetime.now() + timedelta(minutes=settings.reset_code_expire_minutes),
    ))
    db.commit()
    sent = send_mail(
        user.email,
        "智慧教育平台 · 找回密码验证码",
        f"你好，{user.nickname or user.username}：\n\n你的验证码是 {code}，{settings.reset_code_expire_minutes} 分钟内有效。\n"
        "如果不是你本人操作，请忽略这封邮件，你的密码不会被修改。",
    )
    if not sent and not settings.is_production:
        # 开发 / 演示环境没有邮件服务时，直接把验证码返回给前端，便于调试
        data["dev_code"] = code
    return ok(data)


@router.post("/reset-password", dependencies=[Depends(limiter("reset", 20, 600))])
def reset_password(body: ResetPasswordIn, db: Session = Depends(get_db)):
    email = (body.email or "").strip().lower()
    user = db.query(User).filter(User.email == email).first()
    record = None
    if user is not None:
        record = (
            db.query(PasswordResetCode)
            .filter(PasswordResetCode.user_id == user.id, PasswordResetCode.used.is_(False))
            .order_by(PasswordResetCode.id.desc())
            .first()
        )
    if record is None or record.expires_at < datetime.now() or record.attempts >= _MAX_CODE_ATTEMPTS:
        raise HTTPException(400, "验证码无效或已过期，请重新获取")
    if not secrets.compare_digest(record.code_hash, hash_code(body.code.strip())):
        record.attempts += 1
        db.commit()
        raise HTTPException(400, "验证码不正确")
    problem = password_problem(body.new_password, user.username)
    if problem:
        raise HTTPException(400, problem)
    record.used = True
    user.password_hash = hash_password(body.new_password)
    user.token_version = (user.token_version or 0) + 1
    user.failed_logins = 0
    user.locked_until = None
    db.commit()
    return ok({"ok": True})


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return ok(user_out(user))


@router.get("/config")
def public_config():
    """前端启动时读取的公开配置。"""
    return ok({
        "demo_mode": settings.demo,
        "password_min_length": settings.password_min_length,
        "smtp_enabled": settings.smtp_enabled,
        "ai_daily_quota": settings.ai_daily_quota,
    })
