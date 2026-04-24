#!/usr/bin/env python3
"""
测试价格查询功能
"""

import asyncio
import sys
import os

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, "services", "ai-agents"))

from graphs.main_graph import run_agent_stream


async def test_price_query():
    """测试价格查询"""
    print("=" * 60)
    print("测试: 价格查询功能")
    print("=" * 60)

    questions = [
        "SOL 现在多少钱���",
        "USDC 的价格是多少？",
        "帮我查一下 SOL 和 USDC 的价格",
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n\n{'='*60}")
        print(f"问题 {i}: {question}")
        print('='*60)
        print()

        async for event in run_agent_stream(
            user_input=question,
            wallet_address="",
            session_id=f"test_price_{i}",
        ):
            if event["type"] == "token":
                print(event["content"], end="", flush=True)
            elif event["type"] == "agent_status":
                if event["status"] == "running":
                    print(f"\n🤖 [{event['agent']}] {event['message']}", flush=True)
            elif event["type"] == "data":
                data = event["data"]
                print(f"\n\n📊 返回数据:")
                print(f"  - Intent: {data.get('intent')}")
                if data.get('market_prices'):
                    print(f"  - 市场价格:")
                    for token, price_data in data['market_prices'].items():
                        print(f"    • {token}: ${price_data.get('price_usd')}")
            elif event["type"] == "complete":
                print("\n\n✅ 回复完成")

        print(f"\n\n{'='*60}\n")


async def main():
    print("\n🚀 测试价格查询功能\n")
    await test_price_query()
    print("\n\n🎉 测试完成！")


if __name__ == "__main__":
    asyncio.run(main())
