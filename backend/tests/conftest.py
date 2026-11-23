"""测试公共夹具：独立测试库、登录令牌。"""
import os
import sys
import tempfile

# 保证能 import app；使用独立测试库，避免污染开发库
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BACKEND_DIR)
_TEST_DB = os.path.join(tempfile.gettempdir(), "edu_ai_test.db").replace("\\", "/")
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"
os.environ["AI_API_KEY"] = ""  # 强制走内置模拟引擎

import pytest
from fastapi.testclient import TestClient

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    if os.path.exists(_TEST_DB):
        os.remove(_TEST_DB)
    with TestClient(app) as c:
        yield c
    try:
        os.remove(_TEST_DB)
    except OSError:
        pass


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def student_token(client):
    r = client.post("/api/auth/login", json={"username": "student", "password": "student123"})
    assert r.status_code == 200, r.text
    return r.json()["data"]["token"]


@pytest.fixture(scope="session")
def admin_token(client):
    r = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200, r.text
    return r.json()["data"]["token"]


