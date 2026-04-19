from typing import List

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 项目信息
    PROJECT_NAME: str = "Solon AI API"
    VERSION: str = "0.1.0"

    # API配置
    API_V1_PREFIX: str = "/api/v1"

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://*.vercel.app",
    ]

    # 数据库配置（使用 SQLite 本地测试）
    DATABASE_URL: str = "sqlite+aiosqlite:///./solon_ai.db"

    # Redis配置
    REDIS_URL: str = "redis://localhost:6379"

    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Solana配置
    SOLANA_RPC_URL: str = "https://api.devnet.solana.com"
    ALCHEMY_API_KEY: str = ""

    # AI模型配置
    DOUBAO_API_KEY: str = ""
    DOUBAO_API_URL: str = "https://ark.cn-beijing.volces.com/api/v3"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
