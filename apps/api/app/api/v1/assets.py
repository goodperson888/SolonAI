import os
import sys
from typing import Optional

from fastapi import APIRouter, Query

# 动态添加 services/ai-agents 到 Python 路径以便导入 Agent
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../../../services/ai-agents"))

try:
    from agents.data_aggregation_agent import DataAggregationAgent
    from agents.risk_agent import RiskAgent
except ImportError:
    # 兼容有些环境没有安装依赖的情况
    DataAggregationAgent = None
    RiskAgent = None

router = APIRouter()

# 实例化 Agents (当前用 mock 的底层服务占位，等待 AI 组完善依赖)
data_agent = DataAggregationAgent(llm=None, blockchain_service=None) if DataAggregationAgent else None
risk_agent = RiskAgent(blacklist_db=None) if RiskAgent else None

@router.get("/list")
async def get_assets_list(wallet_address: str = Query(..., description="钱包地址")):
    """
    获取钱包资产列表
    调用 DataAggregationAgent.aggregate_wallet_data()
    """
    if not data_agent:
        return {"error": "DataAggregationAgent not found"}
        
    state = {"wallet_address": wallet_address, "task_type": "wallet_analysis"}
    # 调用 DataAggregationAgent 聚合钱包数据
    result = await data_agent.aggregate_wallet_data(state)
    
    return {
        "wallet_address": wallet_address,
        "data": result.get("wallet_data", {})
    }


@router.get("/diagnose")
async def diagnose_assets(wallet_address: str = Query(..., description="钱包地址")):
    """
    资产诊断
    调用 DataAggregationAgent + RiskAgent
    """
    if not data_agent or not risk_agent:
        return {"error": "Agents not found"}
        
    # 1. 聚合钱包和风险数据
    state = {"wallet_address": wallet_address, "task_type": "risk_check"}
    state = await data_agent.aggregate_wallet_data(state)
    state = await data_agent.aggregate_risk_data(state)
    
    # 2. 构造一个 strategy 结构交给 RiskAgent 审计
    strategy_mock = {
        "wallet_data": state.get("wallet_data"),
        "risk_data": state.get("risk_data")
    }
    risk_result = await risk_agent.audit_strategy(strategy_mock)
    
    return {
        "wallet_address": wallet_address,
        "wallet_data": state.get("wallet_data", {}),
        "risk_diagnosis": risk_result
    }


@router.get("/pnl")
async def get_pnl(wallet_address: str = Query(..., description="钱包地址")):
    """
    盈亏分析
    调用 DataAggregationAgent
    """
    if not data_agent:
        return {"error": "DataAggregationAgent not found"}
        
    state = {"wallet_address": wallet_address, "task_type": "wallet_analysis"}
    result = await data_agent.aggregate_wallet_data(state)
    
    # 从 wallet_data 提取或模拟 PnL (具体逻辑由 AI 组实现)
    return {
        "wallet_address": wallet_address,
        "message": "盈亏分析数据获取成功",
        "pnl_data": {
            "total_profit": 0,
            "roi": 0.0,
            "raw_data": result.get("wallet_data", {})
        }
    }
