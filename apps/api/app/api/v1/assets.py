"""
资产诊断 API

提供资产查询、诊断、盈亏分析等接口
"""

import os
import sys
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# 添加区块链服务路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "..", ".."))
services_path = os.path.join(project_root, "services")
sys.path.insert(0, services_path)

from app.core.cache import cache_get_json, cache_set_json  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.database import get_db  # noqa: E402
from app.core.redis import get_redis  # noqa: E402
from app.models import User  # noqa: E402

router = APIRouter()


def get_solana_client_class():
    """Import blockchain dependencies lazily so the whole API can still boot."""
    try:
        from blockchain.solana_client import SolanaClient  # noqa: WPS433, E402

        return SolanaClient
    except ModuleNotFoundError as exc:
        missing_package = exc.name or "unknown dependency"
        raise HTTPException(
            status_code=503,
            detail=(
                "区块链资产服务依赖未安装，当前无法查询链上资产。" f" 缺少依赖: {missing_package}"
            ),
        ) from exc


# ===== 响应模型 =====


class TokenAsset(BaseModel):
    """Token 资产"""

    symbol: str  # Token 符号
    name: str  # Token 名称
    mint: Optional[str] = None  # Mint 地址
    balance: float  # 余额
    price_usd: float  # 美元价格
    value_usd: float  # 美元价值


class WalletAssets(BaseModel):
    """钱包资产"""

    wallet_address: str
    sol_balance: float  # SOL 余额
    sol_price_usd: float  # SOL 价格
    sol_value_usd: float  # SOL 价值
    tokens: List[TokenAsset]  # Token 列表
    total_value_usd: float  # 总价值


class PnLAnalysis(BaseModel):
    """盈亏分析"""

    total_profit: float  # 总盈利
    total_loss: float  # 总亏损
    net_profit: float  # 净盈利
    roi: float  # 投资回报率
    win_rate: float  # 胜率


class RiskFactor(BaseModel):
    """风险因素"""

    category: str  # 风险类别
    severity: str  # 严重程度：low/medium/high
    description: str  # 描述
    suggestion: str  # 建议


class AssetDiagnosis(BaseModel):
    """资产诊断"""

    wallet_address: str
    overall_risk: str  # 总体风险：low/medium/high
    risk_score: float  # 风险评分 0-100
    risk_factors: List[RiskFactor]  # 风险因素列表
    suggestions: List[str]  # 优化建议


# ===== API 接口 =====


@router.get("/{wallet_address}", response_model=WalletAssets)
async def get_assets(wallet_address: str, redis=Depends(get_redis)):
    """
    获取钱包资产

    查询链上真实数据：
    - SOL 余额
    - SPL Token 余额
    - 计算总价值（美元）
    """
    try:
        cache_key = f"assets:wallet:{wallet_address}"
        cached = await cache_get_json(redis, cache_key)
        if cached is not None:
            return cached

        # 创建 Solana 客户端
        SolanaClient = get_solana_client_class()
        client = SolanaClient()

        # 获取 SOL 余额
        sol_balance = await client.get_sol_balance(wallet_address)

        # 获取 Token 账户（暂时返回空列表，后续实现 Token 解析）
        await client.get_token_accounts(wallet_address)  # noqa: F841

        # 关闭客户端
        await client.close()

        # TODO: 接入价格 API 获取实时价格
        # 暂时使用固定价格
        sol_price = 178.32

        # 计算价值
        sol_value = sol_balance * sol_price

        # TODO: 解析 Token 账户数据
        tokens = []

        response = WalletAssets(
            wallet_address=wallet_address,
            sol_balance=sol_balance,
            sol_price_usd=sol_price,
            sol_value_usd=sol_value,
            tokens=tokens,
            total_value_usd=sol_value,
        )
        await cache_set_json(redis, cache_key, response.model_dump(), settings.CACHE_TTL_ASSETS)
        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取资产失败: {str(e)}")


@router.get("/{wallet_address}/diagnosis", response_model=AssetDiagnosis)
async def diagnose_assets(wallet_address: str):
    """
    资产诊断

    分析资产风险、提供优化建议
    """
    try:
        # TODO: 实现真实的风险诊断逻辑
        # 这里返回 mock 数据

        risk_factors = [
            RiskFactor(
                category="授权风险",
                severity="low",
                description="检测到 2 个活跃的代币授权",
                suggestion="定期检查并撤销不再使用的授权",
            ),
            RiskFactor(
                category="资产集中度",
                severity="medium",
                description="90% 的资产集中在 SOL",
                suggestion="考虑适当分散投资，降低单一资产风险",
            ),
        ]

        suggestions = [
            "您的闲置 SOL 可以存入 MarginFi 赚取 4.2% 年化收益",
            "建议将部分资产配置到稳定币，降低波动风险",
            "定期检查并撤销不再使用的代币授权",
        ]

        return AssetDiagnosis(
            wallet_address=wallet_address,
            overall_risk="low",
            risk_score=25.5,
            risk_factors=risk_factors,
            suggestions=suggestions,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"资产诊断失败: {str(e)}")


@router.get("/{wallet_address}/pnl", response_model=PnLAnalysis)
async def get_pnl(
    wallet_address: str,
    db: AsyncSession = Depends(get_db),
):
    """
    盈亏分析

    分析用户的历史交易盈亏
    """
    try:
        # 查找用户
        result = await db.execute(select(User).where(User.wallet_address == wallet_address))
        user = result.scalar_one_or_none()

        if not user:
            # 新用户，返回空数据
            return PnLAnalysis(
                total_profit=0.0,
                total_loss=0.0,
                net_profit=0.0,
                roi=0.0,
                win_rate=0.0,
            )

        # TODO: 查询用户的交易记录，计算盈亏
        # 这里返回 mock 数据

        return PnLAnalysis(
            total_profit=1250.50,
            total_loss=320.80,
            net_profit=929.70,
            roi=15.6,
            win_rate=68.5,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"盈亏分析失败: {str(e)}")
