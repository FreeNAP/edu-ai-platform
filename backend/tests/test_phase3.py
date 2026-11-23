"""三期：安全加固、上传、教师工作台、测验/考试/证书、AI 配额与流式输出、简历投递、审计。"""
import uuid

from conftest import _auth

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
PDF = b"%PDF-1.4\n" + b"0" * 64


def _register(client, password="abc12345"):
    name = "s" + uuid.uuid4().hex[:8]
    r = client.post("/api/auth/register", json={"username": name, "email": f"{name}@test.com", "password": password})
    assert r.status_code == 200, r.text
    return name, r.json()["data"]


def _login(client, username, password):
    return client.post("/api/auth/login", json={"username": username, "password": password})


# ---------- 账号安全 ----------

def test_password_policy_on_register(client):
    for bad in ("short1", "onlyletters", "12345678"):
        name = "p" + uuid.uuid4().hex[:8]
        r = client.post("/api/auth/register", json={"username": name, "email": f"{name}@test.com", "password": bad})
        assert r.status_code == 400


def test_login_lockout(client):
    name, _ = _register(client)
    for _ in range(5):
        assert _login(client, name, "wrong-pass1").status_code == 400
    r = _login(client, name, "abc12345")
    assert r.status_code == 423 and "锁定" in r.json()["detail"]


def test_refresh_and_logout_all(client):
    name, data = _register(client)
    refreshed = client.post("/api/auth/refresh", json={"refresh_token": data["refresh_token"]})
    assert refreshed.status_code == 200 and refreshed.json()["data"]["token"]
    # 访问令牌不能当刷新令牌用
    assert client.post("/api/auth/refresh", json={"refresh_token": data["token"]}).status_code == 401
    token = refreshed.json()["data"]["token"]
    assert client.post("/api/auth/logout-all", headers=_auth(token)).status_code == 200
    assert client.get("/api/auth/me", headers=_auth(token)).status_code == 401
    assert client.post("/api/auth/refresh", json={"refresh_token": data["refresh_token"]}).status_code == 401


def test_forgot_password_does_not_leak_accounts(client):
    r = client.post("/api/auth/forgot-password", json={"email": "nobody-here@test.com"})
    assert r.status_code == 200 and r.json()["data"]["sent"] is True and "dev_code" not in r.json()["data"]


def test_reset_code_attempt_limit(client):
    name, _ = _register(client)
    email = f"{name}@test.com"
    code = client.post("/api/auth/forgot-password", json={"email": email}).json()["data"]["dev_code"]
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(5):
        client.post("/api/auth/reset-password", json={"email": email, "code": wrong, "new_password": "newpass123"})
    r = client.post("/api/auth/reset-password", json={"email": email, "code": code, "new_password": "newpass123"})
    assert r.status_code == 400  # 错误次数用完后正确验证码也失效


def test_public_config_and_health(client):
    cfg = client.get("/api/auth/config").json()["data"]
    assert cfg["demo_mode"] is True and cfg["password_min_length"] == 8
    h = client.get("/api/health")
    assert h.status_code == 200 and h.json()["data"]["database"] == "ok"
    assert h.headers.get("x-request-id") and h.headers.get("x-content-type-options") == "nosniff"


def test_avatar_must_be_safe(client):
    _, data = _register(client)
    tok = data["token"]
    assert client.put("/api/users/profile", json={"avatar": "javascript:alert(1)"}, headers=_auth(tok)).status_code == 400
    assert client.put("/api/users/profile", json={"avatar": "builtin:3"}, headers=_auth(tok)).status_code == 200
    assert client.put("/api/users/profile", json={"resume_url": "/etc/passwd"}, headers=_auth(tok)).status_code == 400


# ---------- 上传 ----------

def test_upload_rules(client, student_token, admin_token):
    ok_img = client.post("/api/uploads?kind=avatar", files={"file": ("a.png", PNG, "image/png")}, headers=_auth(student_token))
    assert ok_img.status_code == 200 and ok_img.json()["data"]["url"].startswith("/uploads/avatar/")
    assert client.get(ok_img.json()["data"]["url"]).status_code == 200
    fake = client.post("/api/uploads?kind=avatar", files={"file": ("a.png", b"<script>x</script>", "image/png")}, headers=_auth(student_token))
    assert fake.status_code == 400  # 改扩展名伪装的文件被识别
    video = client.post("/api/uploads?kind=video", files={"file": ("v.mp4", b"\x00\x00\x00\x18ftypmp42" + b"0" * 32, "video/mp4")}, headers=_auth(student_token))
    assert video.status_code == 403
    video = client.post("/api/uploads?kind=video", files={"file": ("v.mp4", b"\x00\x00\x00\x18ftypmp42" + b"0" * 32, "video/mp4")}, headers=_auth(admin_token))
    assert video.status_code == 200
    assert client.post("/api/uploads?kind=avatar", files={"file": ("a.png", PNG, "image/png")}).status_code == 401


def test_apply_with_uploaded_resume(client):
    _, data = _register(client)
    tok = data["token"]
    up = client.post("/api/uploads?kind=resume", files={"file": ("cv.pdf", PDF, "application/pdf")}, headers=_auth(tok)).json()["data"]
    assert client.put("/api/users/profile", json={"resume_url": up["url"]}, headers=_auth(tok)).status_code == 200
    job = client.get("/api/jobs", params={"size": 1}, headers=_auth(tok)).json()["data"]["items"][0]
    app_ = client.post(f"/api/jobs/{job['id']}/apply", json={"message": "附简历"}, headers=_auth(tok)).json()["data"]
    assert app_["resume_url"] == up["url"]


# ---------- 教师工作台 ----------

def _teacher_token(client):
    return _login(client, "teacher", "teacher123").json()["data"]["token"]


def test_teacher_sees_only_own_courses(client, student_token):
    tok = _teacher_token(client)
    mine = client.get("/api/teacher/courses", headers=_auth(tok)).json()["data"]
    assert mine and all(c["tech_domain"] == "AI" for c in mine)
    assert client.get("/api/teacher/courses", headers=_auth(student_token)).status_code == 403
    other = client.get("/api/courses", params={"tech_domain": "前端", "size": 1}, headers=_auth(tok)).json()["data"]["items"][0]
    assert client.get(f"/api/teacher/courses/{other['id']}/outline", headers=_auth(tok)).status_code == 403
    assert client.get(f"/api/teacher/courses/{mine[0]['id']}/students", headers=_auth(tok)).status_code == 200
    assert client.get("/api/teacher/overview", headers=_auth(tok)).json()["data"]["courses"] == len(mine)


def test_teacher_creates_course_and_quiz(client):
    tok = _teacher_token(client)
    c = client.post("/api/teacher/courses", json={"title": "教师自建课程", "category": "theory", "tech_domain": "AI", "difficulty": "入门", "is_free": True, "price": 0, "brief": "x"}, headers=_auth(tok))
    assert c.status_code == 200, c.text
    course = c.json()["data"]
    assert course["status"] == "off" and course["teacher_id"]
    quiz = {"title": "小测", "kind": "quiz", "pass_score": 60, "questions": [
        {"kind": "single", "stem": "1+1=?", "options": ["1", "2"], "answer": "B", "score": 50},
        {"kind": "judge", "stem": "地球是圆的", "answer": "T", "score": 50},
    ]}
    r = client.post(f"/api/teacher/courses/{course['id']}/quizzes", json=quiz, headers=_auth(tok))
    assert r.status_code == 200 and r.json()["data"]["question_count"] == 2
    bad = dict(quiz, questions=[{"kind": "single", "stem": "x", "options": ["a", "b"], "answer": "E"}])
    assert client.post(f"/api/teacher/courses/{course['id']}/quizzes", json=bad, headers=_auth(tok)).status_code == 400
    audit = client.get("/api/admin/audit-logs", headers=_auth(_login(client, "admin", "admin123").json()["data"]["token"])).json()["data"]
    assert any(a["action"].startswith("teacher.courses") for a in audit["items"])


# ---------- 测验、考试与证书 ----------

def test_quiz_requires_enrollment_and_exam_issues_certificate(client):
    tok = _teacher_token(client)
    course = next(c for c in client.get("/api/teacher/courses", headers=_auth(tok)).json()["data"] if c["quiz_count"] >= 2)
    _, data = _register(client)
    stu = data["token"]
    quizzes = client.get(f"/api/courses/{course['id']}/quizzes", headers=_auth(stu)).json()["data"]
    exam = next(q for q in quizzes if q["kind"] == "exam")
    assert client.get(f"/api/quizzes/{exam['id']}", headers=_auth(stu)).status_code == 403
    if course["is_free"]:
        client.post(f"/api/courses/{course['id']}/enroll", headers=_auth(stu))
    else:
        order = client.post(f"/api/courses/{course['id']}/enroll", headers=_auth(stu)).json()["data"]["order"]
        client.post(f"/api/orders/{order['id']}/pay", headers=_auth(stu))
    detail = client.get(f"/api/quizzes/{exam['id']}", headers=_auth(stu)).json()["data"]
    assert all("answer" not in q for q in detail["questions"])  # 学员看不到答案
    answers = {q["id"]: q["answer"] for q in client.get(f"/api/teacher/courses/{course['id']}/quizzes", headers=_auth(tok)).json()["data"] if q["kind"] == "exam" for q in q["questions"]}
    fail = client.post(f"/api/quizzes/{exam['id']}/submit", json={"answers": {}}, headers=_auth(stu)).json()["data"]
    assert fail["attempt"]["passed"] is False and "certificate" not in fail
    res = client.post(f"/api/quizzes/{exam['id']}/submit", json={"answers": {str(k): v for k, v in answers.items()}}, headers=_auth(stu)).json()["data"]
    assert res["attempt"]["score"] == 100 and res["certificate"]["cert_no"].startswith("EDU")
    cert_no = res["certificate"]["cert_no"]
    assert client.get(f"/api/certificates/{cert_no}").status_code == 200  # 公开查验
    assert client.get("/api/users/me/certificates", headers=_auth(stu)).json()["data"][0]["cert_no"] == cert_no
    # 结业考试最多 3 次
    assert client.post(f"/api/quizzes/{exam['id']}/submit", json={"answers": {}}, headers=_auth(stu)).status_code == 200
    assert client.post(f"/api/quizzes/{exam['id']}/submit", json={"answers": {}}, headers=_auth(stu)).status_code == 400


# ---------- AI 配额与流式输出 ----------

def test_ai_quota(client):
    from app.config import settings

    _, data = _register(client)
    tok = data["token"]
    old = settings.ai_daily_quota
    settings.ai_daily_quota = 2
    try:
        assert client.post("/api/ai/grade", json={"question": "q", "code": "print(1)"}, headers=_auth(tok)).status_code == 200
        assert client.post("/api/ai/grade", json={"question": "q", "code": "print(1)"}, headers=_auth(tok)).status_code == 200
        r = client.post("/api/ai/grade", json={"question": "q", "code": "print(1)"}, headers=_auth(tok))
        assert r.status_code == 429
        usage = client.get("/api/ai/usage", headers=_auth(tok)).json()["data"]
        assert usage["used"] == 2 and usage["remaining"] == 0
    finally:
        settings.ai_daily_quota = old


def test_ai_chat_stream(client, student_token):
    with client.stream("POST", "/api/ai/chat/stream", json={"message": "什么是过拟合"}, headers=_auth(student_token)) as r:
        assert r.status_code == 200 and r.headers["content-type"].startswith("text/event-stream")
        body = "".join(r.iter_text())
    assert "event: meta" in body and "event: delta" in body and body.rstrip().endswith("data: {}")
    sessions = client.get("/api/ai/chat/sessions", headers=_auth(student_token)).json()["data"]
    detail = client.get(f"/api/ai/chat/sessions/{sessions[0]['id']}", headers=_auth(student_token)).json()["data"]
    assert detail["messages"][-1]["role"] == "assistant" and detail["messages"][-1]["content"]
