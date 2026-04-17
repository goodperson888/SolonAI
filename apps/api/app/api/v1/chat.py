"""
AI 对话 API

提供 AI 对话接口，前端通过 HTTP 请求调用。
后端接收用户消息 → 调用 AI 智能体 → 返回结果。
"""

import sys
import os
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# 添加 AI 服务路径
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "services", "ai-agents")
)

from graphs.main_graph import run_agent

router = APIRouter()


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


# ===== API 接口 =====


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
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
        # 调用 AI 智能体工作流
        result = await run_agent(
            user_input=request.message,
            wallet_address=request.wallet_address or "",
            session_id=session_id,
        )

        # 构建附加数据
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

        return ChatResponse(
            reply=result.get("explanation", "抱歉，我暂时无法回答这个问题。"),
            intent=result.get("intent", "chat"),
            intent_params=result.get("intent_params", {}),
            session_id=session_id,
            data=data if data else None,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 服务错误: {str(e)}")


@router.get("/health")
async def chat_health():
    """AI 对话服务健康检查"""
    return {"status": "healthy", "service": "ai-chat"}
