"""内置模拟引擎：未配置 AI_API_KEY 或大模型不可用时，
保证所有 AI 接口产出与契约同构的结果。所有回复标注「（内置模拟模式）」。
"""
from __future__ import annotations

import re
from typing import Any

MOCK_TAG = "（内置模拟模式）"

# ---- 答疑知识库：关键词 -> 解析 ----
_KB: list[tuple[list[str], str]] = [
    (
        ["机器学习", "监督学习", "模型"],
        "机器学习是让计算机从数据中自动学习规律的技术。监督学习用带标签的数据训练模型"
        "（如分类、回归），无监督学习处理无标签数据（如聚类）。一般流程：数据准备 → "
        "特征工程 → 模型训练 → 评估 → 部署。",
    ),
    (
        ["深度学习", "神经网络", "cnn", "rnn"],
        "深度学习是机器学习的分支，使用多层神经网络自动提取特征。CNN 擅长图像，"
        "RNN/Transformer 擅长序列与文本。训练核心是反向传播 + 梯度下降。",
    ),
    (
        ["过拟合", "欠拟合", "正则化"],
        "过拟合指模型在训练集表现好但泛化差。常用对策：增加数据、正则化（L1/L2）、"
        "Dropout、Early Stopping、交叉验证。欠拟合则需要更强的模型或更多特征。",
    ),
    (
        ["python", "列表", "字典", "装饰器", "函数"],
        "Python 是解释型高级语言，核心数据结构有列表（有序可变）、字典（键值对）、"
        "元组（不可变）。装饰器本质是接收函数并返回函数的高阶函数，常用于日志、鉴权。",
    ),
    (
        ["vue", "react", "前端", "组件", "dom"],
        "Vue 是渐进式前端框架，核心是响应式数据绑定与组件化开发。父子组件通过 "
        "props/emit 通信，复杂状态用 Pinia 管理。",
    ),
    (
        ["sql", "数据库", "mysql", "索引", "join"],
        "SQL 用于关系型数据库操作。索引能加速查询但拖慢写入；JOIN 用于多表关联；"
        "避免 SELECT *，注意 N+1 查询问题。",
    ),
    (
        ["云计算", "云原生", "docker", "k8s", "容器"],
        "云计算按需提供计算资源（IaaS/PaaS/SaaS）。Docker 实现容器化打包，"
        "Kubernetes 负责容器编排与弹性伸缩，是云原生的核心。",
    ),
    (
        ["大数据", "spark", "hadoop", "hive"],
        "大数据技术围绕海量数据的存储与计算。Hadoop 提供 HDFS 存储与 MapReduce，"
        "Spark 基于内存计算速度更快，支持批处理与流处理。",
    ),
    (
        ["物联网", "mqtt", "嵌入式", "传感器"],
        "物联网通过传感器采集数据，经网络传输到平台处理。MQTT 是轻量级发布/订阅"
        "协议，适合低带宽不稳定网络环境。",
    ),
    (
        ["http", "接口", "api", "rest", "请求"],
        "RESTful API 用 HTTP 动词表达操作语义：GET 查询、POST 创建、PUT 更新、"
        "DELETE 删除。接口鉴权常用 JWT，即头部携带的签名令牌。",
    ),
    (
        ["jwt", "token", "登录", "鉴权"],
        "JWT 由 Header、Payload、Signature 三部分组成，服务端签发后客户端在 "
        "Authorization: Bearer 头中携带，服务端验签即可识别用户身份。",
    ),
    (
        ["算法", "排序", "数据结构", "复杂度"],
        "常见排序：快速排序平均 O(n log n)，冒泡 O(n²)。选择数据结构看操作特征："
        "查找多用哈希表 O(1)，有序遍历用树结构。",
    ),
]

_DOMAIN_KEYWORDS = {
    "AI": ["ai", "人工智能", "机器学习", "深度学习", "大模型", "nlp", "算法"],
    "大数据": ["大数据", "数据", "spark", "hadoop", "分析"],
    "云计算": ["云", "云计算", "运维", "devops", "容器", "k8s"],
    "前端": ["前端", "vue", "react", "页面", "ui"],
    "后端": ["后端", "java", "python", "接口", "服务端", "django"],
    "物联网": ["物联网", "iot", "嵌入式", "硬件", "传感"],
    "运维": ["运维", "linux", "监控", "devops", "k8s"],
    "数据分析": ["数据", "sql", "分析", "可视化", "excel"],
    "测试": ["测试", "用例", "自动化", "缺陷", "bug"],
}


def _job_domain_keys(job: Any) -> list[str]:
    """职位 category（如 '后端开发'）匹配到 _DOMAIN_KEYWORDS 的关键词列表。"""
    cat = getattr(job, "category", "") or ""
    for domain, kws in _DOMAIN_KEYWORDS.items():
        if domain in cat:
            return kws
    return []


def _hit_kb(text: str) -> str | None:
    low = text.lower()
    for keys, answer in _KB:
        if any(k in low for k in keys):
            return answer
    return None


def chat_reply(message: str, course: Any = None, history: list | None = None) -> str:
    """检索式答疑：知识库命中优先，其次关联课程，最后通用建议。"""
    parts: list[str] = [MOCK_TAG, ""]
    hit = _hit_kb(message)
    if hit:
        parts += [f"关于你问的「{message[:40]}」：", "", hit, ""]
        parts += [
            "知识点拓展：",
            "- 建议先动手做一个小 demo 验证概念，再回到理论查漏补缺；",
            "- 把该知识点和你正在学的课程内容串联起来，形成知识网络；",
            "- 可以在社区问答区发帖讨论，或让 AI 出几道练习题巩固。",
        ]
    elif course is not None:
        parts += [
            f"你正在学习《{course.title}》（{course.tech_domain} · {course.difficulty}）。",
            "",
            f"这门课主要讲：{course.brief or '课程详见章节目录'}",
            "",
            f"针对「{message[:40]}」，建议先回看相关章节的课时，重点理解概念定义和示例；"
            "如果是动手类问题，可以结合实训环节边做边学。",
            "",
            "知识点拓展：",
            f"- {course.tech_domain} 方向的基础概念是该问题的前置知识；",
            "- 可以尝试换一种问法，例如带上具体报错或代码片段，我能给出更精准的分析。",
        ]
    else:
        parts += [
            f"关于「{message[:40]}」：",
            "",
            "这是一个值得拆解的问题。建议按「是什么 → 为什么 → 怎么用」三步走：先明确概念定义，"
            "再理解背后的原理，最后通过练习落地。",
            "",
            "知识点拓展：",
            "- 可以告诉我你正在学习的课程或目标岗位，我会结合课程内容回答；",
            "- 如果是代码类问题，把代码贴出来，我可以顺便给出批改意见。",
        ]
    return "\n".join(parts)


def _match_courses(goal: str, courses: list, limit: int = 6) -> list:
    """按目标关键词匹配站内课程。"""
    low = goal.lower()
    domains = [d for d, kws in _DOMAIN_KEYWORDS.items() if any(k in low for k in kws)]
    scored = []
    for c in courses:
        score = 0
        if c.tech_domain in domains:
            score += 3
        if any(k in (c.title or "").lower() for k in low.split()):
            score += 1
        if getattr(c, "rating", 0):
            score += c.rating / 10
        scored.append((score, c))
    scored.sort(key=lambda x: (-x[0], -x[1].students_count))
    picked = [c for s, c in scored if s > 0][:limit]
    if not picked:  # 目标词无匹配时退回高分课程
        picked = sorted(courses, key=lambda c: -c.rating)[:limit]
    return picked


def _difficulty_rank(d: str) -> int:
    return {"入门": 0, "初级": 1, "中级": 2, "高级": 3}.get(d, 1)


def learning_path(goal: str, hours_per_week: int | None, courses: list) -> dict:
    hours = hours_per_week or 10
    picked = _match_courses(goal, courses)
    by_diff = sorted(picked, key=lambda c: _difficulty_rank(c.difficulty))

    def citem(c):
        return {"id": c.id, "title": c.title}

    stage_names = ["基础夯实", "进阶提升", "实战演练", "冲刺认证"]
    stage_topics = [
        ["核心概念与术语", "开发环境搭建", "基础知识体系梳理"],
        ["进阶语法与框架", "常见设计模式", "工程化思维"],
        ["完整项目实操", "性能调优", "问题排查与复盘"],
        ["考点串讲", "模拟题训练", "面试常见问题"],
    ]
    stages = []
    groups = [by_diff[i::4] for i in range(4)]
    for i in range(4):
        weeks = max(1, round(len(groups[i]) * 12 / hours))
        stages.append(
            {
                "name": stage_names[i],
                "duration": f"{weeks}周（每周约{hours}小时）",
                "topics": stage_topics[i],
                "courses": [citem(c) for c in groups[i]],
            }
        )
    return {
        "title": f"{goal} 学习路径",
        "stages": stages,
        "advice": MOCK_TAG
        + f" 目标「{goal}」建议按四阶段推进，每周保证 {hours} 小时有效学习；"
        "入门阶段重理解，实战阶段重产出作品，认证阶段重刷题与面试准备。"
        "学完每个阶段记得回来更新学习报告，我会帮你调整后续计划。",
    }


def grade_code(question: str, code: str, language: str | None) -> dict:
    lang = (language or "python").lower()
    score = 60
    correct_points: list[str] = []
    issues: list[str] = []
    suggestions: list[str] = []
    improved = code

    n = len(code.strip())
    if n == 0:
        return {
            "score": 0,
            "correct_points": [],
            "issues": ["未提交任何代码"],
            "suggestions": ["请先完成题目要求再提交批改"],
            "improved_code": "",
        }

    if n > 80:
        score += 8
        correct_points.append("代码结构完整，有一定实现量")
    if n > 300:
        score += 4

    kw_map = {
        "def ": "函数定义",
        "class ": "面向对象封装",
        "return": "结果返回",
        "for ": "循环遍历",
        "if ": "条件判断",
        "import ": "模块引入",
        "try": "异常处理意识",
    }
    for kw, label in kw_map.items():
        if kw in code:
            score += 3
            correct_points.append(f"使用了{label}（{kw.strip()}）")

    if "#" in code or "//" in code:
        score += 4
        correct_points.append("包含注释，可读性较好")
    else:
        issues.append("缺少注释，关键逻辑可读性较差")
        suggestions.append("为关键函数与复杂逻辑补充注释")

    if "try" not in code:
        issues.append("未做异常处理，边界情况可能崩溃")
        suggestions.append("对输入校验、除零、越界等情况增加 try/except 或条件保护")

    syntax_err = None
    if lang == "python":
        try:
            compile(code, "<submission>", "exec")
            score += 6
            correct_points.append("Python 语法检查通过")
        except SyntaxError as e:
            syntax_err = e
            score -= 15
            issues.append(f"存在语法错误：{e.msg}（第 {e.lineno} 行附近）")
            suggestions.append("先修复语法错误再运行验证结果")

    if "return" not in code and ("函数" in question or "def " in code):
        issues.append("函数缺少 return 语句，可能无法输出结果")
        suggestions.append("确认函数是否应返回计算结果")

    score = max(0, min(100, score))
    if not correct_points:
        correct_points.append("已提交代码，具备基本结构")
    if not suggestions:
        suggestions.append("代码质量不错，可以尝试补充单元测试进一步验证正确性")
    if not issues:
        issues.append("未发现明显问题，注意边界输入与性能表现")

    improved = (
        f"# {MOCK_TAG} 改进建议版\n"
        f"# 原评分：{score} 分\n"
        + ("" if syntax_err is None else "# 注意：请先修复上方指出的语法错误\n")
        + code
    )
    return {
        "score": score,
        "correct_points": correct_points,
        "issues": issues,
        "suggestions": suggestions,
        "improved_code": improved,
    }


def report_fields(period: str, stats: dict) -> dict:
    """stats: {total_minutes, completed_lessons, courses_progress:[{title,progress}]}"""
    total = stats.get("total_minutes", 0)
    done = stats.get("completed_lessons", 0)
    cps = stats.get("courses_progress", [])
    label = "本周" if period == "week" else "本月"

    strengths, weaknesses, suggestions = [], [], []
    if done > 0:
        strengths.append(f"{label}已完成 {done} 个课时，保持持续学习的习惯")
    if total >= 120:
        strengths.append(f"{label}投入 {total} 分钟学习，学习时长可观")
    high = [c for c in cps if c.get("progress", 0) >= 60]
    for c in high[:2]:
        strengths.append(f"《{c['title']}》进度 {c['progress']}%，推进良好")
    low = [c for c in cps if 0 < c.get("progress", 0) < 30]
    for c in low[:2]:
        weaknesses.append(f"《{c['title']}》进度仅 {c['progress']}%，存在停滞风险")
    if total < 60:
        weaknesses.append(f"{label}学习时长偏少（{total} 分钟），节奏需要加强")
    if not weaknesses:
        weaknesses.append("暂无明显短板，注意定期复盘避免知识遗忘")
    if not strengths:
        strengths.append("已经开始积累学习记录，继续保持")

    suggestions.append("建议每天固定时段学习，形成稳定节奏")
    if low:
        suggestions.append(f"优先推进《{low[0]['title']}》，缩小进度差距")
    suggestions.append("可结合 AI 答疑解决卡点，再用作业批改检验掌握程度")

    summary = (
        f"{MOCK_TAG}{label}共学习 {total} 分钟，完成 {done} 个课时，"
        f"在学课程 {len(cps)} 门。"
        + ("整体进度健康，继续保持。"
           if not low and total >= 60
           else "建议合理安排时间，优先补上停滞课程。")
    )
    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": suggestions,
        "summary": summary,
    }


_INTERVIEW_BANK = {
    "AI算法": [
        "请解释过拟合与欠拟合的区别，以及常用的应对方法。",
        "说说你对 Transformer 注意力机制的理解。",
        "如果训练数据类别不均衡，你会怎么处理？",
        "请介绍一个你做过的机器学习项目，包括特征工程和模型选择。",
        "如何评估一个分类模型的好坏？除了准确率还有哪些指标？",
    ],
    "后端开发": [
        "请解释 RESTful API 的设计原则。",
        "数据库索引是如何加速查询的？什么场景下反而变慢？",
        "说说你对事务 ACID 的理解。",
        "高并发场景下如何设计一个接口限流方案？",
        "请介绍一次你排查线上接口性能问题的经历。",
    ],
    "前端开发": [
        "请解释 Vue/React 中虚拟 DOM 的作用。",
        "组件间通信有哪些方式？分别适用于什么场景？",
        "如何优化一个首屏加载很慢的页面？",
        "说说浏览器从输入 URL 到页面渲染的过程。",
        "请介绍一个你负责过的前端项目及遇到的最大难点。",
    ],
    "大数据": [
        "请对比 Hadoop MapReduce 与 Spark 的计算模型差异。",
        "数据倾斜是什么？在 Spark 中如何处理？",
        "说说你对数据仓库分层的理解。",
        "实时计算与离线计算的架构有何不同？",
        "请介绍一个你参与过的数据处理项目。",
    ],
    "运维": [
        "说说你对 CI/CD 流水线的理解。",
        "Kubernetes 中 Pod 和 Service 分别是什么？",
        "服务器 CPU 飙高，你的排查步骤是什么？",
        "如何设计一套监控告警体系？",
        "请介绍一次故障应急处理的经历。",
    ],
    "数据分析": [
        "常用的数据分析流程是怎样的？",
        "请解释 p 值与置信区间的含义。",
        "如何用 SQL 计算次日留存率？",
        "你会如何向业务方解释一个分析结论？",
        "介绍一个你用数据驱动业务决策的案例。",
    ],
    "物联网": [
        "MQTT 协议为什么适合物联网场景？",
        "说说嵌入式系统中中断与轮询的区别。",
        "设备接入平台时如何保障通信安全？",
        "请介绍一个你参与过的物联网项目。",
        "低功耗设备设计时需要考虑哪些因素？",
    ],
    "测试": [
        "测试用例设计有哪些常用方法？",
        "自动化测试适用于什么场景？如何选型框架？",
        "发现一个偶发 bug 你会怎么定位？",
        "请说说你对接口测试的理解。",
        "介绍一次你发现严重缺陷并推动修复的经历。",
    ],
}
_GENERIC_QUESTIONS = [
    "请做一下自我介绍，并说明你应聘该岗位的优势。",
    "你对这个岗位所需的核心技能有什么理解？",
    "遇到不会的问题时，你通常如何解决？",
    "请介绍一个最能体现你能力的项目经历。",
    "你未来三年的职业规划是什么？",
]


def interview_questions(job: Any) -> list[str]:
    bank = _INTERVIEW_BANK.get(getattr(job, "category", ""), [])
    qs = list(bank[:4]) + _GENERIC_QUESTIONS[: 5 - min(4, len(bank))]
    return qs[:5]


def evaluate_interview(job: Any, answers: list[dict]) -> dict:
    per_question = []
    scores = []
    title = getattr(job, "title", "该岗位")
    for item in answers:
        q = item.get("question", "")
        a = (item.get("answer") or "").strip()
        n = len(a)
        if n == 0:
            s, comment = 0, "未作答，面试中空白回答会严重影响评价。"
        elif n < 30:
            s, comment = 40, "回答过于简短，建议从「概念—原理—实践」三方面展开。"
        elif n < 100:
            s, comment = 65, "覆盖了基本要点，但缺少具体案例或数据支撑。"
        elif n < 300:
            s, comment = 80, "回答较为完整，若能加入个人项目实例会更有说服力。"
        else:
            s, comment = 92, "回答详实、有结构，体现了较好的专业深度。"
        # 关键词加分：命中岗位关键词
        kws = _job_domain_keys(job)
        if any(k in a.lower() for k in kws) and s:
            s = min(100, s + 5)
            comment += " 回答中体现了岗位相关的专业术语，加分。"
        scores.append(s)
        per_question.append(
            {"question": q, "answer": a, "score": s, "comment": comment}
        )
    score = round(sum(scores) / len(scores), 1) if scores else 0
    level = (
        "表现优秀，具备岗位要求的扎实基础"
        if score >= 85
        else "表现良好，部分回答可更深入"
        if score >= 65
        else "基础有待加强，建议系统学习岗位核心知识"
    )
    evaluation = (
        f"{MOCK_TAG}本次「{title}」AI 面试综合得分 {score} 分。{level}。"
        "建议复盘每道题的点评，薄弱处结合站内课程补强后再次尝试。"
    )
    return {"score": score, "evaluation": evaluation, "per_question": per_question}
