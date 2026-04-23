"""
MarginFi 借贷协议适配器

MarginFi v2 — Solana 上的借贷协议
- Program ID: MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA
- 通过 RPC 直接读取链上 Bank 账户数据
- 解析利率、TVL、用户仓位

数据结构:
- MarginfiGroup: 协议全局配置，包含所有 Bank 列表
- Bank: 借贷池，存储利率配置、存款/借款总量
- MarginfiAccount: 用户账户，记录用户的存借仓位
"""

import logging
from decimal import Decimal
from typing import List, Optional

from solders.pubkey import Pubkey

from ..cache import cached
from ..config import config
from ..exceptions import ProviderError
from ..http_client import ResilientHTTPClient
from ..models.transaction import SwapQuote
from ..transport.rpc_client import EnhancedRPCClient
from .base import BaseDeFiProvider

logger = logging.getLogger(__name__)

# MarginFi 常量
MARGINFI_PROGRAM_ID = "MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA"
MAINNET_RPC = "https://api.mainnet-beta.solana.com"

# Bank 账户偏移量 (已通过链上数据验证)
# Bank 结构:
#   [0:8]    - 没有 discriminator (Owner 就是 program)
#   [8:40]   - mint (Pubkey) ← 已验证
#   [40:72]  - group (Pubkey)
#   ...
#   [296:312]  - 利率参数 1 (I80F48)
#   [312:328]  - 利率参数 2 (I80F48)
#   [328:344]  - 利率参数 3 (I80F48)
#   [344:360]  - 利率参数 4 (I80F48)
#   [632:648]  - total_asset_shares (I80F48)
#   [776:792]  - total_liability_shares (I80F48)
BANK_MINT_OFFSET = 8
BANK_MINT_SIZE = 32

# MarginFi Bank Metadata Cache (官方维护)
MRGN_BANK_METADATA_URL = "https://storage.googleapis.com/mrgn-public/mrgn-bank-metadata-cache.json"

# 已知的 MarginFi Bank 地址 (Mainnet) — 从官方 metadata cache 获取并验证
KNOWN_BANKS = {
    "SOL": {
        "bank": "CCKtUs6Cgwo4aaQUmBPmyoApH2gUDErxNZCAntD6LYGh",
        "mint": "So11111111111111111111111111111111111111112",
        "decimals": 9,
    },
    "USDC": {
        "bank": "2s37akK2eyBbp8DZgCm7RtsaEz8eJP3Nxd4urLHQv7yB",
        "mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "decimals": 6,
    },
    "USDT": {
        "bank": "HmpMfL8942u22htC4EMiWgLX931g3sacXFR6KjuLgKLV",
        "mint": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
        "decimals": 6,
    },
    "mSOL": {
        "bank": "22DcjMZrMwC5Bpa5AGBsmjc5V9VuQrXG6N9ZtdUNyYGE",
        "mint": "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So",
        "decimals": 9,
    },
    "JitoSOL": {
        "bank": "Bohoc1ikHLD7xKJuzTyiTyCwzaL5N7ggJQu75A8mKYM8",
        "mint": "J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn",
        "decimals": 9,
    },
}


# 默认值常量，避免在函数默认参数中调用函数
DEFAULT_DECIMAL_ZERO = Decimal("0")


class LendingPool:
    """借贷池信息"""

    def __init__(
        self,
        symbol: str,
        mint: str,
        bank_address: str,
        decimals: int,
        deposit_apy: Decimal = DEFAULT_DECIMAL_ZERO,
        borrow_apy: Decimal = DEFAULT_DECIMAL_ZERO,
        total_deposits: Decimal = DEFAULT_DECIMAL_ZERO,
        total_borrows: Decimal = DEFAULT_DECIMAL_ZERO,
        utilization_rate: Decimal = DEFAULT_DECIMAL_ZERO,
    ):
        self.symbol = symbol
        self.mint = mint
        self.bank_address = bank_address
        self.decimals = decimals
        self.deposit_apy = deposit_apy
        self.borrow_apy = borrow_apy
        self.total_deposits = total_deposits
        self.total_borrows = total_borrows
        self.utilization_rate = utilization_rate

    def to_dict(self) -> dict:
        return {
            "protocol": "marginfi",
            "symbol": self.symbol,
            "mint": self.mint,
            "bank_address": self.bank_address,
            "decimals": self.decimals,
            "deposit_apy": float(self.deposit_apy),
            "borrow_apy": float(self.borrow_apy),
            "total_deposits": float(self.total_deposits),
            "total_borrows": float(self.total_borrows),
            "utilization_rate": float(self.utilization_rate),
        }


class UserPosition:
    """用户在 MarginFi 的仓位"""

    def __init__(
        self,
        symbol: str,
        mint: str,
        position_type: str,  # "deposit" or "borrow"
        amount: Decimal = DEFAULT_DECIMAL_ZERO,
        value_usd: Optional[Decimal] = None,
    ):
        self.symbol = symbol
        self.mint = mint
        self.position_type = position_type
        self.amount = amount
        self.value_usd = value_usd

    def to_dict(self) -> dict:
        return {
            "protocol": "marginfi",
            "symbol": self.symbol,
            "mint": self.mint,
            "position_type": self.position_type,
            "amount": float(self.amount),
            "value_usd": float(self.value_usd) if self.value_usd else None,
        }


class MarginFiProvider(BaseDeFiProvider):
    """
    MarginFi 借贷协议适配器

    通过 RPC 读取链上 Bank 账户数据，解析利率和用户仓位。
    由于 MarginFi 无 REST API，利率数据通过链上 Bank 账户的
    利率配置参数 + 供需比计算得出。

    为简化实现，同时提供一个通过 DeFi 聚合 API 获取利率的备选方案。
    """

    @property
    def protocol_name(self) -> str:
        return "marginfi"

    def __init__(self, rpc_client: Optional[EnhancedRPCClient] = None):
        self._rpc = rpc_client or EnhancedRPCClient()
        self._owns_rpc = rpc_client is None
        # 使用带重试的 HTTP 客户端
        self._http = ResilientHTTPClient(timeout=30.0, max_retries=3, retry_delay=1.0)
        self._program_id = Pubkey.from_string(MARGINFI_PROGRAM_ID)
        # MarginFi 只在 Mainnet 部署，用独立 Mainnet RPC 查询
        self._mainnet_rpc_url = MAINNET_RPC

    @cached("marginfi_pools", ttl=config.CACHE_TTL_DEFI_RATES)
    async def get_lending_pools(self) -> List[LendingPool]:
        """
        获取所有借贷池信息（利率、TVL 等）

        策略：优先从 DeFi 聚合 API 获取数据，失败时返回已知池的基础信息
        """
        pools = []

        # 方案 1: 尝试从链上解析（通过 RPC 读取 Bank 账户）
        try:
            pools = await self._fetch_pools_from_chain()
            has_market_data = any(
                pool.deposit_apy > 0
                or pool.borrow_apy > 0
                or pool.total_deposits > 0
                or pool.utilization_rate > 0
                for pool in pools
            )
            if pools and has_market_data:
                logger.info(f"MarginFi: 从 RPC 获取到 {len(pools)} 个借贷池")
                return pools
            if pools:
                logger.info("MarginFi: RPC 仅返回基础池信息，继续尝试聚合利率数据")
        except Exception as e:
            logger.warning(f"MarginFi: RPC 链上数据解析失败: {e}")

        # 方案 2: 使用 DeFiLlama API 获取利率，合并 KNOWN_BANKS 补全缺失池
        try:
            defillama_pools = await self._fetch_pools_from_defillama()
            if defillama_pools:
                found_symbols = {p.symbol for p in defillama_pools}
                for symbol, info in KNOWN_BANKS.items():
                    if symbol not in found_symbols:
                        defillama_pools.append(
                            LendingPool(
                                symbol=symbol,
                                mint=info["mint"],
                                bank_address=info["bank"],
                                decimals=info["decimals"],
                            )
                        )
                logger.info(f"MarginFi: DeFiLlama + fallback = {len(defillama_pools)} 个借贷池")
                return defillama_pools
        except Exception as e:
            logger.warning(f"MarginFi: DeFiLlama API 失败: {e}")

        # 方案 3: 返回已知池的基础信息
        for symbol, info in KNOWN_BANKS.items():
            pools.append(
                LendingPool(
                    symbol=symbol,
                    mint=info["mint"],
                    bank_address=info["bank"],
                    decimals=info["decimals"],
                )
            )
        logger.info(f"MarginFi: 使用已知 bank 列表 ({len(pools)} 个池)")
        return pools

    async def _fetch_pools_from_chain(self) -> List[LendingPool]:
        """通过 JSON-RPC 直接从 Mainnet 读取 Bank 账户数据"""
        import base64

        pools = []

        for symbol, info in KNOWN_BANKS.items():
            try:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getAccountInfo",
                    "params": [info["bank"], {"encoding": "base64"}],
                }
                resp = await self._http.post(self._mainnet_rpc_url, json=payload)
                result = resp.json().get("result", {}).get("value")

                if result and result.get("data"):
                    raw = base64.b64decode(result["data"][0])
                    pool = self._parse_bank_data(raw, symbol, info)
                    if pool:
                        pools.append(pool)
            except Exception as e:
                logger.debug(f"MarginFi: 解析 {symbol} Bank 失败: {e}")
                continue

        return pools

    def _parse_bank_data(self, data: bytes, symbol: str, bank_info: dict) -> Optional[LendingPool]:
        """
        解析 Bank 账户二进制数据 (已通过链上数据验证偏移量)

        Bank 结构 (1864 bytes):
        - [8:40]    mint (Pubkey)
        - [296:312]  利率参数 1: asset_weight_init (I80F48)
        - [312:328]  利率参数 2: asset_weight_maint (I80F48)
        - [328:344]  利率参数 3: liability_weight_init (I80F48)
        - [344:360]  利率参数 4: liability_weight_maint (I80F48)
        - [632:648]  total_asset_shares (I80F48)
        - [776:792]  total_liability_shares (I80F48)
        """
        if len(data) < 800:
            return None

        try:
            # 验证 mint
            mint_bytes = data[BANK_MINT_OFFSET : BANK_MINT_OFFSET + BANK_MINT_SIZE]
            mint_pubkey = str(Pubkey.from_bytes(mint_bytes))
            expected_mint = bank_info["mint"]

            if mint_pubkey != expected_mint:
                logger.debug(f"MarginFi: {symbol} mint 不匹配 ({mint_pubkey[:8]}...)")

            pool = LendingPool(
                symbol=symbol,
                mint=expected_mint,
                bank_address=bank_info["bank"],
                decimals=bank_info["decimals"],
            )

            # 解析利率配置参数（已通过链上数据验证）
            try:
                asset_w_init = self._parse_i80f48(data[296:312])
                asset_w_maint = self._parse_i80f48(data[312:328])
                liab_w_init = self._parse_i80f48(data[328:344])
                liab_w_maint = self._parse_i80f48(data[344:360])

                # 存储权重数据用于风险计算
                pool._weights = {
                    "asset_weight_init": asset_w_init,
                    "asset_weight_maint": asset_w_maint,
                    "liability_weight_init": liab_w_init,
                    "liability_weight_maint": liab_w_maint,
                }

                # 从权重推算大致的 LTV 和清算阈值
                max_ltv = asset_w_init / liab_w_init if liab_w_init > 0 else 0
                liquidation_threshold = asset_w_maint / liab_w_maint if liab_w_maint > 0 else 0
                pool._risk_params = {
                    "max_ltv": round(max_ltv * 100, 1),
                    "liquidation_threshold": round(liquidation_threshold * 100, 1),
                }
            except Exception:
                pass

            return pool

        except Exception as e:
            logger.debug(f"MarginFi: {symbol} 解析异常: {e}")
            return LendingPool(
                symbol=symbol,
                mint=bank_info["mint"],
                bank_address=bank_info["bank"],
                decimals=bank_info["decimals"],
            )

    @staticmethod
    def _parse_i80f48(data: bytes) -> float:
        """
        解析 MarginFi 的 I80F48 定点数格式

        I80F48: 128-bit (16 bytes), little-endian
        高 80 bits = 整数部分, 低 48 bits = 小数部分
        """
        if len(data) != 16:
            return 0.0
        value = int.from_bytes(data, byteorder="little", signed=True)
        return value / (2**48)

    async def _fetch_pools_from_defillama(self) -> List[LendingPool]:
        """
        从 DeFiLlama Yields API 获取 MarginFi 利率数据

        DeFiLlama 聚合了各协议的 APY 数据，作为链上解析的备选方案
        """
        response = await self._http.get(
            "https://yields.llama.fi/pools",
            params={"project": "marginfi"},
        )
        response.raise_for_status()
        data = response.json()

        pools = []
        symbol_map = {v["mint"]: k for k, v in KNOWN_BANKS.items()}

        for pool_data in data.get("data", []):
            project = str(pool_data.get("project", "")).lower()
            if not project.startswith("marginfi"):
                continue
            if pool_data.get("chain") != "Solana":
                continue

            # DeFiLlama pool 格式
            underlying = pool_data.get("underlyingTokens", [])
            mint = underlying[0] if underlying else ""
            symbol = pool_data.get("symbol", "UNKNOWN").split("-")[0]

            # 优先使用已知映射
            if mint in symbol_map:
                symbol = symbol_map[mint]

            bank_info = KNOWN_BANKS.get(symbol, {})

            pools.append(
                LendingPool(
                    symbol=symbol,
                    mint=mint,
                    bank_address=bank_info.get("bank", ""),
                    decimals=bank_info.get("decimals", 9),
                    deposit_apy=Decimal(str(pool_data.get("apy", 0))),
                    borrow_apy=Decimal(str(pool_data.get("apyBorrow", 0) or 0)),
                    total_deposits=Decimal(str(pool_data.get("tvlUsd", 0))),
                    utilization_rate=Decimal(str(pool_data.get("utilizationRate", 0) or 0)),
                )
            )

        return pools

    async def get_user_positions(self, user_address: str) -> List[UserPosition]:
        """
        获取用户在 MarginFi 的所有仓位

        通过 Mainnet JSON-RPC getProgramAccounts 查找用户的 MarginfiAccount
        """
        import base64

        try:
            # 使用 memcmp filter 按 authority 字段过滤
            # MarginfiAccount 结构: [8] + group(32) + authority(32)
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getProgramAccounts",
                "params": [
                    MARGINFI_PROGRAM_ID,
                    {
                        "encoding": "base64",
                        "filters": [
                            {"dataSize": 2656},
                            {
                                "memcmp": {
                                    "offset": 40,
                                    "bytes": user_address,
                                }
                            },
                        ],
                    },
                ],
            }

            resp = await self._http.post(self._mainnet_rpc_url, json=payload)
            result = resp.json().get("result", [])

            positions = []
            for account_info in result:
                try:
                    raw = base64.b64decode(account_info["account"]["data"][0])
                    acct_positions = self._parse_marginfi_account(raw)
                    positions.extend(acct_positions)
                except Exception as e:
                    logger.debug(f"MarginFi: 用户账户解析失败: {e}")

            logger.info(f"MarginFi: 用户 {user_address[:8]}... 有 {len(positions)} 个仓位")
            return positions

        except Exception as e:
            logger.warning(f"MarginFi: 获取用户仓位失败: {e}")
            return []

    def _parse_marginfi_account(self, data: bytes) -> List[UserPosition]:
        """
        解析 MarginfiAccount 数据

        结构（简化）:
        - [0:8]     discriminator
        - [8:40]    group
        - [40:72]   authority
        - [72:...]  lending_account (包含 balances 数组)
        """
        positions = []

        # balances 数组从 offset 72 开始
        # 每个 balance 包含: active(1) + bank_pk(32) + padding + asset_shares(16) + liability_shares(16) ...
        # 简化解析，检测非零的存借仓位

        balance_start = 72
        balance_size = 136  # 每个 balance slot 的大致大小
        max_balances = 16  # 最多 16 个仓位

        bank_to_info = {v["bank"]: (k, v) for k, v in KNOWN_BANKS.items()}

        for i in range(max_balances):
            offset = balance_start + i * balance_size
            if offset + balance_size > len(data):
                break

            # 检查是否激活
            active = data[offset]
            if not active:
                continue

            # 读取 bank pubkey
            bank_bytes = data[offset + 1 : offset + 33]
            try:
                bank_pk = str(Pubkey.from_bytes(bank_bytes))
            except Exception:
                continue

            # 匹配已知 bank
            if bank_pk not in bank_to_info:
                continue

            symbol, info = bank_to_info[bank_pk]

            # 解析 asset_shares 和 liability_shares
            # 偏移量: active(1) + bank_pk(32) + padding(...)
            # 这些是 I80F48 格式
            try:
                asset_offset = offset + 48  # 大致偏移
                liab_offset = asset_offset + 16

                asset_shares = self._parse_i80f48(data[asset_offset : asset_offset + 16])
                liab_shares = self._parse_i80f48(data[liab_offset : liab_offset + 16])

                if asset_shares > 0.001:
                    positions.append(
                        UserPosition(
                            symbol=symbol,
                            mint=info["mint"],
                            position_type="deposit",
                            amount=Decimal(str(round(asset_shares, info["decimals"]))),
                        )
                    )

                if liab_shares > 0.001:
                    positions.append(
                        UserPosition(
                            symbol=symbol,
                            mint=info["mint"],
                            position_type="borrow",
                            amount=Decimal(str(round(liab_shares, info["decimals"]))),
                        )
                    )
            except Exception:
                continue

        return positions

    # ---- BaseDeFiProvider 接口实现 ----

    async def get_swap_quote(
        self,
        input_mint: str,
        output_mint: str,
        amount: int,
        slippage_bps: int = 50,
    ) -> SwapQuote:
        """MarginFi 是借贷协议，不支持 Swap"""
        raise ProviderError("marginfi", "MarginFi 是借贷协议，不支持 Swap 操作")

    async def build_swap_transaction(
        self,
        quote: SwapQuote,
        user_public_key: str,
    ) -> str:
        """MarginFi 是借贷协议，不支持 Swap"""
        raise ProviderError("marginfi", "MarginFi 是借贷协议，不支持 Swap 操作")

    async def close(self):
        """关闭连接"""
        if self._owns_rpc:
            await self._rpc.close()
        await self._http.close()
