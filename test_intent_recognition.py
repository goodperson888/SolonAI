"""测试 Intent Agent 的意图识别准确性"""
import asyncio
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "services/ai-agents"))

from agents.intent_agent import IntentAgent
from llm_factory import create_llm


async def test_intent_recognition():
    """测试多个查询语句的意图识别"""
    llm = create_llm()
    intent_agent = IntentAgent(llm)

    test_cases = [
        "查询余额",
        "我的账户资产多少",
        "知道我有多少资产吗",
        "帮我看看钱包里有什么",
        "我有多少SOL",
    ]

    wallet_address = "5Ez6umkdCCRiDWBThfoCUa1XPvi7ZWAeKshXQsx7gKh4"

    for user_input in test_cases:
        print(f"\n{'='*60}")
        print(f"测试输入: {user_input}")
        print(f"{'='*60}")

        state = {
            "user_input": user_input,
            "wallet_address": wallet_address,
            "chat_history": [],
        }

        result = await intent_agent.process(state)

        intent = result.get("intent", "未识别")
        params = result.get("intent_params", {})

        print(f"✓ 识别意图: {intent}")
        print(f"✓ 参数: {params}")

        if intent != "query_assets":
            print(f"❌ 错误！应该识别为 query_assets，但识别为 {intent}")
        else:
            print(f"✅ 正确识别为 query_assets")


if __name__ == "__main__":
    asyncio.run(test_intent_recognition())
