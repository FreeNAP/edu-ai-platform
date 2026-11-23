"""FastAPI 应用入口：路由注册、CORS、建表+seed、生产模式 SPA 托管。"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from sqlalchemy import text

from . import models  # noqa: F401  确保模型已注册到 metadata
from .config import settings
from .database import Base, SessionLocal, engine, ensure_sqlite_columns
from .logging_setup import RequestContextMiddleware, setup_logging
from .services.audit import AuditMiddleware
from .routers import (
    admin,
    ai,
    auth,
    community,
    courses,
    jobs,
    notifications,
    orders,
    quizzes,
    teacher,
    uploads,
    users,
)
from .seed import seed_if_empty
from .utils import clean_cover, ok


setup_logging(settings.log_level, settings.log_json)
logger = logging.getLogger("edu.app")
APP_VERSION = "2.0.0"


def init_db() -> None:
    """开发环境：建表 + 旧库补列；演示模式：空库写入演示数据。生产环境由 alembic 管理表结构。"""
    if settings.auto_create:
        Base.metadata.create_all(bind=engine)
        added = ensure_sqlite_columns()
        if added:
            logger.info("数据库已补充新增列: %s", ", ".join(added))
    db = SessionLocal()
    try:
        if settings.demo:
            seed_if_empty(db)
        # 旧库的 emoji 封面统一清空（前端不再使用 emoji 封面）
        fixed = 0
        for c in db.query(models.Course).filter(models.Course.cover != "").all():
            cleaned = clean_cover(c.cover)
            if cleaned != c.cover:
                c.cover = cleaned
                fixed += 1
        if fixed:
            db.commit()
            logger.info("已清空 %d 门课程的非链接封面", fixed)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.is_production:
        problems = settings.check_production()
        if any("SECRET_KEY" in p for p in problems):
            raise RuntimeError("生产环境配置不合格：" + "；".join(problems))
        for p in problems:
            logger.warning("生产环境提示：%s", p)
    elif settings.secret_key == "edu-ai-platform-dev-secret-key":
        logger.warning("SECRET_KEY 仍为默认开发值，部署前请在 .env 中设置随机密钥")
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    init_db()
    logger.info("启动完成 env=%s demo=%s db=%s", settings.app_env, settings.demo, engine.url.get_backend_name())
    yield


app = FastAPI(
    title="智慧教育平台 API",
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None,
    openapi_url=None if settings.is_production else "/openapi.json",
)

app.add_middleware(AuditMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)
app.add_middleware(RequestContextMiddleware)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc: StarletteHTTPException):
    """统一错误格式 {code: 非0, detail: str}。"""
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "detail": detail},
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    errors = exc.errors()
    msg = "请求参数错误"
    if errors:
        first = errors[0]
        loc = ".".join(str(x) for x in first.get("loc", []) if x not in ("body",))
        msg = f"{loc}: {first.get('msg', '')}" if loc else first.get("msg", msg)
    return JSONResponse(
        status_code=422, content={"code": 422, "detail": msg}
    )


@app.exception_handler(IntegrityError)
async def integrity_exception_handler(request, exc: IntegrityError):
    """唯一约束冲突（如并发重复提交）统一返回 409，不暴露 SQL。"""
    logger.warning("数据冲突 %s %s: %s", request.method, request.url.path, exc.orig)
    return JSONResponse(status_code=409, content={"code": 409, "detail": "数据冲突，请勿重复提交"})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc: Exception):
    """兜底：记录堆栈到日志，响应里只给统一错误格式。"""
    logger.exception("未处理异常 %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"code": 500, "detail": "服务器内部错误"})


@app.get("/api/health")
def health():
    """存活 + 数据库连通性检查（供 Docker / 负载均衡探活）。"""
    db_ok = True
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
        logger.exception("健康检查：数据库不可用")
    body = {"status": "ok" if db_ok else "degraded", "version": APP_VERSION, "database": "ok" if db_ok else "error"}
    return JSONResponse(status_code=200 if db_ok else 503, content={"code": 0 if db_ok else 503, "data": body})


for _r in (auth, users, courses, jobs, orders, ai, notifications, community, admin, uploads, quizzes, teacher):
    app.include_router(_r.router)
app.include_router(courses.lessons_router)
app.include_router(community.answers_router)

# ---- 上传文件（生产环境建议由 Nginx 直接提供 /uploads/）----
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# ---- 生产模式：托管前端构建产物（SPA history 回退）----
_FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if (_FRONTEND_DIST / "index.html").exists():

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        if full_path.startswith(("api", "uploads")):
            raise HTTPException(404, "接口不存在")
        if full_path:
            fp = (_FRONTEND_DIST / full_path).resolve()
            if fp.is_file() and fp.is_relative_to(_FRONTEND_DIST.resolve()):
                return FileResponse(fp)
        return FileResponse(_FRONTEND_DIST / "index.html")


# 直接 python app/main.py 也可启动
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
