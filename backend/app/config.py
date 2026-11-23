"""环境变量与全局配置读取。"""
import os

# 项目目录（backend/）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# JWT 密钥，生产环境应通过环境变量覆盖
DEFAULT_SECRET_KEY = "edu-ai-platform-dev-secret-key"
SECRET_KEY = os.getenv("SECRET_KEY", DEFAULT_SECRET_KEY)
# JWT 有效期：7 天
ACCESS_TOKEN_EXPIRE_DAYS = 7
JWT_ALGORITHM = "HS256"

# 数据库：默认 SQLite，可通过 DATABASE_URL 切换 MySQL 等
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///" + os.path.join(BASE_DIR, "edu_platform.db").replace("\\", "/"),
)

# AI 大模型配置（OpenAI 兼容接口）
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.deepseek.com")
AI_MODEL = os.getenv("AI_MODEL", "deepseek-chat")
