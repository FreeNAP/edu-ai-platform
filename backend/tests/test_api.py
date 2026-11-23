"""后端冒烟测试：覆盖契约主流程。"""
import uuid

from conftest import _auth  # noqa: E402


# ---------- 认证 ----------

def test_register_login_me(client):
    name = "u" + uuid.uuid4().hex[:8]
    r = client.post(
        "/api/auth/register",
        json={"username": name, "email": f"{name}@test.com", "password": "abc12345"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["code"] == 0
    token = data["data"]["token"]
    assert data["data"]["user"]["username"] == name

    r = client.post("/api/auth/login", json={"username": name, "password": "abc12345"})
    assert r.status_code == 200
    assert r.json()["data"]["token"]

    r = client.get("/api/auth/me", headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["data"]["username"] == name

    # 重复注册应报错
    r = client.post(
        "/api/auth/register",
        json={"username": name, "email": f"{name}@test.com", "password": "abc12345"},
    )
    assert r.status_code == 400


def test_reset_and_change_password(client):
    name = "u" + uuid.uuid4().hex[:8]
    email = f"{name}@test.com"
    client.post("/api/auth/register", json={"username": name, "email": email, "password": "abc12345"})
    r = client.post("/api/auth/forgot-password", json={"email": email})
    assert r.status_code == 200
    code = r.json()["data"]["dev_code"]  # 测试环境未配置 SMTP，验证码随响应返回
    bad = client.post("/api/auth/reset-password", json={"email": email, "code": "000000" if code != "000000" else "111111", "new_password": "newpass123"})
    assert bad.status_code == 400
    r = client.post("/api/auth/reset-password", json={"email": email, "code": code, "new_password": "newpass123"})
    assert r.status_code == 200 and r.json()["data"]["ok"] is True
    # 同一验证码不能再用
    assert client.post("/api/auth/reset-password", json={"email": email, "code": code, "new_password": "other1234"}).status_code == 400
    r = client.post("/api/auth/login", json={"username": name, "password": "newpass123"})
    assert r.status_code == 200
    token = r.json()["data"]["token"]
    r = client.put("/api/users/password", json={"old_password": "newpass123", "new_password": "abc12345x"}, headers=_auth(token))
    assert r.status_code == 200
    new_token = r.json()["data"]["token"]
    assert client.get("/api/auth/me", headers=_auth(token)).status_code == 401  # 改密后旧令牌失效
    r = client.put("/api/users/profile", json={"nickname": "测试昵称", "major": "人工智能"}, headers=_auth(new_token))
    assert r.json()["data"]["nickname"] == "测试昵称"


# ---------- 课程 ----------

def test_courses_list_filter_sort(client):
    r = client.get("/api/courses", params={"category": "theory", "tech_domain": "AI", "sort": "rating"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["total"] >= 1
    assert all(i["category"] == "theory" and i["tech_domain"] == "AI" for i in data["items"])
    r = client.get("/api/courses", params={"keyword": "前端"})
    assert r.json()["data"]["total"] >= 1
    r = client.get("/api/courses/meta/filters")
    meta = r.json()["data"]
    assert len(meta["categories"]) == 3
    assert len(meta["tech_domains"]) >= 6


def test_course_detail_enroll_complete(client, student_token):
    r = client.get("/api/courses/1", headers=_auth(student_token))
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["course"]["title"]
    assert len(d["chapters"]) >= 3
    assert d["chapters"][0]["lessons"]
    assert d["is_enrolled"] is True  # seed 预置 student 已报名课程1

    # 收藏 toggle
    r = client.post("/api/courses/2/favorite", headers=_auth(student_token))
    assert r.json()["data"]["favorited"] is True
    r = client.post("/api/courses/2/favorite", headers=_auth(student_token))
    assert r.json()["data"]["favorited"] is False

    # 免费课报名（幂等返回已报名或新报名）
    r = client.post("/api/courses/4/enroll", headers=_auth(student_token))
    assert r.status_code == 200
    assert r.json()["data"]["enrolled"] is True

    # 标记课时完成
    lesson_id = d["chapters"][0]["lessons"][-1]["id"]
    r = client.post(
        f"/api/lessons/{lesson_id}/complete",
        json={"study_seconds": 600},
        headers=_auth(student_token),
    )
    assert r.status_code == 200
    assert "progress" in r.json()["data"]

    # 已报名可评论
    r = client.post(
        "/api/courses/1/comments",
        json={"rating": 5, "content": "测试评论：内容很有帮助"},
        headers=_auth(student_token),
    )
    assert r.status_code == 200
    r = client.get("/api/courses/1/comments")
    assert any("测试评论" in c["content"] for c in r.json()["data"])

    r = client.get("/api/users/me/enrollments", headers=_auth(student_token))
    assert r.status_code == 200
    assert len(r.json()["data"]) >= 2
    r = client.get("/api/users/me/favorites", headers=_auth(student_token))
    assert "courses" in r.json()["data"] and "jobs" in r.json()["data"]


def test_paid_course_order_flow(client, student_token):
    # 找一门付费课：课程3 云计算基础架构
    r = client.post("/api/courses/3/enroll", headers=_auth(student_token))
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["enrolled"] is False
    order = d["order"]
    assert order["status"] == "pending"

    r = client.post(f"/api/orders/{order['id']}/pay", headers=_auth(student_token))
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "paid"

    # 支付后自动报名
    r = client.post("/api/courses/3/enroll", headers=_auth(student_token))
    assert r.json()["data"]["enrolled"] is True

    r = client.get("/api/orders", headers=_auth(student_token))
    assert r.status_code == 200
    assert len(r.json()["data"]) >= 2  # 预置订单 + 新支付订单


# ---------- 职位 ----------

def test_jobs_and_apply(client, student_token):
    r = client.get("/api/jobs", params={"keyword": "工程师"})
    assert r.status_code == 200
    assert r.json()["data"]["total"] >= 5
    r = client.get("/api/jobs/meta/filters")
    assert len(r.json()["data"]["categories"]) >= 5

    r = client.get("/api/jobs/1")
    d = r.json()["data"]
    assert d["title"] and "is_favorited" in d and "has_applied" in d

    r = client.post("/api/jobs/5/favorite", headers=_auth(student_token))
    assert r.json()["data"]["favorited"] is True

    r = client.post("/api/jobs/4/apply", json={"message": "希望获得面试机会"}, headers=_auth(student_token))
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "pending"

    r = client.get("/api/users/me/applications", headers=_auth(student_token))
    assert len(r.json()["data"]) >= 1

    # AI 面试
    r = client.post("/api/jobs/1/ai-interview", json={}, headers=_auth(student_token))
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["interview_id"] and len(d["questions"]) >= 3
    answers = [{"question": q, "answer": "我在课程项目中实践过相关内容，能够结合理论与工程经验回答。"} for q in d["questions"]]
    r = client.post(
        f"/api/ai/interview/{d['interview_id']}/answer",
        json={"answers": answers},
        headers=_auth(student_token),
    )
    assert r.status_code == 200
    res = r.json()["data"]
    assert 0 <= res["score"] <= 100
    assert res["per_question"]


# ---------- AI ----------

def test_ai_chat_multi_turn(client, student_token):
    r = client.post(
        "/api/ai/chat",
        json={"message": "什么是机器学习？", "course_id": 1},
        headers=_auth(student_token),
    )
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["session_id"] and d["reply"]
    assert "模拟" in d["reply"]  # 无 key -> mock

    sid = d["session_id"]
    r = client.post(
        "/api/ai/chat",
        json={"session_id": sid, "message": "那过拟合呢？"},
        headers=_auth(student_token),
    )
    assert r.json()["data"]["session_id"] == sid

    r = client.get("/api/ai/chat/sessions", headers=_auth(student_token))
    assert any(s["id"] == sid for s in r.json()["data"])
    r = client.get(f"/api/ai/chat/sessions/{sid}", headers=_auth(student_token))
    assert len(r.json()["data"]["messages"]) >= 4
    r = client.delete(f"/api/ai/chat/sessions/{sid}", headers=_auth(student_token))
    assert r.json()["data"]["ok"] is True


def test_ai_learning_path_grade_report(client, student_token):
    r = client.post(
        "/api/ai/learning-path",
        json={"goal": "前端开发工程师", "hours_per_week": 8},
        headers=_auth(student_token),
    )
    assert r.status_code == 200
    plan = r.json()["data"]["plan"]
    assert plan["title"] and len(plan["stages"]) >= 3
    assert "topics" in plan["stages"][0] and "courses" in plan["stages"][0]

    r = client.post(
        "/api/ai/grade",
        json={"question": "实现一个函数返回列表最大值", "code": "def f(a):\n    return max(a)\n", "language": "python"},
        headers=_auth(student_token),
    )
    assert r.status_code == 200
    d = r.json()["data"]
    assert 0 <= d["score"] <= 100
    assert isinstance(d["issues"], list) and isinstance(d["suggestions"], list)

    r = client.get("/api/ai/report", params={"period": "week"}, headers=_auth(student_token))
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["period"] == "week"
    assert "total_minutes" in d and "summary" in d


# ---------- 通知 / 社区 ----------

def test_notifications_and_community(client, student_token):
    r = client.get("/api/notifications", headers=_auth(student_token))
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["unread_count"] >= 1 and len(d["items"]) >= 2
    nid = d["items"][0]["id"]
    r = client.post(f"/api/notifications/{nid}/read", headers=_auth(student_token))
    assert r.json()["data"]["ok"] is True
    r = client.post("/api/notifications/read-all", headers=_auth(student_token))
    assert r.json()["data"]["ok"] is True

    r = client.get("/api/community/questions")
    assert r.json()["data"]["total"] >= 3
    r = client.post(
        "/api/community/questions",
        json={"title": "测试提问", "content": "这是一个冒烟测试问题内容"},
        headers=_auth(student_token),
    )
    assert r.status_code == 200
    qid = r.json()["data"]["id"]
    r = client.post(
        f"/api/community/questions/{qid}/answers",
        json={"content": "测试回答内容"},
        headers=_auth(student_token),
    )
    assert r.status_code == 200
    r = client.get(f"/api/community/questions/{qid}")
    assert len(r.json()["data"]["answers"]) == 1


# ---------- 后台 ----------

def test_admin(client, admin_token, student_token):
    # 非管理员被拒
    r = client.get("/api/admin/stats", headers=_auth(student_token))
    assert r.status_code == 403

    r = client.get("/api/admin/stats", headers=_auth(admin_token))
    assert r.status_code == 200
    d = r.json()["data"]
    for key in ("users", "courses", "jobs", "orders", "paid_amount", "total_study_minutes", "trend"):
        assert key in d
    assert len(d["trend"]) == 7

    r = client.get("/api/admin/users", params={"keyword": "student"}, headers=_auth(admin_token))
    assert r.json()["data"]["total"] >= 1

    r = client.get("/api/admin/courses", headers=_auth(admin_token))
    assert len(r.json()["data"]) >= 18

    # 新增讲师/课程/职位 + 上下架
    r = client.post("/api/admin/lecturers", json={"name": "测试讲师", "title": "测试"}, headers=_auth(admin_token))
    assert r.status_code == 200
    lid = r.json()["data"]["id"]

    r = client.post(
        "/api/admin/courses",
        json={"title": "临时测试课程", "category": "theory", "lecturer_id": lid},
        headers=_auth(admin_token),
    )
    assert r.status_code == 200
    cid = r.json()["data"]["id"]
    r = client.put(f"/api/admin/courses/{cid}", json={"status": "off"}, headers=_auth(admin_token))
    assert r.json()["data"]["status"] == "off"
    r = client.delete(f"/api/admin/courses/{cid}", headers=_auth(admin_token))
    assert r.json()["data"]["ok"] is True
    r = client.delete(f"/api/admin/lecturers/{lid}", headers=_auth(admin_token))
    assert r.json()["data"]["ok"] is True

    r = client.post(
        "/api/admin/jobs",
        json={"title": "临时职位", "company": "测试公司", "category": "测试", "city": "北京"},
        headers=_auth(admin_token),
    )
    assert r.status_code == 200
    jid = r.json()["data"]["id"]
    r = client.put(f"/api/admin/jobs/{jid}", json={"status": "off"}, headers=_auth(admin_token))
    assert r.json()["data"]["status"] == "off"
    r = client.delete(f"/api/admin/jobs/{jid}", headers=_auth(admin_token))
    assert r.json()["data"]["ok"] is True

    r = client.get("/api/admin/orders", headers=_auth(admin_token))
    assert r.status_code == 200 and len(r.json()["data"]) >= 1
    r = client.get("/api/admin/applications", headers=_auth(admin_token))
    assert r.status_code == 200
    apps = r.json()["data"]
    assert len(apps) >= 1
    r = client.put(
        f"/api/admin/applications/{apps[0]['id']}",
        json={"status": "viewed"},
        headers=_auth(admin_token),
    )
    assert r.json()["data"]["status"] == "viewed"


def test_unauthorized(client):
    r = client.get("/api/users/me/enrollments")
    assert r.status_code in (401, 403)
    r = client.post("/api/ai/chat", json={"message": "hi"})
    assert r.status_code in (401, 403)
