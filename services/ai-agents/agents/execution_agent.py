"""
ExecutionAgent - 执行协调

职责：将策略转换为可执行的链上交易指令。
生成交易预览，等待用户确认后协调执行。

注意：Solon AI 是非托管的，不碰用户私钥。
所有交易都是生成指令 → 用户钱包签名 → 广播上链。
"""

import json
from typing import Any, Dict

from base_agent import BaseAgent
from prompts import get_prompt


class ExecutionAgent(BaseAgent):
    name = "execution_agent"
    description = "将策略转换为链上交易指令"

    @property
    def system_prompt(self) -> str:
        """从文件加载 system prompt"""
        return get_prompt("execution_agent", language="zh", version="v1")

    # 原 prompt 已移至 prompts/execution_agent_zh_v1.txt
    # 如需修改 prompt，请编辑该文件

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """构建交易指令"""
        strategy = state.get("strategy", {})
        wallet_address = state.get("wallet_address", "")

        prompt_input = f"""
请为以下策略构建交易指令：

策略：
{json.dumps(strategy, ensure_ascii=False, indent=2)}

用户钱包地址：{wallet_address or "待用户连接钱包"}

请生成详细的交易步骤，包括每步的 Gas 费预估。"""

        result = await self.call_llm_json(prompt_input)

        if result.get("parse_error"):
            # 降级：根据策略构建简单的交易指令
            steps = strategy.get("steps", [])
            result = {
                "transaction_id": "tx_001",
                "type": "deposit",
                "steps": [
                    {
                        "step": i + 1,
                        "action": s.get("action", "deposit"),
                        "protocol": s.get("protocol", "unknown"),
                        "token": s.get("token", "SOL"),
                        "amount": s.get("amount", 0),
                        "description": s.get("description", ""),
                        "estimated_gas": 0.000005,
                    }
                    for i, s in enumerate(steps)
                ],
                "total_gas": 0.000005 * len(steps),
                "requires_signature": True,
                "warnings": ["请确认金额无误后再签名"],
            }

        state["transaction"] = result
        state["current_agent"] = self.name
        return state
