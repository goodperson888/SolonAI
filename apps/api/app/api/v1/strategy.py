"""
策略生成 API

提供策略生成、查询、执行等接口
"""

import os
import sys
import uuid
from datetime import datetime, timedelta
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import AliasChoices, BaseModel, Field
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
from app.core.demo import build_protocol_capabilities, is_demo_mode_enabled  # noqa: E402
from app.core.redis import get_redis  # noqa: E402
from app.models import Strategy, Transaction, User  # noqa: E402
from app.models.strategy import StrategyStatus  # noqa: E402
from app.models.transaction import TransactionStatus, TransactionType  # noqa: E402

router = APIRouter()
SupportedNetwork = Literal["mainnet", "devnet"]


def normalize_network(network: Optional[str]) -> SupportedNetwork:
    return "devnet" if network == "devnet" else "mainnet"


def build_fallback_strategy(request: "StrategyGenerateRequest") -> dict:
    """AI 工作流不可用时的降级策略。"""
    protocol_map = {
        "conservative": "MarginFi",
        "balanced": "MarginFi",
        "aggressive": "Raydium",
    }
    apy_map = {
        "conservative": 5.2,
        "balanced": 8.5,
        "aggressive": 14.8,
    }

    protocol = protocol_map.get(request.risk_level, "MarginFi")
    estimated_apy = apy_map.get(request.risk_level, 8.5)
    half_amount = round(request.amount / 2, 2)

    if request.risk_level == "conservative":
        steps = [
            {
                "step": 1,
                "action": "deposit",
                "protocol": "MarginFi",
                "token": request.token,
                "amount": request.amount,
                "expected_apy": estimated_apy,
                "description": f"将 {request.amount} {request.token} 存入 MarginFi 获取稳定收益。",
            }
        ]
    elif request.risk_level == "aggressive":
        steps = [
            {
                "step": 1,
                "action": "swap",
                "protocol": "Jupiter",
                "token": request.token,
                "amount": request.amount,
                "expected_apy": 0,
                "description": f"通过 Jupiter 将 {request.token} 调整为更适合高收益策略的资产组合。",
            },
            {
                "step": 2,
                "action": "provide_liquidity",
                "protocol": "Raydium",
                "token": request.token,
                "amount": request.amount,
                "expected_apy": estimated_apy,
                "description": f"将资产投入 Raydium 高收益池，目标年化约 {estimated_apy}%。",
            },
        ]
    else:
        steps = [
            {
                "step": 1,
                "action": "deposit",
                "protocol": "MarginFi",
                "token": request.token,
                "amount": half_amount,
                "expected_apy": 6.0,
                "description": f"先将 {half_amount} {request.token} 存入 MarginFi 获取基础收益。",
            },
            {
                "step": 2,
                "action": "provide_liquidity",
                "protocol": "Raydium",
                "token": request.token,
                "amount": round(request.amount - half_amount, 2),
                "expected_apy": estimated_apy,
                "description": "其余资金进入主流流动性池，在收益和风险之间做平衡。",
            },
        ]

    return {
        "intent": "generate_strategy",
        "strategy": {
            "title": f"{request.risk_level} 策略",
            "protocol": protocol,
            "estimated_apy": estimated_apy,
            "steps": steps,
        },
        "explanation": (
            "当前 AI 工作流依赖未完全安装，已为你生成一套基础降级策略。"
            "安装 AI 依赖后可获得更个性化的结果。"
        ),
        "risk_assessment": {
            "risk_level": "low" if request.risk_level == "conservative" else "medium" if request.risk_level == "balanced" else "high",
            "is_safe": True,
            "score": 72 if request.risk_level == "balanced" else 80 if request.risk_level == "conservative" else 65,
            "checks": [
                {
                    "item": "降级模式",
                    "status": "warning",
                    "detail": "当前使用后端内置模板策略，不是完整 AI 个性化结果。",
                }
            ],
            "warnings": ["建议补齐 AI 依赖后重新生成，以获得更贴近实时市场的数据。"],
            "blockers": [],
        },
    }


def build_protocol_preview_payload(
    protocol_name: Optional[str],
    input_token: str,
    amount: float,
    wallet_address: str,
    network: SupportedNetwork,
) -> dict:
    protocol = (protocol_name or "未知协议").strip() or "未知协议"
    normalized = protocol.lower()

    preview_map = {
        "marginfi": {
            "headline": "借贷存款参数预览",
            "summary": f"将 {amount:g} {input_token} 存入 MarginFi，先展示借贷参数、费用估计和执行提醒。",
            "steps": [
                "校验钱包余额、目标资产和协议可用性",
                f"准备 {amount:g} {input_token} 的存款参数",
                "展示预估手续费、风险提示和下一步签名入口",
            ],
            "next_step": "后续接入完整 MarginFi SDK 后，这里会直接生成可签名存款交易。",
        },
        "kamino": {
            "headline": "自动化策略预览",
            "summary": f"基于 {amount:g} {input_token} 的 Kamino 策略预览，当前展示金库方向、预期收益区间与费用估计。",
            "steps": [
                "识别目标金库或自动化策略类型",
                "展示预期 APY、管理费和主要风险来源",
                "生成执行前确认信息，便于后续接钱包签名",
            ],
            "next_step": "后续接入 Kamino 真实策略/金库 SDK 后，可从这里直接拉起签名。",
        },
        "orca": {
            "headline": "集中流动性预览",
            "summary": f"为 {amount:g} {input_token} 生成 Orca Whirlpool 预览，当前展示池子、价格区间和风险说明。",
            "steps": [
                "匹配目标池子与对应代币对",
                "展示集中流动性范围、无常损失风险和费用估计",
                "保留执行前确认入口，等待后续接真实交易构建",
            ],
            "next_step": "后续接入 Orca Whirlpool 交易构建后，可直接生成加池签名请求。",
        },
        "solend": {
            "headline": "借贷仓位预览",
            "summary": f"为 {amount:g} {input_token} 生成 Solend 借贷预览，当前返回最接近真实的存借参数。",
            "steps": [
                "读取目标市场与资产借贷参数",
                "展示抵押/借款相关风险与费用估计",
                "生成执行确认卡片，便于后续补全真实交易",
            ],
            "next_step": "后续接入 Solend 执行 SDK 后，这里会直接下发待签名交易。",
        },
    }

    selected = preview_map.get(
        normalized,
        {
            "headline": "协议执行预览",
            "summary": f"为 {protocol} 生成 {amount:g} {input_token} 的执行前参数预览。",
            "steps": [
                "确认协议与目标资产",
                "展示参数、费用估计和主要风险",
                "等待后续接入真实交易构建",
            ],
            "next_step": "当前协议仍处于预览模式，后续补齐 SDK 后可直接拉起钱包签名。",
        },
    )

    return {
        "protocol": protocol,
        "wallet_address": wallet_address,
        "network": network,
        "headline": selected["headline"],
        "summary": selected["summary"],
        "steps": selected["steps"],
        "next_step": selected["next_step"],
        "amount_human": amount,
        "input_token": input_token,
    }


def get_run_agent():
    """Import AI workflow lazily so missing AI deps do not break API startup."""
    try:
        from graphs.main_graph import run_agent  # noqa: WPS433, E402

        return run_agent
    except ModuleNotFoundError as exc:
        missing_package = exc.name or "unknown dependency"
        raise HTTPException(
            status_code=503,
            detail=(
                f"AI 策略服务依赖未安装，当前无法调用智能体工作流。 缺少依赖: {missing_package}"
            ),
        ) from exc


def get_transaction_service():
    """Import TransactionService lazily."""
    try:
        # 追加 services 根目录（与 assets.py 的导入保持一致）
        services_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "services")
        )
        if services_path not in sys.path:
            sys.path.insert(0, services_path)

        from blockchain.services.transaction_service import TransactionService  # noqa: WPS433, E402

        return TransactionService()
    except ModuleNotFoundError as exc:
        missing_package = exc.name or "unknown dependency"
        raise HTTPException(
            status_code=503,
            detail=f"区块链交易服务依赖未安装: {missing_package}",
        ) from exc


# ===== 协议常量 =====

# 已知协议的 Program ID（用于 lending/staking 指令元数据）
PROTOCOL_PROGRAM_IDS = {
    "MarginFi": "MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA",
    "Solend": "So1endDq2YkqhipRh3WViPa8hFMqeBg1E6HkT1eLVdk",
    "Jupiter": "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4",
    "Raydium": "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK",
}

# 链上 Mainnet 代币 Mint 地址
TOKEN_MINTS = {
    "SOL": "So11111111111111111111111111111111111111112",
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
}

# 代币精度
TOKEN_DECIMALS = {
    "SOL": 9,
    "USDC": 6,
    "USDT": 6,
}


# ===== 请求/响应模型 =====


class StrategyGenerateRequest(BaseModel):
    """策略生成请求"""

    wallet_address: str  # 钱包地址
    risk_level: str  # 风险等级：conservative/balanced/aggressive
    amount: float  # 投资金额
    token: str = "USDC"  # 投资代币
    duration: Optional[int] = Field(
        default=30,
        validation_alias=AliasChoices("duration", "duration_days"),
    )  # 持续时间（天）


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
    network: Optional[SupportedNetwork] = "mainnet"
    execution_mode: Optional[Literal["auto", "simulate", "build"]] = "auto"


class ChatStrategySaveRequest(BaseModel):
    """将 AI 对话中的策略草案保存到策略工作台。"""

    wallet_address: str
    strategy: dict
    risk_assessment: dict = Field(default_factory=dict)
    summary: Optional[str] = None


class TransactionResponse(BaseModel):
    """交易响应"""

    id: str
    tx_type: str
    status: str
    from_token: Optional[str]
    to_token: Optional[str]
    amount: Optional[float]
    tx_payload: dict
    simulation_result: dict
    network: str = "mainnet"
    execution_mode: str = "auto"
    created_at: datetime


class CompletePreparedTransactionRequest(BaseModel):
    """前端钱包已签名并提交后，回写链上签名和状态。"""

    signature: str
    status: Literal["submitted", "confirmed"] = "submitted"


class StrategiesListResponse(BaseModel):
    """策略列表响应"""

    strategies: List[StrategyResponse]


class StrategyDetailResponse(BaseModel):
    """策略详情响应"""

    strategy: StrategyResponse


class StrategyCapabilitiesResponse(BaseModel):
    demo_mode: bool
    summary: dict
    protocols: dict
    testing_guidance: dict


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
        user_input = f"我想用 {request.amount} {request.token} 进行 {request.risk_level} 风险等级的投资，帮我生成一个策略"

        try:
            run_agent = get_run_agent()
            agent_result = await run_agent(
                user_input=user_input,
                wallet_address=request.wallet_address,
            )
        except HTTPException as exc:
            if exc.status_code != 503:
                raise
            agent_result = build_fallback_strategy(request)

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


@router.post("/save-draft", response_model=StrategyResponse)
async def save_strategy_draft(
    request: ChatStrategySaveRequest,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """保存 AI 对话中的结构化策略为工作台草案。"""
    try:
        result = await db.execute(select(User).where(User.wallet_address == request.wallet_address))
        user = result.scalar_one_or_none()

        if not user:
            user = User(wallet_address=request.wallet_address)
            db.add(user)
            await db.commit()
            await db.refresh(user)

        strategy_payload = request.strategy or {}
        steps = strategy_payload.get("steps", []) or []
        first_step = steps[0] if steps else {}
        risk_level = (
            strategy_payload.get("risk_level")
            or request.risk_assessment.get("risk_level")
            or "balanced"
        )
        title = strategy_payload.get("title") or strategy_payload.get("strategy_name") or "AI 策略草案"
        protocol_name = strategy_payload.get("protocol") or strategy_payload.get("protocol_name") or "待定"
        estimated_apy = strategy_payload.get("estimated_apy", strategy_payload.get("expected_apy"))

        strategy = Strategy(
            user_id=user.id,
            strategy_type="generate_strategy",
            status=StrategyStatus.DRAFT,
            input_token=first_step.get("token") or "USDC",
            input_amount=first_step.get("amount"),
            estimated_apy=estimated_apy,
            risk_level=risk_level,
            protocol_name=protocol_name,
            title=title,
            summary=request.summary or "来自 AI 助手的策略草案",
            steps=steps,
            strategy_payload=strategy_payload,
            risk_assessment=request.risk_assessment or {},
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存策略草案失败: {str(e)}")


@router.get("/list", response_model=StrategiesListResponse)
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
            return StrategiesListResponse(strategies=cached)

        # 查找用户
        result = await db.execute(select(User).where(User.wallet_address == wallet_address))
        user = result.scalar_one_or_none()

        if not user:
            return StrategiesListResponse(strategies=[])

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
        return StrategiesListResponse(strategies=payload)

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

        normalized_network = normalize_network(request.network)

        # 根据策略类型和协议决定交易类型
        protocol = (strategy.protocol_name or "").lower()
        strategy_type = strategy.strategy_type or ""
        input_token = strategy.input_token or "USDC"
        amount = float(strategy.input_amount) if strategy.input_amount else 0.0
        token_mints = TOKEN_MINTS if normalized_network == "mainnet" else {
            "SOL": "So11111111111111111111111111111111111111112",
            "USDC": "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU",
            "USDT": "EJwZgeZrdC8TXTQbQBoL6bfuAnFUUy1PVCMB4DYPzVaS",
        }

        # 决定交易类型
        is_swap = "swap" in strategy_type or protocol in ("jupiter", "raydium")
        tx_type = TransactionType.SWAP if is_swap else TransactionType.LEND

        demo_mode = is_demo_mode_enabled()
        devnet_forces_simulation = normalized_network != "mainnet"
        protocol_requires_mainnet = protocol in ("marginfi", "jupiter", "raydium", "solend")
        requested_mode = request.execution_mode or "auto"
        should_simulate_only = (
            requested_mode == "simulate"
            or demo_mode
            or devnet_forces_simulation
            or (normalized_network != "mainnet" and protocol_requires_mainnet)
        )
        execution_mode = "simulate" if should_simulate_only else ("build" if requested_mode == "build" else "auto")

        # 构建真实交易指令
        tx_payload = {
            "protocol": strategy.protocol_name,
            "action": "swap" if is_swap else "deposit",
            "network": normalized_network,
            "execution_mode": execution_mode,
        }
        simulation_result = {}

        try:
            if should_simulate_only:
                simulation_result = {
                    "simulated": True,
                    "success": True,
                    "mode": "demo" if demo_mode else "mock" if devnet_forces_simulation else "simulate",
                    "estimated_fee_sol": 0.000005,
                    "note": (
                        "当前为 DEMO 演示模式，返回稳定的预览结果，不会生成真实可广播交易。"
                        if demo_mode
                        else
                        "当前为安全测试模式，未生成真实可广播交易。"
                        if devnet_forces_simulation
                        else "当前按 simulate 模式执行，未生成真实可广播交易。"
                    ),
                }
                if normalized_network != "mainnet":
                    simulation_result["network_hint"] = (
                        f"{strategy.protocol_name or '当前协议'} 在 {normalized_network} 下默认走模拟，"
                        "这样你可以先验证页面、参数和风控提示。"
                    )
                tx_payload.update({
                    "wallet_address": request.wallet_address,
                    "input_mint": token_mints.get(input_token, ""),
                    "amount_human": amount,
                    "simulation_only": True,
                    "next_step": (
                        "关闭 DEMO 模式并切换主网后，可尝试生成真实待签名交易。"
                        if demo_mode
                        else "切换主网并选择 build 模式后，可尝试生成真实待签名交易。"
                    ),
                })
            else:
                tx_service = get_transaction_service()
                try:
                    if is_swap:
                        # 获取 Swap 报价并构建交易
                        input_mint = token_mints.get(input_token, token_mints.get("USDC"))
                        output_token = strategy.output_token or "SOL"
                        output_mint = token_mints.get(output_token, token_mints.get("SOL"))

                        decimals = TOKEN_DECIMALS.get(input_token, 6)
                        amount_raw = int(amount * (10 ** decimals))

                        # 获取报价
                        quote = await tx_service.get_swap_quote(
                            input_mint=input_mint,
                            output_mint=output_mint,
                            amount=amount_raw,
                            slippage_bps=50,
                            provider="auto",
                        )

                        # 构建交易
                        swap_tx_base64 = await tx_service.build_swap_transaction(
                            quote=quote,
                            user_public_key=request.wallet_address,
                        )

                        # 模拟交易
                        try:
                            sim = await tx_service._rpc.simulate_transaction(swap_tx_base64)
                            simulation_result = {
                                "simulated": True,
                                "success": sim.get("err") is None,
                                "mode": "real_build",
                                "logs": sim.get("logs", [])[:10],
                                "units_consumed": sim.get("units_consumed"),
                            }
                        except Exception:
                            simulation_result = {"simulated": False, "mode": "real_build"}

                    # 估算手续费
                        try:
                            fee_info = await tx_service._rpc.estimate_fee_for_transaction(swap_tx_base64)
                            simulation_result["estimated_fee_sol"] = fee_info.get("fee_sol")
                        except Exception:
                            simulation_result["estimated_fee_sol"] = 0.000005

                        tx_payload.update({
                            "swap_transaction_base64": swap_tx_base64,
                            "quote": {
                                "provider": quote.provider,
                                "input_mint": quote.input_mint,
                                "output_mint": quote.output_mint,
                                "in_amount": str(quote.in_amount),
                                "out_amount": str(quote.out_amount),
                                "price_impact_pct": str(quote.price_impact_pct or 0),
                                "slippage_bps": quote.slippage_bps,
                            },
                            "simulation_only": False,
                        })
                    else:
                        # Lending 策略 — 提供协议信息和操作参数，前端需签名
                        program_id = PROTOCOL_PROGRAM_IDS.get(
                            strategy.protocol_name, PROTOCOL_PROGRAM_IDS.get("MarginFi", "")
                        )
                        input_mint = token_mints.get(input_token, token_mints.get("USDC"))
                        decimals = TOKEN_DECIMALS.get(input_token, 6)
                        amount_raw = int(amount * (10 ** decimals))
                        preview_payload = build_protocol_preview_payload(
                            strategy.protocol_name,
                            input_token,
                            amount,
                            request.wallet_address,
                            normalized_network,
                        )

                        tx_payload.update({
                            "program_id": program_id,
                            "input_mint": input_mint,
                            "amount_raw": amount_raw,
                            "amount_human": amount,
                            "decimals": decimals,
                            "wallet_address": request.wallet_address,
                            "simulation_only": True,
                            "preview_payload": preview_payload,
                            "next_step": preview_payload["next_step"],
                        })
                        simulation_result = {
                            "simulated": True,
                            "success": True,
                            "mode": "protocol_placeholder",
                            "note": preview_payload["summary"],
                            "estimated_fee_sol": 0.000005,
                            "preview_payload": preview_payload,
                        }
                finally:
                    await tx_service.close()

        except HTTPException:
            raise
        except Exception as e:
            # 区块链服务调用失败时降级
            import logging
            logging.warning(f"交易构建失败，降级处理: {e}")
            tx_payload.update({
                "error": f"交易构建服务暂不可用: {str(e)}",
                "wallet_address": request.wallet_address,
                "input_mint": token_mints.get(input_token, ""),
                "amount_human": amount,
            })
            simulation_result = {
                "simulated": False,
                "success": False,
                "mode": "fallback_error",
                "error": str(e),
                "estimated_fee_sol": 0.000005,
            }

        # 创建交易记录
        transaction = Transaction(
            user_id=strategy.user_id,
            strategy_id=strategy.id,
            status=TransactionStatus.PREPARED,
            tx_type=tx_type,
            from_token=strategy.input_token,
            to_token=strategy.output_token,
            amount=strategy.input_amount,
            tx_payload=tx_payload,
            simulation_result=simulation_result,
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
            simulation_result=transaction.simulation_result,
            network=normalized_network,
            execution_mode=execution_mode,
            created_at=transaction.created_at,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的策略 ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行策略失败: {str(e)}")


@router.post("/transactions/{transaction_id}/complete", response_model=TransactionResponse)
async def complete_prepared_transaction(
    transaction_id: str,
    request: CompletePreparedTransactionRequest,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """回写前端钱包已提交/确认的交易签名。"""
    try:
        result = await db.execute(select(Transaction).where(Transaction.id == uuid.UUID(transaction_id)))
        transaction = result.scalar_one_or_none()
        if not transaction:
            raise HTTPException(status_code=404, detail="交易记录不存在")

        transaction.signature = request.signature
        transaction.status = (
            TransactionStatus.CONFIRMED
            if request.status == "confirmed"
            else TransactionStatus.SUBMITTED
        )
        if request.status == "submitted":
            transaction.submitted_at = datetime.utcnow()
        else:
            transaction.submitted_at = transaction.submitted_at or datetime.utcnow()
            transaction.confirmed_at = datetime.utcnow()

        strategy = None
        if transaction.strategy_id:
            strategy_result = await db.execute(
                select(Strategy).where(Strategy.id == transaction.strategy_id)
            )
            strategy = strategy_result.scalar_one_or_none()
            if strategy:
                strategy.status = (
                    StrategyStatus.EXECUTED
                    if request.status == "confirmed"
                    else StrategyStatus.APPROVED
                )

        await db.commit()
        await db.refresh(transaction)

        if strategy:
            await cache_delete(redis, f"strategy:detail:{strategy.id}")
        await cache_delete_by_patterns(redis, ["strategy:list:*"])

        return TransactionResponse(
            id=str(transaction.id),
            tx_type=transaction.tx_type.value,
            status=transaction.status.value,
            from_token=transaction.from_token,
            to_token=transaction.to_token,
            amount=float(transaction.amount) if transaction.amount else None,
            tx_payload=transaction.tx_payload,
            simulation_result=transaction.simulation_result,
            network=str(transaction.tx_payload.get("network", "mainnet")),
            execution_mode=str(transaction.tx_payload.get("execution_mode", "auto")),
            created_at=transaction.created_at,
        )
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的交易 ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回写交易状态失败: {str(e)}")


@router.get("/health")
async def strategy_health():
    """策略服务健康检查"""
    return {
        "status": "healthy",
        "service": "strategy",
        "demo_mode": is_demo_mode_enabled(),
    }


@router.get("/meta/capabilities", response_model=StrategyCapabilitiesResponse)
async def strategy_capabilities():
    """返回当前策略/协议执行能力矩阵，方便前端或演示环境使用。"""
    return StrategyCapabilitiesResponse(**build_protocol_capabilities(is_demo_mode_enabled()))
