"""
Solon AI - 配置管理

读取 .env 文件中的配置，统一管理所有 AI 服务的配置项。
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


@dataclass
class LLMConfig:
    """大模型配置"""

    provider: str = os.getenv("LLM_PROVIDER", "deepseek")
    api_key: str = os.getenv("LLM_API_KEY", "")
    base_url: str = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
    model: str = os.getenv("LLM_MODEL", "deepseek-chat")
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "4096"))


@dataclass
class VectorDBConfig:
    """向量数据库配置"""

    db_type: str = os.getenv("VECTOR_DB_TYPE", "chroma")
    chroma_persist_dir: str = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")


# 全局配置实例
llm_config = LLMConfig()
vector_db_config = VectorDBConfig()
