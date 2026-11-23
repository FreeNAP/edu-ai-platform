"""种子数据：仅在空库（无用户）时执行，重复启动幂等。

按 API契约.md 最后一节：
- admin/admin123、teacher/teacher123、student/student123
- 讲师 >=6；课程 >=18（三大模块各 >=6，覆盖 AI/大数据/云计算/前端/后端/物联网，免费付费混合）
- 职位 >=10
- student 预置 2 门报名+部分课时进度、若干评论、1 订单、1 申请、2 通知、
  1 条已完成 AI 面试、1 条学习路径、收藏 1 门课程
- 每个课时 content 为 2~4 段与标题相关的讲解；课程 cover 为空（不用 emoji）
"""
import json
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .models import (
    Answer,
    Application,
    Chapter,
    Comment,
    Course,
    Enrollment,
    Favorite,
    Interview,
    Job,
    JobFavorite,
    Lecturer,
    Lesson,
    LearningPlan,
    LessonProgress,
    Notification,
    Order,
    Question,
    User,
)
from .security import hash_password
from .seed_content import lesson_content
from .serializers import normalize_per_question
from .services import mock_engine
from .services.plans import estimate_due_date

_LECTURERS = [
    ("张明远", "AI 方向教授", "深耕机器学习与深度学习教学十余年，主持多项国家级 AI 课题。"),
    ("李思颖", "大数据技术专家", "前头部互联网公司大数据平台负责人，专注分布式计算与数据治理。"),
    ("王浩然", "云计算架构师", "云原生架构师，主导过多个大型上云与容器化改造项目。"),
    ("陈雨薇", "前端技术专家", "前端框架与工程化专家，开源社区活跃贡献者。"),
    ("刘子昂", "后端架构师", "高并发服务端架构师，熟悉 Java/Python 微服务体系。"),
    ("赵天宇", "物联网专家", "物联网通信与嵌入式系统专家，智能硬件领域资深从业者。"),
    ("孙佳琪", "华为认证讲师", "华为 ICT 认证资深讲师，累计培养认证学员 3000+。"),
]

# (title, category, tech_domain, difficulty, is_free, price, lecturer_idx, cover(空=前端默认封面), brief)
_COURSES = [
    # ---- 理论课程 theory x6 ----
    ("人工智能导论", "theory", "AI", "入门", True, 0, 0, "",
     "系统介绍人工智能的发展脉络、核心概念与典型应用，零基础建立 AI 知识框架。"),
    ("大数据技术原理", "theory", "大数据", "初级", True, 0, 1, "",
     "讲解 Hadoop、Spark 等大数据技术的底层原理与生态系统，理解海量数据处理思想。"),
    ("云计算基础架构", "theory", "云计算", "入门", False, 99, 2, "",
     "覆盖 IaaS/PaaS/SaaS 服务模式、虚拟化与容器基础，构建云计算整体认知。"),
    ("Vue.js 前端开发基础", "theory", "前端", "入门", True, 0, 3, "",
     "从模板语法到组件化开发，循序渐进入门 Vue3 与前端工程化思想。"),
    ("Python 后端开发进阶", "theory", "后端", "中级", False, 129, 4, "",
     "深入 Python 服务端开发：Web 框架、ORM、异步编程与接口设计最佳实践。"),
    ("物联网通信协议详解", "theory", "物联网", "中级", False, 89, 5, "",
     "详解 MQTT、CoAP、LoRaWAN 等主流物联网协议的原理与选型。"),
    # ---- 实训课程 practice x6 ----
    ("机器学习实战：从数据到模型", "practice", "AI", "中级", False, 199, 0, "",
     "以真实数据集完成特征工程、模型训练与调优全流程，产出可展示的实战项目。"),
    ("Spark 大数据处理实训", "practice", "大数据", "中级", False, 179, 1, "",
     "基于 Spark 完成批处理、流处理与 SQL 分析实战，掌握企业级数据处理能力。"),
    ("云原生应用部署实战", "practice", "云计算", "高级", False, 229, 2, "",
     "Docker + Kubernetes 从镜像构建到集群编排的完整云原生部署演练。"),
    ("前端工程化项目实战", "practice", "前端", "中级", True, 0, 3, "",
     "以真实业务场景完成组件库、状态管理与构建优化，沉淀工程化经验。"),
    ("Django 电商平台后端实战", "practice", "后端", "中级", False, 159, 4, "",
     "从 0 搭建电商后端：商品、订单、支付模拟与权限体系，覆盖典型业务开发。"),
    ("智能家居物联网实训", "practice", "物联网", "初级", True, 0, 5, "",
     "模拟智能家居场景，完成设备接入、数据采集与远程控制全链路实验。"),
    # ---- 认证课程 certification x6 ----
    ("HCIA-AI 认证精讲", "certification", "AI", "初级", False, 299, 6, "",
     "对标 HCIA-AI 考纲逐章精讲，配套真题解析与考前冲刺串讲。"),
    ("大数据分析师认证备考", "certification", "大数据", "中级", False, 259, 1, "",
     "覆盖认证全部考点：数据采集、清洗、建模分析与可视化报告撰写。"),
    ("HCIA-Cloud 云计算认证", "certification", "云计算", "初级", False, 299, 6, "",
     "围绕华为云认证体系，讲解云服务、网络、存储与运维核心考点。"),
    ("前端开发工程师认证", "certification", "前端", "初级", False, 199, 3, "",
     "覆盖 HTML/CSS/JS 与主流框架考点，配大量模拟题与错题精讲。"),
    ("Java 后端开发认证", "certification", "后端", "中级", False, 249, 4, "",
     "对标后端工程师认证，串讲 JVM、并发、Spring 生态与数据库考点。"),
    ("物联网工程师认证", "certification", "物联网", "中级", False, 219, 5, "",
     "覆盖物联网架构、协议、边缘计算与安全等认证核心内容。"),
]

_CHAPTER_TPL = [
    "基础知识与环境准备",
    "核心概念详解",
    "关键技术深入",
    "综合案例分析",
    "前沿拓展与课程总结",
]
_LESSON_TPL = [
    "导学与知识点概览",
    "核心概念精讲",
    "动手实践演练",
    "典型案例剖析",
    "习题与巩固",
    "本章小结",
]
_LESSON_KINDS = ["video", "video", "article", "video", "lab", "article"]

# (title, company, city, category, salary, tags, headcount, description, requirements)
_JOBS = [
    ("AI 算法工程师", "前沿智能", "深圳", "AI算法", "20-35K·14薪",
     "机器学习,深度学习,Python", 3,
     "负责推荐/CV 场景的算法研发与模型优化，参与算法工程化落地。",
     "熟悉常见机器学习算法；熟练使用 Python 与主流深度学习框架；有项目或竞赛经验优先。"),
    ("Python 后端开发工程师", "码上科技", "杭州", "后端开发", "15-25K",
     "Python,Django,MySQL", 5,
     "参与业务后端接口设计与开发，保障服务稳定性与性能。",
     "熟悉 Django/Flask 等框架；掌握 MySQL、Redis；了解 RESTful 设计。"),
    ("前端开发工程师", "视界互联", "北京", "前端开发", "14-22K",
     "Vue3,TypeScript,工程化", 4,
     "负责 C 端产品前端页面开发与组件库建设，优化用户体验。",
     "熟悉 Vue3 全家桶；了解前端工程化与性能优化；有移动端适配经验优先。"),
    ("大数据开发工程师", "星图数据", "上海", "大数据", "18-30K",
     "Spark,Hadoop,数仓", 3,
     "负责数据平台开发与数仓建模，支撑业务数据分析需求。",
     "熟悉 Spark/Flink；掌握 SQL 与数仓分层建模；了解 Kafka 者优先。"),
    ("云计算运维工程师", "云启科技", "广州", "运维", "12-20K",
     "Linux,K8s,监控", 3,
     "负责云上基础设施运维、监控告警与故障应急处理。",
     "熟悉 Linux 与 Shell；了解 Docker/Kubernetes；具备网络基础知识。"),
    ("数据分析师", "数海信息", "北京", "数据分析", "12-18K",
     "SQL,Excel,可视化", 2,
     "面向业务输出数据分析报告，驱动产品与运营决策。",
     "熟练使用 SQL 与 BI 工具；具备统计学基础；表达能力强。"),
    ("物联网嵌入式工程师", "物联智慧", "深圳", "物联网", "15-25K",
     "C,嵌入式,MQTT", 2,
     "负责智能终端设备固件开发与云平台接入。",
     "熟悉 C/C++ 与常见 MCU；了解 MQTT 等物联网协议；有硬件调试经验。"),
    ("测试工程师", "轻舟软件", "成都", "测试", "10-16K",
     "功能测试,自动化,接口测试", 4,
     "负责产品测试计划制定、用例设计与缺陷跟踪。",
     "熟悉测试理论与方法；了解 Python/自动化测试框架者优先。"),
    ("Java 后端工程师", "蓝海网络", "杭州", "后端开发", "16-26K",
     "Java,Spring,微服务", 4,
     "参与微服务系统设计与核心模块开发。",
     "熟悉 Spring Boot/Cloud；掌握 JVM 调优与并发编程；了解分布式架构。"),
    ("大模型应用工程师", "智联云科技", "北京", "AI算法", "25-40K",
     "LLM,RAG,Prompt", 2,
     "负责大模型应用落地：RAG、Agent 与 Prompt 工程。",
     "了解主流大模型 API；熟悉 LangChain 等框架；有 AI 应用项目经验。"),
    ("DevOps 工程师", "云启科技", "上海", "运维", "18-28K",
     "CI/CD,K8s,自动化", 2,
     "建设 CI/CD 流水线与基础设施自动化，提升交付效率。",
     "熟悉 Jenkins/GitLab CI；掌握容器与编排技术；有运维开发经验。"),
    ("数据可视化工程师", "星图数据", "深圳", "数据分析", "14-22K",
     "ECharts,可视化,前端", 2,
     "负责数据大屏与可视化报表的设计开发。",
     "熟悉 ECharts/D3；具备前端基础；对数据呈现有审美追求。"),
]


def _seed_courses(db: Session, lecturers: list[Lecturer]) -> list[Course]:
    courses: list[Course] = []
    base_time = datetime.now() - timedelta(days=60)
    for idx, (title, cat, domain, diff, free, price, li, cover, brief) in enumerate(_COURSES):
        course = Course(
            title=title, cover=cover, category=cat, tech_domain=domain,
            difficulty=diff, is_free=free, price=price,
            students_count=400 + (idx * 173) % 3600,
            rating=round(4.1 + (idx % 8) * 0.1, 1),
            lecturer_id=lecturers[li].id, brief=brief, status="on",
            created_at=base_time + timedelta(days=idx * 2),
        )
        db.add(course)
        db.flush()
        # 3-5 章，每章 3-6 课时（确定性生成）
        n_ch = 3 + (idx % 3)
        for ci in range(n_ch):
            chapter = Chapter(
                course_id=course.id,
                title=f"第{ci + 1}章 {_CHAPTER_TPL[ci % len(_CHAPTER_TPL)]}",
                order_index=ci,
            )
            db.add(chapter)
            db.flush()
            n_ls = 3 + ((idx + ci) % 4)
            for li2 in range(n_ls):
                minutes = 8 + ((idx * 5 + ci * 7 + li2 * 3) % 20)
                tpl = _LESSON_TPL[(ci + li2) % len(_LESSON_TPL)]
                db.add(Lesson(
                    chapter_id=chapter.id,
                    title=f"{li2 + 1}.{tpl}",
                    content=lesson_content(
                        idx, title, _CHAPTER_TPL[ci % len(_CHAPTER_TPL)], ci, tpl
                    ),
                    duration=f"{minutes}分钟",
                    duration_minutes=minutes,
                    kind=_LESSON_KINDS[(ci + li2) % len(_LESSON_KINDS)],
                    order_index=li2,
                ))
        courses.append(course)
    return courses


def _complete_lessons(db: Session, user_id: int, course_id: int,
                      chapter_ids: list[int], count: int, seconds: int) -> int:
    """为用户标记 course 内前 count 个课时完成，返回总秒数。"""
    lessons = (
        db.query(Lesson)
        .join(Chapter, Lesson.chapter_id == Chapter.id)
        .filter(Chapter.course_id == course_id)
        .order_by(Chapter.order_index, Lesson.order_index)
        .limit(count)
        .all()
    )
    total = 0
    for ls in lessons:
        sec = seconds + (ls.id % 3) * 60
        total += sec
        db.add(LessonProgress(
            user_id=user_id, lesson_id=ls.id, course_id=course_id,
            study_seconds=sec,
            completed_at=datetime.now() - timedelta(hours=ls.id % 72),
        ))
    return total


def seed_if_empty(db: Session) -> None:
    if db.query(User).count() > 0:
        return

    # ---- 账号 ----
    admin = User(username="admin", email="admin@edu.local", nickname="平台管理员",
                 role="admin", password_hash=hash_password("admin123"), major="")
    teacher = User(username="teacher", email="teacher@edu.local", nickname="示例教师",
                   role="teacher", password_hash=hash_password("teacher123"), major="计算机科学")
    student = User(username="student", email="student@edu.local", nickname="示例学员",
                   role="student", password_hash=hash_password("student123"), major="软件工程")
    demo1 = User(username="lily", email="lily@edu.local", nickname="莉莉",
                 role="student", password_hash=hash_password("lily123456"), major="数据科学")
    demo2 = User(username="tom", email="tom@edu.local", nickname="汤姆",
                 role="student", password_hash=hash_password("tom123456"), major="网络工程")
    db.add_all([admin, teacher, student, demo1, demo2])

    # ---- 讲师 ----
    lecturers = [Lecturer(name=n, title=t, bio=b, avatar="") for n, t, b in _LECTURERS]
    db.add_all(lecturers)
    db.flush()

    # ---- 课程/章节/课时 ----
    courses = _seed_courses(db, lecturers)

    # ---- 职位 ----
    base_time = datetime.now() - timedelta(days=30)
    jobs = []
    for idx, (t, co, city, cat, sal, tags, hc, desc, req) in enumerate(_JOBS):
        j = Job(title=t, company=co, city=city, category=cat, salary=sal, tags=tags,
                headcount=hc, description=desc, requirements=req, status="on",
                created_at=base_time + timedelta(days=idx))
        db.add(j)
        jobs.append(j)
    db.flush()

    # ---- student 预置：报名 2 门 + 部分进度 ----
    c1, c2 = courses[0], courses[6]  # 人工智能导论（免费）/ 机器学习实战（付费）
    e1 = Enrollment(user_id=student.id, course_id=c1.id, created_at=datetime.now() - timedelta(days=10))
    e2 = Enrollment(user_id=student.id, course_id=c2.id, created_at=datetime.now() - timedelta(days=5))
    db.add_all([e1, e2])
    db.flush()

    def _course_lesson_total(cid: int) -> int:
        return (
            db.query(Lesson).join(Chapter, Lesson.chapter_id == Chapter.id)
            .filter(Chapter.course_id == cid).count()
        )

    done1 = _complete_lessons(db, student.id, c1.id, [], 6, 900)
    done2 = _complete_lessons(db, student.id, c2.id, [], 3, 1200)
    e1.study_seconds = done1
    e1.progress = round(6 * 100 / _course_lesson_total(c1.id))
    e2.study_seconds = done2
    e2.progress = round(3 * 100 / _course_lesson_total(c2.id))
    c1.students_count += 1
    c2.students_count += 1

    # ---- 付费订单（课程 c2）----
    db.add(Order(
        user_id=student.id, course_id=c2.id,
        order_no="EDU" + datetime.now().strftime("%Y%m%d") + "000001",
        amount=c2.price, status="paid",
        created_at=datetime.now() - timedelta(days=5),
        paid_at=datetime.now() - timedelta(days=5),
    ))

    # ---- 评论 ----
    comments = [
        Comment(user_id=student.id, course_id=c1.id, rating=5,
                content="讲解清晰，入门 AI 非常合适，章节目录安排合理。"),
        Comment(user_id=student.id, course_id=c2.id, rating=4,
                content="实战环节很有收获，个别实验步骤需要更详细的说明。"),
        Comment(user_id=demo1.id, course_id=c1.id, rating=5,
                content="零基础也能跟上，老师案例很多，推荐！"),
        Comment(user_id=demo2.id, course_id=courses[3].id, rating=4,
                content="Vue 入门讲得不错，期待后续进阶内容。"),
        Comment(user_id=demo1.id, course_id=courses[9].id, rating=5,
                content="免费的实战课质量超出预期，项目驱动学习很有效。"),
    ]
    db.add_all(comments)

    # ---- 申请 ----
    db.add(Application(
        user_id=student.id, job_id=jobs[2].id,
        message="我是软件工程专业学生，已完成前端工程化实战课程，希望获得实习机会。",
        status="pending", created_at=datetime.now() - timedelta(days=2),
    ))
    db.add(JobFavorite(user_id=student.id, job_id=jobs[0].id))
    db.add(Favorite(user_id=student.id, course_id=c1.id))

    # ---- 预置 1 条已完成的 AI 面试 ----
    iv_job = jobs[2]  # 前端开发工程师
    questions = mock_engine.interview_questions(iv_job)
    answers = [
        {
            "question": q,
            "answer": "在课程项目里我负责前端部分，用 Vue3 组合式 API 拆分组件，"
                      "通过 Pinia 管理登录状态，接口统一封装并处理异常。"
                      "上线前做了打包体积分析，把大依赖改为按需引入，首屏加载时间明显缩短。",
        }
        for q in questions
    ]
    raw = mock_engine.evaluate_interview(iv_job, answers)
    per_question = normalize_per_question(raw.get("per_question"), answers)
    result = {"score": raw["score"], "evaluation": raw["evaluation"], "per_question": per_question}
    db.add(Interview(
        user_id=student.id, job_id=iv_job.id,
        questions=json.dumps(questions, ensure_ascii=False),
        answers=json.dumps(answers, ensure_ascii=False),
        per_question=json.dumps(per_question, ensure_ascii=False),
        result=json.dumps(result, ensure_ascii=False),
        score=raw["score"], status="done",
        created_at=datetime.now() - timedelta(days=3),
    ))

    # ---- 预置 1 条学习路径（未到期）----
    plan_created = datetime.now() - timedelta(days=7)
    plan = mock_engine.learning_path("前端开发工程师", 8, courses)
    db.add(LearningPlan(
        user_id=student.id, goal="前端开发工程师", hours_per_week=8,
        plan_json=json.dumps(plan, ensure_ascii=False),
        created_at=plan_created,
        due_date=estimate_due_date(plan, plan_created),
        reminded=False,
    ))

    # ---- 通知 ----
    db.add_all([
        Notification(user_id=student.id, type="study", title="学习计划提醒",
                     content="你的《机器学习实战：从数据到模型》本周学习计划还有课时未完成，继续加油！"),
        Notification(user_id=student.id, type="course", title="收藏课程更新",
                     content="你报名的《人工智能导论》新增了章节内容，快去学习吧。"),
    ])

    # ---- 社区问答 ----
    q1 = Question(user_id=demo1.id, title="学习机器学习需要先补哪些数学基础？",
                  content="准备开始学机器学习，线性代数和概率论要学到什么程度才够用？",
                  views=56, answers_count=1)
    q2 = Question(user_id=demo2.id, title="Vue3 中 ref 和 reactive 怎么选择？",
                  content="写组合式 API 时经常纠结用 ref 还是 reactive，有没有简单原则？",
                  views=88, answers_count=1)
    q3 = Question(user_id=student.id, title="Spark 数据倾斜一般怎么处理？",
                  content="跑作业时个别 task 特别慢，怀疑是数据倾斜，求排查思路。",
                  views=34, answers_count=0)
    db.add_all([q1, q2, q3])
    db.flush()
    db.add_all([
        Answer(question_id=q1.id, user_id=teacher.id,
               content="重点是线性代数（矩阵运算）与概率统计（分布、期望、贝叶斯），微积分了解梯度即可。边学算法边补数学效率最高。"),
        Answer(question_id=q2.id, user_id=demo1.id,
               content="简单原则：基本类型用 ref；对象想整体替换用 ref，想直接操作属性用 reactive。"),
    ])

    db.commit()
