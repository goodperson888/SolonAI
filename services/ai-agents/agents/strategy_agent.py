from langchain.prompts import ChatPromptTemplate
from typing import Dict, Any

class StrategyAgent:
    """
    策略生成Agent

    职责：
    - 基于用户需求生成DeFi策略
    - 收益测算
    - 风险评级
    - 操作步骤拆解
    """

    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools
        self.prompt = self._load_prompt()

    def _load_prompt(self) -> ChatPromptTemplate:
        """加载Prompt模板"""
        return ChatPromptTemplate.from_messages([
            ("system", """你是Solana DeFi策略专家，负责生成安全、可落地的投资策略。

你需要：
1. 根据用户的风险偏好和资金规模，推荐合适的DeFi协议
2. 计算预期收益和最大风险
3. 拆解详细的操作步骤
4. 标注涉及协议的审计情况

可用的协议：
- MarginFi（借贷）：年化3-8%，风险极低
- Raydium（流动性挖矿）：年化8-20%，风险中低
- Kamino（质押）：年化5-12%，风险低

请以JSON格式返回策略。"""),
            ("user", "{input}")
        ])

    async def generate_strategy(
        self,
        user_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成投资策略

        Args:
            user_input: 用户输入（风险偏好、资金规模等）

        Returns:
            策略详情

        TODO: 实现完整的策略生成逻辑
        """
        # 1. 参数校验
        self._validate_input(user_input)

        # 2. 调用LLM生成策略
        # TODO: 实现LLM调用逻辑

        # 3. 结果校验
        # TODO: 实现结果校验逻辑

        return {
            "strategy_id": "strategy_001",
            "name": "MarginFi稳健生息策略",
            "risk_level": "conservative",
            "expected_apy": "4.2%",
            "steps": [
                "将SOL存入MarginFi",
                "开始赚取利息"
            ]
        }

    def _validate_input(self, user_input: Dict[str, Any]):
        """输入校验"""
        required_fields = ["risk_level", "amount"]
        for field in required_fields:
            if field not in user_input:
                raise ValueError(f"Missing required field: {field}")
