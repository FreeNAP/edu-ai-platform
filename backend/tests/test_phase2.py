"""二期功能测试：新增接口、自动通知、权限与边界。"""
import uuid

import pytest

from conftest import _auth


def _new_user(client, admin_token, role="student"):
    name = "t" + uuid.uuid4().hex[:8]
    r = client.post(
        "/api/admin/users",
        json={"username": name, "email": f"{name}@test.com", "password": "abc12345", "role": role},
        headers=_auth(admin_token),
    )
    assert r.status_code == 200, r.text
    tok = client.post("/api/auth/login", json={"username": name, "password": "abc12345"}).json()["data"]["token"]
    return r.json()["data"], tok


def _notif_types(client, token):
    return [n["type"] for n in client.get("/api/notifications", headers=_auth(token)).json()["data"]["items"]]


def _first_course(client, token, **params):
    return client.get("/api/courses", params={"size": 1, **params}, headers=_auth(token)).json()["data"]["items"][0]


# ---------- 管理员新建用户 ----------

def test_admin_create_user_and_duplicate(client, admin_token):
    user, tok = _new_user(client, admin_token)
    assert user["role"] == "student"
    r = client.post(
        "/api/admin/users",
        json={"username": user["username"], "email": "x" + user["email"], "password": "abc12345", "role": "student"},
        headers=_auth(admin_token),
    )
    assert r.status_code == 400


def test_admin_create_user_forbidden_for_student(client, student_token):
    r = client.post(
        "/api/admin/users",
        json={"username": "nope", "email": "nope@test.com", "password": "abc12345", "role": "admin"},
        headers=_auth(student_token),
    )
    assert r.status_code == 403


# ---------- 面试 ----------

def test_interview_detail_and_list(client, admin_token):
    _, tok = _new_user(client, admin_token)
    job = client.get("/api/jobs", params={"size": 1}, headers=_auth(tok)).json()["data"]["items"][0]
    r = client.post(f"/api/jobs/{job['id']}/ai-interview", json={}, headers=_auth(tok))
    assert r.status_code == 200, r.text
    iid = r.json()["data"]["interview_id"]
    d = client.get(f"/api/ai/interview/{iid}", headers=_auth(tok)).json()["data"]
    assert d["status"] == "pending" and d["questions"]
    answers = [{"question": q, "answer": "我会先分析需求，再给出实现和测试方案。"} for q in d["questions"]]
    assert client.post(f"/api/ai/interview/{iid}/answer", json={"answers": answers}, headers=_auth(tok)).status_code == 200
    d = client.get(f"/api/ai/interview/{iid}", headers=_auth(tok)).json()["data"]
    assert d["status"] == "done" and isinstance(d["score"], (int, float))
    assert {"question", "answer", "score", "comment"} <= set(d["per_question"][0])
    lst = client.get("/api/users/me/interviews", headers=_auth(tok)).json()["data"]
    assert lst[0]["id"] == iid


def test_interview_not_owner_and_missing(client, admin_token, student_token):
    _, tok = _new_user(client, admin_token)
    job = client.get("/api/jobs", params={"size": 1}, headers=_auth(tok)).json()["data"]["items"][0]
    iid = client.post(f"/api/jobs/{job['id']}/ai-interview", json={}, headers=_auth(tok)).json()["data"]["interview_id"]
    assert client.get(f"/api/ai/interview/{iid}", headers=_auth(student_token)).status_code in (403, 404)
    assert client.get("/api/ai/interview/999999", headers=_auth(tok)).status_code == 404


def test_seeded_student_interview(client, student_token):
    lst = client.get("/api/users/me/interviews", headers=_auth(student_token)).json()["data"]
    assert any(i["status"] == "done" for i in lst)


# ---------- 学习路径 ----------

def test_learning_plans_history_and_delete(client, admin_token):
    _, tok = _new_user(client, admin_token)
    r = client.post("/api/ai/learning-path", json={"goal": "后端开发工程师", "hours_per_week": 6}, headers=_auth(tok))
    assert r.status_code == 200
    plans = client.get("/api/ai/learning-plans", headers=_auth(tok)).json()["data"]
    assert len(plans) == 1 and plans[0]["due_date"]
    pid = plans[0]["id"]
    assert client.delete(f"/api/ai/learning-plans/{pid}", headers=_auth(tok)).status_code == 200
    assert client.get("/api/ai/learning-plans", headers=_auth(tok)).json()["data"] == []
    assert client.delete(f"/api/ai/learning-plans/{pid}", headers=_auth(tok)).status_code == 404


def test_learning_plan_other_user_cannot_delete(client, admin_token, student_token):
    plans = client.get("/api/ai/learning-plans", headers=_auth(student_token)).json()["data"]
    assert plans, "种子数据应为 student 预置学习路径"
    _, tok = _new_user(client, admin_token)
    assert client.delete(f"/api/ai/learning-plans/{plans[0]['id']}", headers=_auth(tok)).status_code in (403, 404)


def test_learning_plan_due_reminder_once(client, admin_token):
    from datetime import datetime, timedelta

    from app.database import SessionLocal
    from app.models import LearningPlan

    user, tok = _new_user(client, admin_token)
    client.post("/api/ai/learning-path", json={"goal": "数据分析师"}, headers=_auth(tok))
    with SessionLocal() as db:
        p = db.query(LearningPlan).filter(LearningPlan.user_id == user["id"]).first()
        p.due_date = datetime.now() - timedelta(days=1)
        db.commit()
    assert _notif_types(client, tok).count("study") == 1
    assert _notif_types(client, tok).count("study") == 1  # 再次拉取不重复提醒


# ---------- 社区 ----------

def test_community_delete_permissions(client, admin_token, student_token):
    _, tok = _new_user(client, admin_token)
    q = client.post("/api/community/questions", json={"title": "怎么入门机器学习", "content": "求推荐"}, headers=_auth(tok)).json()["data"]
    a = client.post(f"/api/community/questions/{q['id']}/answers", json={"content": "先学线性代数"}, headers=_auth(student_token)).json()["data"]
    assert client.delete(f"/api/community/answers/{a['id']}", headers=_auth(tok)).status_code == 403
    assert client.delete(f"/api/community/answers/{a['id']}", headers=_auth(student_token)).status_code == 200
    assert client.delete(f"/api/community/answers/{a['id']}", headers=_auth(student_token)).status_code == 404
    assert client.delete(f"/api/community/questions/{q['id']}", headers=_auth(student_token)).status_code == 403
    assert client.delete(f"/api/community/questions/{q['id']}", headers=_auth(tok)).status_code == 200
    assert client.get(f"/api/community/questions/{q['id']}", headers=_auth(tok)).status_code == 404


def test_admin_questions_list_and_delete(client, admin_token, student_token):
    q = client.post("/api/community/questions", json={"title": "待清理的问题", "content": "x"}, headers=_auth(student_token)).json()["data"]
    data = client.get("/api/admin/questions", params={"keyword": "待清理"}, headers=_auth(admin_token)).json()["data"]
    assert any(i["id"] == q["id"] for i in data["items"])
    assert client.get("/api/admin/questions", headers=_auth(student_token)).status_code == 403
    assert client.delete(f"/api/admin/questions/{q['id']}", headers=_auth(admin_token)).status_code == 200


def test_new_answer_notifies_asker(client, admin_token, student_token):
    _, tok = _new_user(client, admin_token)
    q = client.post("/api/community/questions", json={"title": "Vue 和 React 选哪个", "content": "纠结"}, headers=_auth(tok)).json()["data"]
    client.post(f"/api/community/questions/{q['id']}/answers", json={"content": "看团队"}, headers=_auth(tok))
    assert "community" not in _notif_types(client, tok)  # 自己回答不通知
    client.post(f"/api/community/questions/{q['id']}/answers", json={"content": "都可以"}, headers=_auth(student_token))
    assert "community" in _notif_types(client, tok)


# ---------- 课程目录 ----------

def test_outline_get_put_and_notify(client, admin_token):
    _, tok = _new_user(client, admin_token)
    course = _first_course(client, tok)
    client.post(f"/api/courses/{course['id']}/favorite", headers=_auth(tok))
    ol = client.get(f"/api/admin/courses/{course['id']}/outline", headers=_auth(admin_token)).json()["data"]
    total_before = sum(len(ch["lessons"]) for ch in ol)
    ol[0]["lessons"].append({"title": "补充练习", "duration": 600, "kind": "text", "content": "练习说明"})
    r = client.put(f"/api/admin/courses/{course['id']}/outline", json=ol, headers=_auth(admin_token))
    assert r.status_code == 200, r.text
    ol2 = client.get(f"/api/admin/courses/{course['id']}/outline", headers=_auth(admin_token)).json()["data"]
    assert sum(len(ch["lessons"]) for ch in ol2) == total_before + 1
    assert "course" in _notif_types(client, tok)


def test_outline_remove_lesson_clears_progress(client, admin_token):
    _, tok = _new_user(client, admin_token)
    course = _first_course(client, tok, is_free="true")
    client.post(f"/api/courses/{course['id']}/enroll", headers=_auth(tok))
    d = client.get(f"/api/courses/{course['id']}", headers=_auth(tok)).json()["data"]
    lid = d["chapters"][0]["lessons"][0]["id"]
    client.post(f"/api/lessons/{lid}/complete", json={"study_seconds": 60}, headers=_auth(tok))
    ol = client.get(f"/api/admin/courses/{course['id']}/outline", headers=_auth(admin_token)).json()["data"]
    ol[0]["lessons"] = [ls for ls in ol[0]["lessons"] if ls["id"] != lid]
    assert client.put(f"/api/admin/courses/{course['id']}/outline", json=ol, headers=_auth(admin_token)).status_code == 200
    d = client.get(f"/api/courses/{course['id']}", headers=_auth(tok)).json()["data"]
    assert lid not in d["lesson_status"]


def test_outline_rejects_foreign_lesson(client, admin_token, student_token):
    courses = client.get("/api/courses", params={"size": 2}, headers=_auth(student_token)).json()["data"]["items"]
    a, b = courses[0]["id"], courses[1]["id"]
    foreign = client.get(f"/api/admin/courses/{b}/outline", headers=_auth(admin_token)).json()["data"][0]["lessons"][0]
    ol = client.get(f"/api/admin/courses/{a}/outline", headers=_auth(admin_token)).json()["data"]
    ol[0]["lessons"].append(foreign)
    assert client.put(f"/api/admin/courses/{a}/outline", json=ol, headers=_auth(admin_token)).status_code == 400
    assert client.get("/api/admin/courses/999999/outline", headers=_auth(admin_token)).status_code == 404


def test_lesson_content_only_for_enrolled(client, admin_token):
    _, tok = _new_user(client, admin_token)
    course = _first_course(client, tok, is_free="true")
    d = client.get(f"/api/courses/{course['id']}", headers=_auth(tok)).json()["data"]
    assert d["chapters"][0]["lessons"][0]["content"] == ""
    client.post(f"/api/courses/{course['id']}/enroll", headers=_auth(tok))
    d = client.get(f"/api/courses/{course['id']}", headers=_auth(tok)).json()["data"]
    assert d["chapters"][0]["lessons"][0]["content"]


# ---------- 通知规则 ----------

def test_job_update_notifies_favoriters(client, admin_token):
    _, tok = _new_user(client, admin_token)
    job = client.get("/api/jobs", params={"size": 1}, headers=_auth(tok)).json()["data"]["items"][0]
    client.post(f"/api/jobs/{job['id']}/favorite", headers=_auth(tok))
    r = client.put(f"/api/admin/jobs/{job['id']}", json={"salary": "20-30K"}, headers=_auth(admin_token))
    assert r.status_code == 200, r.text
    assert "job" in _notif_types(client, tok)


def test_application_status_notifies(client, admin_token):
    _, tok = _new_user(client, admin_token)
    job = client.get("/api/jobs", params={"size": 1}, headers=_auth(tok)).json()["data"]["items"][0]
    app_ = client.post(f"/api/jobs/{job['id']}/apply", json={"message": "想试试"}, headers=_auth(tok)).json()["data"]
    r = client.put(f"/api/admin/applications/{app_['id']}", json={"status": "accepted"}, headers=_auth(admin_token))
    assert r.status_code == 200
    assert "application" in _notif_types(client, tok)


def test_order_paid_notifies(client, admin_token):
    _, tok = _new_user(client, admin_token)
    course = _first_course(client, tok, is_free="false")
    order = client.post(f"/api/courses/{course['id']}/enroll", headers=_auth(tok)).json()["data"]["order"]
    assert client.post(f"/api/orders/{order['id']}/pay", headers=_auth(tok)).status_code == 200
    assert "order" in _notif_types(client, tok)


# ---------- 越权、下架、禁用、边界 ----------

def test_order_not_owner(client, admin_token):
    _, a = _new_user(client, admin_token)
    _, b = _new_user(client, admin_token)
    course = _first_course(client, a, is_free="false")
    order = client.post(f"/api/courses/{course['id']}/enroll", headers=_auth(a)).json()["data"]["order"]
    assert client.post(f"/api/orders/{order['id']}/pay", headers=_auth(b)).status_code in (403, 404)


def test_chat_session_not_owner(client, admin_token, student_token):
    sid = client.post("/api/ai/chat", json={"message": "你好"}, headers=_auth(student_token)).json()["data"]["session_id"]
    _, tok = _new_user(client, admin_token)
    assert client.get(f"/api/ai/chat/sessions/{sid}", headers=_auth(tok)).status_code in (403, 404)


def _admin_course_ids(client, admin_token):
    d = client.get("/api/admin/courses", params={"size": 50}, headers=_auth(admin_token)).json()["data"]
    items = d["items"] if isinstance(d, dict) else d
    return [c["id"] for c in items]


def test_offline_course_hidden(client, admin_token):
    _, tok = _new_user(client, admin_token)
    course = _first_course(client, tok)
    client.put(f"/api/admin/courses/{course['id']}", json={"status": "off"}, headers=_auth(admin_token))
    try:
        ids = [c["id"] for c in client.get("/api/courses", params={"size": 50}, headers=_auth(tok)).json()["data"]["items"]]
        assert course["id"] not in ids
        assert client.get(f"/api/courses/{course['id']}", headers=_auth(tok)).status_code == 404
        assert client.post(f"/api/courses/{course['id']}/enroll", headers=_auth(tok)).status_code in (400, 404)
        assert course["id"] in _admin_course_ids(client, admin_token)
    finally:
        client.put(f"/api/admin/courses/{course['id']}", json={"status": "on"}, headers=_auth(admin_token))


def test_offline_job_cannot_apply(client, admin_token):
    _, tok = _new_user(client, admin_token)
    job = client.get("/api/jobs", params={"size": 1}, headers=_auth(tok)).json()["data"]["items"][0]
    client.put(f"/api/admin/jobs/{job['id']}", json={"status": "off"}, headers=_auth(admin_token))
    try:
        assert client.post(f"/api/jobs/{job['id']}/apply", json={}, headers=_auth(tok)).status_code in (400, 404)
    finally:
        client.put(f"/api/admin/jobs/{job['id']}", json={"status": "on"}, headers=_auth(admin_token))


def test_disabled_user_blocked(client, admin_token):
    user, tok = _new_user(client, admin_token)
    client.put(f"/api/admin/users/{user['id']}", json={"status": "disabled"}, headers=_auth(admin_token))
    assert client.get("/api/auth/me", headers=_auth(tok)).status_code in (401, 403)
    r = client.post("/api/auth/login", json={"username": user["username"], "password": "abc12345"})
    assert r.status_code in (401, 403)


@pytest.mark.parametrize("params", [{"size": 999}, {"page": 0}])
def test_pagination_bounds(client, student_token, params):
    r = client.get("/api/courses", params=params, headers=_auth(student_token))
    if r.status_code == 200:
        d = r.json()["data"]
        assert d["size"] <= 50 and d["page"] >= 1
    else:
        assert r.status_code in (400, 422)


def test_comment_rating_range(client, admin_token):
    _, tok = _new_user(client, admin_token)
    course = _first_course(client, tok, is_free="true")
    client.post(f"/api/courses/{course['id']}/enroll", headers=_auth(tok))
    for bad in (0, 6):
        r = client.post(f"/api/courses/{course['id']}/comments", json={"rating": bad, "content": "好"}, headers=_auth(tok))
        assert r.status_code in (400, 422)
    r = client.post(f"/api/courses/{course['id']}/comments", json={"rating": 5, "content": "   "}, headers=_auth(tok))
    assert r.status_code in (400, 422)


def test_idempotent_enroll_and_apply(client, admin_token):
    _, tok = _new_user(client, admin_token)
    course = _first_course(client, tok, is_free="true")
    for _ in range(2):
        assert client.post(f"/api/courses/{course['id']}/enroll", headers=_auth(tok)).status_code == 200
    ids = [(e.get("course") or e)["id"] for e in client.get("/api/users/me/enrollments", headers=_auth(tok)).json()["data"]]
    assert ids.count(course["id"]) == 1
    job = client.get("/api/jobs", params={"size": 1}, headers=_auth(tok)).json()["data"]["items"][0]
    client.post(f"/api/jobs/{job['id']}/apply", json={}, headers=_auth(tok))
    client.post(f"/api/jobs/{job['id']}/apply", json={}, headers=_auth(tok))
    apps = client.get("/api/users/me/applications", headers=_auth(tok)).json()["data"]
    assert [a["job"]["id"] for a in apps].count(job["id"]) == 1


def test_delete_course_no_500(client, admin_token):
    lecturers = client.get("/api/admin/lecturers", headers=_auth(admin_token)).json()["data"]
    lec = (lecturers["items"] if isinstance(lecturers, dict) else lecturers)[0]["id"]
    r = client.post(
        "/api/admin/courses",
        json={"title": "临时课程", "category": "theory", "tech_domain": "AI", "difficulty": "入门",
              "is_free": True, "price": 0, "brief": "x", "lecturer_id": lec},
        headers=_auth(admin_token),
    )
    assert r.status_code == 200, r.text
    cid = r.json()["data"]["id"]
    assert client.delete(f"/api/admin/courses/{cid}", headers=_auth(admin_token)).status_code == 200
    assert client.get(f"/api/admin/courses/{cid}/outline", headers=_auth(admin_token)).status_code == 404


def test_error_format(client, student_token):
    r = client.get("/api/courses/999999", headers=_auth(student_token))
    assert r.status_code == 404 and r.json()["code"] != 0 and "detail" in r.json()
