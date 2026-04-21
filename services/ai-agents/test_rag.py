"""
测试 RAG 知识库检索功能
"""

import asyncio
import logging
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_user_knowledge():
    """测试用户知识库检索"""
    from rag.user_knowledge import retrieve_user_knowledge

    # 使用一个测试钱包地址
    test_wallet = "test_wallet_123"
    test_query = "DeFi"

    logger.info(f"测试用户知识库检索: wallet={test_wallet}, query={test_query}")

    result = retrieve_user_knowledge(test_wallet, test_query, top_k=3)

    logger.info(f"检索结果长度: {len(result)}")
    if result:
        logger.info(f"检索结果预览:\n{result[:500]}")
    else:
        logger.info("未检索到任何内容")

    return result


async def test_explanation_agent():
    """测试 ExplanationAgent 的 RAG 集成"""
    from agents.explanation_agent import _retrieve_rag_context

    test_wallet = "test_wallet_123"
    test_query = "什么是 DeFi"

    logger.info(f"测试 ExplanationAgent RAG: wallet={test_wallet}, query={test_query}")

    result = _retrieve_rag_context(test_query, test_wallet)

    logger.info(f"RAG 上下文长度: {len(result)}")
    if result:
        logger.info(f"RAG 上下文预览:\n{result[:500]}")
    else:
        logger.info("未检索到 RAG 上下文")

    return result


if __name__ == "__main__":
    print("=" * 60)
    print("测试 1: 用户知识库检索")
    print("=" * 60)
    asyncio.run(test_user_knowledge())

    print("\n" + "=" * 60)
    print("测试 2: ExplanationAgent RAG 集成")
    print("=" * 60)
    asyncio.run(test_explanation_agent())
