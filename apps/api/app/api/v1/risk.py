"""
风控监控 API

提供风险评估、交易历史、实时预警等接口
"""

import uuid
from datetime import datetime
from typing import List, Optional

from app.core.database import get_db
from app.models import Transaction, User
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


# ===== 响应模型 =====


class RiskFactor(BaseModel):
    """风险因素"""

    category: str  # 风险类别
    severity: str  # 严重程度：low/medium/high
    description: str  # 描述
    suggestion: str  # 建议


class RiskAssessment(BaseModel):
    """风险评估"""

    wallet_address: str
    overall_risk: str  # 总体风险：low/medium/high
    risk_score: float  # 风险评分 0-100
    risk_factors: List[RiskFactor]  # 风险因素列表
    checked_at: datetime  # 检查时间


class TransactionItem(BaseModel):
    """交易记录"""

    id: str
    tx_type: str  # 交易类型
    status: str  # 状态
    from_token: Optional[str]
    to_token: Optional[str]
    amount: Optional[float]
    protocol_name: Optional[str]  # 协议名称
    signature: Optional[str]  # 链上签名
    created_at: datetime


class Authorization(BaseModel):
    """合约授权"""

    id: str
    contract_address: str  # 合约地址
    dapp_name: str  # DApp 名称
    risk_level: str  # 风险等级：low/medium/high
    authorization_type: str  # 授权类型：unlimited/limited
    authorized_amount: Optional[float]  # 授权额度
    last_used: Optional[datetime]  # 最后使用时间
    created_at: datetime


class Alert(BaseModel):
    """预警信息"""

    id: str
    alert_type: str  # 预警类型
    severity: str  # 严重程度
    message: str  # 预警消息
    created_at: datetime


# ===== API 接口 =====


@router.get("/assessment", response_model=RiskAssessment)
async def get_risk_assessment(wallet_address: str):
    """
    风险评估

    分析钱包的整体风险状况
    """
    try:
        # TODO: 实现真实的风险评估逻辑
        # 调用 AI Agent 的 RiskAgent

        risk_factors = [
            RiskFactor(
                category="协议风险",
                severity="low",
                description="使用的 DeFi 协议均已通过审计",
                suggestion="继续使用经过审计的主流协议",
            ),
            RiskFactor(
                category="授权风险",
                severity="medium",
                description="检测到 3 个无限授权",
                suggestion="建议撤销不再使用的无限授权",
            ),
            RiskFactor(
                category="资产集中度",
                severity="low",
                description="资产分散度良好",
                suggestion="保持当前的资产配置策略",
            ),
        ]

        return RiskAssessment(
            wallet_address=wallet_address,
            overall_risk="low",
            risk_score=28.5,
            risk_factors=risk_factors,
            checked_at=datetime.utcnow(),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"风险评估失败: {str(e)}")


@router.get("/transactions", response_model=List[TransactionItem])
async def get_transactions(
    wallet_address: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """
    交易历史

    查询用户的历史交易记录
    """
    try:
        # 查找用户
        result = await db.execute(select(User).where(User.wallet_address == wallet_address))
        user = result.scalar_one_or_none()

        if not user:
            return []

        # 查询交易记录
        result = await db.execute(
            select(Transaction)
            .where(Transaction.user_id == user.id)
            .order_by(desc(Transaction.created_at))
            .limit(limit)
        )
        transactions = result.scalars().all()

        return [
            TransactionItem(
                id=str(tx.id),
                tx_type=tx.tx_type.value,
                status=tx.status.value,
                from_token=tx.from_token,
                to_token=tx.to_token,
                amount=float(tx.amount) if tx.amount else None,
                protocol_name=tx.tx_payload.get("protocol") if tx.tx_payload else None,
                signature=tx.signature,
                created_at=tx.created_at,
            )
            for tx in transactions
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询交易历史失败: {str(e)}")


@router.get("/alerts", response_model=List[Alert])
async def get_alerts(wallet_address: str):
    """
    实时预警

    获取用户的预警信息
    """
    try:
        # TODO: 实现真实的预警逻辑
        # 从数据库或缓存中查询预警信息

        # 返回 mock 数据
        alerts = [
            Alert(
                id=str(uuid.uuid4()),
                alert_type="price_change",
                severity="medium",
                message="SOL 价格下跌 5%，建议关注市场动态",
                created_at=datetime.utcnow(),
            ),
            Alert(
                id=str(uuid.uuid4()),
                alert_type="apy_change",
                severity="low",
                message="MarginFi USDC 存款 APY 上涨至 5.2%",
                created_at=datetime.utcnow(),
            ),
        ]

        return alerts

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预警信息失败: {str(e)}")


@router.get("/health")
async def risk_health():
    """风控服务健康检查"""
    return {"status": "healthy", "service": "risk"}


@router.get("/authorizations", response_model=List[Authorization])
async def get_authorizations(wallet_address: str):
    """
    获取合约授权列表

    查询钱包的所有合约授权
    """
    try:
        # TODO: 实现真实的授权查询逻辑
        # 从链上查询 Token Account 的授权信息

        # 返回 mock 数据
        authorizations = [
            Authorization(
                id=str(uuid.uuid4()),
                contract_address="7xKXt...9mPq",
                dapp_name="Unknown DApp",
                risk_level="high",
                authorization_type="unlimited",
                authorized_amount=None,
                last_used=None,
                created_at=datetime.utcnow(),
            ),
            Authorization(
                id=str(uuid.uuid4()),
                contract_address="CAMMCzo...5xfM",
                dapp_name="Raydium V3",
                risk_level="medium",
                authorization_type="unlimited",
                authorized_amount=None,
                last_used=datetime.utcnow(),
                created_at=datetime.utcnow(),
            ),
            Authorization(
                id=str(uuid.uuid4()),
                contract_address="JUP4Fb2...cKzZ",
                dapp_name="Jupiter Aggregator",
                risk_level="low",
                authorization_type="limited",
                authorized_amount=100.0,
                last_used=datetime.utcnow(),
                created_at=datetime.utcnow(),
            ),
        ]

        return authorizations

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取授权列表失败: {str(e)}")


@router.post("/authorizations/{authorization_id}/revoke")
async def revoke_authorization(authorization_id: str, wallet_address: str):
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
