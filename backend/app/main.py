"""FastAPI 应用入口：路由注册、CORS、建表+seed、生产模式 SPA 托管。"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import config
from . import models  # noqa: F401  确保模型已注册到 metadata
from .database import Base, SessionLocal, engine, ensure_sqlite_columns
from .routers import (
    admin,
    ai,
    auth,
    community,
    courses,
    jobs,
    notifications,
    orders,
    users,
)
from .seed import seed_if_empty
from .utils import clean_cover, ok


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
)
logger = logging.getLogger("edu.app")


def init_db() -> None:
    """建表 + 旧库补列 + 空库时写入种子数据（幂等）。"""
    Base.metadata.create_all(bind=engine)
    added = ensure_sqlite_columns()
    if added:
        logger.info("数据库已补充新增列: %s", ", ".join(added))
    db = SessionLocal()
    try:
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
    if config.SECRET_KEY == config.DEFAULT_SECRET_KEY:
        logger.warning("SECRET_KEY 仍为默认开发值，生产环境请通过环境变量 SECRET_KEY 设置随机密钥")
    init_db()
    yield


app = FastAPI(title="智慧教育平台 API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    return ok({"status": "ok"})


for _r in (auth, users, courses, jobs, orders, ai, notifications, community, admin):
    app.include_router(_r.router)
app.include_router(courses.lessons_router)
app.include_router(community.answers_router)

# ---- 生产模式：托管前端构建产物（SPA history 回退）----
_FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if (_FRONTEND_DIST / "index.html").exists():

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        if full_path.startswith("api"):
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
