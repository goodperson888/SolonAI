"""
错误处理和降级机制

提供统一的错误处理、重试、降级策略
"""

import asyncio
import traceback
from enum import Enum
from typing import Any, Callable, Dict, Optional


class ErrorSeverity(Enum):
    """错误严重程度"""

    LOW = "low"  # 轻微错误，可以忽略
    MEDIUM = "medium"  # 中等错误，需要重试
    HIGH = "high"  # 严重错误，需要降级
    CRITICAL = "critical"  # 致命错误，必须中断


class AgentError(Exception):
    """Agent 错误基类"""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict] = None,
    ):
        self.message = message
        self.severity = severity
        self.details = details or {}
        super().__init__(self.message)


class LLMError(AgentError):
    """LLM 调用错误"""

    pass


class DataFetchError(AgentError):
    """数据获取错误"""

    pass


class ValidationError(AgentError):
    """验证错误"""

    pass


class ErrorHandler:
    """统一错误处理器"""

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def handle_with_retry(
        self, func: Callable, *args, error_context: str = "", **kwargs
    ) -> tuple[bool, Any, Optional[str]]:
        """
        带重试的错误处理

        Returns:
            (success, result, error_message)
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                result = await func(*args, **kwargs)
                return True, result, None

            except AgentError as e:
                last_error = e
                print(
                    f"[ErrorHandler] {error_context} 失败 (尝试 {attempt + 1}/{self.max_retries}): {e.message}"
                )

                # 根据严重程度决定是否重试
                if e.severity == ErrorSeverity.CRITICAL:
                    print("[ErrorHandler] 致命错误，停止重试")
                    break

                if e.severity == ErrorSeverity.LOW:
                    print("[ErrorHandler] 轻微错误，继续执行")
                    return True, None, None

                # 中等和严重错误，等待后重试
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))  # 指数退避

            except Exception as e:
                last_error = e
                print(
                    f"[ErrorHandler] {error_context} 未知错误 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}"
                )
                traceback.print_exc()

                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))

        # 所有重试都失败
        error_msg = str(last_error) if last_error else "未知错误"
        return False, None, error_msg

    def wrap_agent_process(self, agent_name: str):
        """
        装饰器：包装 Agent 的 process 方法，添加错误处理

        用法：
        @error_handler.wrap_agent_process("IntentAgent")
        async def process(self, state):
            ...
        """

        def decorator(func: Callable):
            async def wrapper(*args, **kwargs):
                success, result, error = await self.handle_with_retry(
                    func, *args, error_context=f"{agent_name}.process", **kwargs
                )

                if not success:
                    # 返回降级状态
                    state = args[1] if len(args) > 1 else kwargs.get("state", {})
                    return self._create_fallback_state(state, agent_name, error)

                return result

            return wrapper

        return decorator

    def _create_fallback_state(
        self, state: Dict[str, Any], agent_name: str, error: str
    ) -> Dict[str, Any]:
        """创建降级状态"""
        state["error"] = True
        state["error_agent"] = agent_name
        state["error_message"] = error
        state["fallback_mode"] = True

        # 根据不同 Agent 提供不同的降级策略
        if agent_name == "intent_agent":
            # 意图识别失败，默认为普通聊天
            state["intent"] = "chat"
            state["reasoning"] = "意图识别失败，使用默认聊天模式"

        elif agent_name == "data_aggregation_agent":
            # 数据获取失败，使用空数据
            state["wallet_assets"] = []
            state["total_value_usd"] = 0
            state["protocol_data"] = {}
            state["reasoning"] = "数据获取失败，使用空数据"

        elif agent_name == "explanation_agent":
            # 解释失败，返回简单错误提示
            state["explanation"] = (
                f"抱歉，处理你的请求时遇到了问题：{error}\n\n请稍后重试，或者换个方式问我。"
            )
            state["reasoning"] = "解释生成失败，返回错误提示"

        return state


class CircuitBreaker:
    """熔断器：防止频繁调用失败的服务"""

    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold  # 失败次数阈值
        self.timeout = timeout  # 熔断超时时间（秒）
        self.failure_count = 0
        self.last_failure_time = 0
        self.is_open = False

    def record_success(self):
        """记录成功"""
        self.failure_count = 0
        self.is_open = False

    def record_failure(self):
        """记录失败"""
        import time

        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            print(f"[CircuitBreaker] 熔断器打开，失败次数: {self.failure_count}")

    def can_execute(self) -> bool:
        """检查是否可以执行"""
        import time

        if not self.is_open:
            return True

        # 检查是否超过超时时间
        if time.time() - self.last_failure_time > self.timeout:
            print("[CircuitBreaker] 熔断器恢复")
            self.is_open = False
            self.failure_count = 0
            return True

        return False


# 全局错误处理器实例
error_handler = ErrorHandler(max_retries=3, retry_delay=1.0)

# 全局熔断器（针对 LLM 调用）
llm_circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60.0)
