import operator
from typing import Annotated, Sequence, TypedDict

from langchain.schema import BaseMessage
from langgraph.graph import END, StateGraph


class AgentState(TypedDict):
    """全局状态定义"""

    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_input: str
    intent: dict
    strategy: dict
    risk_audit: dict
    transaction: dict
    final_result: dict


class MainGraph:
    """
    主流程图

    协调各个Agent的执行流程：
    用户输入 → 意图理解 → 策略生成 → 风控审计 → 执行准备 → 返回结果
    """

    def __init__(self, agents):
        self.agents = agents
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """构建LangGraph流程图"""
        workflow = StateGraph(AgentState)

        # 添加节点
        workflow.add_node("intent", self._intent_node)
        workflow.add_node("strategy", self._strategy_node)
        workflow.add_node("risk", self._risk_node)
        workflow.add_node("execution", self._execution_node)

        # 定义流程
        workflow.set_entry_point("intent")
        workflow.add_edge("intent", "strategy")
        workflow.add_edge("strategy", "risk")
        workflow.add_edge("risk", "execution")
        workflow.add_edge("execution", END)

        return workflow.compile()

    async def _intent_node(self, state: AgentState) -> AgentState:
        """意图理解节点"""
        intent = await self.agents["intent"].understand_intent(state["user_input"])
        state["intent"] = intent
        return state

    async def _strategy_node(self, state: AgentState) -> AgentState:
        """策略生成节点"""
        strategy = await self.agents["strategy"].generate_strategy(state["intent"]["parameters"])
        state["strategy"] = strategy
        return state

    async def _risk_node(self, state: AgentState) -> AgentState:
        """风控审计节点"""
        risk_audit = await self.agents["risk"].audit_strategy(state["strategy"])
        state["risk_audit"] = risk_audit
        return state

    async def _execution_node(self, state: AgentState) -> AgentState:
        """执行准备节点"""
        if state["risk_audit"]["is_safe"]:
            transaction = await self.agents["execution"].prepare_transaction(
                state["strategy"], state.get("wallet_address", "")
            )
            state["transaction"] = transaction
        state["final_result"] = {
            "strategy": state["strategy"],
            "risk_audit": state["risk_audit"],
            "transaction": state.get("transaction", {}),
        }
        return state

    async def run(self, user_input: str, wallet_address: str = "") -> dict:
        """
        运行完整流程

        Args:
            user_input: 用户输入
            wallet_address: 钱包地址

        Returns:
            最终结果

        TODO: 添加错误处理和重试机制
        """
        initial_state = {
            "messages": [],
            "user_input": user_input,
            "wallet_address": wallet_address,
            "intent": {},
            "strategy": {},
            "risk_audit": {},
            "transaction": {},
            "final_result": {},
        }

        result = await self.graph.ainvoke(initial_state)
        return result["final_result"]
