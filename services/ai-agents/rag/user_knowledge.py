"""
用户知识库检索 - 通过 HTTP API 从后端检索用户上传的文档

通过调用后端 /api/v1/knowledge/search 接口检索用户文档，
避免在 AI Agent 进程中直接访问数据库。
"""

import logging
import os

logger = logging.getLogger(__name__)


def retrieve_user_knowledge_with_sources(wallet_address: str, query: str, top_k: int = 3) -> dict:
    """
    从后端 API 检索用户上传的文档内容，返回上下文和来源信息

    Returns:
        dict: {"context": str, "sources": [{"filename": str}]}
    """
    try:
        import httpx

        logger.info(f"[UserKnowledge] 开始检索，用户: {wallet_address}, 查询: {query}")

        api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
        url = f"{api_base}/api/v1/knowledge/search"

        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                url,
                params={"wallet_address": wallet_address, "query": query, "top_k": top_k},
            )

            logger.info(f"[UserKnowledge] API 响应状态: {response.status_code}")

            if response.status_code != 200:
                logger.warning(f"[UserKnowledge] API 调用失败: {response.status_code}")
                return {"context": "", "sources": []}

            data = response.json()
            results = data.get("results", [])

            logger.info(f"[UserKnowledge] 找到 {len(results)} 个匹配结果")

            if not results:
                return {"context": "", "sources": []}

            parts = ["以下是用户上传的文档中的相关内容，请参考这些内容来回答：\n"]
            sources = []
            seen_files = set()
            for i, result in enumerate(results):
                doc_name = result.get("filename", "未知文档")
                content = result.get("content", "")
                score = result.get("score", 0)
                logger.info(
                    f"[UserKnowledge] 结果 {i+1}: {doc_name}, 评分: {score}, 长度: {len(content)}"
                )
                parts.append(f"【{doc_name}】\n{content}\n")
                if doc_name not in seen_files:
                    sources.append({"filename": doc_name})
                    seen_files.add(doc_name)

            context = "\n".join(parts)
            logger.info(f"[UserKnowledge] 返回结果总长度: {len(context)}, 来源: {sources}")
            return {"context": context, "sources": sources}

    except Exception as e:
        logger.error(f"[UserKnowledge] 检索失败: {e}", exc_info=True)
        return {"context": "", "sources": []}


def retrieve_user_knowledge(wallet_address: str, query: str, top_k: int = 3) -> str:
    """
    从后端 API 检索用户上传的文档内容

    Args:
        wallet_address: 用户钱包地址
        query: 查询文本
        top_k: 返回的最大结果数

    Returns:
        格式化的上下文字符串
    """
    try:
        import httpx

        logger.info(f"[UserKnowledge] 开始检索，用户: {wallet_address}, 查询: {query}")

        # 从环境变量获取后端 API 地址
        api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
        url = f"{api_base}/api/v1/knowledge/search"

        logger.info(f"[UserKnowledge] 调用 API: {url}")

        # 调用后端搜索接口
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                url,
                params={
                    "wallet_address": wallet_address,
                    "query": query,
                    "top_k": top_k,
                },
            )

            logger.info(f"[UserKnowledge] API 响应状态: {response.status_code}")

            if response.status_code != 200:
                logger.warning(
                    f"[UserKnowledge] API 调用失败: {response.status_code}, {response.text}"
                )
                return ""

            data = response.json()
            results = data.get("results", [])

            logger.info(f"[UserKnowledge] 找到 {len(results)} 个匹配结果")

            if not results:
                logger.info("[UserKnowledge] 未找到匹配内容")
                return ""

            # 格式化结果
            parts = ["以下是你上传的文档中的相关内容：\n"]
            for i, result in enumerate(results):
                doc_name = result.get("filename", "未知文档")
                content = result.get("content", "")
                score = result.get("score", 0)
                logger.info(
                    f"[UserKnowledge] 结果 {i+1}: {doc_name}, 评分: {score}, 内容长度: {len(content)}"
                )
                parts.append(f"【{doc_name}】\n{content}\n")

            result_text = "\n".join(parts)
            logger.info(f"[UserKnowledge] 返回结果总长度: {len(result_text)}")
            logger.info(f"[UserKnowledge] 结果预览: {result_text[:200]}...")
            return result_text

    except Exception as e:
        logger.error(f"[UserKnowledge] 检索失败: {e}", exc_info=True)
        return ""
