"""
Solon AI - 快速测试脚本

测试整个 Agent 工作流是否能跑通。

使用方法：
1. 复制 .env.example 为 .env
2. 填写你的大模型 API Key
3. 安装依赖：pip install -r requirements.txt
4. 运行测试：python test_workflow.py
"""

import asyncio
import json
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graphs.main_graph import run_agent  # noqa: E402


async def test_query_assets():
    """测试场景1：查询资产"""
    print("\n" + "=" * 60)
    print("测试场景1：查询资产")
    print("=" * 60)

    result = await run_agent(
        user_input="帮我看看钱包里有什么资产",
        wallet_address="7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
    )

    print(f"\n识别意图: {result.get('intent')}")
    print(f"资产总值: ${result.get('total_value_usd', 0):,.2f}")
    print(f"代币数量: {len(result.get('wallet_assets', []))}")
    print("\nAI 回复:")
    print(result.get("explanation", "无回复"))
    print(f"\n是否完成: {result.get('completed')}")
    print(f"错误: {result.get('error', '无')}")


async def test_generate_strategy():
    """测试场景2：生成策略"""
    print("\n" + "=" * 60)
    print("测试场景2：生成策略")
    print("=" * 60)

    result = await run_agent(
        user_input="给我推荐一个稳健的DeFi策略，我有100个SOL",
        wallet_address="7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
    )

    print(f"\n识别意图: {result.get('intent')}")
    print(f"意图参数: {json.dumps(result.get('intent_params', {}), ensure_ascii=False)}")

    strategy = result.get("strategy", {})
    print(f"\n策略名称: {strategy.get('strategy_name', 'N/A')}")
    print(f"风险等级: {strategy.get('risk_level', 'N/A')}")
    print(f"预期年化: {strategy.get('expected_apy', 'N/A')}%")

    risk = result.get("risk_assessment", {})
    print(f"\n风控评分: {risk.get('score', 'N/A')}")
    print(f"是否安全: {risk.get('is_safe', 'N/A')}")

    validation = result.get("validation_result", {})
    print(f"\n验证通过: {validation.get('is_valid', 'N/A')}")
    if validation.get("warnings"):
        print(f"警告: {validation.get('warnings')}")

    print("\nAI 回复:")
    print(result.get("explanation", "无回复"))


async def test_risk_check():
    """测试场景3：风控检查"""
    print("\n" + "=" * 60)
    print("测试场景3：风控检查")
    print("=" * 60)

    result = await run_agent(
        user_input="帮我检查一下这个代币是否安全：JUP",
    )

    print(f"\n识别意图: {result.get('intent')}")

    risk = result.get("risk_assessment", {})
    print(f"\n风险等级: {risk.get('risk_level', 'N/A')}")
    print(f"安全评分: {risk.get('score', 'N/A')}")

    print("\nAI 回复:")
    print(result.get("explanation", "无回复"))


async def test_chat():
    """测试场景4：普通聊天"""
    print("\n" + "=" * 60)
    print("测试场景4：普通聊天")
    print("=" * 60)

    result = await run_agent(
        user_input="什么是无常损失？请用大白话解释一下",
    )

    print(f"\n识别意图: {result.get('intent')}")
    print("\nAI 回复:")
    print(result.get("explanation", "无回复"))


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("Solon AI - Agent 工作流测试")
    print("=" * 60)

    try:
        await test_query_assets()
        await test_generate_strategy()
        await test_risk_check()
        await test_chat()

        print("\n" + "=" * 60)
        print("所有测试完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n测试失败: {e}")
        print("\n请检查：")
        print("1. 是否已创建 .env 文件并填写 API Key")
        print("2. 是否已安装依赖: pip install -r requirements.txt")
        print("3. API Key 是否有效")
        raise


if __name__ == "__main__":
    asyncio.run(main())
