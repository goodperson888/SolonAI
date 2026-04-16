"""
结果校验Agent
职责：所有智能体的输出结果都需经过该Agent校验，确保内容准确、无幻觉、符合用户需求、合规要求
"""

from typing import Dict, List

from langchain_core.messages import HumanMessage, SystemMessage


class ValidationAgent:
    """结果校验Agent - 结果准确性校验、幻觉识别、合规校验、格式标准化"""

    def __init__(self, llm, rag_knowledge_base):
        self.llm = llm
        self.rag = rag_knowledge_base
        self.system_prompt = """你是Solon AI的结果校验专家。
你的职责是：
1. 校验其他Agent输出的准确性
2. 识别和拦截大模型幻觉
3. 确保输出符合合规要求
4. 标准化输出格式

核心原则：
- 零容忍幻觉：所有信息必须有依据
- 严格合规：不能有投资建议、保本承诺等违规内容
- 格式规范：输出必须符合预定义的格式
- 用户安全第一：有疑问的内容一律拒绝

校验标准：
1. 事实准确性：协议名称、APY数据、地址等必须准确
2. 逻辑一致性：策略步骤、风险评估必须逻辑自洽
3. 合规性：不能有违规表述
4. 完整性：必填字段不能缺失
"""

    async def validate_strategy(self, state: Dict) -> Dict:
        """
        校验策略生成结果

        Args:
            state: 包含strategy的全局状态

        Returns:
            更新后的state，包含validation_result字段
        """
        strategy = state.get("strategy", {})

        # TODO: AI团队实现以下校验逻辑
        # 1. 校验协议名称是否真实存在
        # 2. 校验APY数据是否合理（对比RAG知识库）
        # 3. 校验策略步骤是否可执行
        # 4. 校验风险评级是否准确
        # 5. 检查是否有幻觉内容（虚构的协议、不存在的功能）
        # 6. 检查合规性（是否有保本承诺、投资建议等违规内容）

        validation_result = {"is_valid": True, "errors": [], "warnings": [], "suggestions": []}

        # 示例：校验协议名称
        protocol_name = strategy.get("protocol")
        if protocol_name:
            # 从RAG知识库查询协议信息
            protocol_info = await self._check_protocol_exists(protocol_name)
            if not protocol_info:
                validation_result["is_valid"] = False
                validation_result["errors"].append(
                    {
                        "field": "protocol",
                        "message": f"协议 '{protocol_name}' 不存在或未被支持",
                        "action": "reject",
                    }
                )

        # 示例：校验APY合理性
        expected_apy = strategy.get("expected_apy", 0)
        if expected_apy > 100:  # APY超过100%需要特别警惕
            validation_result["warnings"].append(
                {
                    "field": "expected_apy",
                    "message": f"APY {expected_apy}% 异常高，可能存在风险",
                    "action": "warn_user",
                }
            )

        # 示例：检查合规性
        description = strategy.get("description", "")
        forbidden_words = ["保本", "无风险", "稳赚", "保证收益"]
        for word in forbidden_words:
            if word in description:
                validation_result["is_valid"] = False
                validation_result["errors"].append(
                    {
                        "field": "description",
                        "message": f"包含违规词汇 '{word}'，违反合规要求",
                        "action": "rewrite",
                    }
                )

        state["validation_result"] = validation_result
        return state

    async def validate_risk_assessment(self, state: Dict) -> Dict:
        """
        校验风险评估结果

        Args:
            state: 包含risk_assessment的全局状态

        Returns:
            更新后的state，包含validation_result字段
        """
        # TODO: AI团队实现以下校验逻辑
        # 1. 校验风险等级是否合理
        # 2. 校验风险因素是否真实存在
        # 3. 校验黑名单数据是否准确
        # 4. 检查是否遗漏重要风险

        validation_result = {"is_valid": True, "errors": [], "warnings": []}

        state["validation_result"] = validation_result
        return state

    async def validate_transaction(self, state: Dict) -> Dict:
        """
        校验交易指令

        Args:
            state: 包含transaction的全局状态

        Returns:
            更新后的state，包含validation_result字段
        """
        transaction = state.get("transaction", {})

        # TODO: AI团队实现以下校验逻辑
        # 1. 校验交易参数完整性
        # 2. 校验目标地址有效性
        # 3. 校验金额合理性
        # 4. 校验Gas费是否异常
        # 5. 检查是否有恶意指令

        validation_result = {"is_valid": True, "errors": [], "warnings": []}

        # 示例：校验金额
        amount = transaction.get("amount", 0)
        if amount <= 0:
            validation_result["is_valid"] = False
            validation_result["errors"].append(
                {"field": "amount", "message": "交易金额必须大于0", "action": "reject"}
            )

        # 示例：校验Gas费
        gas_fee = transaction.get("gas_fee", 0)
        if gas_fee > 0.1:  # Gas费超过0.1 SOL需要警告
            validation_result["warnings"].append(
                {
                    "field": "gas_fee",
                    "message": f"Gas费 {gas_fee} SOL 异常高，请确认",
                    "action": "warn_user",
                }
            )

        state["validation_result"] = validation_result
        return state

    async def check_for_hallucination(self, content: str, context: Dict) -> List[str]:
        """
        检查内容是否存在幻觉

        Args:
            content: 待检查的内容
            context: 上下文信息

        Returns:
            幻觉列表
        """
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(
                content=f"""
请检查以下内容是否存在幻觉（虚构的信息）：

内容: {content}

上下文: {context}

请识别：
1. 虚构的协议名称
2. 不存在的功能
3. 错误的数据
4. 不合理的承诺

如果发现幻觉，请列出具体内容。
"""
            ),
        ]

        await self.llm.ainvoke(messages)

        # TODO: AI团队解析LLM响应，提取幻觉列表
        hallucinations = []

        return hallucinations

    async def _check_protocol_exists(self, protocol_name: str) -> Dict:
        """
        从RAG知识库检查协议是否存在

        Args:
            protocol_name: 协议名称

        Returns:
            协议信息，如果不存在返回None
        """
        # TODO: AI团队实现RAG查询
        # 从知识库中查询协议信息

        # 示例返回
        known_protocols = ["MarginFi", "Jupiter", "Raydium", "Kamino", "Drift"]
        if protocol_name in known_protocols:
            return {"name": protocol_name, "exists": True}
        return None

    async def generate_rewrite_instruction(self, validation_result: Dict) -> str:
        """
        生成重写指令

        Args:
            validation_result: 校验结果

        Returns:
            重写指令
        """
        errors = validation_result.get("errors", [])

        if not errors:
            return ""

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(
                content=f"""
以下内容校验失败，请生成重写指令：

错误列表: {errors}

请生成清晰的重写指令，告诉原Agent如何修正。
"""
            ),
        ]

        response = await self.llm.ainvoke(messages)
        return response.content

    async def __call__(self, state: Dict) -> Dict:
        """
        Agent主入口
        """
        # 根据任务类型选择校验方式
        task_type = state.get("task_type")

        if task_type == "strategy_generation":
            state = await self.validate_strategy(state)
        elif task_type == "risk_check":
            state = await self.validate_risk_assessment(state)
        elif task_type == "transaction_preview":
            state = await self.validate_transaction(state)

        # 如果校验失败，生成重写指令
        validation_result = state.get("validation_result", {})
        if not validation_result.get("is_valid"):
            rewrite_instruction = await self.generate_rewrite_instruction(validation_result)
            state["rewrite_instruction"] = rewrite_instruction
            state["needs_rewrite"] = True

        return state
