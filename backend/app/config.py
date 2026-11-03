from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # 后端项目的根路径


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_EXPIRE_HOURS: int = 24
    JWT_ALGORITHM: str = "HS256"

    # DeepSeek / OpenAI 兼容接口配置
    LLM_API_KEY: str | None = None
    LLM_BASE_URL: str = "https://api.deepseek.com"
    LLM_MODEL: str = "deepseek-chat"

    # Embedding（默认硅基流动 bge-m3）
    EMBEDDING_API_KEY: str | None = None
    EMBEDDING_BASE_URL: str = "https://api.siliconflow.cn/v1"
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_DIM: int = 1024

    # 可选：启用独立 MCP 工具服务
    MCP_SERVER_URL: str | None = None

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8"
    )


settings = Settings()

UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100M

# 课程资料文件目录与限制
COURSE_DOC_DIR = UPLOAD_DIR / "course_docs"
COURSE_DOC_DIR.mkdir(parents=True, exist_ok=True)
MAX_COURSE_DOC_SIZE = 20 * 1024 * 1024
COURSE_DOC_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}

# 本地 Chroma 持久化目录
CHROMA_DIR = BASE_DIR / "chroma_data"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)


ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".zip",
}
