"""
DataAggregationAgent - 数据聚合

职责：从区块链获取钱包资产、DeFi协议数据等。
集成真实的 Solana 区块链数据。
"""

import os
import sys
from typing import Any, Dict

# 添加 blockchain 服务路径
current_dir = os.path.dirname(os.path.abspath(__file__))
services_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
sys.path.insert(0, services_root)

from base_agent import BaseAgent  # noqa: E402
from blockchain.services.defi_aggregation_service import DeFiAggregationService  # noqa: E402
from blockchain.services.wallet_service import WalletService  # noqa: E402
from blockchain.solana_client import SolanaClient  # noqa: E402
from prompts import get_prompt  # noqa: E402

# ===== Mock DeFi 协议数据（后续可对接真实协议 API）=====

MOCK_PROTOCOL_DATA = {
    "marginfi": {
        "name": "MarginFi",
        "type": "lending",
        "apy": {"SOL": 6.5, "USDC": 8.2, "USDT": 7.8},
        "tvl": 850_000_000,
    },
    "raydium": {
        "name": "Raydium",
        "type": "dex",
        "pools": {
            "SOL-USDC": {"apy": 25.3, "tvl": 120_000_000},
            "RAY-USDC": {"apy": 45.7, "tvl": 35_000_000},
        },
    },
    "jupiter": {
        "name": "Jupiter",
        "type": "aggregator",
        "supported_tokens": ["SOL", "USDC", "USDT", "JUP", "RAY", "BONK"],
    },
    "orca": {
        "name": "Orca",
        "type": "dex",
        "pools": {
            "SOL-USDC": {"apy": 22.1, "tvl": 95_000_000},
        },
    },
}


class DataAggregationAgent(BaseAgent):
    name = "data_aggregation_agent"
    description = "聚合链上资产和DeFi协议数据"

    def __init__(self, llm):
        super().__init__(llm)
        # 不在初始化时创建客户端，每次请求时创建新的

    @property
    def system_prompt(self) -> str:
        """从文件加载 system prompt"""
        return get_prompt("data_aggregation_agent", language="zh", version="v1")

    # 原 prompt 已移至 prompts/data_aggregation_agent_zh_v1.txt
    # 如需修改 prompt，请编辑该文件

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取并整理链上数据
        """
        wallet_address = state.get("wallet_address")

        if wallet_address:
            # 每次请求创建新的客户端
            solana_client = SolanaClient()

            try:
                # 获取 SOL 余额
                sol_balance = await solana_client.get_sol_balance(wallet_address)
                print(f"[DataAggregationAgent] 钱包地址: {wallet_address}")
                print(f"[DataAggregationAgent] SOL 余额: {sol_balance}")

                # 获取 Token 账户（暂未使用，待实现）
                # token_accounts = await solana_client.get_token_accounts(wallet_address)

                # Prefer the shared real-time price service; fall back to a
                # conservative zero value rather than stale hard-coded prices.
                defi_service = DeFiAggregationService()
                try:
                    prices = await defi_service.get_realtime_prices()
                    sol_price = prices.get("SOL", {}).get("price_usd") or 0
                finally:
                    await defi_service.close()

                # 转换为 Agent 使用的格式
                wallet_assets = []

                # 添加 SOL
                if sol_balance > 0:
                    wallet_assets.append(
                        {
                            "token": "SOL",
                            "balance": sol_balance,
                            "price_usd": sol_price,
                            "value_usd": sol_balance * sol_price,
                        }
                    )
                    print(
                        "[DataAggregationAgent] 添加 SOL 资产: "
                        f"{sol_balance} SOL = ${sol_balance * sol_price}"
                    )
                else:
                    print("[DataAggregationAgent] SOL 余额为 0，不添加资产")

                try:
                    wallet_service = WalletService()
                    try:
                        portfolio = await wallet_service.get_wallet_portfolio(wallet_address)
                    finally:
                        await wallet_service.close()

                    for token in portfolio.tokens:
                        wallet_assets.append(
                            {
                                "token": token.symbol or token.mint[:8],
                                "mint": token.mint,
                                "balance": float(token.balance),
                                "price_usd": (
                                    float(token.usd_value / token.balance)
                                    if token.usd_value and token.balance
                                    else 0
                                ),
                                "value_usd": float(token.usd_value or 0),
                            }
                        )
                    state["total_value_usd"] = float(portfolio.total_usd_value)
                except Exception as e:
                    print(f"[DataAggregationAgent] Token 资产聚合失败，保留 SOL 数据: {e}")
                    state["total_value_usd"] = sol_balance * sol_price

                print(f"[DataAggregationAgent] 最终资产列表: {wallet_assets}")
                state["wallet_assets"] = wallet_assets

            except Exception as e:
                print(f"Error fetching wallet assets: {e}")
                import traceback

                traceback.print_exc()
                # 如果获取失败，使用空数据
                state["wallet_assets"] = []
                state["total_value_usd"] = 0
            finally:
                # 关闭客户端连接
                await solana_client.close()
        else:
            # 没有钱包地址，使用空数据
            state["wallet_assets"] = []
            state["total_value_usd"] = 0

        try:
            defi_service = DeFiAggregationService()
            try:
                overview = await defi_service.get_overview()
            finally:
                await defi_service.close()
            state["protocol_data"] = overview.get("yields", {}).get("protocols", {})
            state["market_prices"] = overview.get("prices", {})
            state["defi_best_opportunities"] = overview.get("yields", {}).get(
                "best_opportunities",
                [],
            )
        except Exception as e:
            print(f"[DataAggregationAgent] DeFi 聚合失败，使用 Mock 数据: {e}")
            state["protocol_data"] = MOCK_PROTOCOL_DATA

        state["current_agent"] = self.name
        return state
