"""
AI 对话 API

提供 AI 对话接口，前端通过 HTTP 请求调用。
后端接收用户消息 → 调用 AI 智能体 → 返回结果。
"""

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
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

from app.core.cache import cache_delete_by_patterns, cache_get_json, cache_set_json  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.database import get_db  # noqa: E402
from app.core.redis import get_redis  # noqa: E402
from app.models import ChatMessage, ChatSession, User  # noqa: E402
from app.models.chat_message import MessageRole  # noqa: E402

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
            detail=(
                f"AI 对话服务依赖未安装，当前无法调用智能体工作流。 缺少依赖: {missing_package}"
            ),
        ) from exc


def get_run_agent_stream():
    """Import AI streaming workflow lazily."""
    try:
        from graphs.main_graph import run_agent_stream  # noqa: WPS433, E402

        return run_agent_stream
    except ModuleNotFoundError as exc:
        missing_package = exc.name or "unknown dependency"
        raise HTTPException(
            status_code=503,
            detail=(
                f"AI 对话服务依赖未安装，当前无法调用智能体工作流。 缺少依赖: {missing_package}"
            ),
        ) from exc


# ===== 请求/响应模型 =====


class ChatRequest(BaseModel):
    """对话请求"""

    message: str  # 用户消息
    wallet_address: Optional[str] = ""  # 钱包地址（可选）
    session_id: Optional[str] = ""  # 会话ID（可选，不传则自动生成）


class ChatResponse(BaseModel):
    """对话响应"""

    reply: str  # AI 回复（大白话）
    intent: str  # 识别的意图
    intent_params: dict  # 提取的参数
    session_id: str  # 会话ID
    data: Optional[dict] = None  # 附加数据（策略、风控结果等）


class SessionItem(BaseModel):
    """会话项"""

    id: str
    session_id: str
    title: Optional[str]
    created_at: datetime


class MessageItem(BaseModel):
    """消息项"""

    id: str
    role: str
    content: str
    intent: Optional[str]
    created_at: datetime


async def get_or_create_user(db: AsyncSession, user_key: str) -> User:
    result = await db.execute(select(User).where(User.wallet_address == user_key))
    user = result.scalar_one_or_none()

    if user:
        return user

    user = User(wallet_address=user_key)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_or_create_session(
    db: AsyncSession,
    user: User,
    session_id: str,
    title: str,
) -> ChatSession:
    result = await db.execute(select(ChatSession).where(ChatSession.session_id == session_id))
    chat_session = result.scalar_one_or_none()

    if chat_session:
        return chat_session

    chat_session = ChatSession(
        user_id=user.id,
        session_id=session_id,
        title=title[:50],
    )
    db.add(chat_session)
    await db.commit()
    await db.refresh(chat_session)
    return chat_session


async def save_chat_message(
    db: AsyncSession,
    chat_session: ChatSession,
    role: MessageRole,
    content: str,
    intent: str = "",
    extra_data: Optional[dict] = None,
) -> None:
    chat_session.updated_at = datetime.now(timezone.utc)
    message = ChatMessage(
        session_id=chat_session.id,
        role=role,
        content=content,
        intent=intent,
        extra_data=extra_data,
    )
    db.add(message)
    await db.commit()


async def run_chat_agent(
    request: ChatRequest,
    wallet_address: str,
    session_id: str,
    chat_history: list = None,
) -> dict:
    try:
        run_agent = get_run_agent()
        return await run_agent(
            user_input=request.message,
            wallet_address=wallet_address,
            session_id=session_id,
            chat_history=chat_history or [],
        )
    except HTTPException as exc:
        if exc.status_code != 503:
            raise

        # Allow frontend/API/database integration testing even when optional
        # AI workflow dependencies are not installed locally.
        return {
            "explanation": exc.detail,
            "intent": "chat_unavailable",
            "intent_params": {},
            "validation_result": None,
        }


def build_chat_data(result: dict) -> Optional[dict]:
    data = {}
    if result.get("strategy"):
        data["strategy"] = result["strategy"]
    if result.get("risk_assessment"):
        data["risk_assessment"] = result["risk_assessment"]
    if result.get("transaction"):
        data["transaction"] = result["transaction"]
    if result.get("wallet_assets"):
        data["wallet_assets"] = result["wallet_assets"]
        data["total_value_usd"] = result.get("total_value_usd", 0)
    if result.get("monitoring_config"):
        data["monitoring"] = result["monitoring_config"]
    if result.get("validation_result"):
        data["validation"] = result["validation_result"]
    return data or None


# ===== API 接口 =====


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    发送消息给 AI

    前端调用示例：
    POST /api/v1/chat/message
    {
        "message": "帮我看看钱包里有什么资产",
        "wallet_address": "7xKXtg...",
        "session_id": "abc123"
    }
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")

    # 生成会话ID
    session_id = request.session_id or str(uuid.uuid4())

    try:
        # 查找或创建用户
        wallet_address = request.wallet_address.strip() if request.wallet_address else ""
        user_key = wallet_address or f"guest:{session_id}"
        user = await get_or_create_user(db, user_key)

        # 查找或创建会话
        chat_session = await get_or_create_session(
            db,
            user,
            session_id,
            request.message,
        )

        # 保存用户消息
        await save_chat_message(
            db,
            chat_session,
            MessageRole.USER,
            request.message,
        )

        # 查询最近的对话历史（最多10轮）
        history_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == chat_session.id)
            .order_by(desc(ChatMessage.created_at))
            .limit(20)  # 最近20条（10轮对话）
        )
        history_messages = list(reversed(history_result.scalars().all()))
        chat_history = [
            {"role": m.role.value, "content": m.content}
            for m in history_messages[:-1]  # 排除刚刚保存的当前消息
        ]

        # 调用 AI 智能体工作流
        result = await run_chat_agent(request, wallet_address, session_id, chat_history)

        # 保存 AI 回复
        assistant_extra_data = dict(result)
        if result.get("reasoning"):
            assistant_extra_data["reasoning"] = result["reasoning"]

        await save_chat_message(
            db,
            chat_session,
            MessageRole.ASSISTANT,
            result.get("explanation", ""),
            result.get("intent", ""),
            assistant_extra_data,
        )
        await cache_delete_by_patterns(
            redis,
            [
                f"chat:sessions:{user_key}:*",
                f"chat:messages:{session_id}:*",
            ],
        )

        # 构建附加数据
        data = build_chat_data(result)

        return ChatResponse(
            reply=result.get("explanation", "抱歉，我暂时无法回答这个问题。"),
            intent=result.get("intent", "chat"),
            intent_params=result.get("intent_params", {}),
            session_id=session_id,
            data=data,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 服务错误: {str(e)}")


@router.post("/message/stream")
async def send_message_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    流式发送消息给 AI（SSE）

    前端使用 EventSource 或 fetch + ReadableStream 接收：
    - event: token  → 逐字输出 AI 回复
    - event: data   → 附加数据（策略、风控等）
    - event: done   → 结束标志
    - event: error  → 错误信息
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")

    session_id = request.session_id or str(uuid.uuid4())

    async def event_generator():
        try:
            wallet_address = request.wallet_address.strip() if request.wallet_address else ""
            user_key = wallet_address or f"guest:{session_id}"
            user = await get_or_create_user(db, user_key)
            chat_session = await get_or_create_session(db, user, session_id, request.message)

            await save_chat_message(db, chat_session, MessageRole.USER, request.message)

            # 查询对话历史
            history_result = await db.execute(
                select(ChatMessage)
                .where(ChatMessage.session_id == chat_session.id)
                .order_by(desc(ChatMessage.created_at))
                .limit(20)
            )
            history_messages = list(reversed(history_result.scalars().all()))
            chat_history = [
                {"role": m.role.value, "content": m.content} for m in history_messages[:-1]
            ]

            # 发送 session_id
            yield f"event: session\ndata: {json.dumps({'session_id': session_id})}\n\n"

            # 调用 AI 工作流（流式版本）
            run_agent_stream = get_run_agent_stream()
            full_explanation = ""
            final_result = None

            async for event in run_agent_stream(
                user_input=request.message,
                wallet_address=wallet_address,
                session_id=session_id,
                chat_history=chat_history,
            ):
                event_type = event.get("type")

                # LLM 生成的 token - 立即发送到前端
                if event_type == "token":
                    token = event.get("content", "")
                    if token:
                        full_explanation += token
                        yield f"event: token\ndata: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"

                # 工作流完成
                elif event_type == "complete":
                    final_result = event.get("result", {})

                # 工作流中断（需要用户确认）
                elif event_type == "interrupt":
                    final_result = {
                        "interrupted": True,
                        "thread_id": event.get("thread_id"),
                        "approval_preview": event.get("approval_preview"),
                        "explanation": full_explanation or "请确认以下操作：",
                    }

                # 错误
                elif event_type == "error":
                    final_result = event.get("result", {})
                    yield f"event: error\ndata: {json.dumps({'error': event.get('error', '未知错误')})}\n\n"

            # 如果没有收到任何 token，使用 result 中的 explanation
            if not final_result:
                final_result = {"explanation": "抱歉，我暂时无法回答这个问题。"}

            if not full_explanation and final_result.get("explanation"):
                explanation = final_result["explanation"]
                import re

                tokens = re.findall(
                    r"[\u4e00-\u9fff]+|[a-zA-Z0-9]+|[^\u4e00-\u9fffa-zA-Z0-9\s]|\s+", explanation
                )
                for token in tokens:
                    yield f"event: token\ndata: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"
                full_explanation = explanation

            # 发送附加数据
            data = build_chat_data(final_result)
            yield f"event: data\ndata: {json.dumps({'intent': final_result.get('intent', 'chat'), 'intent_params': final_result.get('intent_params', {}), 'data': data}, ensure_ascii=False)}\n\n"

            # 保存 AI 回复
            await save_chat_message(
                db,
                chat_session,
                MessageRole.ASSISTANT,
                full_explanation,
                final_result.get("intent", ""),
            )
            await cache_delete_by_patterns(
                redis,
                [f"chat:sessions:{user_key}:*", f"chat:messages:{session_id}:*"],
            )

            yield "event: done\ndata: {}\n\n"

        except Exception as e:
            import traceback

            traceback.print_exc()
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/sessions", response_model=List[SessionItem])
async def get_sessions(
    wallet_address: str,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    获取会话列表
    """
    try:
        cache_key = f"chat:sessions:{wallet_address}:{limit}"
        cached = await cache_get_json(redis, cache_key)
        if cached is not None:
            return cached

        # 查找用户
        result = await db.execute(select(User).where(User.wallet_address == wallet_address))
        user = result.scalar_one_or_none()

        if not user:
            return []

        # 查询会话列表
        result = await db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user.id)
            .order_by(desc(ChatSession.updated_at))
            .limit(limit)
        )
        sessions = result.scalars().all()

        payload = [
            SessionItem(
                id=str(s.id),
                session_id=s.session_id,
                title=s.title,
                created_at=s.created_at,
            )
            for s in sessions
        ]
        await cache_set_json(
            redis,
            cache_key,
            [item.model_dump() for item in payload],
            settings.CACHE_TTL_CHAT_SESSIONS,
        )
        return payload

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询会话列表失败: {str(e)}")


@router.get("/sessions/{session_id}/messages", response_model=List[MessageItem])
async def get_messages(
    session_id: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    获取会话的历史消息
    """
    try:
        cache_key = f"chat:messages:{session_id}:{limit}"
        cached = await cache_get_json(redis, cache_key)
        if cached is not None:
            return cached

        # 查找会话
        result = await db.execute(select(ChatSession).where(ChatSession.session_id == session_id))
        chat_session = result.scalar_one_or_none()

        if not chat_session:
            return []

        # 查询消息列表
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == chat_session.id)
            .order_by(ChatMessage.created_at)
            .limit(limit)
        )
        messages = result.scalars().all()

        payload = [
            MessageItem(
                id=str(m.id),
                role=m.role.value,
                content=m.content,
                intent=m.intent,
                created_at=m.created_at,
            )
            for m in messages
        ]
        await cache_set_json(
            redis,
            cache_key,
            [item.model_dump() for item in payload],
            settings.CACHE_TTL_CHAT_MESSAGES,
        )
        return payload

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询消息历史失败: {str(e)}")


@router.get("/health")
async def chat_health():
    """AI 对话服务健康检查"""
    return {"status": "healthy", "service": "ai-chat"}
