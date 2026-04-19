"""
策略生成 API

提供策略生成、查询、执行等接口
"""

import os
import sys
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

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

from app.core.cache import (  # noqa: E402
    cache_delete,
    cache_delete_by_patterns,
    cache_get_json,
    cache_set_json,
)
from app.core.config import settings  # noqa: E402
from app.core.database import get_db  # noqa: E402
from app.core.redis import get_redis  # noqa: E402
from app.models import Strategy, Transaction, User  # noqa: E402
from app.models.strategy import StrategyStatus  # noqa: E402
from app.models.transaction import TransactionStatus, TransactionType  # noqa: E402

router = APIRouter()


def get_run_agent():
    """Import AI workflow lazily so missing AI deps do not break API startup."""
    try:
        from graphs.main_graph import run_agent  # noqa: WPS433, E402

        return run_agent
    except ModuleNotFoundError as exc:
        missing_package = exc.name or "unknown dependency"
        raise HTTPException(
            status_code=503,
            detail=("AI 策略服务依赖未安装，当前无法调用智能体工作流。" f" 缺少依赖: {missing_package}"),
        ) from exc


# ===== 请求/响应模型 =====


class StrategyGenerateRequest(BaseModel):
    """策略生成请求"""

    wallet_address: str  # 钱包地址
    risk_level: str  # 风险等级：conservative/balanced/aggressive
    amount: float  # 投资金额
    token: str = "USDC"  # 投资代币
    duration: Optional[int] = 30  # 持续时间（天）


class StrategyResponse(BaseModel):
    """策略响应"""

    id: str
    title: str
    summary: Optional[str]
    strategy_type: str
    risk_level: str
    estimated_apy: Optional[float]
    protocol_name: Optional[str]
    input_token: str
    input_amount: Optional[float]
    steps: list
    risk_assessment: dict
    status: str
    created_at: datetime


class StrategyExecuteRequest(BaseModel):
    """策略执行请求"""

    wallet_address: str


class TransactionResponse(BaseModel):
    """交易响应"""

    id: str
    tx_type: str
    status: str
    from_token: Optional[str]
    to_token: Optional[str]
    amount: Optional[float]
    tx_payload: dict
    created_at: datetime


# ===== API 接口 =====


@router.post("/generate", response_model=StrategyResponse)
async def generate_strategy(
    request: StrategyGenerateRequest,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    生成策略

    调用 AI Agent 生成 DeFi 策略
    """
    try:
        # 查找或创建用户
        result = await db.execute(select(User).where(User.wallet_address == request.wallet_address))
        user = result.scalar_one_or_none()

        if not user:
            # 创建新用户
            user = User(
                wallet_address=request.wallet_address,
                risk_level=request.risk_level,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        # 调用 AI Agent 生成策略
        user_input = (
            f"我想用 {request.amount} {request.token} 进行 {request.risk_level} 风险等级的投资，帮我生成一个策略"
        )

        run_agent = get_run_agent()
        agent_result = await run_agent(
            user_input=user_input,
            wallet_address=request.wallet_address,
        )

        # 保存策略到数据库
        strategy = Strategy(
            user_id=user.id,
            strategy_type=agent_result.get("intent", "generate_strategy"),
            status=StrategyStatus.GENERATED,
            input_token=request.token,
            input_amount=request.amount,
            estimated_apy=agent_result.get("strategy", {}).get("estimated_apy", 8.5),
            risk_level=request.risk_level,
            protocol_name=agent_result.get("strategy", {}).get("protocol", "MarginFi"),
            title=agent_result.get("strategy", {}).get("title", f"{request.risk_level} 策略"),
            summary=agent_result.get("explanation", ""),
            steps=agent_result.get("strategy", {}).get("steps", []),
            strategy_payload=agent_result.get("strategy", {}),
            risk_assessment=agent_result.get("risk_assessment", {}),
            expires_at=datetime.utcnow() + timedelta(days=7),
        )

        db.add(strategy)
        await db.commit()
        await db.refresh(strategy)
        await cache_delete_by_patterns(redis, [f"strategy:list:{request.wallet_address}:*"])

        return StrategyResponse(
            id=str(strategy.id),
            title=strategy.title,
            summary=strategy.summary,
            strategy_type=strategy.strategy_type,
            risk_level=strategy.risk_level,
            estimated_apy=(float(strategy.estimated_apy) if strategy.estimated_apy else None),
            protocol_name=strategy.protocol_name,
            input_token=strategy.input_token,
            input_amount=(float(strategy.input_amount) if strategy.input_amount else None),
            steps=strategy.steps,
            risk_assessment=strategy.risk_assessment,
            status=strategy.status.value,
            created_at=strategy.created_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成策略失败: {str(e)}")


@router.get("/list", response_model=List[StrategyResponse])
async def list_strategies(
    wallet_address: str,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    获取策略列表

    查询用户的历史策略
    """
    try:
        cache_key = f"strategy:list:{wallet_address}:{limit}"
        cached = await cache_get_json(redis, cache_key)
        if cached is not None:
            return cached

        # 查找用户
        result = await db.execute(select(User).where(User.wallet_address == wallet_address))
        user = result.scalar_one_or_none()

        if not user:
            return []

        # 查询策略列表
        result = await db.execute(
            select(Strategy)
            .where(Strategy.user_id == user.id)
            .order_by(desc(Strategy.created_at))
            .limit(limit)
        )
        strategies = result.scalars().all()

        payload = [
            StrategyResponse(
                id=str(s.id),
                title=s.title,
                summary=s.summary,
                strategy_type=s.strategy_type,
                risk_level=s.risk_level,
                estimated_apy=float(s.estimated_apy) if s.estimated_apy else None,
                protocol_name=s.protocol_name,
                input_token=s.input_token,
                input_amount=float(s.input_amount) if s.input_amount else None,
                steps=s.steps,
                risk_assessment=s.risk_assessment,
                status=s.status.value,
                created_at=s.created_at,
            )
            for s in strategies
        ]
        await cache_set_json(
            redis,
            cache_key,
            [item.model_dump() for item in payload],
            settings.CACHE_TTL_STRATEGY,
        )
        return payload

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询策略列表失败: {str(e)}")


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: str,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    获取策略详情
    """
    try:
        cache_key = f"strategy:detail:{strategy_id}"
        cached = await cache_get_json(redis, cache_key)
        if cached is not None:
            return cached

        result = await db.execute(select(Strategy).where(Strategy.id == uuid.UUID(strategy_id)))
        strategy = result.scalar_one_or_none()

        if not strategy:
            raise HTTPException(status_code=404, detail="策略不存在")

        response = StrategyResponse(
            id=str(strategy.id),
            title=strategy.title,
            summary=strategy.summary,
            strategy_type=strategy.strategy_type,
            risk_level=strategy.risk_level,
            estimated_apy=(float(strategy.estimated_apy) if strategy.estimated_apy else None),
            protocol_name=strategy.protocol_name,
            input_token=strategy.input_token,
            input_amount=(float(strategy.input_amount) if strategy.input_amount else None),
            steps=strategy.steps,
            risk_assessment=strategy.risk_assessment,
            status=strategy.status.value,
            created_at=strategy.created_at,
        )
        await cache_set_json(redis, cache_key, response.model_dump(), settings.CACHE_TTL_STRATEGY)
        return response

    except ValueError:
        raise HTTPException(status_code=400, detail="无效的策略 ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询策略失败: {str(e)}")


@router.post("/{strategy_id}/execute", response_model=TransactionResponse)
async def execute_strategy(
    strategy_id: str,
    request: StrategyExecuteRequest,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    执行策略

    生成交易指令，返回给前端签名
    """
    try:
        # 查询策略
        result = await db.execute(select(Strategy).where(Strategy.id == uuid.UUID(strategy_id)))
        strategy = result.scalar_one_or_none()

        if not strategy:
            raise HTTPException(status_code=404, detail="策略不存在")

        # 创建交易记录
        transaction = Transaction(
            user_id=strategy.user_id,
            strategy_id=strategy.id,
            status=TransactionStatus.PREPARED,
            tx_type=TransactionType.LEND,  # 根据策略类型设置
            from_token=strategy.input_token,
            amount=strategy.input_amount,
            tx_payload={
                "protocol": strategy.protocol_name,
                "action": "deposit",
                "instructions": [],  # TODO: 调用区块链服务生成真实交易指令
            },
            simulation_result={
                "simulated": True,
                "success": True,
                "estimated_fee_sol": 0.00001,
            },
        )

        db.add(transaction)

        # 更新策略状态
        strategy.status = StrategyStatus.APPROVED
        await db.commit()
        await db.refresh(transaction)
        await cache_delete(redis, f"strategy:detail:{strategy_id}")
        await cache_delete_by_patterns(
            redis,
            [
                f"strategy:list:{request.wallet_address}:*",
                f"risk:transactions:{request.wallet_address}:*",
            ],
        )

        return TransactionResponse(
            id=str(transaction.id),
            tx_type=transaction.tx_type.value,
            status=transaction.status.value,
            from_token=transaction.from_token,
            to_token=transaction.to_token,
            amount=float(transaction.amount) if transaction.amount else None,
            tx_payload=transaction.tx_payload,
            created_at=transaction.created_at,
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="无效的策略 ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行策略失败: {str(e)}")


@router.get("/health")
async def strategy_health():
    """策略服务健康检查"""
    return {"status": "healthy", "service": "strategy"}
