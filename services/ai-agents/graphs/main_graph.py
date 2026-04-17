"""
Solon AI - LangGraph 主工作流

将8个 Agent 串联成完整的工作流：

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
    │                      → ExecutionAgent        │
    │                      → MonitoringAgent       │
    │                      → ExplanationAgent      │
    │                                             │
    │  execute_trade → ExecutionAgent              │
    │                → ExplanationAgent            │
    │                                             │
    │  risk_check → RiskAgent                     │
    │             ��� ExplanationAgent               │
    │                                             │
    │  chat → ExplanationAgent                    │
    └─────────────────────────────────────────────┘
       ↓
    返回给用户
"""

import sys
import os
from typing import Any, Dict

from langgraph.graph import StateGraph, END

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_factory import create_llm
from agents.intent_agent import IntentAgent
from agents.data_aggregation_agent import DataAggregationAgent
from agents.strategy_agent import StrategyAgent
from agents.risk_agent import RiskAgent
from agents.validation_agent import ValidationAgent
from agents.execution_agent import ExecutionAgent
from agents.monitoring_agent import MonitoringAgent
from agents.explanation_agent import ExplanationAgent


def create_workflow():
    """
    创建完整的 Agent 工作流

    Returns:
        编译后的 LangGraph 工作流
    """
    # 创建 LLM 实例
    llm = create_llm()

    # 初始化8个 Agent
    intent_agent = IntentAgent(llm)
    data_agent = DataAggregationAgent(llm)
    strategy_agent = StrategyAgent(llm)
    risk_agent = RiskAgent(llm)
    validation_agent = ValidationAgent(llm)
    execution_agent = ExecutionAgent(llm)
    monitoring_agent = MonitoringAgent(llm)
    explanation_agent = ExplanationAgent(llm)

    # 创建状态图
    workflow = StateGraph(dict)

    # 添加节点（每个 Agent 就是一个节点）
    workflow.add_node("intent", intent_agent)
    workflow.add_node("data_aggregation", data_agent)
    workflow.add_node("strategy", strategy_agent)
    workflow.add_node("risk", risk_agent)
    workflow.add_node("validation", validation_agent)
    workflow.add_node("execution", execution_agent)
    workflow.add_node("monitoring", monitoring_agent)
    workflow.add_node("explanation", explanation_agent)

    # 设置入口
    workflow.set_entry_point("intent")

    # Intent → DataAggregation（所有意图都先获取数据）
    workflow.add_edge("intent", "data_aggregation")

    # DataAggregation → 根据意图路由
    workflow.add_conditional_edges(
        "data_aggregation",
        route_by_intent,
        {
            "query_assets": "explanation",
            "generate_strategy": "strategy",
            "execute_trade": "execution",
            "risk_check": "risk",
            "chat": "explanation",
        },
    )

    # 策略生成完整流程
    workflow.add_edge("strategy", "risk")

    # Risk → 根据来源路由（策略生成走validation，风控检查直接走explanation）
    workflow.add_conditional_edges(
        "risk",
        route_after_risk,
        {
            "validation": "validation",
            "explanation": "explanation",
        },
    )

    # Validation → 根据是否通过路由
    workflow.add_conditional_edges(
        "validation",
        route_after_validation,
        {
            "execution": "execution",
            "explanation": "explanation",
        },
    )

    workflow.add_edge("execution", "monitoring")
    workflow.add_edge("monitoring", "explanation")

    # Explanation → 结束
    workflow.add_edge("explanation", END)

    # 编译工作流
    return workflow.compile()


def route_by_intent(state: Dict[str, Any]) -> str:
    """根据意图路由到不同的 Agent"""
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


def route_after_risk(state: Dict[str, Any]) -> str:
    """Risk之后的路由：策略生成走validation，风控检查直接走explanation"""
    intent = state.get("intent", "")
    if intent == "generate_strategy":
        return "validation"
    else:
        return "explanation"


def route_after_validation(state: Dict[str, Any]) -> str:
    """验证通过后路由"""
    validation = state.get("validation_result")

    if validation is None or validation.get("is_valid", True):
        return "execution"
    else:
        # 验证不通过，直接跳到解释（告诉用户为什么不通过）
        return "explanation"


# ===== 对外暴露的接口 =====

_workflow = None


def get_workflow():
    """获取工作流单例"""
    global _workflow
    if _workflow is None:
        _workflow = create_workflow()
    return _workflow


async def run_agent(
    user_input: str,
    wallet_address: str = "",
    session_id: str = "",
) -> Dict[str, Any]:
    """
    运行 Agent 工作流（对外主接口）

    Args:
        user_input: 用户输入的自然语言
        wallet_address: 用户钱包地址
        session_id: 会话ID

    Returns:
        完整的处理结果

    使用示例:
        result = await run_agent("帮我看看钱包里有什么资产")
        print(result["explanation"])
    """
    workflow = get_workflow()

    # 初始状态
    initial_state = {
        "user_input": user_input,
        "wallet_address": wallet_address,
        "session_id": session_id,
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
        "current_agent": "",
        "error": None,
        "completed": False,
    }

    # 运行工作流
    result = await workflow.ainvoke(initial_state)

    return result
