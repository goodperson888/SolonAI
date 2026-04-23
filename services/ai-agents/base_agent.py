"""
Solon AI - Agent 基类

所有 Agent 都继承这个基类，统一接口和错误处理。
"""

import hashlib
import json
import logging
import re
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from error_handler import ErrorSeverity, LLMError, error_handler, llm_circuit_breaker
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


THINK_BLOCK_RE = re.compile(r"<think>(.*?)</think>", re.DOTALL | re.IGNORECASE)


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
        self.prompt = self._build_prompt()
        # 简单内存缓存（生产环境建议用 Redis）
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._cache_ttl = 300  # 缓存 5 分钟

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """系统提示词，子类必须实现"""
        pass

    def _build_prompt(self):
        """Provide a sensible default so simple agents need only define `system_prompt`."""
        return self.system_prompt

    def _get_cache_key(self, user_input: str, state: Dict[str, Any]) -> str:
        """生成缓存键"""
        # 对于相同的输入和钱包地址，可以复用结果
        key_data = f"{self.name}:{user_input}:{state.get('wallet_address', '')}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_cached_result(self, cache_key: str) -> Optional[Any]:
        """获取缓存结果"""
        if cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                logger.info(f"[{self.name}] 使用缓存结果")
                return result
            else:
                # 过期，删除
                del self._cache[cache_key]
        return None

    def _set_cached_result(self, cache_key: str, result: Any):
        """保存缓存结果"""
        self._cache[cache_key] = (result, time.time())
        # 简单的缓存清理：超过 100 条时清理过期的
        if len(self._cache) > 100:
            now = time.time()
            expired_keys = [k for k, (_, ts) in self._cache.items() if now - ts > self._cache_ttl]
            for k in expired_keys:
                del self._cache[k]

    def _compress_chat_history(self, chat_history: list) -> list:
        """
        压缩对话历史，避免上下文过长

        策略：
        - 保留最近 5 条完整对话
        - 早期对话进行摘要（简化为关键信息）
        """
        if not chat_history or len(chat_history) <= 10:
            return chat_history or []

        # 保留最近 5 轮对话（10 条消息）
        recent = chat_history[-10:]

        # 早期对话简化为摘要
        early = chat_history[:-10]
        if early:
            # 简单摘要：只保留用户的关键问题
            summary = []
            for i in range(0, len(early), 2):  # 每 2 条取 1 条
                if i < len(early) and early[i].get("role") == "user":
                    summary.append(early[i])

            logger.info(f"[{self.name}] 压缩历史：{len(early)} 条 -> {len(summary)} 条摘要")
            return summary + recent

        return recent

    @staticmethod
    def _normalize_llm_response(response: Any) -> Dict[str, str]:
        """
        Normalize provider-specific response payloads into visible text plus optional reasoning.
        """
        content = response.content
        additional_kwargs = getattr(response, "additional_kwargs", {}) or {}

        reasoning = additional_kwargs.get("reasoning_content", "") or additional_kwargs.get(
            "thinking", ""
        )

        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    item_type = item.get("type")
                    if item_type in {"thinking", "reasoning"} and item.get("text"):
                        reasoning = reasoning or item["text"]
                    elif item_type == "text" and item.get("text"):
                        text_parts.append(item["text"])
                elif isinstance(item, str):
                    text_parts.append(item)
            content = "\n".join(part.strip() for part in text_parts if part and part.strip())

        content = content or ""
        think_blocks = THINK_BLOCK_RE.findall(content)
        if think_blocks and not reasoning:
            reasoning = "\n\n".join(block.strip() for block in think_blocks if block.strip())
        content = THINK_BLOCK_RE.sub("", content).strip()

        return {
            "text": content,
            "reasoning": reasoning.strip(),
        }

    async def call_llm(self, user_input: str, chat_history: list = None) -> str:
        """
        调用大模型（带熔断器保护和历史压缩）

        Args:
            user_input: 用户输入
            chat_history: 对话历史 [{"role": "user/assistant", "content": "..."}]

        Returns:
            大模型的回复文本
        """
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        # 检查熔断器
        if not llm_circuit_breaker.can_execute():
            raise LLMError(
                "LLM 服务暂时不可用，请稍后重试",
                severity=ErrorSeverity.HIGH,
                details={"circuit_breaker": "open"},
            )

        try:
            messages = [SystemMessage(content=self.system_prompt)]

            # 压缩对话历史（避免上下文过长）
            if chat_history:
                compressed_history = self._compress_chat_history(chat_history)
                for msg in compressed_history:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    else:
                        messages.append(AIMessage(content=msg["content"]))

            messages.append(HumanMessage(content=user_input))
            response = await self.llm.ainvoke(messages)
            normalized = self._normalize_llm_response(response)

            # 记录成功
            llm_circuit_breaker.record_success()
            return normalized["text"]

        except Exception as e:
            logger.error(f"[{self.name}] LLM 调用失败: {e}")
            # 记录失败
            llm_circuit_breaker.record_failure()
            raise LLMError(
                f"LLM 调用失败: {str(e)}",
                severity=ErrorSeverity.MEDIUM,
                details={"agent": self.name, "error": str(e)},
            )

    async def call_llm_with_metadata(
        self, user_input: str, chat_history: list = None
    ) -> Dict[str, str]:
        """调用大模型并返回文本和推理过程（带熔断器保护和历史压缩）"""
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        # 检查熔断器
        if not llm_circuit_breaker.can_execute():
            raise LLMError(
                "LLM 服务暂时不可用，请稍后重试",
                severity=ErrorSeverity.HIGH,
                details={"circuit_breaker": "open"},
            )

        try:
            messages = [SystemMessage(content=self.system_prompt)]

            # 压缩对话历史
            if chat_history:
                compressed_history = self._compress_chat_history(chat_history)
                for msg in compressed_history:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    else:
                        messages.append(AIMessage(content=msg["content"]))

            messages.append(HumanMessage(content=user_input))
            response = await self.llm.ainvoke(messages)

            # 记录成功
            llm_circuit_breaker.record_success()
            return self._normalize_llm_response(response)

        except Exception as e:
            logger.error(f"[{self.name}] LLM 调用失败: {e}")
            # 记录失败
            llm_circuit_breaker.record_failure()
            raise LLMError(
                f"LLM 调用失败: {str(e)}",
                severity=ErrorSeverity.MEDIUM,
                details={"agent": self.name, "error": str(e)},
            )

    async def call_llm_stream(self, user_input: str, chat_history: list = None):
        """
        流式调用大模型（带熔断器保护和历史压缩）

        Args:
            user_input: 用户输入
            chat_history: 对话历史

        Yields:
            str: 每个生成的 token
        """
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        # 检查熔断器
        if not llm_circuit_breaker.can_execute():
            raise LLMError(
                "LLM 服务暂时不可用，请稍后重试",
                severity=ErrorSeverity.HIGH,
                details={"circuit_breaker": "open"},
            )

        try:
            messages = [SystemMessage(content=self.system_prompt)]

            # 压缩对话历史
            if chat_history:
                compressed_history = self._compress_chat_history(chat_history)
                for msg in compressed_history:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    else:
                        messages.append(AIMessage(content=msg["content"]))

            messages.append(HumanMessage(content=user_input))

            # 使用 astream 进行流式调用
            async for chunk in self.llm.astream(messages):
                if hasattr(chunk, "content") and chunk.content:
                    yield chunk.content

            # 记录成功
            llm_circuit_breaker.record_success()

        except Exception as e:
            logger.error(f"[{self.name}] LLM 流式调用失败: {e}")
            # 记录失败
            llm_circuit_breaker.record_failure()
            raise LLMError(
                f"LLM 流式调用失败: {str(e)}",
                severity=ErrorSeverity.MEDIUM,
                details={"agent": self.name, "error": str(e)},
            )

    async def call_llm_json(self, user_input: str, chat_history: list = None) -> Dict[str, Any]:
        """
        调用大模型并解析 JSON 返回

        Args:
            user_input: 用户输入
            chat_history: 对话历史

        Returns:
            解析后的 JSON 字典
        """
        response = await self.call_llm(user_input, chat_history)

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
        """让 Agent 可以直接被 LangGraph 调用（带重试和降级）"""
        logger.info(f"[{self.name}] 开始处理...")

        success, result, error_msg = await error_handler.handle_with_retry(
            self.process, state, error_context=f"{self.name}"
        )

        if success and result is not None:
            logger.info(f"[{self.name}] 处理完成")
            return result

        # 处理失败，创建降级状态
        logger.warning(f"[{self.name}] 处理失败，启用降级: {error_msg}")
        return error_handler._create_fallback_state(state, self.name, error_msg or "未知错误")
