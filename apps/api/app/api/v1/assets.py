import sys
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

# 添加区块链服务路径 - 从当前文件向上找到项目根目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# apps/api/app/api/v1 -> apps/api/app/api -> apps/api/app -> apps/api -> apps -> project_root
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "..", ".."))
services_path = os.path.join(project_root, "services")
sys.path.insert(0, services_path)

from blockchain.solana_client import SolanaClient

router = APIRouter()


# ===== 响应模型 =====


class TokenAsset(BaseModel):
    """Token 资产"""

    token: str  # Token 符号
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


@router.get("/{wallet_address}", response_model=WalletAssets)
async def get_assets(wallet_address: str):
    """
    获取钱包资产

    查询链上真实数据：
    - SOL 余额
    - SPL Token 余额
    - 计算总价值（美元）
    """
    try:
        # 创建 Solana 客户端
        client = SolanaClient()

        # 获取 SOL 余额
        sol_balance = await client.get_sol_balance(wallet_address)

        # 获取 Token 账户（暂时返回空列表，后续实现 Token 解析）
        token_accounts = await client.get_token_accounts(wallet_address)

        # 关闭客户端
        await client.close()

        # TODO: 接入价格 API 获取实时价格
        # 暂时使用固定价格
        sol_price = 178.32

        # 计算价值
        sol_value = sol_balance * sol_price

        # TODO: 解析 Token 账户数据
        tokens = []

        return WalletAssets(
            wallet_address=wallet_address,
            sol_balance=sol_balance,
            sol_price_usd=sol_price,
            sol_value_usd=sol_value,
            tokens=tokens,
            total_value_usd=sol_value,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取资产失败: {str(e)}")


@router.get("/{wallet_address}/diagnosis")
async def diagnose_assets(wallet_address: str):
    """
    资产诊断

    TODO: 实现资产诊断逻辑
    - 盈亏分析
    - 风险诊断
    - 收益优化建议
    """
    return {"wallet_address": wallet_address, "message": "资产诊断接口 - 待实现"}
