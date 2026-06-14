"""
配置管理模块
从环境变量或 .env 文件加载系统配置
"""

import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class Settings:
    # OpenAI 配置
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    # 模型配置
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "openai")  # openai 或 huggingface

    # Rerank 配置
    RERANK_ENABLED: bool = os.getenv("RERANK_ENABLED", "false").lower() == "true"
    RERANK_MODEL: str = os.getenv("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
    RERANK_TOP_K: int = int(os.getenv("RERANK_TOP_K", "4"))

    # 混合检索配置
    HYBRID_SEARCH_ENABLED: bool = os.getenv("HYBRID_SEARCH_ENABLED", "true").lower() == "true"
    BM25_WEIGHT: float = float(os.getenv("BM25_WEIGHT", "0.3"))
    VECTOR_WEIGHT: float = float(os.getenv("VECTOR_WEIGHT", "0.7"))

    # JWT 配置
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-me")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_HOURS: int = int(os.getenv("JWT_EXPIRE_HOURS", "24"))

    # 数据库配置
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/rag_knowledge.db")

    # 文件上传配置
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "data/uploads")
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    ALLOWED_EXTENSIONS: set = {".pdf", ".txt", ".md", ".markdown", ".docx", ".xlsx", ".pptx", ".html", ".csv"}

    # RAG 参数
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "4"))
    RETRIEVAL_SCORE_THRESHOLD: float = float(os.getenv("RETRIEVAL_SCORE_THRESHOLD", "0.0"))

    # ChromaDB 持久化路径
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "data/chroma_db")

    # 管理员默认账户
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")


settings = Settings()
