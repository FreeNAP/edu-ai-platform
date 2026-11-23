"""SQLAlchemy 引擎与会话。"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from . import config

_connect_args = (
    {"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {}
)
engine = create_engine(config.DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI 依赖：每请求一个会话。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_sqlite_columns() -> list[str]:
    """轻量迁移：SQLite 旧库缺少新增列时自动 ALTER TABLE ADD COLUMN。

    create_all 只建新表不加列，旧库直接访问新字段会 500。返回补上的列名。
    """
    if not str(engine.url).startswith("sqlite"):
        return []
    from sqlalchemy import inspect, text

    added = []
    insp = inspect(engine)
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if not insp.has_table(table.name):
                continue
            existing = {c["name"] for c in insp.get_columns(table.name)}
            for col in table.columns:
                if col.name in existing:
                    continue
                col_type = col.type.compile(dialect=engine.dialect)
                conn.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN "{col.name}" {col_type}'))
                added.append(f"{table.name}.{col.name}")
    return added
