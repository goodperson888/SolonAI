#!/usr/bin/env python3
"""
测试修复后的 DeFi 数据展示功能
"""

import asyncio
import sys
import os

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, "services", "ai-agents"))

from graphs.main_graph import run_agent_stream


async def test_defi_recommendations():
    """测试 DeFi 推荐功能"""
    print("=" * 60)
    print("测试: 询问 DeFi 收益机会")
    print("=" * 60)

    test_questions = [
        "有什么好的 DeFi 收益机会？",
        "推荐一个稳健的投资策略",
        "现在哪个协议收益率最高？",
        "SOL 现在多少钱？",
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n\n{'='*60}")
        print(f"问题 {i}: {question}")
        print('='*60)
        print()

        full_response = ""
        async for event in run_agent_stream(
            user_input=question,
            wallet_address="",  # 不需要钱包
            session_id=f"test_session_{i}",
        ):
            if event["type"] == "token":
                content = event["content"]
                print(content, end="", flush=True)
                full_response += content
            elif event["type"] == "agent_status":
                if event["status"] == "running":
                    print(f"\n🤖 [{event['agent']}] {event['message']}", flush=True)
            elif event["type"] == "data":
                data = event["data"]
                print(f"\n\n📊 返回数据:")
                print(f"  - Intent: {data.get('intent')}")
                if data.get('defi_best_opportunities'):
                    print(f"  - 最佳机会数量: {len(data['defi_best_opportunities'])}")
                if data.get('market_prices'):
                    print(f"  - 价格数据: {list(data['market_prices'].keys())}")
            elif event["type"] == "complete":
                print("\n\n✅ 回复完成")

        print(f"\n\n{'='*60}\n")


async def main():
    print("\n🚀 测试修复后的 DeFi 数据展示功能\n")
    await test_defi_recommendations()
    print("\n\n🎉 测试完成！")


if __name__ == "__main__":
    asyncio.run(main())
