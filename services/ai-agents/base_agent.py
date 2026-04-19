"""
Solon AI - Agent 基类

所有 Agent 都继承这个基类，统一接口和错误处理。
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Agent 基类

    所有 Agent 必须实现:
    - name: Agent 名称
    - description: Agent 描述
    - system_prompt: 系统提示词
    - process(): 核心处理逻辑
    """

    name: str = "base"
    description: str = "基础Agent"

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """系统提示词，子类必须实现"""
        pass

    async def call_llm(self, user_input: str) -> str:
        """
        调用大模型

        Args:
            user_input: 用户输入

        Returns:
            大模型的回复文本
        """
        from langchain_core.messages import HumanMessage, SystemMessage

        try:
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_input),
            ]
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"[{self.name}] LLM 调用失败: {e}")
            raise

    async def call_llm_json(self, user_input: str) -> Dict[str, Any]:
        """
        调用大模型并解析 JSON 返回

        Args:
            user_input: 用户输入

        Returns:
            解析后的 JSON 字典
        """
        response = await self.call_llm(user_input)

        # 尝试提取 JSON
        try:
            # 处理 markdown 代码块包裹的 JSON
            text = response.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                # 去掉首尾的 ```
                lines = [line for line in lines if not line.strip().startswith("```")]
                text = "\n".join(lines)
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning(f"[{self.name}] JSON 解析失败，原始回复: {response}")
            return {"raw_response": response, "parse_error": True}

    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心处理逻辑，子类必须实现

        Args:
            state: LangGraph 状态字典

        Returns:
            更新后的状态字典
        """
        pass

    async def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """让 Agent 可以直接被 LangGraph 调用"""
        logger.info(f"[{self.name}] 开始处理...")
        try:
            result = await self.process(state)
            logger.info(f"[{self.name}] 处理完成")
            return result
        except Exception as e:
            logger.error(f"[{self.name}] 处理失败: {e}")
            state["error"] = f"{self.name} 处理失败: {str(e)}"
            return state
