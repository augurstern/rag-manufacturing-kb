"""
全局配置管理 —— 从 .env 文件读取所有配置项。
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """应用配置"""

    # DeepSeek API
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

    # Embedding
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "deepseek")

    # 服务端口
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    FRONTEND_PORT: int = int(os.getenv("FRONTEND_PORT", "8501"))

    # 数据库
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "./data/rag_system.db")

    # ChromaDB
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

    # 日志
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # 文件上传
    MAX_UPLOAD_SIZE_MB: int = 20
    ALLOWED_FILE_TYPES: set = {".pdf", ".docx", ".txt"}

    @property
    def api_key_configured(self) -> bool:
        """检查 DeepSeek API Key 是否已配置"""
        return bool(self.DEEPSEEK_API_KEY and self.DEEPSEEK_API_KEY != "your-deepseek-api-key-here")


settings = Settings()
