"""
自然语言解读Agent
职责：把专业的链上数据、策略报告、风险提示、交易明细翻译成大白话，生成可视化的解读内容
"""

from typing import Dict

from langchain_core.messages import HumanMessage, SystemMessage


class ExplanationAgent:
    """自然语言解读Agent - 专业内容通俗化、可视化报告生成、多轮对话答疑"""

    def __init__(self, llm):
        self.llm = llm
        self.system_prompt = """你是Solon AI的自然语言解读专家。
你的职责是：
1. 把复杂的链上数据翻译成大白话
2. 把专业的DeFi术语解释给新手用户
3. 生成可视化的报告和图表描述
4. 回答用户的疑问，保持上下文记忆

核心原则：
- 用最简单的语言解释复杂概念
- 避免使用专业术语，必须用时要解释
- 用类比和例子帮助理解
- 语气友好、耐心、鼓励性
- 永远站在用户角度思考

示例：
- "健康度1.5" → "你的借贷安全系数是1.5，相当于你借了100元，但抵押了150元的资产，还算安全"
- "APY 12%" → "年化收益率12%，相当于存1万元，一年后能赚1200元"
- "无常损失" → "提供流动性时，如果两个币的价格变化太大，你可能会比单纯持有损失一些，这叫无常损失"
"""

    async def explain_wallet_data(self, state: Dict) -> Dict:
        """
        解读钱包数据

        Args:
            state: 包含wallet_data的全局状态

        Returns:
            更新后的state，包含wallet_explanation字段
        """
        wallet_data = state.get("wallet_data", {})

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(
                content=f"""
请用大白话解读以下钱包数据，让新手用户能看懂：

钱包地址: {wallet_data.get('address', 'N/A')}
总资产价值: ${wallet_data.get('total_value_usd', 0):.2f}
代币数量: {len(wallet_data.get('balances', {}))}
NFT数量: {len(wallet_data.get('nfts', []))}
LP头寸数量: {len(wallet_data.get('lp_positions', []))}
借贷仓位数量: {len(wallet_data.get('lending_positions', []))}

要求：
1. 用简单的语言总结资产情况
2. 指出值得关注的地方
3. 给出通俗易懂的建议
4. 不超过200字
"""
            ),
        ]

        response = await self.llm.ainvoke(messages)
        state["wallet_explanation"] = response.content
        return state

    async def explain_strategy(self, state: Dict) -> Dict:
        """
        解读策略内容

        Args:
            state: 包含strategy的全局状态

        Returns:
            更新后的state，包含strategy_explanation字段
        """
        strategy = state.get("strategy", {})

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(
                content=f"""
请用大白话解读以下DeFi策略，让新手用户能看懂：

策略名称: {strategy.get('name', 'N/A')}
风险等级: {strategy.get('risk_level', 'N/A')}
预期年化收益: {strategy.get('expected_apy', 0)}%
涉及协议: {', '.join(strategy.get('protocols', []))}
操作步骤: {len(strategy.get('steps', []))}步

要求：
1. 用最简单的语言解释这个策略是做什么的
2. 用类比说明风险和收益
3. 解释为什么选择这些协议
4. 告诉用户需要注意什么
5. 不超过300字
"""
            ),
        ]

        response = await self.llm.ainvoke(messages)
        state["strategy_explanation"] = response.content
        return state

    async def explain_risk(self, state: Dict) -> Dict:
        """
        解读风险信息

        Args:
            state: 包含risk_assessment的全局状态

        Returns:
            更新后的state，包含risk_explanation字段
        """
        risk_assessment = state.get("risk_assessment", {})

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(
                content=f"""
请用大白话解读以下风险评估，让新手用户能看懂：

风险等级: {risk_assessment.get('risk_level', 'N/A')}
风险因素: {risk_assessment.get('risk_factors', [])}
建议操作: {risk_assessment.get('recommendations', [])}

要求：
1. 用最简单的语言说明有什么风险
2. 用生活中的例子类比风险程度
3. 明确告知可能的后果
4. 提供具体的解决方案
5. 语气严肃但不吓人
6. 不超过200字
"""
            ),
        ]

        response = await self.llm.ainvoke(messages)
        state["risk_explanation"] = response.content
        return state

    async def explain_transaction(self, state: Dict) -> Dict:
        """
        解读交易内容

        Args:
            state: 包含transaction的全局状态

        Returns:
            更新后的state，包含transaction_explanation字段
        """
        transaction = state.get("transaction", {})

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(
                content=f"""
请用大白话解读以下交易，让新手用户能看懂：

交易类型: {transaction.get('type', 'N/A')}
涉及金额: {transaction.get('amount', 'N/A')}
目标地址: {transaction.get('to', 'N/A')}
预估费用: {transaction.get('fee', 'N/A')} SOL

要求：
1. 用一句话说明这笔交易要做什么
2. 告诉用户钱会怎么流动
3. 解释费用是否合理
4. 提醒需要注意的地方
5. 不超过150字
"""
            ),
        ]

        response = await self.llm.ainvoke(messages)
        state["transaction_explanation"] = response.content
        return state

    async def answer_question(self, state: Dict) -> Dict:
        """
        回答用户问题（保持上下文）

        Args:
            state: 包含user_question和conversation_history的全局状态

        Returns:
            更新后的state，包含answer字段
        """
        user_question = state.get("user_question", "")
        conversation_history = state.get("conversation_history", [])

        messages = [
            SystemMessage(content=self.system_prompt),
        ]

        # 添加历史对话
        messages.extend(conversation_history[-10:])  # 保留最近10轮对话

        # 添加当前问题
        messages.append(
            HumanMessage(
                content=f"""
用户问题: {user_question}

请用大白话回答，要求：
1. 简单易懂，避免专业术语
2. 如果必须用术语，要解释清楚
3. 用例子和类比帮助理解
4. 语气友好、耐心
5. 不超过200字
"""
            )
        )

        response = await self.llm.ainvoke(messages)
        state["answer"] = response.content

        # 更新对话历史
        conversation_history.append(HumanMessage(content=user_question))
        conversation_history.append(response)
        state["conversation_history"] = conversation_history

        return state

    async def __call__(self, state: Dict) -> Dict:
        """
        Agent主入口
        """
        # 根据任务类型选择解读方式
        task_type = state.get("task_type")

        if task_type == "wallet_analysis":
            state = await self.explain_wallet_data(state)
        elif task_type == "strategy_generation":
            state = await self.explain_strategy(state)
        elif task_type == "risk_check":
            state = await self.explain_risk(state)
        elif task_type == "transaction_preview":
            state = await self.explain_transaction(state)
        elif task_type == "question_answering":
            state = await self.answer_question(state)

        return state
