"""
DataAggregationAgent - 数据聚合

职责：从区块链获取钱包资产、DeFi协议数据等。
集成真实的 Solana 区块链数据。
"""

from typing import Any, Dict
import sys
import os

# 添加 blockchain 服务路径
current_dir = os.path.dirname(os.path.abspath(__file__))
services_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
sys.path.insert(0, services_root)

from base_agent import BaseAgent
from blockchain.solana_client import SolanaClient


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
        return """你是数据聚合助手，负责整理链上数据。
根据用户意图，筛选并整理相关的链上数据。
直接返回整理后的数据摘要。"""

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

                # 获取 Token 账户
                token_accounts = await solana_client.get_token_accounts(wallet_address)

                # TODO: 接入价格 API，暂时使用固定价格
                sol_price = 178.32

                # 转换为 Agent 使用的格式
                wallet_assets = []

                # 添加 SOL
                if sol_balance > 0:
                    wallet_assets.append({
                        "token": "SOL",
                        "balance": sol_balance,
                        "price_usd": sol_price,
                        "value_usd": sol_balance * sol_price,
                    })
                    print(f"[DataAggregationAgent] 添加 SOL 资产: {sol_balance} SOL = ${sol_balance * sol_price}")
                else:
                    print(f"[DataAggregationAgent] SOL 余额为 0，不添加资产")

                # TODO: 解析 Token 账户数据
                # 目前 token_accounts 返回原始数据，需要进一步解析

                print(f"[DataAggregationAgent] 最终资产列表: {wallet_assets}")
                state["wallet_assets"] = wallet_assets
                state["total_value_usd"] = sol_balance * sol_price

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

        # DeFi 协议数据（目前使用 Mock）
        state["protocol_data"] = MOCK_PROTOCOL_DATA

        state["current_agent"] = self.name
        return state
