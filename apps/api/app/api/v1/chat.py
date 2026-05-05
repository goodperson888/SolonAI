"""
AI 对话 API

提供 AI 对话接口，前端通过 HTTP 请求调用。
后端接收用户消息 → 调用 AI 智能体 → 返回结果。
"""

import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)
from sqlalchemy import delete, desc, select
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


def _infer_protocol_from_steps(strategy: dict) -> Optional[str]:
    if not strategy:
        return None

    protocol = strategy.get("protocol") or strategy.get("protocol_name")
    if isinstance(protocol, str) and protocol.strip():
        return protocol.strip()

    steps = strategy.get("steps") or []
    for step in steps:
        step_protocol = step.get("protocol")
        if isinstance(step_protocol, str) and step_protocol.strip():
            return step_protocol.strip()

    protocols = strategy.get("protocols") or []
    if protocols and isinstance(protocols[0], str) and protocols[0].strip():
        return protocols[0].strip()

    return None


def _normalize_strategy_payload(strategy: dict) -> dict:
    normalized = dict(strategy or {})
    inferred_protocol = _infer_protocol_from_steps(normalized)
    if inferred_protocol:
        normalized["protocol"] = inferred_protocol
        normalized["protocol_name"] = inferred_protocol

    title = normalized.get("title") or normalized.get("strategy_name")
    if isinstance(title, str) and title.strip():
        normalized["title"] = title.strip()
        normalized["strategy_name"] = title.strip()

    return normalized


def _normalize_risk_payload(risk_assessment: dict, strategy: Optional[dict]) -> dict:
    normalized = dict(risk_assessment or {})
    warnings = normalized.get("warnings") or []
    protocol = (_infer_protocol_from_steps(strategy or {}) or "").lower()
    steps = (strategy or {}).get("steps") or []
    actions = {str(step.get("action") or "").lower() for step in steps}

    # 借贷/存款策略不应该出现 LP 无常损失提示
    if protocol in {"marginfi", "solend"} or actions.issubset({"deposit", "lend", ""}):
        warnings = [
            warning
            for warning in warnings
            if "无常损失" not in str(warning)
        ]

    normalized["warnings"] = warnings
    return normalized


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
    extra_data: Optional[dict] = None


class ApprovalRequest(BaseModel):
    """用户对 AI 提议的确认结果。"""

    user_approved: bool = True


class ThreadStateResponse(BaseModel):
    """AI 工作流线程状态。"""

    thread_id: str
    interrupted: bool
    next: list[str] = []


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
    intent = result.get("intent", "chat")
    should_include_asset_cards = intent in {
        "query_assets",
        "generate_strategy",
        "execute_trade",
        "risk_check",
    }
    normalized_assets = []
    if result.get("strategy"):
        data["strategy"] = _normalize_strategy_payload(result["strategy"])
    if result.get("risk_assessment"):
        data["risk_assessment"] = _normalize_risk_payload(
            result["risk_assessment"],
            result.get("strategy"),
        )
    if result.get("transaction"):
        data["transaction"] = result["transaction"]
    if should_include_asset_cards and result.get("wallet_assets"):
        for asset in result["wallet_assets"]:
            normalized_assets.append(
                {
                    **asset,
                    "symbol": asset.get("symbol") or asset.get("token"),
                    "usd_value": asset.get("usd_value", asset.get("value_usd", 0)),
                }
            )
        data["wallet_assets"] = normalized_assets
        total_value_usd = result.get("total_value_usd", 0) or 0
        asset_total_from_rows = sum(
            float(asset.get("usd_value", 0) or 0) for asset in normalized_assets
        )
        has_non_zero_balance = any(
            float(asset.get("balance", 0) or 0) > 0 for asset in normalized_assets
        )

        if total_value_usd <= 0:
            total_value_usd = asset_total_from_rows

        if total_value_usd <= 0 and has_non_zero_balance:
            data["total_value_usd"] = None
        else:
            data["total_value_usd"] = total_value_usd
    if result.get("monitoring_config"):
        data["monitoring"] = result["monitoring_config"]
    if result.get("validation_result"):
        data["validation"] = result["validation_result"]
    if result.get("approval_preview"):
        data["approval_preview"] = result["approval_preview"]
    if "interrupted" in result:
        data["interrupted"] = result.get("interrupted")
    if result.get("thread_id"):
        data["thread_id"] = result["thread_id"]
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

            # 只有登录用户才保存到数据库
            chat_history = []
            user = None
            chat_session = None

            if wallet_address:
                user_key = wallet_address
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

            # 在 API 层直接做知识库检索（避免 Agent 自调用 HTTP 死锁）
            rag_context = ""
            rag_sources = []
            if wallet_address:
                try:
                    from app.models.knowledge import KnowledgeChunk, KnowledgeDocument

                    doc_result = await db.execute(
                        select(KnowledgeDocument).where(KnowledgeDocument.user_id == wallet_address)
                    )
                    docs = doc_result.scalars().all()
                    if docs:
                        doc_ids = [doc.id for doc in docs]
                        chunk_result = await db.execute(
                            select(KnowledgeChunk).where(KnowledgeChunk.document_id.in_(doc_ids))
                        )
                        chunks = chunk_result.scalars().all()
                        if chunks:
                            import re as re_mod

                            query_lower = request.message.lower()
                            en_kw = [
                                w
                                for w in query_lower.split()
                                if any(c.isascii() and c.isalpha() for c in w) and len(w) >= 2
                            ]
                            cn_segs = re_mod.findall(r"[\u4e00-\u9fff]+", query_lower)
                            cn_kw = []
                            for seg in cn_segs:
                                if len(seg) >= 2:
                                    cn_kw.append(seg)  # 完整片段
                                if len(seg) >= 3:
                                    cn_kw.extend(seg[i : i + 3] for i in range(len(seg) - 2))
                            cn_kw = list(set(cn_kw))
                            all_kw = en_kw + cn_kw
                            if not all_kw:
                                pass  # 无有效关键词，跳过
                            else:
                                # 计算最大可能分数用于归一化
                                max_possible = sum(len(kw) for kw in all_kw)
                                scored = []
                                for chunk in chunks:
                                    cl = chunk.content.lower()
                                    score = sum(len(kw) for kw in all_kw if kw in cl)
                                    # 要求至少匹配 30% 的关键词权重
                                    if score >= max(max_possible * 0.3, 6):
                                        doc = next(
                                            (d for d in docs if d.id == chunk.document_id),
                                            None,
                                        )
                                        scored.append(
                                            {
                                                "content": chunk.content,
                                                "filename": doc.filename if doc else "",
                                                "score": score,
                                            }
                                        )
                                scored.sort(key=lambda x: x["score"], reverse=True)
                            top = scored[:3] if all_kw and scored else []
                            if top:
                                parts = [
                                    "以下是用户上传的文档中的相关内容，请参考这些内容来回答：\n"
                                ]
                                seen = set()
                                for item in top:
                                    parts.append(f"【{item['filename']}】\n{item['content']}\n")
                                    if item["filename"] not in seen:
                                        rag_sources.append({"filename": item["filename"]})
                                        seen.add(item["filename"])
                                rag_context = "\n".join(parts)
                                logger.info(
                                    f"[Chat] RAG 检索到 {len(top)} 个文本块, 来源: {rag_sources}"
                                )
                except Exception as e:
                    logger.warning(f"[Chat] RAG 检索失败: {e}")

            # 发送 RAG 来源
            if rag_sources:
                yield f"event: rag_sources\ndata: {json.dumps({'sources': rag_sources}, ensure_ascii=False)}\n\n"

            # 调用 AI 工作流（流式版本）
            run_agent_stream = get_run_agent_stream()
            full_explanation = ""
            final_result = None

            async for event in run_agent_stream(
                user_input=request.message,
                wallet_address=wallet_address,
                session_id=session_id,
                chat_history=chat_history,
                rag_context=rag_context,
            ):
                event_type = event.get("type")

                # Agent 状态更新
                if event_type == "agent_status":
                    yield f"event: agent_status\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"

                # LLM 生成的 token - 立即发送到前端
                elif event_type == "token":
                    token = event.get("content", "")
                    if token:
                        full_explanation += token
                        yield f"event: token\ndata: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"

                # 附加数据（intent、资产等）
                elif event_type == "data":
                    final_result = event.get("data", {})

                elif event_type == "card_patch":
                    patch_result = event.get("data", {})
                    patch_payload = {
                        "card": event.get("card"),
                        "intent": patch_result.get("intent", "chat"),
                        "intent_params": patch_result.get("intent_params", {}),
                        "data": build_chat_data(patch_result),
                    }
                    yield (
                        "event: card_patch\n"
                        f"data: {json.dumps(patch_payload, ensure_ascii=False)}\n\n"
                    )

                # 工作流完成
                elif event_type == "complete":
                    pass

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

            # 只有登录用户才保存 AI 回复到数据库
            if wallet_address and chat_session:
                assistant_extra_data = dict(final_result)
                if full_explanation:
                    assistant_extra_data["explanation"] = full_explanation

                await save_chat_message(
                    db,
                    chat_session,
                    MessageRole.ASSISTANT,
                    full_explanation,
                    final_result.get("intent", ""),
                    assistant_extra_data,
                )
                user_key = wallet_address
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
                extra_data=m.extra_data,
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


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    wallet_address: str,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """删除会话及其所有消息"""
    try:
        # 查找用户
        result = await db.execute(select(User).where(User.wallet_address == wallet_address))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        # 查找会话
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.session_id == session_id, ChatSession.user_id == user.id
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")

        # 删除消息
        await db.execute(delete(ChatMessage).where(ChatMessage.session_id == session.id))
        # 删除会话
        await db.delete(session)
        await db.commit()

        # 清除缓存
        await cache_delete_by_patterns(
            redis,
            [
                f"chat:sessions:{wallet_address}:*",
                f"chat:messages:{session_id}:*",
            ],
        )

        return {"success": True, "message": "会话删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除会话失败: {str(e)}")


@router.post("/threads/{thread_id}/approval")
async def approve_thread_action(thread_id: str, request: ApprovalRequest):
    """确认或拒绝当前 AI 提议的动作。"""
    try:
        from graphs.main_graph import get_agent_state, resume_agent  # noqa: WPS433, E402

        state = await get_agent_state(thread_id)
        if not state.get("interrupted"):
            raise HTTPException(
                status_code=409,
                detail="当前会话没有等待确认的 AI 操作，可能已经处理过或线程已失效。",
            )

        result = await resume_agent(
            thread_id=thread_id,
            user_approved=request.user_approved,
        )
        return {
            "reply": result.get("explanation", "已处理你的选择。"),
            "intent": result.get("intent", "chat"),
            "intent_params": result.get("intent_params", {}),
            "data": build_chat_data(result),
            "thread_id": result.get("thread_id", thread_id),
            "interrupted": bool(result.get("interrupted", False)),
        }
    except ModuleNotFoundError as exc:
        missing_package = exc.name or "unknown dependency"
        raise HTTPException(
            status_code=503,
            detail=f"AI 审批服务依赖未安装: {missing_package}",
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"审批处理失败: {exc}") from exc


@router.get("/threads/{thread_id}/state", response_model=ThreadStateResponse)
async def get_thread_state(thread_id: str):
    """查询某条 AI 审批线程当前是否仍可继续。"""
    try:
        from graphs.main_graph import get_agent_state  # noqa: WPS433, E402

        state = await get_agent_state(thread_id)
        return ThreadStateResponse(
            thread_id=thread_id,
            interrupted=bool(state.get("interrupted", False)),
            next=state.get("next", []),
        )
    except ModuleNotFoundError as exc:
        missing_package = exc.name or "unknown dependency"
        raise HTTPException(
            status_code=503,
            detail=f"AI 审批状态服务依赖未安装: {missing_package}",
        ) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"查询线程状态失败: {exc}") from exc


@router.get("/health")
async def chat_health():
    """AI 对话服务健康检查"""
    return {"status": "healthy", "service": "ai-chat"}
