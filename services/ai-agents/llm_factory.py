"""
Solon AI - LLM 工厂

根据配置创建大模型实例。
支持 DeepSeek、通义千问、豆包、OpenAI 等所有 OpenAI 兼容接口。
"""

from config import llm_config
from langchain_openai import ChatOpenAI

def create_llm(
    temperature: float = None,
    max_tokens: int = None,
    model: str = None,
) -> ChatOpenAI:
    """
    创建大模型实例

    所有支持 OpenAI 兼容接口的模型都可以用 ChatOpenAI 来调用，
    只需要改 base_url 和 api_key 就行。

    Args:
        temperature: 温度参数，越高越随机
        max_tokens: 最大输出 token 数
        model: 模型名称，不传就用配置文件的
    """
    return ChatOpenAI(
        openai_api_key=llm_config.api_key,
        openai_api_base=llm_config.base_url,
        model_name=model or llm_config.model,
        temperature=temperature if temperature is not None else llm_config.temperature,
        max_tokens=max_tokens or llm_config.max_tokens,
    )
