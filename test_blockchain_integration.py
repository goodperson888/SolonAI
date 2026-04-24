#!/usr/bin/env python3
"""
测试 AI Agent 调用区块链功能

测试场景：
1. 查询钱包资产（SOL + SPL Token）
2. 获取 DeFi 协议数据（Jupiter 价格、收益率）
3. 完整的 AI 对话流程
"""

import asyncio
import sys
import os

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, "services", "ai-agents"))

from graphs.main_graph import run_agent_stream


async def test_wallet_query():
    """测试查询钱包资产"""
    print("=" * 60)
    print("测试 1: 查询钱包资产")
    print("=" * 60)

    # 使用一个 Devnet 测试钱包地址
    test_wallet = "9B5XszUGdMaxCZ7uSQhPzdks5ZQSmWxrmzCSvtJ6Ns6g"

    print(f"\n📍 测试钱包: {test_wallet}")
    print("\n💬 用户问题: 帮我看看钱包里有什么资产\n")

    full_response = ""
    agent_statuses = []

    async for event in run_agent_stream(
        user_input="帮我看看钱包里有什么资产",
        wallet_address=test_wallet,
        session_id="test_session_1",
    ):
        if event["type"] == "token":
            content = event["content"]
            print(content, end="", flush=True)
            full_response += content
        elif event["type"] == "agent_status":
            status = f"[{event['agent']}] {event['message']}"
            agent_statuses.append(status)
            if event["status"] == "running":
                print(f"\n🤖 {status}", flush=True)
        elif event["type"] == "data":
            data = event["data"]
            print(f"\n\n📊 返回数据:")
            print(f"  - Intent: {data.get('intent')}")
            print(f"  - 资产数量: {len(data.get('wallet_assets', []))}")
            print(f"  - 总价值: ${data.get('total_value_usd', 0):.2f}")
            if data.get('wallet_assets'):
                print(f"\n  资产明细:")
                for asset in data['wallet_assets']:
                    print(f"    • {asset['token']}: {asset['balance']:.4f} (${asset['value_usd']:.2f})")
        elif event["type"] == "error":
            print(f"\n❌ 错误: {event['error']}")
        elif event["type"] == "complete":
            print("\n\n✅ 测试完成")

    print(f"\n\n📝 Agent 执行流程:")
    for status in agent_statuses:
        print(f"  {status}")

    return full_response


async def test_defi_query():
    """测试查询 DeFi 协议"""
    print("\n\n" + "=" * 60)
    print("测试 2: 查询 DeFi 协议收益率")
    print("=" * 60)

    print("\n💬 用户问题: 现在哪个协议的收益率最高？\n")

    full_response = ""

    async for event in run_agent_stream(
        user_input="现在哪个协议的收益率最高？",
        wallet_address="",  # 不需要钱包地址
        session_id="test_session_2",
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
                print(f"  - 最佳机会: {len(data['defi_best_opportunities'])} 个")
        elif event["type"] == "complete":
            print("\n\n✅ 测试完成")

    return full_response


async def test_chat_without_wallet():
    """测试纯聊天（无钱包）"""
    print("\n\n" + "=" * 60)
    print("测试 3: 纯聊天（快速路径）")
    print("=" * 60)

    print("\n💬 用户问题: 什么是 DeFi？\n")

    async for event in run_agent_stream(
        user_input="什么是 DeFi？",
        wallet_address="",  # 无钱包
        session_id="test_session_3",
    ):
        if event["type"] == "token":
            print(event["content"], end="", flush=True)
        elif event["type"] == "agent_status":
            if event["status"] == "running":
                print(f"\n🤖 [{event['agent']}] {event['message']}", flush=True)
        elif event["type"] == "complete":
            print("\n\n✅ 测试完成")


async def test_price_query():
    """测试价格查询"""
    print("\n\n" + "=" * 60)
    print("测试 4: 查询代币价格")
    print("=" * 60)

    print("\n💬 用户问题: SOL 现在多少钱？\n")

    async for event in run_agent_stream(
        user_input="SOL 现在多少钱？",
        wallet_address="",
        session_id="test_session_4",
    ):
        if event["type"] == "token":
            print(event["content"], end="", flush=True)
        elif event["type"] == "agent_status":
            if event["status"] == "running":
                print(f"\n🤖 [{event['agent']}] {event['message']}", flush=True)
        elif event["type"] == "data":
            data = event["data"]
            if data.get('market_prices'):
                print(f"\n\n📊 市场价格:")
                for token, price_data in data['market_prices'].items():
                    print(f"  - {token}: ${price_data.get('price_usd', 'N/A')}")
        elif event["type"] == "complete":
            print("\n\n✅ 测试完成")


async def main():
    """运行所有测试"""
    print("\n🚀 开始测试 AI Agent 区块链集成\n")

    try:
        # 测试 1: 查询钱包资产
        await test_wallet_query()

        # 测试 2: 查询 DeFi 协议
        await test_defi_query()

        # 测试 3: 纯聊天
        await test_chat_without_wallet()

        # 测试 4: 价格查询
        await test_price_query()

        print("\n\n" + "=" * 60)
        print("🎉 所有测试完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
