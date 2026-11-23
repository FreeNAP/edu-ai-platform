"""Pydantic 请求体模型（含长度上限，超限返回 422 统一错误格式）。"""
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---- 认证与用户 ----
class RegisterIn(BaseModel):
    username: str = Field(max_length=32)
    email: str = Field(max_length=128)
    password: str = Field(max_length=128)
    nickname: Optional[str] = Field(None, max_length=32)


class LoginIn(BaseModel):
    username: str = Field(max_length=128)
    password: str = Field(max_length=128)


class ForgotPasswordIn(BaseModel):
    email: str = Field(max_length=128)


class ResetPasswordIn(BaseModel):
    email: str = Field(max_length=128)
    code: str = Field(min_length=4, max_length=12)
    new_password: str = Field(max_length=128)


class RefreshIn(BaseModel):
    refresh_token: str = Field(max_length=2048)


class ProfileIn(BaseModel):
    nickname: Optional[str] = Field(None, max_length=32)
    avatar: Optional[str] = Field(None, max_length=255)
    major: Optional[str] = Field(None, max_length=64)
    bio: Optional[str] = Field(None, max_length=500)
    resume_url: Optional[str] = Field(None, max_length=255)


class ChangePasswordIn(BaseModel):
    old_password: str = Field(max_length=128)
    new_password: str = Field(max_length=128)


# ---- 课程 ----
class CommentIn(BaseModel):
    rating: int
    content: str = Field(max_length=1000)


class LessonCompleteIn(BaseModel):
    study_seconds: int = 0


# ---- 职位 ----
class ApplyIn(BaseModel):
    message: Optional[str] = Field(None, max_length=1000)
    resume_url: Optional[str] = Field(None, max_length=255)


# ---- AI ----
class ChatIn(BaseModel):
    session_id: Optional[int] = None
    message: str = Field(max_length=4000)
    course_id: Optional[int] = None


class LearningPathIn(BaseModel):
    goal: str = Field(max_length=100)
    hours_per_week: Optional[int] = Field(None, ge=1, le=100)


class GradeIn(BaseModel):
    question: str = Field(max_length=2000)
    code: str = Field(max_length=20000)
    language: Optional[str] = Field("python", max_length=32)


class InterviewAnswerItem(BaseModel):
    question: str = Field("", max_length=1000)
    answer: str = Field("", max_length=5000)


class InterviewAnswerIn(BaseModel):
    answers: list[InterviewAnswerItem] = Field(max_length=20)


# ---- 社区 ----
class QuestionIn(BaseModel):
    title: str = Field(max_length=100)
    content: str = Field(max_length=5000)


class AnswerIn(BaseModel):
    content: str = Field(max_length=5000)


# ---- 后台 ----
class AdminUserIn(BaseModel):
    role: Optional[str] = None
    status: Optional[str] = None


class AdminUserCreateIn(BaseModel):
    username: str = Field(max_length=32)
    email: str = Field(max_length=128)
    password: str = Field(max_length=128)
    role: str = "student"
    nickname: Optional[str] = Field(None, max_length=32)


class AdminCourseIn(BaseModel):
    title: Optional[str] = Field(None, max_length=128)
    cover: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = None
    tech_domain: Optional[str] = Field(None, max_length=32)
    difficulty: Optional[str] = None
    is_free: Optional[bool] = None
    price: Optional[float] = Field(None, ge=0, le=100000)
    lecturer_id: Optional[int] = None
    teacher_id: Optional[int] = None
    brief: Optional[str] = Field(None, max_length=2000)
    status: Optional[str] = None


class OutlineLessonIn(BaseModel):
    id: Optional[int] = None
    title: str = Field(max_length=128)
    duration: Optional[str] = Field(None, max_length=16)
    kind: Optional[str] = "video"
    content: Optional[str] = Field("", max_length=20000)
    video_url: Optional[str] = Field("", max_length=255)

    @field_validator("duration", mode="before")
    @classmethod
    def _duration_str(cls, v):
        if isinstance(v, (int, float)):
            return f"{max(1, round(v / 60))}分钟"
        return v


class OutlineChapterIn(BaseModel):
    id: Optional[int] = None
    title: str = Field(max_length=128)
    lessons: list[OutlineLessonIn] = Field(default_factory=list, max_length=100)


class OutlineIn(BaseModel):
    """兼容 {chapters:[...]} 包裹写法；契约主写法是直接传数组。"""
    chapters: list[OutlineChapterIn] = Field(max_length=50)


class AdminLecturerIn(BaseModel):
    name: Optional[str] = Field(None, max_length=64)
    title: Optional[str] = Field(None, max_length=64)
    bio: Optional[str] = Field(None, max_length=2000)
    avatar: Optional[str] = Field(None, max_length=255)


class AdminJobIn(BaseModel):
    title: Optional[str] = Field(None, max_length=128)
    company: Optional[str] = Field(None, max_length=128)
    city: Optional[str] = Field(None, max_length=32)
    category: Optional[str] = Field(None, max_length=32)
    salary: Optional[str] = Field(None, max_length=32)
    tags: Optional[list[str]] = Field(None, max_length=20)
    description: Optional[str] = Field(None, max_length=5000)
    requirements: Optional[str] = Field(None, max_length=5000)
    headcount: Optional[int] = Field(None, ge=1, le=10000)
    status: Optional[str] = None


class AdminOrderIn(BaseModel):
    status: Optional[str] = None


class AdminApplicationIn(BaseModel):
    status: Optional[str] = None


class QuizQuestionIn(BaseModel):
    kind: str = Field("single", pattern="^(single|multiple|judge)$")
    stem: str = Field(min_length=1, max_length=2000)
    options: list[str] = Field(default_factory=list, max_length=8)
    answer: str = Field(min_length=1, max_length=8)
    explanation: Optional[str] = Field("", max_length=2000)
    score: int = Field(10, ge=1, le=100)


class QuizIn(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    kind: str = Field("quiz", pattern="^(quiz|exam)$")
    lesson_id: Optional[int] = None
    pass_score: int = Field(60, ge=1, le=100)
    time_limit_minutes: int = Field(0, ge=0, le=600)
    max_attempts: int = Field(0, ge=0, le=100)
    questions: list[QuizQuestionIn] = Field(default_factory=list, max_length=200)
