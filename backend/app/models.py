"""SQLAlchemy 数据模型（表结构见 API契约.md 数据模型约定）。"""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=False)
    nickname = Column(String(64), default="")
    avatar = Column(String(255), default="")
    major = Column(String(64), default="")
    role = Column(String(16), default="student", index=True)  # student|teacher|admin
    status = Column(String(16), default="active")  # active|disabled
    password_hash = Column(String(255), nullable=False)
    bio = Column(Text, default="")
    resume_url = Column(String(255), default="")  # 简历文件（/uploads/...）
    token_version = Column(Integer, default=0, nullable=False)  # 改密/禁用时 +1，使旧令牌失效
    failed_logins = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class Lecturer(Base):
    __tablename__ = "lecturers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False)
    title = Column(String(64), default="")
    bio = Column(Text, default="")
    avatar = Column(String(255), default="")


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(128), index=True, nullable=False)
    cover = Column(String(255), default="")  # 封面 url，可为空
    category = Column(String(32), index=True, default="theory")  # theory|practice|certification
    tech_domain = Column(String(32), index=True, default="")
    difficulty = Column(String(16), default="入门")  # 入门|初级|中级|高级
    is_free = Column(Boolean, default=True)
    price = Column(Float, default=0)
    students_count = Column(Integer, default=0)
    rating = Column(Float, default=0)
    lecturer_id = Column(Integer, ForeignKey("lecturers.id"))
    teacher_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=True)  # 负责该课程的教师账号
    brief = Column(Text, default="")
    status = Column(String(8), index=True, default="on")  # on|off
    created_at = Column(DateTime, default=datetime.now, index=True)

    lecturer = relationship("Lecturer")


class Chapter(Base):
    __tablename__ = "chapters"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), index=True)
    title = Column(String(128), default="")
    order_index = Column(Integer, default=0)


class Lesson(Base):
    __tablename__ = "lessons"
    id = Column(Integer, primary_key=True, index=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), index=True)
    title = Column(String(128), default="")
    duration = Column(String(16), default="10分钟")
    duration_minutes = Column(Integer, default=10)
    kind = Column(String(16), default="video")  # video|article|lab
    content = Column(Text, default="")  # 课时正文（讲解文字）
    video_url = Column(String(255), default="")  # 视频地址（上传文件或外链）
    order_index = Column(Integer, default=0)


class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), index=True)
    progress = Column(Integer, default=0)  # 0-100
    study_seconds = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    __table_args__ = (UniqueConstraint("user_id", "course_id", name="uq_enroll"),)


class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), index=True)
    study_seconds = Column(Integer, default=0)
    completed_at = Column(DateTime, default=datetime.now)
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_lesson_progress"),)


class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), index=True)
    created_at = Column(DateTime, default=datetime.now)
    __table_args__ = (UniqueConstraint("user_id", "course_id", name="uq_fav"),)


class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), index=True)
    rating = Column(Integer, default=5)
    content = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User")


class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(128), index=True)
    company = Column(String(128), index=True)
    city = Column(String(32), index=True)
    category = Column(String(32), index=True)
    salary = Column(String(32), default="")
    tags = Column(String(255), default="")  # 逗号分隔
    description = Column(Text, default="")
    requirements = Column(Text, default="")
    headcount = Column(Integer, default=1)
    status = Column(String(8), default="on", index=True)  # on|off
    created_at = Column(DateTime, default=datetime.now)


class JobFavorite(Base):
    __tablename__ = "job_favorites"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), index=True)
    created_at = Column(DateTime, default=datetime.now)
    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_job_fav"),)


class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), index=True)
    message = Column(Text, default="")
    resume_url = Column(String(255), default="")  # 投递时附带的简历快照
    status = Column(String(16), default="pending", index=True)  # pending|viewed|accepted|rejected
    created_at = Column(DateTime, default=datetime.now)
    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_application"),)


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), index=True)
    order_no = Column(String(40), unique=True, index=True)
    amount = Column(Float, default=0)
    status = Column(String(16), default="pending", index=True)  # pending|paid|cancelled
    created_at = Column(DateTime, default=datetime.now)
    paid_at = Column(DateTime, nullable=True)

    course = relationship("Course")


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    title = Column(String(128), default="新会话")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), index=True)
    role = Column(String(16), default="user")  # user|assistant
    content = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)


class LearningPlan(Base):
    __tablename__ = "learning_plans"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    goal = Column(String(128), default="")
    hours_per_week = Column(Integer, nullable=True)
    plan_json = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    due_date = Column(DateTime, nullable=True)  # 按各阶段时长估算的完成日期
    reminded = Column(Boolean, default=False)  # 是否已发送到期提醒


class Interview(Base):
    __tablename__ = "interviews"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), index=True)
    questions = Column(Text, default="[]")  # JSON list[str]
    answers = Column(Text, default="[]")
    per_question = Column(Text, default="")  # JSON list[{question,answer,score,comment}]
    result = Column(Text, default="")  # JSON 评估结果（score/evaluation/per_question 全量）
    score = Column(Float, default=0)
    status = Column(String(16), default="pending")  # pending|done（旧数据可能为 ongoing，按 pending 处理）
    created_at = Column(DateTime, default=datetime.now)


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    type = Column(String(32), default="system")  # system|course|study|job|application|order|community
    title = Column(String(128), default="")
    content = Column(Text, default="")
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)


class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    title = Column(String(200), index=True)
    content = Column(Text, default="")
    views = Column(Integer, default=0)
    answers_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User")


class Answer(Base):
    __tablename__ = "answers"
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    content = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User")


class PasswordResetCode(Base):
    """找回密码邮件验证码（只存哈希）。"""
    __tablename__ = "password_reset_codes"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    code_hash = Column(String(128), nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now)


class AuditLog(Base):
    """管理员与教师的关键操作审计。"""
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    actor_name = Column(String(64), default="")
    action = Column(String(64), index=True, nullable=False)  # 如 course.update
    target_type = Column(String(32), default="")
    target_id = Column(String(32), default="")
    detail = Column(Text, default="")
    ip = Column(String(64), default="")
    created_at = Column(DateTime, default=datetime.now, index=True)


class AiUsage(Base):
    """每用户每日 AI 调用计数（配额）。"""
    __tablename__ = "ai_usage"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    day = Column(String(10), nullable=False)  # YYYY-MM-DD
    count = Column(Integer, default=0, nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "day", name="uq_ai_usage_day"),)


class Quiz(Base):
    """测验/考试：挂在课时（lesson_id）上为课时测验，挂在课程上（lesson_id 为空）为结业/认证考试。"""
    __tablename__ = "quizzes"
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), index=True, nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), index=True, nullable=True)
    title = Column(String(128), nullable=False)
    kind = Column(String(16), default="quiz")  # quiz|exam
    pass_score = Column(Integer, default=60)
    time_limit_minutes = Column(Integer, default=0)  # 0 表示不限时
    max_attempts = Column(Integer, default=0)  # 0 表示不限次数
    created_at = Column(DateTime, default=datetime.now)

    questions = relationship("QuizQuestion", order_by="QuizQuestion.order_index", cascade="all, delete-orphan")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), index=True, nullable=False)
    kind = Column(String(16), default="single")  # single|multiple|judge
    stem = Column(Text, nullable=False)
    options = Column(Text, default="[]")  # JSON 数组
    answer = Column(String(64), nullable=False)  # 单选 "B"，多选 "AC"，判断 "T"/"F"
    explanation = Column(Text, default="")
    score = Column(Integer, default=10)
    order_index = Column(Integer, default=0)


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    answers = Column(Text, default="{}")  # JSON {question_id: "A"}
    score = Column(Integer, default=0)
    total = Column(Integer, default=0)
    passed = Column(Boolean, default=False)
    started_at = Column(DateTime, default=datetime.now)
    submitted_at = Column(DateTime, nullable=True)


class Certificate(Base):
    """通过结业/认证考试后颁发的证书。"""
    __tablename__ = "certificates"
    id = Column(Integer, primary_key=True)
    cert_no = Column(String(32), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), index=True, nullable=False)
    score = Column(Integer, default=0)
    issued_at = Column(DateTime, default=datetime.now)
    __table_args__ = (UniqueConstraint("user_id", "course_id", name="uq_certificate"),)
