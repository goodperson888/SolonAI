"""
知识库 API 接口

提供文档上传、检索、管理功能。
支持 PDF/DOC/DOCX/MD/TXT 格式。
"""

import os
import shutil
import sys
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

# 添加 AI 服务路径（与 chat.py 保持一致）
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "..",
        "..",
        "services",
        "ai-agents",
    ),
)

from app.core.database import get_db  # noqa: E402
from app.models.knowledge import DocumentType, KnowledgeChunk, KnowledgeDocument  # noqa: E402

router = APIRouter()

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".md", ".txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def _get_document_parser():
    """懒加载 DocumentParser，避免启动时依赖缺失"""
    try:
        from rag.document_parser import DocumentParser

        return DocumentParser
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"文档解析服务依赖未安装: {exc.name or 'unknown'}",
        ) from exc


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    wallet_address: str = Form(...),
    title: str = Form(None),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """上传文档到知识库"""
    import logging

    logger = logging.getLogger(__name__)

    logger.info(f"[知识库上传] 开始处理，文件: {file.filename}, 钱包: {wallet_address}")

    # 验证文件扩展名
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型。允许的类型: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # 验证文件大小
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    logger.info(f"[知识库上传] 文件大小: {file_size} 字节")

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件过大。最大允许: {MAX_FILE_SIZE / 1024 / 1024:.0f}MB",
        )

    # 保存文件（使用钱包地址作为目录名）
    user_dir_name = wallet_address[:8]  # 使用钱包地址前8位作为目录名
    user_upload_dir = UPLOAD_DIR / user_dir_name
    user_upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = user_upload_dir / file.filename
    logger.info(f"[知识库上传] 保存文件到: {file_path}")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        DocumentParser = _get_document_parser()

        # 创建数据库记录（使用 wallet_address 作为 user_id）
        doc_type = DocumentType(file_ext.lstrip("."))
        db_doc = KnowledgeDocument(
            user_id=wallet_address,
            filename=file.filename,
            file_path=str(file_path),
            file_type=doc_type,
            file_size=file_size,
            title=title or file.filename,
            description=description,
        )
        db.add(db_doc)
        await db.flush()  # 获取 id

        logger.info(f"[知识库上传] 文档记录已创建，ID: {db_doc.id}")

        # 解析文档并分块
        logger.info("[知识库上传] 开始解析文档...")
        text = DocumentParser.parse(str(file_path))
        logger.info(f"[知识库上传] 文档解析完成，文本长度: {len(text)}")

        chunks = DocumentParser.chunk_text(text)
        logger.info(f"[知识库上传] 文本分块完成，共 {len(chunks)} 个块")

        for i, chunk_content in enumerate(chunks):
            chunk = KnowledgeChunk(
                document_id=db_doc.id,
                chunk_index=i,
                content=chunk_content,
                embedding_id=f"{db_doc.id}_{i}",
            )
            db.add(chunk)

        await db.commit()
        await db.refresh(db_doc)

        logger.info("[知识库上传] 文本块已保存到数据库")

        # 向量化后删除原始文件以节省空间
        if file_path.exists():
            file_path.unlink()
            logger.info("[知识库上传] 原始文件已删除")

        return {
            "document": {
                "id": db_doc.id,
                "user_id": db_doc.user_id,
                "filename": db_doc.filename,
                "file_type": db_doc.file_type.value,
                "file_size": db_doc.file_size,
                "chunk_count": len(chunks),
                "upload_time": str(db_doc.created_at),
                "metadata": {
                    "title": db_doc.title,
                    "description": db_doc.description,
                },
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[知识库上传] 处理文档失败: {e}", exc_info=True)
        await db.rollback()
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"处理文档失败: {str(e)}")


@router.get("/documents")
async def list_documents(
    wallet_address: str,
    db: AsyncSession = Depends(get_db),
):
    """列出用户上传的文档"""
    query = select(KnowledgeDocument).where(KnowledgeDocument.user_id == wallet_address)
    query = query.order_by(desc(KnowledgeDocument.created_at))

    result = await db.execute(query)
    docs = result.scalars().all()

    # 批量查询每个文档的 chunk 数量
    chunk_counts = {}
    if docs:
        doc_ids = [doc.id for doc in docs]
        count_query = (
            select(KnowledgeChunk.document_id, func.count(KnowledgeChunk.id))
            .where(KnowledgeChunk.document_id.in_(doc_ids))
            .group_by(KnowledgeChunk.document_id)
        )
        count_result = await db.execute(count_query)
        chunk_counts = dict(count_result.all())

    return {
        "documents": [
            {
                "id": doc.id,
                "user_id": doc.user_id,
                "filename": doc.filename,
                "file_type": doc.file_type.value,
                "file_size": doc.file_size,
                "chunk_count": chunk_counts.get(doc.id, 0),
                "upload_time": str(doc.created_at),
                "metadata": {
                    "title": doc.title,
                    "description": doc.description,
                },
            }
            for doc in docs
        ]
    }


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    wallet_address: str,
    db: AsyncSession = Depends(get_db),
):
    """删除文档"""
    result = await db.execute(
        select(KnowledgeDocument).where(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.user_id == wallet_address,
        )
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在或无权限")

    # 删除文件（如果存在）
    if doc.file_path:
        file_path = Path(doc.file_path)
        if file_path.exists():
            file_path.unlink()

    # 删除 chunks
    await db.execute(delete(KnowledgeChunk).where(KnowledgeChunk.document_id == document_id))
    # 删除文档记录
    await db.delete(doc)
    await db.commit()

    return {"success": True, "message": "文档删除成功"}


@router.get("/search")
async def search_knowledge(
    wallet_address: str,
    query: str,
    top_k: int = 5,
    db: AsyncSession = Depends(get_db),
):
    """搜索用户上传的文档内容（基于关键词匹配 + 智能重排序）"""
    import logging

    logger = logging.getLogger(__name__)

    try:
        logger.info(f"[知识库搜索] 开始搜索，钱包: {wallet_address}, 查询: {query}, top_k: {top_k}")

        # 查询用户的所有文档
        doc_result = await db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.user_id == wallet_address)
        )
        docs = doc_result.scalars().all()

        logger.info(f"[知识库搜索] 找到 {len(docs)} 个文档")

        if not docs:
            return {"results": []}

        # 获取所有文档的文本块
        doc_ids = [doc.id for doc in docs]
        chunk_result = await db.execute(
            select(KnowledgeChunk).where(KnowledgeChunk.document_id.in_(doc_ids))
        )
        chunks = chunk_result.scalars().all()

        logger.info(f"[知识库搜索] 找到 {len(chunks)} 个文本块")

        if not chunks:
            return {"results": []}

        # 中文友好的关键词匹配评分
        query_lower = query.lower()
        import re

        en_keywords = [
            w
            for w in query_lower.split()
            if any(c.isascii() and c.isalpha() for c in w) and len(w) >= 2
        ]
        cn_segments = re.findall(r"[\u4e00-\u9fff]+", query_lower)
        cn_keywords = []
        for seg in cn_segments:
            if len(seg) >= 2:
                cn_keywords.append(seg)  # 完整片段
            if len(seg) >= 3:
                cn_keywords.extend(seg[i : i + 3] for i in range(len(seg) - 2))
        cn_keywords = list(set(cn_keywords))
        all_keywords = en_keywords + cn_keywords

        logger.info(f"[知识库搜索] 关键词: en={en_keywords}, cn={cn_keywords}")

        # 初步筛选：基于关键词匹配
        max_possible = sum(len(kw) for kw in all_keywords) if all_keywords else 0
        scored_chunks = []
        for chunk in chunks:
            content_lower = chunk.content.lower()

            # 计算基础匹配分数
            base_score = sum(len(kw) for kw in all_keywords if kw in content_lower)

            # 至少匹配 30% 的关键词权重，且最低分 6
            if base_score >= max(max_possible * 0.3, 6):
                # 增强评分：考虑多个因素
                enhanced_score = base_score

                # 1. 完整短语匹配加分（权重 x2）
                for kw in cn_keywords:
                    if len(kw) >= 4 and kw in content_lower:
                        enhanced_score += len(kw) * 2

                # 2. 关键词密度加分
                keyword_count = sum(content_lower.count(kw) for kw in all_keywords)
                density_bonus = min(keyword_count * 2, 20)  # 最多加 20 分
                enhanced_score += density_bonus

                # 3. 关键词位置加分（出现在前 100 字符内）
                position_bonus = 0
                for kw in all_keywords:
                    pos = content_lower.find(kw)
                    if 0 <= pos < 100:
                        position_bonus += 5
                enhanced_score += min(position_bonus, 15)  # 最多加 15 分

                # 4. 文本块长度惩罚（过短或过长都不好）
                content_len = len(chunk.content)
                if content_len < 50:
                    enhanced_score *= 0.5  # 太短，减半
                elif content_len > 2000:
                    enhanced_score *= 0.8  # 太长，打 8 折

                doc = next((d for d in docs if d.id == chunk.document_id), None)
                scored_chunks.append(
                    {"chunk": chunk, "doc": doc, "score": enhanced_score, "base_score": base_score}
                )

        logger.info(f"[知识库搜索] 初步匹配到 {len(scored_chunks)} 个相关文本块")

        # 按增强分数排序
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)

        # 取 top_k * 2 进行重排序（如果结果足够多）
        candidates = scored_chunks[: min(top_k * 2, len(scored_chunks))]

        # 重排序：去重相似内容
        final_results = []
        seen_content_hashes = set()

        for item in candidates:
            chunk = item["chunk"]
            # 使用内容前 100 字符的哈希去重
            content_hash = hash(chunk.content[:100])

            if content_hash not in seen_content_hashes:
                seen_content_hashes.add(content_hash)
                final_results.append(item)

                if len(final_results) >= top_k:
                    break

        logger.info(f"[知识库搜索] 重排序后保留 {len(final_results)} 个结果")

        # 格式化结果
        results = []
        for item in final_results:
            chunk = item["chunk"]
            doc = item["doc"]
            results.append(
                {
                    "chunk_id": str(chunk.id),
                    "document_id": str(doc.id) if doc else "",
                    "filename": doc.filename if doc else "未知文档",
                    "content": chunk.content,
                    "score": item["score"],
                }
            )

        logger.info(f"[知识库搜索] 返回 {len(results)} 个结果")
        if results:
            logger.info(f"[知识库搜索] 第一个结果预览: {results[0]['content'][:100]}...")
            logger.info(f"[知识库搜索] 评分分布: {[r['score'] for r in results]}")

        return {"results": results}

    except Exception as e:
        logger.error(f"[知识库搜索] 搜索失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/stats")
async def get_knowledge_stats(
    wallet_address: str,
    db: AsyncSession = Depends(get_db),
):
    """获取知识库统计信息"""
    doc_count_result = await db.execute(
        select(KnowledgeDocument).where(KnowledgeDocument.user_id == wallet_address)
    )
    docs = doc_count_result.scalars().all()

    total_size = sum(doc.file_size for doc in docs)
    doc_types = {}
    for doc in docs:
        doc_type = doc.file_type.value
        doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

    chunk_count_result = await db.execute(
        select(KnowledgeChunk).where(KnowledgeChunk.document_id.in_([doc.id for doc in docs]))
    )
    chunks = chunk_count_result.scalars().all()

    return {
        "total_documents": len(docs),
        "total_chunks": len(chunks),
        "total_size_bytes": total_size,
        "document_types": doc_types,
    }
