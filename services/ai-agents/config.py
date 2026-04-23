"""
Solon AI - 配置管理

读取 .env 文件中的配置，统一管理所有 AI 服务的配置项。
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent

# Load local AI service config first, then allow the API app config to fill in
# missing shared values during integrated local development. The API .env is
# allowed to override empty Docker Compose defaults such as DOUBAO_API_KEY="".
load_dotenv(CURRENT_DIR / ".env")
load_dotenv(PROJECT_ROOT / "apps" / "api" / ".env", override=True)


def _clean_env_value(value: str) -> str:
    """Normalize placeholders/comments from `.env` files into usable values."""
    if not value:
        return ""

    cleaned = value.split(" #", 1)[0].strip()
    placeholders = {
        "你的API_KEY",
        "your_api_key",
        "your_openai_key",
        "your_deepseek_key",
        "your-model-endpoint",
        "你的模型endpoint",
    }
    if cleaned in placeholders:
        return ""
    return cleaned


def _get_first_env(*keys: str, default: str = "") -> str:
    for key in keys:
        value = _clean_env_value(os.getenv(key, ""))
        if value:
            return value
    return default


@dataclass
class LLMConfig:
    """大模型配置"""

    provider: str = _get_first_env("LLM_PROVIDER", default="deepseek")
    api_key: str = _get_first_env("LLM_API_KEY", "DOUBAO_API_KEY", default="")
    base_url: str = _get_first_env(
        "LLM_BASE_URL",
        "DOUBAO_API_URL",
        default="https://api.deepseek.com",
    )
    model: str = _get_first_env("LLM_MODEL", default="deepseek-chat")
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
