"""
Solon AI - 状态定义

LangGraph 工作流中传递的状态结构。
所有 Agent 共享这个状态，每个 Agent 读取和更新其中的字段。
"""

from typing import Any, Dict, List, Optional, TypedDict

from pydantic import BaseModel, Field


# ===== LangGraph 工作流使用的 TypedDict 状态 =====


class GraphState(TypedDict, total=False):
    """
    LangGraph 工作流状态（TypedDict 版本）

    LangGraph 的 StateGraph 需要 TypedDict 而非 Pydantic，
    因此这里定义一个与 AgentState 对应的 TypedDict。
    """

    # 用户输入
    user_input: str
    wallet_address: str
    session_id: str
    chat_history: list

    # IntentAgent 输出
    intent: str
    intent_params: dict

    # DataAggregationAgent 输出
    wallet_assets: list
    total_value_usd: float
    protocol_data: dict

    # StrategyAgent 输出
    strategy: Optional[dict]

    # RiskAgent 输出
    risk_assessment: Optional[dict]

    # ValidationAgent 输出
    validation_result: Optional[dict]

    # ExecutionAgent 输出
    transaction: Optional[dict]

    # MonitoringAgent 输出
    monitoring_config: Optional[dict]

    # ExplanationAgent 输出
    explanation: str
    reasoning: str

    # 人机在回路（交易审批）
    requires_approval: bool
    approval_preview: Optional[dict]
    user_approved: bool

    # 流程控制
    current_agent: str
    error: Optional[str]
    error_agent: str
    error_message: str
    fallback_mode: bool
    completed: bool


class AgentState(BaseModel):
    """
    全局状态，在所有 Agent 之间传递

    数据流向:
    用户输入 → IntentAgent(意图) → DataAggregation(数据)
    → StrategyAgent(策略) → RiskAgent(风控)
    → ValidationAgent(验证) → ExecutionAgent(执行)
    → MonitoringAgent(监控) → ExplanationAgent(解释) → 用户
    """

    # ===== 用户输入 =====
    user_input: str = ""  # 用户原始输入
    wallet_address: str = ""  # 用户钱包地址
    session_id: str = ""  # 会话ID
    chat_history: List[Dict[str, str]] = Field(default_factory=list)  # 对话历史 [{"role": "user/assistant", "content": "..."}]

    # ===== IntentAgent 输出 =====
    intent: str = ""  # 识别的意图: query_assets, generate_strategy, execute_trade, risk_check, chat
    intent_params: Dict[str, Any] = Field(default_factory=dict)  # 提取的参数

    # ===== DataAggregationAgent 输出 =====
    wallet_assets: List[Dict[str, Any]] = Field(default_factory=list)  # 钱包资产列表
    total_value_usd: float = 0.0  # 总资产价值(USD)
    protocol_data: Dict[str, Any] = Field(default_factory=dict)  # DeFi协议数据(APY等)

    # ===== StrategyAgent 输出 =====
    strategy: Optional[Dict[str, Any]] = None  # 生成的策略

    # ===== RiskAgent 输出 =====
    risk_assessment: Optional[Dict[str, Any]] = None  # 风控评估结果

    # ===== ValidationAgent 输出 =====
    validation_result: Optional[Dict[str, Any]] = None  # 验证结果

    # ===== ExecutionAgent 输出 =====
    transaction: Optional[Dict[str, Any]] = None  # 构建的交易指令

    # ===== MonitoringAgent 输出 =====
    monitoring_config: Optional[Dict[str, Any]] = None  # 监控配置

    # ===== ExplanationAgent 输出 =====
    explanation: str = ""  # 给用户的大白话解释
    reasoning: str = ""  # 推理过程

    # ===== 人机在回路（交易审批） =====
    requires_approval: bool = False  # 是否需要用户确认
    approval_preview: Optional[Dict[str, Any]] = None  # 交易预览信息
    user_approved: bool = False  # 用户是否已确认

    # ===== 流程控制 =====
    current_agent: str = ""  # 当前执行的Agent
    error: Optional[str] = None  # 错误信息
    error_agent: str = ""  # 出错的Agent名称
    error_message: str = ""  # 详细错误信息
    fallback_mode: bool = False  # 是否处于降级模式
    completed: bool = False  # 是否完成
