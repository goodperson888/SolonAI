"""
Solon AI - LangGraph 主工作流

将8个 Agent 串联成完整的工作流，支持：
- 类型化状态管理（GraphState TypedDict）
- 错误恢复与降级
- 人机在回路（交易执行前需用户确认）
- 状态检查点（支持中断/恢复）

工作流架构：

    用户输入
       ↓
    IntentAgent（理解意图）
       ↓
    DataAggregationAgent（获取数据）
       ↓
    ┌─────────────── 根据意图路由 ───────────────┐
    │                                             │
    │  query_assets → ExplanationAgent            │
    │                                             │
    │  generate_strategy → StrategyAgent          │
    │                      → RiskAgent            │
    │                      → ValidationAgent      │
    │                      → [用户确认] ←── 人机在回路
    │                      → ExecutionAgent        │
    │                      → MonitoringAgent       │
    │                      → ExplanationAgent      │
    │                                             │
    │  execute_trade → [用户确认] ←── 人机在回路   │
    │                → ExecutionAgent              │
    │                → ExplanationAgent            │
    │                                             │
    │  risk_check → RiskAgent                     │
    │             → ExplanationAgent               │
    │                                             │
    │  chat → ExplanationAgent                    │
    └─────────────────────────────────────────────┘
       ↓
    返回给用户
"""

import logging
import os
import sys
import uuid
from typing import Any, Dict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.data_aggregation_agent import DataAggregationAgent  # noqa: E402
from agents.execution_agent import ExecutionAgent  # noqa: E402
from agents.explanation_agent import ExplanationAgent  # noqa: E402
from agents.intent_agent import IntentAgent  # noqa: E402
from agents.monitoring_agent import MonitoringAgent  # noqa: E402
from agents.risk_agent import RiskAgent  # noqa: E402
from agents.strategy_agent import StrategyAgent  # noqa: E402
from agents.validation_agent import ValidationAgent  # noqa: E402
from llm_factory import create_llm  # noqa: E402
from state import GraphState  # noqa: E402

logger = logging.getLogger(__name__)


# ===== 工作流节点 =====


async def error_recovery_node(state: GraphState) -> dict:
    """
    错误恢复节点

    当某个 Agent 处理失败时，提供降级响应，确保用户始终能收到回复。
    """
    error_agent = state.get("error_agent", "unknown")
    error_message = state.get("error_message", "未知错误")

    logger.warning(f"[ErrorRecovery] Agent '{error_agent}' 失败: {error_message}，执行降级策略")

    result = {}
    if not state.get("explanation"):
        result["explanation"] = (
            f"抱歉，在处理你的请求时遇到了一些问题（{error_agent} 服务暂时不可用）。\n\n"
            f"你可以：\n"
            f"1. 稍后重新尝试\n"
            f"2. 换一种方式描述你的需求\n"
            f"3. 尝试更简单的操作"
        )

    result["completed"] = True
    return result


async def human_approval_node(state: GraphState) -> dict:
    """
    人机在回路节点 - 交易审批

    在 ExecutionAgent 执行前，生成交易预览供用户确认。
    工作流会在此节点之后、execution 节点之前被 interrupt，
    等待用户通过 resume_agent() 确认后继续。
    """
    intent = state.get("intent", "")
    result: dict = {}

    # 构建交易预览信息
    preview: Dict[str, Any] = {
        "intent": intent,
        "wallet_address": state.get("wallet_address", ""),
    }

    if intent == "generate_strategy" and state.get("strategy"):
        strategy = state["strategy"]
        preview["strategy_name"] = strategy.get("strategy_name", "未知策略")
        preview["risk_level"] = strategy.get("risk_level", "unknown")
        preview["expected_apy"] = strategy.get("expected_apy", "N/A")
        preview["protocols"] = strategy.get("protocols", [])
        preview["steps"] = strategy.get("steps", [])

        # 如果有风控评估，也加上
        if state.get("risk_assessment"):
            risk = state["risk_assessment"]
            preview["risk_score"] = risk.get("score", "N/A")
            preview["risk_warnings"] = risk.get("warnings", [])
            preview["risk_blockers"] = risk.get("blockers", [])

        # 如果有验证结果
        if state.get("validation_result"):
            validation = state["validation_result"]
            preview["validation_passed"] = validation.get("is_valid", False)
            preview["validation_warnings"] = validation.get("warnings", [])

    elif intent == "execute_trade":
        preview["trade_params"] = state.get("intent_params", {})
        preview["total_value_usd"] = state.get("total_value_usd", 0)

    preview["message"] = "请确认以上交易信息。确认后将生成链上交易指令（需要钱包签名）。"

    result["requires_approval"] = True
    result["approval_preview"] = preview
    logger.info(f"[HumanApproval] 等待用户确认交易: intent={intent}")

    return result


# ===== 路由函数 =====


def route_after_intent(state: GraphState) -> str:
    """Intent 之后的路由：检查是否降级"""
    if state.get("fallback_mode") and state.get("error_agent") == "intent_agent":
        logger.info("[Router] 意图识别降级，使用默认 chat 模式继续")
        return "data_aggregation"
    if state.get("error") and not state.get("intent"):
        return "error_recovery"
    return "data_aggregation"


def route_by_intent(state: GraphState) -> str:
    """根据意图路由到不同的 Agent"""
    # 数据获取降级时，非聊天意图也走 explanation
    if state.get("fallback_mode") and state.get("error_agent") == "data_aggregation_agent":
        intent = state.get("intent", "chat")
        if intent == "chat":
            return "chat"
        logger.info(f"[Router] 数据获取降级，intent={intent}，降级到 explanation")
        return "chat"

    intent = state.get("intent", "chat")

    if intent == "query_assets":
        return "query_assets"
    elif intent == "generate_strategy":
        return "generate_strategy"
    elif intent == "execute_trade":
        return "execute_trade"
    elif intent == "risk_check":
        return "risk_check"
    else:
        return "chat"


def route_after_risk(state: GraphState) -> str:
    """Risk 之后的路由：策略生成走 validation，风控检查直接走 explanation"""
    intent = state.get("intent", "")
    if intent == "generate_strategy":
        return "validation"
    else:
        return "explanation"


def route_after_validation(state: GraphState) -> str:
    """验证后路由：通过走 human_approval，不通过走 explanation"""
    validation = state.get("validation_result")

    if validation is None or validation.get("is_valid", True):
        return "human_approval"
    else:
        return "explanation"


# ===== 工作流创建 =====

# 全局 checkpointer（内存存储，支持 interrupt/resume）
_checkpointer = MemorySaver()


def create_workflow():
    """
    创建完整的 Agent 工作流

    Returns:
        编译后的 LangGraph 工作流（支持 interrupt/resume）
    """
    llm = create_llm()

    # 初始化 8 个 Agent
    intent_agent = IntentAgent(llm)
    data_agent = DataAggregationAgent(llm)
    strategy_agent = StrategyAgent(llm)
    risk_agent = RiskAgent(llm)
    validation_agent = ValidationAgent(llm)
    execution_agent = ExecutionAgent(llm)
    monitoring_agent = MonitoringAgent(llm)
    explanation_agent = ExplanationAgent(llm)

    # 创建类型化状态图
    workflow = StateGraph(GraphState)

    # ===== 添加节点 =====
    workflow.add_node("intent_node", intent_agent)
    workflow.add_node("data_aggregation_node", data_agent)
    workflow.add_node("strategy_node", strategy_agent)
    workflow.add_node("risk_node", risk_agent)
    workflow.add_node("validation_node", validation_agent)
    workflow.add_node("human_approval_node", human_approval_node)
    workflow.add_node("execution_node", execution_agent)
    workflow.add_node("monitoring_node", monitoring_agent)
    workflow.add_node("explanation_node", explanation_agent)
    workflow.add_node("error_recovery_node", error_recovery_node)

    # ===== 设置入口 =====
    workflow.set_entry_point("intent_node")

    # ===== 定义边 =====

    # Intent → DataAggregation（含错误恢复分支）
    workflow.add_conditional_edges(
        "intent_node",
        route_after_intent,
        {
            "data_aggregation": "data_aggregation_node",
            "error_recovery": "error_recovery_node",
        },
    )

    # DataAggregation → 根据意图路由
    workflow.add_conditional_edges(
        "data_aggregation_node",
        route_by_intent,
        {
            "query_assets": "explanation_node",
            "generate_strategy": "strategy_node",
            "execute_trade": "human_approval_node",  # 交易执行先走人机确认
            "risk_check": "risk_node",
            "chat": "explanation_node",
        },
    )

    # 策略生成流程
    workflow.add_edge("strategy_node", "risk_node")

    # Risk → Validation（策略生成）或 Explanation（风控检查）
    workflow.add_conditional_edges(
        "risk_node",
        route_after_risk,
        {
            "validation": "validation_node",
            "explanation": "explanation_node",
        },
    )

    # Validation → HumanApproval（通过）或 Explanation（不通过）
    workflow.add_conditional_edges(
        "validation_node",
        route_after_validation,
        {
            "human_approval": "human_approval_node",
            "explanation": "explanation_node",
        },
    )

    # HumanApproval → Execution（interrupt 会在 execution 之前暂停）
    workflow.add_edge("human_approval_node", "execution_node")

    # Execution → Monitoring → Explanation → END
    workflow.add_edge("execution_node", "monitoring_node")
    workflow.add_edge("monitoring_node", "explanation_node")
    workflow.add_edge("explanation_node", END)

    # ErrorRecovery → END
    workflow.add_edge("error_recovery_node", END)

    # 编译工作流，启用 checkpointer 和 interrupt
    # interrupt_before=["execution"] 表示在 execution 节点执行前暂停
    return workflow.compile(
        checkpointer=_checkpointer,
        interrupt_before=["execution_node"],
    )


# ===== 对外暴露的接口 =====

_workflow = None


def get_workflow():
    """获取工作流单例"""
    global _workflow
    if _workflow is None:
        _workflow = create_workflow()
    return _workflow


def _build_initial_state(
    user_input: str,
    wallet_address: str = "",
    session_id: str = "",
    chat_history: list = None,
) -> GraphState:
    """构建初始状态"""
    return {
        "user_input": user_input,
        "wallet_address": wallet_address,
        "session_id": session_id,
        "chat_history": chat_history or [],
        "intent": "",
        "intent_params": {},
        "wallet_assets": [],
        "total_value_usd": 0.0,
        "protocol_data": {},
        "strategy": None,
        "risk_assessment": None,
        "validation_result": None,
        "transaction": None,
        "monitoring_config": None,
        "explanation": "",
        "reasoning": "",
        "requires_approval": False,
        "approval_preview": None,
        "user_approved": False,
        "current_agent": "",
        "error": None,
        "error_agent": "",
        "error_message": "",
        "fallback_mode": False,
        "completed": False,
    }


async def run_agent(
    user_input: str,
    wallet_address: str = "",
    session_id: str = "",
    chat_history: list = None,
    thread_id: str = None,
) -> Dict[str, Any]:
    """
    运行 Agent 工作流（对外主接口）

    Args:
        user_input: 用户输入的自然语言
        wallet_address: 用户钱包地址
        session_id: 会话ID
        chat_history: 对话历史列表
        thread_id: 线程ID（用于 checkpoint，可选，不传则自动生成）

    Returns:
        处理结果字典，包含以下关键字段：
        - explanation: 给用户的回复
        - interrupted: 是否被中断等待用户确认
        - thread_id: 线程ID（用于后续 resume）
        - approval_preview: 交易预览（interrupted=True 时有值）

    使用示例:
        # 普通聊天（不会被中断）
        result = await run_agent("帮我看看钱包里有什么资产")
        print(result["explanation"])

        # 交易执行（会被中断等待确认）
        result = await run_agent("帮我把 100 USDC 存入 MarginFi")
        if result["interrupted"]:
            print("交易预览:", result["approval_preview"])
            # 用户确认后调用 resume_agent
            final = await resume_agent(result["thread_id"], user_approved=True)
            print(final["explanation"])
    """
    workflow = get_workflow()
    tid = thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": tid}}

    initial_state = _build_initial_state(user_input, wallet_address, session_id, chat_history)

    try:
        result = await workflow.ainvoke(initial_state, config=config)
    except Exception as e:
        logger.error(f"[MainGraph] 工作流执行失败: {e}", exc_info=True)
        return {
            **initial_state,
            "error": str(e),
            "error_agent": "workflow",
            "error_message": str(e),
            "fallback_mode": True,
            "explanation": "抱歉，系统在处理你的请求时遇到了问题。请稍后重试，或者换个方式问我。",
            "completed": True,
            "interrupted": False,
            "thread_id": tid,
        }

    # 检查是否被 interrupt（等待用户确认交易）
    snapshot = await workflow.aget_state(config)
    interrupted = bool(snapshot.next)  # next 非空表示还有待执行的节点

    result["interrupted"] = interrupted
    result["thread_id"] = tid

    if interrupted:
        logger.info(f"[MainGraph] 工作流被中断，等待用户确认: thread_id={tid}")

    return result


async def run_agent_stream(
    user_input: str,
    wallet_address: str = "",
    session_id: str = "",
    chat_history: list = None,
    thread_id: str = None,
):
    """
    运行 Agent 工作流（流式输出版本）

    先运行工作流到 ExplanationAgent 之前的所有节点，
    然后使用 ExplanationAgent 的流式方法生成最终回复。

    Args:
        user_input: 用户输入的自然语言
        wallet_address: 用户钱包地址
        session_id: 会话ID
        chat_history: 对话历史列表
        thread_id: 线程ID（用于 checkpoint，可选，不传则自动生成）

    Yields:
        dict: 流式事件，包含以下类型：
        - {"type": "token", "content": "..."}: LLM 生成的 token
        - {"type": "data", "data": {...}}: 附加数据（intent、资产等）
        - {"type": "error", "error": "..."}: 错误信息
        - {"type": "complete"}: 流式完成
    """
    tid = thread_id or str(uuid.uuid4())

    initial_state = _build_initial_state(user_input, wallet_address, session_id, chat_history)

    try:
        logger.info(f"[MainGraph] 开始流式执行工作流: thread_id={tid}")

        # 创建临时的 LLM 和 Agent 实例用于流式输出
        llm = create_llm()
        explanation_agent = ExplanationAgent(llm)

        # 步骤1: 运行 IntentAgent
        intent_agent = IntentAgent(llm)
        state = await intent_agent.process(initial_state)

        # 检查是否有错误
        if state.get("fallback_mode"):
            yield {"type": "error", "error": state.get("error_message", "处理失败")}
            return

        # 步骤2: 运行 DataAggregationAgent
        data_agent = DataAggregationAgent(llm)
        state = await data_agent.process(state)

        # 步骤3: 根据 intent 决定是否需要运行其他 Agent
        intent = state.get("intent", "chat")

        if intent == "generate_strategy":
            # 策略生成流程：strategy -> risk -> validation
            strategy_agent = StrategyAgent(llm)
            state = await strategy_agent.process(state)

            risk_agent = RiskAgent(llm)
            state = await risk_agent.process(state)

            validation_agent = ValidationAgent(llm)
            state = await validation_agent.process(state)

        elif intent == "risk_check":
            # 风控检查流程
            risk_agent = RiskAgent(llm)
            state = await risk_agent.process(state)

        # 步骤4: 使用 ExplanationAgent 的流式方法生成最终回复
        logger.info("[MainGraph] 开始流式生成回复")
        async for token in explanation_agent.process_stream(state):
            yield {"type": "token", "content": token}

        # 发送附加数据
        yield {
            "type": "data",
            "data": {
                "intent": state.get("intent", ""),
                "intent_params": state.get("intent_params", {}),
                "wallet_assets": state.get("wallet_assets", []),
                "total_value_usd": state.get("total_value_usd", 0),
            },
        }

        # 流式完成
        yield {"type": "complete"}

    except Exception as e:
        logger.error(f"[MainGraph] 流式工作流执行失败: {e}", exc_info=True)
        yield {
            "type": "error",
            "error": str(e),
            "explanation": "抱歉，系统在处理你的请求时遇到了问题。请稍后重试，或者换个方式问我。",
        }


async def resume_agent(
    thread_id: str,
    user_approved: bool = True,
) -> Dict[str, Any]:
    """
    恢复被中断的工作流（用户确认/拒绝交易后调用）

    Args:
        thread_id: 之前 run_agent 返回的 thread_id
        user_approved: 用户是否批准交易

    Returns:
        最终处理结果

    使用示例:
        # 用户批准交易
        result = await resume_agent(thread_id="xxx", user_approved=True)

        # 用户拒绝交易
        result = await resume_agent(thread_id="xxx", user_approved=False)
    """
    workflow = get_workflow()
    config = {"configurable": {"thread_id": thread_id}}

    if not user_approved:
        # 用户拒绝：更新状态并让工作流跳过 execution，直接到 explanation
        await workflow.aupdate_state(
            config,
            {
                "user_approved": False,
                "explanation": "已取消交易。如需重新操作，请再次告诉我。",
                "completed": True,
            },
            as_node="explanation",  # 跳到 explanation 节点（之后直接 END）
        )
        snapshot = await workflow.aget_state(config)
        result = snapshot.values
        result["interrupted"] = False
        result["thread_id"] = thread_id
        return result

    # 用户批准：更新状态后继续执行
    await workflow.aupdate_state(
        config,
        {"user_approved": True},
        as_node="human_approval",
    )

    try:
        result = await workflow.ainvoke(None, config=config)
    except Exception as e:
        logger.error(f"[MainGraph] 恢复工作流失败: {e}", exc_info=True)
        return {
            "error": str(e),
            "error_agent": "workflow_resume",
            "error_message": str(e),
            "fallback_mode": True,
            "explanation": "抱歉，执行交易时遇到了问题。请稍后重试。",
            "completed": True,
            "interrupted": False,
            "thread_id": thread_id,
        }

    result["interrupted"] = False
    result["thread_id"] = thread_id
    return result


async def get_agent_state(thread_id: str) -> Dict[str, Any]:
    """
    查询工作流当前状态

    Args:
        thread_id: 线程ID

    Returns:
        当前状态快照，包含：
        - values: 当前���态值
        - next: 下一个待执行的节点列表（空表示已完成）
        - interrupted: 是否处于中断状态
    """
    workflow = get_workflow()
    config = {"configurable": {"thread_id": thread_id}}

    snapshot = await workflow.aget_state(config)
    return {
        "values": snapshot.values,
        "next": list(snapshot.next) if snapshot.next else [],
        "interrupted": bool(snapshot.next),
    }
