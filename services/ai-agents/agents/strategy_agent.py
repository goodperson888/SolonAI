"""
StrategyAgent - 策略生成

职责：基于用户需求和链上数据，生成 DeFi 投资策略。
包含收益测算、风险评级、操作步骤拆解。
"""

import json
import re
from typing import Any, Dict

from base_agent import BaseAgent
from prompts import get_prompt


class StrategyAgent(BaseAgent):
    name = "strategy_agent"
    description = "基于用户需求生成DeFi策略"

    @property
    def system_prompt(self) -> str:
        """从文件加载 system prompt"""
        return get_prompt("strategy_agent", language="zh", version="v1")

    # 原 prompt 已移至 prompts/strategy_agent_zh_v1.txt
    # 如需修改 prompt，请编辑该文件

    @staticmethod
    def _get_available_balance(wallet_assets: list[dict], token: str) -> float:
        normalized_token = (token or "").upper()
        for asset in wallet_assets:
            symbol = (asset.get("symbol") or asset.get("token") or "").upper()
            if symbol == normalized_token:
                return float(asset.get("balance", 0) or 0)
        return 0.0

    @staticmethod
    def _sanitize_strategy_amounts(
        strategy: Dict[str, Any],
        wallet_assets: list[dict],
        default_token: str,
    ) -> Dict[str, Any]:
        steps = strategy.get("steps") or []
        sanitized_steps = []
        total_investment = 0.0

        for index, step in enumerate(steps, start=1):
            new_step = dict(step)
            token = new_step.get("token") or default_token or "SOL"
            available_balance = StrategyAgent._get_available_balance(wallet_assets, token)
            amount = new_step.get("amount")

            try:
                numeric_amount = float(amount)
            except (TypeError, ValueError):
                numeric_amount = 0.0

            if available_balance > 0 and (numeric_amount <= 0 or numeric_amount > available_balance):
                numeric_amount = available_balance

            if numeric_amount > 0:
                total_investment += numeric_amount
                new_step["amount"] = numeric_amount
                if new_step.get("description"):
                    new_step["description"] = (
                        str(new_step["description"])
                        .replace("5000 SOL", f"{numeric_amount:g} {token}")
                        .replace("5000 USDC", f"{numeric_amount:g} {token}")
                    )

            new_step["step"] = new_step.get("step", index)
            new_step["token"] = token
            sanitized_steps.append(new_step)

        strategy["steps"] = sanitized_steps
        if total_investment > 0:
            strategy["total_investment"] = total_investment

        return strategy

    @staticmethod
    def _localize_strategy_copy(strategy: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        if not re.search(r"[\u4e00-\u9fff]", user_input or ""):
            return strategy

        risk_level = str(strategy.get("risk_level", "balanced")).lower()
        token = strategy.get("steps", [{}])[0].get("token") or "SOL"
        risk_label_map = {
            "conservative": "保守型",
            "balanced": "稳健型",
            "aggressive": "进取型",
        }
        localized_title = f"{risk_label_map.get(risk_level, '稳健型')}{token}投资策略"

        current_title = str(strategy.get("title") or strategy.get("strategy_name") or "").strip()
        if not current_title or re.fullmatch(r"[A-Za-z0-9 ._-]+", current_title):
            strategy["title"] = localized_title
            strategy["strategy_name"] = localized_title

        localized_steps = []
        for step in strategy.get("steps", []) or []:
            new_step = dict(step)
            description = str(new_step.get("description") or "").strip()
            action = str(new_step.get("action") or "").lower()
            protocol = str(new_step.get("protocol") or "当前协议")
            amount = new_step.get("amount")
            token_symbol = new_step.get("token") or token
            amount_text = f"{float(amount):g}" if isinstance(amount, (int, float)) else str(amount or "")

            if description and re.fullmatch(r"[A-Za-z0-9 .,:_%()/-]+", description):
                if action == "deposit":
                    new_step["description"] = f"将 {amount_text} {token_symbol} 存入 {protocol} 赚取利息。"
                elif action == "swap":
                    new_step["description"] = f"通过 {protocol} 将 {amount_text} {token_symbol} 调整为目标资产。"
                elif action == "provide_liquidity":
                    new_step["description"] = f"把 {amount_text} {token_symbol} 投入 {protocol} 流动性池获取收益。"
            localized_steps.append(new_step)

        strategy["steps"] = localized_steps
        return strategy

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """生成投资策略"""
        intent_params = state.get("intent_params", {})
        wallet_assets = state.get("wallet_assets", [])
        protocol_data = state.get("protocol_data", {})

        # 构建给 LLM 的输入
        prompt_input = f"""
用户需求：
- 风险偏好：{intent_params.get("risk_level", "conservative")}
- 投资金额：{intent_params.get("amount", "未指定")}
- 指定代币：{intent_params.get("token", "未指定")}

用户当前持仓：
{json.dumps(wallet_assets, ensure_ascii=False, indent=2)}

可用协议数据：
{json.dumps(protocol_data, ensure_ascii=False, indent=2)}

请生成一个可执行的 DeFi 投资策略。"""

        result = await self.call_llm_json(prompt_input)

        if result.get("parse_error"):
            sol_balance = 0.0
            for asset in wallet_assets:
                symbol = asset.get("symbol") or asset.get("token")
                if symbol == "SOL":
                    sol_balance = float(asset.get("balance", 0) or 0)
                    break

            fallback_amount = intent_params.get("amount")
            if fallback_amount in (None, "", "未指定"):
                fallback_amount = sol_balance if sol_balance > 0 else 1

            # 降级：返回一个默认的保守策略
            result = {
                "strategy_name": "MarginFi 稳健生息",
                "title": "MarginFi 稳健生息",
                "protocol": "MarginFi",
                "risk_level": "conservative",
                "expected_apy": 8.2,
                "estimated_apy": 8.2,
                "protocols": ["MarginFi"],
                "steps": [
                    {
                        "step": 1,
                        "action": "deposit",
                        "protocol": "MarginFi",
                        "token": intent_params.get("token", "SOL"),
                        "amount": fallback_amount,
                        "expected_apy": 8.2,
                        "description": f"将 {fallback_amount} {intent_params.get('token', 'SOL')} 存入 MarginFi 赚取利息",
                    }
                ],
                "risk_warnings": ["协议合约风险"],
                "total_investment": fallback_amount,
                "estimated_daily_income": round(float(fallback_amount) * 0.082 / 365, 4),
                "estimated_monthly_income": round(float(fallback_amount) * 0.082 / 12, 4),
            }

        result = self._sanitize_strategy_amounts(
            result,
            wallet_assets,
            intent_params.get("token", "SOL"),
        )
        result = self._localize_strategy_copy(result, state.get("user_input", ""))

        state["strategy"] = result
        state["current_agent"] = self.name
        return state
