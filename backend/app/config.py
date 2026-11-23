"""全局配置：从环境变量与 backend/.env 读取（pydantic-settings）。

模块级常量（config.SECRET_KEY 等）保留，业务代码可继续 `from . import config` 使用。
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
DEFAULT_SECRET_KEY = "edu-ai-platform-dev-secret-key"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.getenv("EDU_ENV_FILE", str(BASE_DIR / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- 运行环境 ----
    app_env: str = Field("development", description="development / production / test")
    demo_mode: bool | None = Field(None, description="写入演示数据并在登录页展示演示账号；默认开发环境开启、生产关闭")
    log_level: str = "INFO"
    log_json: bool = False
    public_base_url: str = "http://127.0.0.1:8000"

    # ---- 安全 ----
    secret_key: str = DEFAULT_SECRET_KEY
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 14
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    login_max_attempts: int = 5
    login_lock_minutes: int = 15
    password_min_length: int = 8
    reset_code_expire_minutes: int = 10

    # ---- 数据库 ----
    database_url: str = ""
    db_pool_size: int = 10
    db_auto_create: bool | None = Field(None, description="启动时 create_all；默认非生产开启，生产应使用 alembic upgrade")

    # ---- 文件上传 ----
    upload_dir: str = str(BASE_DIR / "uploads")
    max_image_mb: int = 5
    max_document_mb: int = 10
    max_video_mb: int = 500

    # ---- 邮件（找回密码验证码） ----
    smtp_host: str = ""
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_ssl: bool = True

    # ---- AI ----
    ai_api_key: str = ""
    ai_base_url: str = "https://api.deepseek.com"
    ai_model: str = "deepseek-chat"
    ai_timeout_seconds: int = 30
    ai_daily_quota: int = Field(100, description="每个学生每日可调用 AI 次数；0 表示不限")

    @field_validator("app_env")
    @classmethod
    def _env(cls, v: str) -> str:
        v = (v or "development").lower()
        if v not in {"development", "production", "test"}:
            raise ValueError("APP_ENV 只能是 development / production / test")
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def demo(self) -> bool:
        return (not self.is_production) if self.demo_mode is None else self.demo_mode

    @property
    def auto_create(self) -> bool:
        return (not self.is_production) if self.db_auto_create is None else self.db_auto_create

    @property
    def db_url(self) -> str:
        return self.database_url or "sqlite:///" + str(BASE_DIR / "edu_platform.db").replace("\\", "/")

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def smtp_enabled(self) -> bool:
        return bool(self.smtp_host and self.smtp_from)

    def check_production(self) -> list[str]:
        """生产环境必须满足的条件，返回问题列表（为空表示通过）。"""
        problems = []
        if self.secret_key == DEFAULT_SECRET_KEY or len(self.secret_key) < 32:
            problems.append("SECRET_KEY 必须设置为至少 32 位的随机字符串")
        if self.db_url.startswith("sqlite"):
            problems.append("生产环境建议使用 PostgreSQL 或 MySQL（DATABASE_URL）")
        return problems


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

# ---- 兼容旧代码的模块级常量 ----
SECRET_KEY = settings.secret_key
JWT_ALGORITHM = settings.jwt_algorithm
DATABASE_URL = settings.db_url
AI_API_KEY = settings.ai_api_key
AI_BASE_URL = settings.ai_base_url
AI_MODEL = settings.ai_model
