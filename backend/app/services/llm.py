"""LLM 接入层：OpenAI 兼容 Chat Completions 接口。

- 配置 AI_API_KEY 时调用 {AI_BASE_URL}/v1/chat/completions（httpx，30s 超时）
- 未配置或任何异常 -> 回退 mock_engine，保证接口永不 500
"""
from __future__ import annotations

import json
import re
from typing import Any

import httpx

from .. import config
from . import mock_engine


def _call_llm(messages: list[dict], temperature: float = 0.6) -> str | None:
    """调用大模型，失败返回 None。"""
    if not config.AI_API_KEY:
        return None
    try:
        resp = httpx.post(
            f"{config.AI_BASE_URL.rstrip('/')}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {config.AI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": config.AI_MODEL,
                "messages": messages,
                "temperature": temperature,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception:
        return None


def _extract_json(text: str) -> Any:
    """从大模型回复中提取 JSON（容忍 ```json 围栏与首尾杂文本）。"""
    if not text:
        raise ValueError("empty")
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    candidate = m.group(1) if m else text
    candidate = candidate.strip()
    # 截取第一个 { 或 [ 到末尾对应符号，容忍前后解释文字
    start = min(
        [i for i in (candidate.find("{"), candidate.find("[")) if i != -1],
        default=-1,
    )
    if start != -1:
        candidate = candidate[start:]
    return json.loads(candidate)


def chat_reply(message: str, course: Any = None, history: list | None = None) -> str:
    """多轮答疑。history: [{role, content}]（已含本条 user 消息前的历史）。"""
    system = (
        "你是智慧教育平台的 AI 学习助手，用中文回答，语气专业且鼓励学习者。"
        "回答结合课程内容，给出知识点拓展，使用 Markdown 排版，长度适中。"
    )
    if course is not None:
        system += (
            f" 当前课程：《{course.title}》，方向 {course.tech_domain}，"
            f"难度 {course.difficulty}，简介：{course.brief}"
        )
    msgs = [{"role": "system", "content": system}]
    for h in (history or [])[-10:]:
        msgs.append({"role": h["role"], "content": h["content"]})
    msgs.append({"role": "user", "content": message})
    reply = _call_llm(msgs)
    if reply:
        return reply
    return mock_engine.chat_reply(message, course=course, history=history)


def gen_learning_path(goal: str, hours_per_week: int | None, courses: list) -> dict:
    course_list = "\n".join(
        f"- id={c.id} 《{c.title}》({c.category}/{c.tech_domain}/{c.difficulty})"
        for c in courses[:40]
    )
    prompt = (
        f"学员目标岗位/方向：{goal}；每周可学习 {hours_per_week or 10} 小时。\n"
        f"站内课程：\n{course_list}\n"
        "请生成学习路径，严格返回 JSON（不要多余文字），结构：\n"
        '{"title": str, "stages": [{"name": str, "duration": str, "topics": [str], '
        '"courses": [{"id": int, "title": str}]}], "advice": str}\n'
        "stages 3-5 个，courses 必须从上面站内课程中选（id 必须真实存在）。"
    )
    reply = _call_llm(
        [{"role": "user", "content": prompt}], temperature=0.4
    )
    if reply:
        try:
            plan = _extract_json(reply)
            if isinstance(plan, dict) and isinstance(plan.get("stages"), list):
                valid_ids = {c.id for c in courses}
                for st in plan["stages"]:
                    st.setdefault("topics", [])
                    st["courses"] = [
                        c for c in st.get("courses", []) if c.get("id") in valid_ids
                    ]
                plan.setdefault("title", f"{goal} 学习路径")
                plan.setdefault("advice", "")
                return plan
        except Exception:
            pass
    return mock_engine.learning_path(goal, hours_per_week, courses)


def grade_code(question: str, code: str, language: str | None) -> dict:
    prompt = (
        f"请批改以下编程作业，严格返回 JSON（不要多余文字）：\n"
        f"题目：{question}\n语言：{language or 'python'}\n代码：\n```\n{code[:4000]}\n```\n"
        '返回结构：{"score": 0-100的整数, "correct_points": [str], "issues": [str], '
        '"suggestions": [str], "improved_code": str}'
    )
    reply = _call_llm([{"role": "user", "content": prompt}], temperature=0.3)
    if reply:
        try:
            result = _extract_json(reply)
            if isinstance(result, dict) and "score" in result:
                result.setdefault("correct_points", [])
                result.setdefault("issues", [])
                result.setdefault("suggestions", [])
                result.setdefault("improved_code", code)
                return result
        except Exception:
            pass
    return mock_engine.grade_code(question, code, language)


def gen_report(period: str, stats: dict) -> dict:
    """返回 {strengths, weaknesses, suggestions, summary}。"""
    prompt = (
        f"学员{('本周' if period == 'week' else '本月')}学习数据：\n"
        f"- 学习时长：{stats.get('total_minutes', 0)} 分钟\n"
        f"- 完成课时：{stats.get('completed_lessons', 0)} 个\n"
        f"- 课程进度：{json.dumps(stats.get('courses_progress', []), ensure_ascii=False)}\n"
        "请生成学习报告评语，严格返回 JSON："
        '{"strengths": [str], "weaknesses": [str], "suggestions": [str], "summary": str}'
    )
    reply = _call_llm([{"role": "user", "content": prompt}], temperature=0.4)
    if reply:
        try:
            result = _extract_json(reply)
            if isinstance(result, dict) and "summary" in result:
                result.setdefault("strengths", [])
                result.setdefault("weaknesses", [])
                result.setdefault("suggestions", [])
                return result
        except Exception:
            pass
    return mock_engine.report_fields(period, stats)


def gen_interview_questions(job: Any) -> list[str]:
    prompt = (
        f"请为岗位「{job.title}」（{job.company}，{job.category}）生成 5 道面试题。"
        "岗位要求：" + (job.requirements or "")[:500] + "\n"
        '严格返回 JSON 数组：["题目1","题目2",...]'
    )
    reply = _call_llm([{"role": "user", "content": prompt}], temperature=0.5)
    if reply:
        try:
            result = _extract_json(reply)
            if isinstance(result, list) and result:
                return [str(q) for q in result][:5]
        except Exception:
            pass
    return mock_engine.interview_questions(job)


def evaluate_interview(job: Any, answers: list[dict]) -> dict:
    qa = "\n".join(
        f"Q: {a.get('question','')}\nA: {a.get('answer','')}" for a in answers
    )[:6000]
    prompt = (
        f"请评估以下针对岗位「{job.title}」的面试作答，严格返回 JSON：\n{qa}\n"
        '返回结构：{"score": 0-100, "evaluation": str, '
        '"per_question": [{"question": str, "answer": str, "score": 0-100, "comment": str}]}'
    )
    reply = _call_llm([{"role": "user", "content": prompt}], temperature=0.3)
    if reply:
        try:
            result = _extract_json(reply)
            if isinstance(result, dict) and "score" in result:
                result.setdefault("evaluation", "")
                result.setdefault("per_question", [])
                return result
        except Exception:
            pass
    return mock_engine.evaluate_interview(job, answers)
