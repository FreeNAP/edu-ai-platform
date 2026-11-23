"""运维命令：python -m app.cli <命令>

  create-admin  --username --email [--password]   创建或提升管理员（密码不填则交互输入）
  seed-demo                                        空库写入演示数据
  check                                            检查配置与数据库连接
"""
from __future__ import annotations

import argparse
import getpass
import sys

from sqlalchemy import text

from .config import settings
from .database import SessionLocal, engine
from .models import User
from .security import hash_password, password_problem


def create_admin(username: str, email: str, password: str | None) -> int:
    password = password or getpass.getpass("管理员密码：")
    problem = password_problem(password, username)
    if problem:
        print(f"密码不合格：{problem}", file=sys.stderr)
        return 1
    with SessionLocal() as db:
        user = db.query(User).filter((User.username == username) | (User.email == email.lower())).first()
        if user:
            user.role, user.status = "admin", "active"
            user.password_hash = hash_password(password)
            user.token_version = (user.token_version or 0) + 1
            print(f"已将 {user.username} 设为管理员并重置密码")
        else:
            db.add(User(username=username, email=email.lower(), nickname=username, role="admin", status="active", password_hash=hash_password(password)))
            print(f"已创建管理员 {username}")
        db.commit()
    return 0


def seed_demo() -> int:
    from .seed import seed_if_empty

    with SessionLocal() as db:
        seed_if_empty(db)
    print("演示数据已就绪（非空库不会重复写入）")
    return 0


def check() -> int:
    print(f"APP_ENV={settings.app_env} DEMO={settings.demo} DB={engine.url.render_as_string(hide_password=True)}")
    problems = settings.check_production() if settings.is_production else []
    for p in problems:
        print(f"[配置] {p}")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[数据库] 连接正常")
    except Exception as e:  # noqa: BLE001
        print(f"[数据库] 连接失败：{e}", file=sys.stderr)
        return 1
    print(f"[邮件] {'已配置' if settings.smtp_enabled else '未配置（找回密码验证码只写日志）'}")
    print(f"[AI] {'已配置 ' + settings.ai_model if settings.ai_api_key else '未配置（使用内置引擎）'}")
    return 1 if any("SECRET_KEY" in p for p in problems) else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description="智慧教育平台运维命令")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("create-admin", help="创建或提升管理员")
    p.add_argument("--username", required=True)
    p.add_argument("--email", required=True)
    p.add_argument("--password")
    sub.add_parser("seed-demo", help="写入演示数据")
    sub.add_parser("check", help="检查配置与数据库")
    args = parser.parse_args(argv)
    if args.cmd == "create-admin":
        return create_admin(args.username, args.email, args.password)
    if args.cmd == "seed-demo":
        return seed_demo()
    return check()


if __name__ == "__main__":
    raise SystemExit(main())
