"""
钱包认证 API

提供 Solana 钱包签名验证登录、JWT 令牌管理
"""

import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Union

from fastapi import APIRouter, Depends, HTTPException
from jose import jwt
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models import User

router = APIRouter()

# 存储 nonce（生产环境应使用 Redis）
_nonce_store: Dict[str, Dict[str, Union[str, float]]] = {}

# JWT 配置
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24


# ===== 请求/响应模型 =====


class NonceRequest(BaseModel):
    """获取 nonce 请求"""

    wallet_address: str


class NonceResponse(BaseModel):
    """nonce 响应"""

    nonce: str
    message: str  # 待签名消息


class LoginRequest(BaseModel):
    """登录请求"""

    wallet_address: str
    signature: str  # 钱包签名，支持 hex 或 Base58 编码
    message: str  # 签名的原始消息


class LoginResponse(BaseModel):
    """登录响应"""

    token: str
    wallet_address: str
    expires_at: str


class VerifyRequest(BaseModel):
    """验证请求"""

    wallet_address: str
    signature: str
    message: str


# ===== 工具函数 =====


def _create_jwt(wallet_address: str) -> tuple[str, datetime]:
    """创建 JWT token"""
    expires = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {
        "sub": wallet_address,
        "exp": expires,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token, expires


def _decode_signature(signature: str) -> bytes:
    """兼容前端常见的 hex / Base58 签名格式。"""
    import base58

    try:
        return bytes.fromhex(signature)
    except ValueError:
        return base58.b58decode(signature)


def _verify_signature(wallet_address: str, signature: str, message: str) -> bool:
    """
    验证 Solana 钱包签名

    Solana 使用 Ed25519 签名算法
    wallet_address 是 Base58 编码的公钥
    signature 支持 hex 或 Base58 编码
    """
    try:
        import base58

        # 解码公钥 (Base58 -> bytes)
        public_key_bytes = base58.b58decode(wallet_address)

        # 解码签名
        signature_bytes = _decode_signature(signature)

        # 编码消息
        message_bytes = message.encode("utf-8")

        # 使用 nacl 验证 Ed25519 签名
        verify_key = VerifyKey(public_key_bytes)
        verify_key.verify(message_bytes, signature_bytes)
        return True

    except (BadSignatureError, ValueError, Exception):
        return False


def _cleanup_expired_nonces():
    """清理过期的 nonce（5分钟过期）"""
    now = time.time()
    expired = [k for k, v in _nonce_store.items() if now - float(v["created_at"]) > 300]
    for k in expired:
        del _nonce_store[k]


# ===== API 接口 =====


@router.post("/nonce", response_model=NonceResponse)
async def get_nonce(request: NonceRequest):
    """
    获取 nonce

    前端在签名前需要先获取一个 nonce，防止重放攻击
    """
    _cleanup_expired_nonces()

    # 生成随机 nonce
    nonce = secrets.token_hex(16)

    # 构造待签名消息
    message = (
        f"Welcome to Solon AI!\n\n"
        f"Please sign this message to verify your wallet.\n\n"
        f"Wallet: {request.wallet_address}\n"
        f"Nonce: {nonce}\n"
        f"Timestamp: {int(time.time())}"
    )

    # 存储 nonce
    _nonce_store[nonce] = {
        "created_at": time.time(),
        "wallet_address": request.wallet_address,
    }

    return NonceResponse(nonce=nonce, message=message)


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    钱包签名登录

    流程:
    1. 前端调用 /nonce 获取待签名消息
    2. 用户使用钱包签名
    3. 前端将签名结果发到此接口
    4. 后端验证签名，返回 JWT
    """
    # 验证签名
    if not _verify_signature(request.wallet_address, request.signature, request.message):
        raise HTTPException(status_code=401, detail="签名验证失败")

    # 从消息中提取 nonce 并验证
    nonce = None
    for line in request.message.split("\n"):
        if line.startswith("Nonce: "):
            nonce = line[7:]
            break

    if not nonce:
        raise HTTPException(status_code=401, detail="签名消息缺少 nonce")

    nonce_data = _nonce_store.get(nonce)
    if not nonce_data:
        raise HTTPException(status_code=401, detail="无效的 nonce")

    if nonce_data.get("wallet_address") != request.wallet_address:
        del _nonce_store[nonce]
        raise HTTPException(status_code=401, detail="nonce 与钱包地址不匹配")

    # 验证 nonce 未过期（5分钟有效）
    if time.time() - float(nonce_data["created_at"]) > 300:
        del _nonce_store[nonce]
        raise HTTPException(status_code=401, detail="签名已过期，请重新获取 nonce")

    # 使用后删除（防重放）
    del _nonce_store[nonce]

    # 查找或创建用户
    result = await db.execute(
        select(User).where(User.wallet_address == request.wallet_address)
    )
    user = result.scalar_one_or_none()

    if not user:
        user = User(wallet_address=request.wallet_address)
        db.add(user)

    # 更新登录时间
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    # 生成 JWT
    token, expires = _create_jwt(request.wallet_address)

    return LoginResponse(
        token=token,
        wallet_address=request.wallet_address,
        expires_at=expires.isoformat(),
    )


@router.post("/verify")
async def verify_wallet(request: VerifyRequest):
    """
    验证钱包地址

    验证签名是否由指定钱包地址生成，不执行登录流程
    """
    is_valid = _verify_signature(
        request.wallet_address, request.signature, request.message
    )

    if not is_valid:
        raise HTTPException(status_code=401, detail="签名验证失败")

    return {
        "valid": True,
        "wallet_address": request.wallet_address,
        "message": "钱包验证成功",
    }


@router.get("/me")
async def get_current_user(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前登录用户信息

    通过 JWT token 获取用户信息
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])
        wallet_address = payload.get("sub")
        if not wallet_address:
            raise HTTPException(status_code=401, detail="无效的 token")
    except Exception:
        raise HTTPException(status_code=401, detail="token 已过期或无效")

    result = await db.execute(
        select(User).where(User.wallet_address == wallet_address)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {
        "wallet_address": user.wallet_address,
        "risk_level": user.risk_level.value if hasattr(user.risk_level, 'value') else str(user.risk_level),
        "status": user.status.value if hasattr(user.status, 'value') else str(user.status),
        "created_at": str(user.created_at),
        "last_login_at": str(user.last_login_at) if user.last_login_at else None,
    }
