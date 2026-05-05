"""
资产诊断 API

提供资产查询、诊断、盈亏分析等接口
"""

import os
import sys
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

# 添加区块链服务路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "..", ".."))
services_path = os.path.join(project_root, "services")
sys.path.insert(0, services_path)

from app.core.cache import cache_get_json, cache_set_json  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.database import get_db  # noqa: E402
from app.core.demo import (  # noqa: E402
    build_demo_diagnosis,
    build_demo_pnl,
    build_demo_wallet_assets,
    is_demo_mode_enabled,
)
from app.core.redis import get_redis  # noqa: E402
from app.models import Strategy, Transaction, User  # noqa: E402

router = APIRouter()

SupportedNetwork = Literal["mainnet", "devnet"]


def normalize_network(network: Optional[str]) -> SupportedNetwork:
    return "devnet" if network == "devnet" else "mainnet"


def get_wallet_service(network: Optional[str] = None):
    """Import WalletService lazily so the whole API can still boot."""
    try:
        from blockchain.services.wallet_service import WalletService  # noqa: WPS433, E402

        return WalletService(network=normalize_network(network))
    except ModuleNotFoundError as exc:
        missing_package = exc.name or "unknown dependency"
        raise HTTPException(
            status_code=503,
            detail=(
                f"区块链资产服务依赖未安装，当前无法查询链上资产。 缺少依赖: {missing_package}"
            ),
        ) from exc


def get_transaction_service():
    """Import TransactionService lazily."""
    try:
        from blockchain.services.transaction_service import TransactionService  # noqa: WPS433

        return TransactionService()
    except ModuleNotFoundError as exc:
        missing_package = exc.name or "unknown dependency"
        raise HTTPException(
            status_code=503,
            detail=f"区块链交易服务依赖未安装。缺少: {missing_package}",
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
    queried_network: str = "mainnet"  # 当前查询网络
    alternate_network: Optional[str] = None  # 检测到资产的备用网络
    alternate_sol_balance: Optional[float] = None  # 备用网络 SOL 余额
    network_hint: Optional[str] = None  # 网络提示文案


async def detect_alternate_network_hint(
    wallet_address: str,
    current_network: SupportedNetwork,
) -> dict:
    """当当前网络查询为空时，探测常见备用网络，帮助定位资产去向。"""
    try:
        from blockchain.transport.rpc_client import EnhancedRPCClient  # noqa: WPS433, E402

        if current_network != "mainnet":
            return {
                "queried_network": current_network,
                "alternate_network": None,
                "alternate_sol_balance": None,
                "network_hint": None,
            }

        devnet_client = EnhancedRPCClient(rpc_urls=["https://api.devnet.solana.com"])
        try:
            devnet_lamports = await devnet_client.get_balance(wallet_address)
        finally:
            await devnet_client.close()

        devnet_sol = float(devnet_lamports) / 1_000_000_000
        if devnet_sol > 0:
            return {
                "queried_network": current_network,
                "alternate_network": "devnet",
                "alternate_sol_balance": devnet_sol,
                "network_hint": (
                    f"当前查询的是 {current_network}，但该钱包在 devnet 上检测到 "
                    f"{devnet_sol:g} SOL。"
                ),
            }

        return {
            "queried_network": current_network,
            "alternate_network": None,
            "alternate_sol_balance": None,
            "network_hint": None,
        }
    except Exception:
        return {
            "queried_network": current_network,
            "alternate_network": None,
            "alternate_sol_balance": None,
            "network_hint": None,
        }


class SwapQuoteRequest(BaseModel):
    """Swap 报价请求"""

    input_mint: str
    output_mint: str
    amount: float  # 人类可读数量
    slippage_bps: int = 50
    provider: str = "auto"  # jupiter / raydium / auto


class SwapQuoteResponse(BaseModel):
    """Swap 报价响应"""

    provider: str
    input_mint: str
    output_mint: str
    in_amount: str
    out_amount: str
    price_impact_pct: str
    slippage_bps: int


class PnLBreakdownItem(BaseModel):
    """盈亏明细项"""

    asset: str
    type: str
    pnl: float
    percentage: float


class PnLAnalysis(BaseModel):
    """盈亏分析"""

    wallet_address: str
    total_pnl: float  # 总盈亏
    total_pnl_percentage: float  # 总盈亏百分比
    realized_pnl: float  # 已实现盈亏
    unrealized_pnl: float  # 未实现盈亏
    roi_percentage: float  # 投资回报率
    breakdown: Optional[List[PnLBreakdownItem]] = None  # 盈亏明细


class DiagnosisIssue(BaseModel):
    """诊断问题"""

    type: str  # 问题类型
    severity: str  # 严重程度：low/medium/high/critical
    description: str  # 描述
    recommendation: str  # 建议


class HealthMetrics(BaseModel):
    """健康指标"""

    diversification_score: float  # 多样化评分
    liquidity_score: float  # 流动性评分
    volatility_score: float  # 波动性评分


class AssetDiagnosis(BaseModel):
    """资产诊断"""

    wallet_address: str
    risk_level: str  # 风险等级：low/medium/high
    risk_score: float  # 风险评分 0-100
    issues: List[DiagnosisIssue]  # 问题列表
    health_metrics: HealthMetrics  # 健康指标


# ===== API 接口 =====


@router.get("/{wallet_address}", response_model=WalletAssets)
async def get_assets(
    wallet_address: str,
    network: Optional[SupportedNetwork] = None,
    redis=Depends(get_redis),
):
    """
    获取钱包资产

    查询链上真实数据：
    - SOL 余额
    - SPL Token 余额
    - 计算总价值（美元）
    """
    try:
        normalized_network = normalize_network(network)
        cache_key = f"assets:wallet:{normalized_network}:{wallet_address}"
        cached = await cache_get_json(redis, cache_key)
        if cached is not None:
            return cached

        if is_demo_mode_enabled():
            response = WalletAssets(**build_demo_wallet_assets(wallet_address, normalized_network))
            await cache_set_json(redis, cache_key, response.model_dump(), settings.CACHE_TTL_ASSETS)
            return response

        # 使用新的 WalletService 获取资产
        wallet_service = get_wallet_service(normalized_network)
        try:
            portfolio = await wallet_service.get_wallet_portfolio(wallet_address)
        finally:
            await wallet_service.close()

        # 转换为 API 响应格式
        tokens = [
            TokenAsset(
                symbol=t.symbol or "UNKNOWN",
                name=t.name or t.mint[:8] + "...",
                mint=t.mint,
                balance=float(t.balance),
                price_usd=float(t.usd_value / t.balance) if t.usd_value and t.balance else 0.0,
                value_usd=float(t.usd_value) if t.usd_value else 0.0,
            )
            for t in portfolio.tokens
        ]

        sol_price = 0.0
        sol_value = 0.0
        if portfolio.sol_balance.usd_value and portfolio.sol_balance.sol:
            sol_price = float(portfolio.sol_balance.usd_value / portfolio.sol_balance.sol)
            sol_value = float(portfolio.sol_balance.usd_value)

        response = WalletAssets(
            wallet_address=wallet_address,
            sol_balance=float(portfolio.sol_balance.sol),
            sol_price_usd=sol_price,
            sol_value_usd=sol_value,
            tokens=tokens,
            total_value_usd=float(portfolio.total_usd_value),
            queried_network=normalized_network,
        )
        if response.sol_balance == 0 and len(response.tokens) == 0:
            response = response.model_copy(
                update=await detect_alternate_network_hint(wallet_address, normalized_network)
            )
        await cache_set_json(redis, cache_key, response.model_dump(), settings.CACHE_TTL_ASSETS)
        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取资产失败: {str(e)}")


@router.get("/{wallet_address}/diagnosis", response_model=AssetDiagnosis)
async def diagnose_assets(
    wallet_address: str,
    network: Optional[SupportedNetwork] = None,
    redis=Depends(get_redis),
):
    """
    资产诊断

    基于真实链上资产数据分析风险、提供优化建议
    """
    try:
        normalized_network = normalize_network(network)
        cache_key = f"assets:diagnosis:{normalized_network}:{wallet_address}"
        cached = await cache_get_json(redis, cache_key)
        if cached is not None:
            return cached

        if is_demo_mode_enabled():
            response = AssetDiagnosis(**build_demo_diagnosis(wallet_address))
            await cache_set_json(redis, cache_key, response.model_dump(), settings.CACHE_TTL_ASSETS)
            return response

        # 获取链上真实资产
        wallet_service = get_wallet_service(normalized_network)
        try:
            portfolio = await wallet_service.get_wallet_portfolio(wallet_address)
        finally:
            await wallet_service.close()

        total_value = float(portfolio.total_usd_value) if portfolio.total_usd_value else 0.0
        sol_value = float(portfolio.sol_balance.usd_value) if portfolio.sol_balance.usd_value else 0.0
        token_count = len(portfolio.tokens)

        issues: List[DiagnosisIssue] = []

        # 分析资产集中度
        if total_value > 0:
            sol_ratio = sol_value / total_value * 100
            if sol_ratio > 80:
                issues.append(DiagnosisIssue(
                    type="资产集中度",
                    severity="medium",
                    description=f"{sol_ratio:.0f}% 的资产集中在 SOL",
                    recommendation="考虑适当分散投资到稳定币或其他优质资产，降低单一资产波动风险",
                ))
            elif sol_ratio > 50:
                issues.append(DiagnosisIssue(
                    type="资产集中度",
                    severity="low",
                    description=f"{sol_ratio:.0f}% 的资产为 SOL",
                    recommendation="资产分布尚可，可考虑进一步分散到不同类别的资产",
                ))

        # 检查是否有小额代币（灰尘攻击风险）
        dust_tokens = [t for t in portfolio.tokens if t.usd_value and float(t.usd_value) < 0.01]
        if len(dust_tokens) > 2:
            issues.append(DiagnosisIssue(
                type="灰尘代币",
                severity="low",
                description=f"检测到 {len(dust_tokens)} 个极小额代币，可能为灰尘攻击",
                recommendation="请勿与未知小额代币交互，避免点击相关链接",
            ))

        # 检查资产总值
        if total_value < 1.0 and total_value > 0:
            issues.append(DiagnosisIssue(
                type="低余额",
                severity="low",
                description=f"钱包总价值仅 ${total_value:.2f}",
                recommendation="资产余额较低，请注意交易手续费消耗",
            ))

        # 计算健康指标
        # 多样化评分：基于代币数量和分布
        if token_count == 0:
            diversification = 20.0
        elif token_count == 1:
            diversification = 30.0
        elif token_count <= 3:
            diversification = 50.0
        elif token_count <= 6:
            diversification = 70.0
        else:
            diversification = 85.0

        # 如果 SOL 占比过大，降低多样化评分
        if total_value > 0 and sol_value / total_value > 0.8:
            diversification = min(diversification, 35.0)

        # 流动性评分：SOL 和主流代币流动性高
        liquidity = 85.0  # SOL 本身流动性好
        # 波动性评分：基于 SOL 占比（SOL 波动较大）
        volatility = 40.0 + (60.0 - (sol_value / total_value * 60 if total_value > 0 else 0))

        # 计算总风险评分
        risk_score = 100 - (diversification * 0.3 + liquidity * 0.3 + volatility * 0.4)
        risk_score = max(0, min(100, risk_score))

        if risk_score < 30:
            risk_level = "low"
        elif risk_score < 60:
            risk_level = "medium"
        else:
            risk_level = "high"

        if not issues:
            issues.append(DiagnosisIssue(
                type="整体健康",
                severity="low",
                description="未检测到明显风险，资产状态良好",
                recommendation="继续保持良好的资产管理习惯",
            ))

        health_metrics = HealthMetrics(
            diversification_score=round(diversification, 1),
            liquidity_score=round(liquidity, 1),
            volatility_score=round(volatility, 1),
        )

        response = AssetDiagnosis(
            wallet_address=wallet_address,
            risk_level=risk_level,
            risk_score=round(risk_score, 1),
            issues=issues,
            health_metrics=health_metrics,
        )
        await cache_set_json(redis, cache_key, response.model_dump(), settings.CACHE_TTL_ASSETS)
        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"资产诊断失败: {str(e)}")


@router.post("/swap/quote", response_model=SwapQuoteResponse)
async def get_swap_quote(request: SwapQuoteRequest):
    """
    获取 Swap 报价

    聚合 Jupiter + Raydium 获取最优报价
    """
    try:
        tx_service = get_transaction_service()
        try:
            # 将人类可读数量转为 lamports/最小单位
            # 默认假设 9 decimals (SOL)，实际应根据代币 decimals 转换
            amount_raw = int(request.amount * 1_000_000_000)

            quote = await tx_service.get_swap_quote(
                input_mint=request.input_mint,
                output_mint=request.output_mint,
                amount=amount_raw,
                slippage_bps=request.slippage_bps,
                provider=request.provider,
            )
        finally:
            await tx_service.close()

        return SwapQuoteResponse(
            provider=quote.provider,
            input_mint=quote.input_mint,
            output_mint=quote.output_mint,
            in_amount=str(quote.in_amount),
            out_amount=str(quote.out_amount),
            price_impact_pct=str(quote.price_impact_pct or 0),
            slippage_bps=quote.slippage_bps,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取报价失败: {str(e)}")


@router.get("/{wallet_address}/pnl", response_model=PnLAnalysis)
async def get_pnl(
    wallet_address: str,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    盈亏分析

    基于用户策略和交易数据计算盈亏
    """
    try:
        cache_key = f"assets:pnl:{wallet_address}"
        cached = await cache_get_json(redis, cache_key)
        if cached is not None:
            return cached

        if is_demo_mode_enabled():
            response = PnLAnalysis(**build_demo_pnl(wallet_address))
            await cache_set_json(redis, cache_key, response.model_dump(), settings.CACHE_TTL_ASSETS)
            return response

        # 查找用户
        result = await db.execute(select(User).where(User.wallet_address == wallet_address))
        user = result.scalar_one_or_none()

        if not user:
            return PnLAnalysis(
                wallet_address=wallet_address,
                total_pnl=0.0,
                total_pnl_percentage=0.0,
                realized_pnl=0.0,
                unrealized_pnl=0.0,
                roi_percentage=0.0,
                breakdown=[],
            )

        # 查询用户的策略数据
        strategies_result = await db.execute(
            select(Strategy)
            .where(Strategy.user_id == user.id)
            .order_by(desc(Strategy.created_at))
        )
        strategies = strategies_result.scalars().all()

        # 基于策略数据计算盈亏
        total_invested = 0.0
        unrealized_pnl = 0.0
        realized_pnl = 0.0
        breakdown: List[PnLBreakdownItem] = []

        for s in strategies:
            amount = float(s.input_amount) if s.input_amount else 0.0
            apy = float(s.estimated_apy) if s.estimated_apy else 0.0
            total_invested += amount

            if amount > 0 and apy > 0:
                # 计算基于 APY 的估算收益（按持有天数比例）
                from datetime import datetime, timezone

                created_at = s.created_at
                if created_at and created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)

                days_held = (datetime.now(timezone.utc) - created_at).days if created_at else 0
                estimated_profit = amount * (apy / 100) * (days_held / 365)

                status = s.status.value if hasattr(s.status, 'value') else str(s.status)
                if status in ('approved', 'executed'):
                    unrealized_pnl += estimated_profit
                    breakdown.append(PnLBreakdownItem(
                        asset=s.input_token or "UNKNOWN",
                        type=f"{s.protocol_name or 'DeFi'} 收益",
                        pnl=round(estimated_profit, 2),
                        percentage=round(apy * days_held / 365, 2),
                    ))
                elif status == 'expired':
                    realized_pnl += estimated_profit
                    breakdown.append(PnLBreakdownItem(
                        asset=s.input_token or "UNKNOWN",
                        type=f"{s.protocol_name or 'DeFi'} 已结算",
                        pnl=round(estimated_profit, 2),
                        percentage=round(apy * days_held / 365, 2),
                    ))

        total_pnl = realized_pnl + unrealized_pnl
        roi = (total_pnl / total_invested * 100) if total_invested > 0 else 0.0

        response = PnLAnalysis(
            wallet_address=wallet_address,
            total_pnl=round(total_pnl, 2),
            total_pnl_percentage=round(roi, 2),
            realized_pnl=round(realized_pnl, 2),
            unrealized_pnl=round(unrealized_pnl, 2),
            roi_percentage=round(roi, 2),
            breakdown=breakdown if breakdown else [],
        )
        await cache_set_json(redis, cache_key, response.model_dump(), settings.CACHE_TTL_ASSETS)
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"盈亏分析失败: {str(e)}")
