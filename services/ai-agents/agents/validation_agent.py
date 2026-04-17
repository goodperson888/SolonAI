"""
ValidationAgent - 结果验证

职责：校验其他 Agent 输出的准确性，拦截幻觉，确保合规。
"""

from typing import Any, Dict

from base_agent import BaseAgent


# 已知协议白名单
KNOWN_PROTOCOLS = [
    "MarginFi",
    "Jupiter",
    "Raydium",
    "Orca",
    "Kamino",
    "Drift",
    "Marinade",
    "Jito",
]

# 合规违禁词
FORBIDDEN_WORDS = ["保本", "无风险", "稳赚", "保证收益", "零风险", "必赚"]


class ValidationAgent(BaseAgent):
    name = "validation_agent"
    description = "校验结果准确性，拦截幻觉"

    @property
    def system_prompt(self) -> str:
        return """你是结果校验专家，负责检查其他 Agent 输出的准确性。
你的核心原则：
1. 零容忍幻觉：所有信息必须有依据
2. 严格合规：不能有投资建议、保本承诺等违规内容
3. 用户安全第一：有疑问的内容一律标记"""

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """验证策略和风控结果"""
        strategy = state.get("strategy", {})
        risk_assessment = state.get("risk_assessment", {})

        errors = []
        warnings = []

        # 1. 校验协议是否真实存在
        protocols = strategy.get("protocols", [])
        for p in protocols:
            if p not in KNOWN_PROTOCOLS:
                errors.append(f"未知协议 '{p}'，可能是幻觉")

        # 2. 校验 APY 合理性
        expected_apy = strategy.get("expected_apy", 0)
        if isinstance(expected_apy, (int, float)):
            if expected_apy > 100:
                warnings.append(f"APY {expected_apy}% 异常高，可能存在风险或数据错误")
            elif expected_apy > 50:
                warnings.append(f"APY {expected_apy}% 偏高，建议用户谨慎评估")

        # 3. 合规性检查
        strategy_str = str(strategy)
        for word in FORBIDDEN_WORDS:
            if word in strategy_str:
                errors.append(f"包含违规词汇 '{word}'，违反合规要求")

        # 4. 步骤完整性检查
        steps = strategy.get("steps", [])
        if not steps:
            warnings.append("策略缺少具体操作步骤")

        state["validation_result"] = {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

        state["current_agent"] = self.name
        return state
