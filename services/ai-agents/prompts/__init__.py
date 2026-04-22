"""
Prompt 管理模块

统一管理所有 Agent 的 system prompt，支持：
- 从文件加载 prompt
- 多语言版本支持
- Prompt 版本控制
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent


def load_prompt(agent_name: str, language: str = "zh", version: str = "v1") -> str:
    """
    加载指定 Agent 的 prompt

    Args:
        agent_name: Agent 名称（如 "explanation_agent"）
        language: 语言代码（zh/en）
        version: Prompt 版本（v1/v2/...）

    Returns:
        Prompt 文本内容

    文件命名规则：
        {agent_name}_{language}_{version}.txt
        例如：explanation_agent_zh_v1.txt
    """
    filename = f"{agent_name}_{language}_{version}.txt"
    file_path = PROMPTS_DIR / filename

    # 如果指定版本不存在，尝试加载默认版本
    if not file_path.exists():
        default_filename = f"{agent_name}_{language}_v1.txt"
        file_path = PROMPTS_DIR / default_filename

    # 如果指定语言不存在，尝试加载中文版本
    if not file_path.exists():
        fallback_filename = f"{agent_name}_zh_v1.txt"
        file_path = PROMPTS_DIR / fallback_filename

    if not file_path.exists():
        logger.error(f"[PromptLoader] Prompt 文件不存在: {filename}")
        raise FileNotFoundError(f"Prompt 文件不存在: {filename}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        logger.info(f"[PromptLoader] 成功加载 prompt: {file_path.name}")
        return content
    except Exception as e:
        logger.error(f"[PromptLoader] 加载 prompt 失败: {e}")
        raise


def get_prompt(agent_name: str, language: str = "zh", version: Optional[str] = None) -> str:
    """
    获取 Agent 的 prompt（带缓存）

    Args:
        agent_name: Agent 名称
        language: 语言代码
        version: Prompt 版本（None 表示使用最新版本）

    Returns:
        Prompt 文本内容
    """
    # 默认使用 v1
    version = version or "v1"
    return load_prompt(agent_name, language, version)
