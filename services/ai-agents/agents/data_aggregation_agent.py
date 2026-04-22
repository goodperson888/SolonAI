"""
DataAggregationAgent - 数据聚合

职责：从区块链获取钱包资产、DeFi协议数据等。
支持 Mock 模式用于开发和测试。
"""

import os
import sys
from datetime import datetime
from typing import Dict

# 添加 blockchain 服务路径
current_dir = os.path.dirname(os.path.abspath(__file__))
services_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
sys.path.insert(0, services_root)

from mock.chain_data import (
    generate_mock_defi,
    generate_mock_risk,
    generate_mock_wallet,
)

# Mock 模式下的协议数据
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

# 小协议 TVL 阈值（USD）
SMALL_PROTOCOL_TVL_THRESHOLD = 100_000_000


class DataAggregationAgent:
    """链上数据聚合Agent - 多源数据聚合、数据清洗、标准化处理"""

    name = "data_aggregation_agent"
    description = "聚合链上资产和DeFi协议数据"

    def __init__(self, llm=None, blockchain_service=None, use_mock: bool = True):
        self.llm = llm
        self.blockchain_service = blockchain_service
        self.use_mock = use_mock
        self.system_prompt = """你是Solon AI的链上数据聚合专家。
你的职责是：
1. 从多个数据源获取链上数据（Solana RPC、Helius、DeFi协议API）
2. 清洗和标准化数据格式
3. 识别异常数据并告警
4. 实时更新数据缓存

核心能力：
- 多源数据聚合
- 数据清洗与验证
- 标准化处理
- 实时更新
- 异常数据告警
"""

    async def aggregate_wallet_data(self, state: Dict) -> Dict:
        """
        聚合用户钱包数据

        Args:
            state: 包含wallet_address的全局状态

        Returns:
            更新后的state，包含wallet_data字段
        """
        wallet_address = state.get("wallet_address")

        if self.use_mock:
            wallet_data = generate_mock_wallet(
                address=wallet_address or "Unknown",
                include_low_health=True,
            )
        else:
            # 真实模式：调用区块链服务
            wallet_data = {
                "address": wallet_address,
                "balances": {},
                "nfts": [],
                "lp_positions": [],
                "lending_positions": [],
                "authorizations": [],
                "total_value_usd": 0.0,
                "last_updated": None,
            }
            if self.blockchain_service:
                # TODO: 对接真实区块链服务
                pass

        # 数据清洗：过滤零值余额
        wallet_data["balances"] = {
            mint: info
            for mint, info in wallet_data["balances"].items()
            if info.get("usd_value", 0) > 0
        }

        # 重新计算 total_value_usd
        wallet_data["total_value_usd"] = sum(
            info["usd_value"] for info in wallet_data["balances"].values()
        )

        # 异常检测：标记价格异常
        anomaly_detection = []
        for mint, info in wallet_data["balances"].items():
            amount = info.get("amount", 0)
            usd_value = info.get("usd_value", 0)
            if amount > 0 and usd_value > 0:
                price_per_unit = usd_value / amount
                symbol = info.get("token_info", {}).get("symbol", mint[:8])
                # 简单异常检测逻辑：SOL 价格应在合理范围
                if symbol == "SOL" and (price_per_unit < 50 or price_per_unit > 500):
                    anomaly_detection.append({
                        "type": "price_anomaly",
                        "token": symbol,
                        "message": f"{symbol} 价格异常: ${price_per_unit:.2f}",
                    })

        wallet_data["anomaly_detection"] = anomaly_detection
        wallet_data["last_updated"] = datetime.now().isoformat()

        state["wallet_data"] = wallet_data
        return state

    async def aggregate_defi_data(self, state: Dict) -> Dict:
        """
        聚合DeFi协议数据

        Args:
            state: 全局状态

        Returns:
            更新后的state，包含defi_data字段
        """
        if self.use_mock:
            defi_data = generate_mock_defi()
        else:
            defi_data = {
                "lending_protocols": {},
                "liquidity_pools": {},
                "staking_protocols": {},
                "last_updated": None,
            }
            if self.blockchain_service:
                # TODO: 对接真实区块链服务
                pass

        # APY 排序：按 supply_apy 降序
        protocols = defi_data["lending_protocols"]
        sorted_protocols = dict(
            sorted(protocols.items(), key=lambda x: x[1].get("supply_apy", 0), reverse=True)
        )
        defi_data["lending_protocols"] = sorted_protocols

        # 标记小协议
        for _name, info in defi_data["lending_protocols"].items():
            info["is_small_protocol"] = info.get("tvl", 0) < SMALL_PROTOCOL_TVL_THRESHOLD

        defi_data["last_updated"] = datetime.now().isoformat()

        state["defi_data"] = defi_data
        return state

    async def aggregate_risk_data(self, state: Dict) -> Dict:
        """
        聚合风险数据

        Args:
            state: 全局状态

        Returns:
            更新后的state，包含risk_data字段
        """
        if self.use_mock:
            risk_data = generate_mock_risk()
        else:
            risk_data = {
                "blacklist_addresses": set(),
                "risky_tokens": {},
                "phishing_patterns": [],
                "protocol_audits": {},
                "last_updated": None,
            }
            if self.blockchain_service:
                # TODO: 对接真实区块链服务
                pass

        # 黑名单地址格式校验
        validated_blacklist = set()
        for addr in risk_data.get("blacklist_addresses", set()):
            if isinstance(addr, str) and 32 <= len(addr) <= 44:
                validated_blacklist.add(addr)
        risk_data["blacklist_addresses"] = validated_blacklist

        risk_data["last_updated"] = datetime.now().isoformat()

        state["risk_data"] = risk_data
        return state

    async def validate_data(self, data: Dict) -> bool:
        """
        验证数据完整性和准确性

        Args:
            data: 待验证的数据

        Returns:
            是否通过验证
        """
        # 检查是否为钱包数据（有 address + balances 字段）
        if "address" in data and "balances" in data:
            required_wallet_fields = [
                "address", "balances", "nfts", "lp_positions",
                "lending_positions", "authorizations", "total_value_usd", "last_updated",
            ]
            for field in required_wallet_fields:
                if field not in data:
                    return False

            # 数值合理性检查：余额 >= 0
            for _mint, info in data.get("balances", {}).items():
                if info.get("amount", 0) < 0:
                    return False

            return True

        # 检查是否为 DeFi 数据（有 lending_protocols 字段）
        if "lending_protocols" in data:
            for _name, info in data.get("lending_protocols", {}).items():
                supply_apy = info.get("supply_apy", 0)
                if supply_apy < 0 or supply_apy > 500:
                    return False
            return True

        # 检查是否为风险数据（有 blacklist_addresses 字段）
        if "blacklist_addresses" in data:
            return True

        # 未知数据类型，无法验证
        return False

    async def __call__(self, state: Dict) -> Dict:
        """
        Agent主入口
        """
        # 根据任务类型聚合不同的数据
        task_type = state.get("task_type")

        if task_type == "wallet_analysis":
            state = await self.aggregate_wallet_data(state)
        elif task_type == "strategy_generation":
            state = await self.aggregate_wallet_data(state)
            state = await self.aggregate_defi_data(state)
        elif task_type == "risk_check":
            state = await self.aggregate_wallet_data(state)
            state = await self.aggregate_risk_data(state)
        else:
            # 默认聚合所有数据
            state = await self.aggregate_wallet_data(state)
            state = await self.aggregate_defi_data(state)
            state = await self.aggregate_risk_data(state)

        state["current_agent"] = self.name
        return state
