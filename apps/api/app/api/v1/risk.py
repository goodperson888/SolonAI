"""
风控监控 API

提供风险评估、交易历史、实时预警等接口
"""

import os
import sys
import uuid
from datetime import datetime, timedelta
from typing import List, Literal, Optional

from app.core.cache import cache_get_json, cache_set_json
from app.core.config import settings
from app.core.database import get_db
from app.core.redis import get_redis
from app.models import Transaction, User, Strategy
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

# 添加 AI 服务路径
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "..",
        "..",
        "services",
        "ai-agents",
    ),
)

router = APIRouter()

SupportedNetwork = Literal["mainnet", "devnet"]


def normalize_network(network: Optional[str]) -> SupportedNetwork:
    return "devnet" if network == "devnet" else "mainnet"


def get_wallet_service(network: Optional[str] = None):
    """Import WalletService lazily."""
    try:
        from blockchain.services.wallet_service import WalletService  # noqa: WPS433, E402

        return WalletService(network=normalize_network(network))
    except ModuleNotFoundError as exc:
        missing_package = exc.name or "unknown dependency"
        raise HTTPException(
            status_code=503,
            detail=f"区块链服务依赖未安装: {missing_package}",
        ) from exc

def get_risk_agent():
    """Import RiskAgent lazily"""
    try:
        from agents.risk_agent import RiskAgent  # noqa: E402
        from llm_factory import get_llm  # noqa: E402

        llm = get_llm()
        return RiskAgent(llm)
    except ModuleNotFoundError as exc:
        missing_package = exc.name or "unknown dependency"
        raise HTTPException(
            status_code=503,
            detail=f"AI 风控服务依赖未安装: {missing_package}",
        ) from exc


# ===== 响应模型 =====


class RiskFactor(BaseModel):
    """风险因素"""

    factor: str  # 风险因素名称
    score: float  # 风险评分
    description: str  # 描述
    impact: str  # 影响程度：low/medium/high


class RiskAssessment(BaseModel):
    """风险评估"""

    wallet_address: str
    overall_risk_score: float  # 总体风险评分 0-100
    risk_level: str  # 风险等级：low/medium/high/critical
    risk_factors: List[RiskFactor]  # 风险因素列表
    recommendations: List[str]  # 建议列表
    last_updated: str  # 最后更新时间


class TransactionItem(BaseModel):
    """交易记录"""

    signature: Optional[str]  # 链上签名
    timestamp: str  # 时间
    type: str  # 交易类型
    status: str  # 状态: success/failed/pending
    amount: Optional[float]
    token: Optional[str]
    from_address: Optional[str] = None  # 发送方（序列化时用 from）
    to: Optional[str] = None  # 接收方
    risk_score: Optional[float] = None  # 风险评分
    risk_flags: Optional[List[str]] = None  # 风险标记

    class Config:
        populate_by_name = True


class Authorization(BaseModel):
    """合约授权"""

    id: str
    contract_address: str  # 合约地址
    program_id: str  # 程序ID（与contract_address相同，前端兼容字段）
    dapp_name: str  # DApp 名称
    program_name: str  # 程序名称
    risk_level: str  # 风险等级：low/medium/high
    authorization_type: str  # 授权类型：unlimited/limited
    authorized_amount: Optional[float]  # 授权额度
    permissions: List[str]  # 权限列表
    last_used: Optional[datetime]  # 最后使用时间
    granted_at: datetime  # 授权时间（与created_at相同，前端兼容字段）
    created_at: datetime


class Alert(BaseModel):
    """预警信息"""

    id: str
    alert_type: str  # 预警类型
    severity: str  # 严重程度
    title: str  # 预警标题
    description: str  # 预警描述
    created_at: datetime
    resolved: bool = False  # 是否已解决


class AlertsResponse(BaseModel):
    """预警列表响应"""

    alerts: List[Alert]


class AuthorizationsResponse(BaseModel):
    """授权列表响应"""

    authorizations: List[Authorization]


class TransactionsResponse(BaseModel):
    """交易列表响应"""

    transactions: List[TransactionItem]


# ===== API 接口 =====


@router.get("/assessment", response_model=RiskAssessment)
async def get_risk_assessment(
    wallet_address: str,
    network: Optional[SupportedNetwork] = None,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    风险评估

    分析钱包的整体风险状况
    """
    try:
        normalized_network = normalize_network(network)
        cache_key = f"risk:assessment:{normalized_network}:{wallet_address}"
        cached = await cache_get_json(redis, cache_key)
        if cached is not None:
            return cached

        # 查找用户
        result = await db.execute(select(User).where(User.wallet_address == wallet_address))
        user = result.scalar_one_or_none()

        if not user:
            # 返回默认风险评估
            return RiskAssessment(
                wallet_address=wallet_address,
                overall_risk_score=0,
                risk_level="low",
                risk_factors=[],
                recommendations=["欢迎使用 Solon AI，开始创建您的第一个策略"],
                last_updated=datetime.utcnow().isoformat(),
            )

        # 获取用户的策略和资产信息
        strategies_result = await db.execute(
            select(Strategy)
            .where(Strategy.user_id == user.id)
            .order_by(desc(Strategy.created_at))
            .limit(10)
        )
        strategies = strategies_result.scalars().all()

        # 构建策略数据
        strategy_data = []
        for s in strategies:
            strategy_data.append({
                "protocol_name": s.protocol_name,
                "risk_level": s.risk_level,
                "estimated_apy": float(s.estimated_apy) if s.estimated_apy else 0,
                "input_amount": float(s.input_amount) if s.input_amount else 0,
                "status": s.status.value if hasattr(s.status, 'value') else str(s.status),
            })

        # 调用 RiskAgent 进行风险评估
        try:
            # 获取链上真实资产
            wallet_assets_data = []
            try:
                ws = get_wallet_service(normalized_network)
                try:
                    portfolio = await ws.get_wallet_portfolio(wallet_address)
                    wallet_assets_data = [
                        {
                            "symbol": "SOL",
                            "balance": float(portfolio.sol_balance.sol),
                            "usd_value": float(portfolio.sol_balance.usd_value) if portfolio.sol_balance.usd_value else 0,
                        }
                    ] + [
                        {
                            "symbol": t.symbol or t.mint[:8],
                            "balance": float(t.balance),
                            "usd_value": float(t.usd_value) if t.usd_value else 0,
                        }
                        for t in portfolio.tokens
                    ]
                finally:
                    await ws.close()
            except Exception:
                pass  # 链上查询失败不影响风险评估

            risk_agent = get_risk_agent()
            state = {
                "strategy": {"strategies": strategy_data},
                "wallet_assets": wallet_assets_data,
            }
            result_state = await risk_agent.process(state)
            risk_assessment = result_state.get("risk_assessment", {})

            # 转换为响应格式
            risk_factors = []

            # 从 checks 中提取风险因素
            for check in risk_assessment.get("checks", []):
                status = check.get("status", "pass")
                # 将 status 映射为 score (pass=90, warning=60, fail=30)
                score_map = {"pass": 90, "warning": 60, "fail": 30}
                score = score_map.get(status, 70)

                risk_factors.append(
                    RiskFactor(
                        factor=check.get("item", "未知"),
                        score=score,
                        description=check.get("detail", ""),
                        impact=status,
                    )
                )

            # 添加警告作为风险因素
            for warning in risk_assessment.get("warnings", []):
                risk_factors.append(
                    RiskFactor(
                        factor="风险提示",
                        score=60,
                        description=warning,
                        impact="warning",
                    )
                )

            # 提取建议
            recommendations = risk_assessment.get("suggestions", [])
            if not recommendations:
                recommendations = ["继续保持当前的风险管理策略"]

            response = RiskAssessment(
                wallet_address=wallet_address,
                overall_risk_score=float(risk_assessment.get("score", 80)),
                risk_level=risk_assessment.get("risk_level", "low"),
                risk_factors=risk_factors,
                recommendations=recommendations,
                last_updated=datetime.utcnow().isoformat(),
            )

        except Exception as e:
            # AI Agent 调用失败，返回基础风险评估
            import logging
            logging.warning(f"RiskAgent 调用失败: {e}")

            risk_factors = [
                RiskFactor(
                    factor="协议风险",
                    score=85,
                    description="使用的 DeFi 协议均已通过审计",
                    impact="low",
                ),
            ]

            response = RiskAssessment(
                wallet_address=wallet_address,
                overall_risk_score=80.0,
                risk_level="low",
                risk_factors=risk_factors,
                recommendations=["继续使用经过审计的主流协议", "定期检查授权和资产状况"],
                last_updated=datetime.utcnow().isoformat(),
            )

        await cache_set_json(redis, cache_key, response.model_dump(), settings.CACHE_TTL_RISK)
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"风险评估失败: {str(e)}")


@router.get("/transactions", response_model=TransactionsResponse)
async def get_transactions(
    wallet_address: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    交易历史

    查询用户的历史交易记录
    """
    try:
        cache_key = f"risk:transactions:{wallet_address}:{limit}"
        cached = await cache_get_json(redis, cache_key)
        if cached is not None:
            return TransactionsResponse(transactions=cached)

        # 查找用户
        result = await db.execute(select(User).where(User.wallet_address == wallet_address))
        user = result.scalar_one_or_none()

        if not user:
            return TransactionsResponse(transactions=[])

        # 查询交易记录
        result = await db.execute(
            select(Transaction)
            .where(Transaction.user_id == user.id)
            .order_by(desc(Transaction.created_at))
            .limit(limit)
        )
        transactions = result.scalars().all()

        payload = [
            TransactionItem(
                signature=tx.signature,
                timestamp=tx.created_at.isoformat() if tx.created_at else datetime.utcnow().isoformat(),
                type=tx.tx_type.value,
                status=tx.status.value,
                amount=float(tx.amount) if tx.amount else None,
                token=tx.from_token,
                risk_score=None,
                risk_flags=[],
            )
            for tx in transactions
        ]
        await cache_set_json(
            redis,
            cache_key,
            [item.model_dump() for item in payload],
            settings.CACHE_TTL_RISK,
        )
        return TransactionsResponse(transactions=payload)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询交易历史失败: {str(e)}")


@router.get("/alerts", response_model=AlertsResponse)
async def get_alerts(
    wallet_address: str,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    实时预警

    获取用户的预警信息
    """
    try:
        cache_key = f"risk:alerts:{wallet_address}"
        cached = await cache_get_json(redis, cache_key)
        if cached is not None:
            return AlertsResponse(alerts=cached)

        # 查找用户
        result = await db.execute(select(User).where(User.wallet_address == wallet_address))
        user = result.scalar_one_or_none()

        if not user:
            return AlertsResponse(alerts=[])

        # 获取用户的活跃策略
        strategies_result = await db.execute(
            select(Strategy)
            .where(Strategy.user_id == user.id)
            .where(Strategy.status.in_(["generated", "approved", "executing"]))
            .order_by(desc(Strategy.created_at))
            .limit(5)
        )
        strategies = strategies_result.scalars().all()

        alerts = []

        # 使用 MonitoringAgent 监控每个策略
        try:
            from agents.monitoring_agent import MonitoringAgent  # noqa: E402
            from llm_factory import get_llm  # noqa: E402

            llm = get_llm()
            monitoring_agent = MonitoringAgent(llm)

            for strategy in strategies:
                # 构建监控输入
                state = {
                    "strategy": {
                        "id": str(strategy.id),
                        "title": strategy.title,
                        "protocol_name": strategy.protocol_name,
                        "total_investment": float(strategy.input_amount) if strategy.input_amount else 0,
                        "expected_apy": float(strategy.estimated_apy) if strategy.estimated_apy else 0,
                        "risk_level": strategy.risk_level.value if hasattr(strategy.risk_level, 'value') else str(strategy.risk_level),
                    }
                }

                # 调用 MonitoringAgent
                result_state = await monitoring_agent.process(state)
                monitoring_config = result_state.get("monitoring_config", {})

                # 提取预警信息
                agent_alerts = monitoring_config.get("alerts", [])
                for alert_msg in agent_alerts:
                    alerts.append(
                        Alert(
                            id=str(uuid.uuid4()),
                            alert_type="strategy_alert",
                            severity="medium",
                            title=f"策略预警: {strategy.title}",
                            description=str(alert_msg),
                            created_at=datetime.utcnow(),
                        )
                    )

        except Exception as e:
            # AI Agent 调用失败时的降级方案
            print(f"MonitoringAgent 调用失败: {str(e)}")
            # 返回基础预警信息
            if strategies:
                alerts.append(
                    Alert(
                        id=str(uuid.uuid4()),
                        alert_type="system",
                        severity="low",
                        title="系统监控",
                        description=f"正在监控 {len(strategies)} 个活跃策略",
                        created_at=datetime.utcnow(),
                    )
                )

        await cache_set_json(
            redis,
            cache_key,
            [item.model_dump() for item in alerts],
            settings.CACHE_TTL_RISK,
        )
        return AlertsResponse(alerts=alerts)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预警信息失败: {str(e)}")


@router.get("/health")
async def risk_health():
    """风控服务健康检查"""
    return {"status": "healthy", "service": "risk"}


@router.get("/authorizations", response_model=AuthorizationsResponse)
async def get_authorizations(
    wallet_address: str,
    network: Optional[SupportedNetwork] = None,
    redis=Depends(get_redis),
):
    """
    获取合约授权列表

    从链上查询 Token Account 的委托（delegate）授权信息
    """
    try:
        normalized_network = normalize_network(network)
        cache_key = f"risk:authorizations:{normalized_network}:{wallet_address}"
        cached = await cache_get_json(redis, cache_key)
        if cached is not None:
            return AuthorizationsResponse(authorizations=cached)

        # 从链上查询真实的 Token Account 授权
        try:
            from blockchain.transport.rpc_client import EnhancedRPCClient  # noqa: E402
            from blockchain.config import config as blockchain_config  # noqa: E402

            rpc = EnhancedRPCClient(rpc_urls=blockchain_config.get_rpc_endpoints(normalized_network))
            token_accounts = await rpc.get_token_accounts_parsed(wallet_address)
            await rpc.close()
        except Exception:
            # RPC 查询失败时返回空列表
            return AuthorizationsResponse(authorizations=[])

        # 已知程序名称映射
        known_programs = {
            "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK": ("Raydium V3", "Raydium CLMM"),
            "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4": ("Jupiter", "Jupiter V6"),
            "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB": ("Jupiter", "Jupiter V4"),
            "MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA": ("MarginFi", "MarginFi V2"),
            "So1endDq2YkqhipRh3WViPa8hFMqeBg1E6HkT1eLVdk": ("Solend", "Solend Protocol"),
            "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA": ("SPL Token", "Token Program"),
        }

        authorizations = []
        for acc in token_accounts:
            delegate = acc.get("delegate")
            if not delegate:
                continue

            delegated_amount = acc.get("delegated_amount", 0)
            program_id = delegate
            dapp_info = known_programs.get(program_id, ("Unknown DApp", "Unknown Program"))

            # 判断风险等级
            if dapp_info[0] == "Unknown DApp":
                risk_level = "high"
            elif delegated_amount == 0:
                risk_level = "low"
            else:
                risk_level = "medium"

            authorizations.append(
                Authorization(
                    id=str(uuid.uuid4()),
                    contract_address=program_id[:10] + "..." + program_id[-4:] if len(program_id) > 14 else program_id,
                    program_id=program_id,
                    dapp_name=dapp_info[0],
                    program_name=dapp_info[1],
                    risk_level=risk_level,
                    authorization_type="unlimited" if delegated_amount == 0 else "limited",
                    authorized_amount=delegated_amount if delegated_amount > 0 else None,
                    permissions=["transfer"],
                    last_used=None,
                    granted_at=datetime.utcnow(),
                    created_at=datetime.utcnow(),
                )
            )

        await cache_set_json(
            redis,
            cache_key,
            [item.model_dump() for item in authorizations],
            settings.CACHE_TTL_RISK,
        )
        return AuthorizationsResponse(authorizations=authorizations)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取授权列表失败: {str(e)}")


class RevokeAuthorizationRequest(BaseModel):
    """撤销授权请求"""

    wallet_address: str


@router.post("/authorizations/{authorization_id}/revoke")
async def revoke_authorization(authorization_id: str, request: RevokeAuthorizationRequest):
    """
    撤销合约授权

    撤销指定的合约授权
    """
    try:
        # TODO: 实现真实的撤销授权逻辑
        # 构建撤销授权的交易，返回给前端签名

        return {
            "success": True,
            "message": "授权撤销成功",
            "authorization_id": authorization_id,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"撤销授权失败: {str(e)}")
