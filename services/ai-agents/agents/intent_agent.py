from langchain.prompts import ChatPromptTemplate
from langchain.schema import BaseMessage
from typing import Dict, Any, List

class IntentAgent:
    """
    意图理解Agent

    职责：
    - 解析用户自然语言输入
    - 识别用户核心需求
    - 提取关键参数
    """

    def __init__(self, llm):
        self.llm = llm
        self.prompt = self._load_prompt()

    def _load_prompt(self) -> ChatPromptTemplate:
        """加载Prompt模板"""
        return ChatPromptTemplate.from_messages([
            ("system", """你是Solana DeFi专家，负责理解用户的投资需求。

你需要从用户输入中提取：
1. 用户意图（查询资产、生成策略、执行交易等）
2. 风险偏好（保守、稳健、进取）
3. 资金规模
4. 其他约束条件

请以JSON格式返回结果。"""),
            ("user", "{input}")
        ])

    async def understand_intent(self, user_input: str) -> Dict[str, Any]:
        """
        理解用户意图

        Args:
            user_input: 用户输入的自然语言

        Returns:
            解析后的意图和参数

        TODO: 实现完整的意图理解逻辑
        """
        # 调用LLM
        messages = self.prompt.format_messages(input=user_input)
        response = await self.llm.ainvoke(messages)

        # 解析响应
        # TODO: 添加结果验证和错误处理

        return {
            "intent": "generate_strategy",
            "parameters": {
                "risk_level": "conservative",
                "amount": 100
            }
        }
