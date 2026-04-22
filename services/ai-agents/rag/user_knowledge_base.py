"""用户知识库 - 基于 FAISS"""

import os
import pickle
from pathlib import Path
from typing import Dict, List, Optional

import faiss
import numpy as np
from langchain_openai import OpenAIEmbeddings

from .document_parser import DocumentParser


class UserKnowledgeBase:
    """用户专属知识库，使用 FAISS 向量检索"""

    def __init__(self, user_id: Optional[int] = None, base_dir: str = "data/knowledge"):
        """初始化用户知识库

        Args:
            user_id: 用户 ID（None 表示系统知识库）
            base_dir: 知识库存储根目录
        """
        self.user_id = user_id
        self.base_dir = Path(base_dir)
        self.user_dir = self.base_dir / (f"user_{user_id}" if user_id else "system")
        self.user_dir.mkdir(parents=True, exist_ok=True)

        self.index_path = self.user_dir / "faiss.index"
        self.metadata_path = self.user_dir / "metadata.pkl"

        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small", openai_api_key=os.getenv("OPENAI_API_KEY")
        )

        self.index: Optional[faiss.IndexFlatL2] = None
        self.metadata: List[Dict] = []

        self._load_or_create_index()

    def _load_or_create_index(self):
        """加载已有索引或创建新索引"""
        if self.index_path.exists() and self.metadata_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            with open(self.metadata_path, "rb") as f:
                self.metadata = pickle.load(f)
        else:
            # 创建新索引（text-embedding-3-small 的维度是 1536）
            self.index = faiss.IndexFlatL2(1536)
            self.metadata = []

    def add_document(self, file_path: str, document_id: int, title: str = "") -> int:
        """添加文档到知识库

        Args:
            file_path: 文档文件路径
            document_id: 数据库中的文档 ID
            title: 文档标题

        Returns:
            添加的文本块数量
        """
        # 解析文档
        text = DocumentParser.parse(file_path)
        chunks = DocumentParser.chunk_text(text)

        # 生成向量嵌入
        embeddings = self.embeddings.embed_documents(chunks)
        embeddings_array = np.array(embeddings, dtype=np.float32)

        # 添加到 FAISS 索引
        start_id = len(self.metadata)
        self.index.add(embeddings_array)

        # 存储元数据
        for i, chunk in enumerate(chunks):
            self.metadata.append(
                {
                    "id": start_id + i,
                    "document_id": document_id,
                    "chunk_index": i,
                    "content": chunk,
                    "title": title,
                }
            )

        # 保存索引
        self._save_index()

        return len(chunks)

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """搜索知识库

        Args:
            query: 搜索查询
            top_k: 返回结果数量

        Returns:
            匹配的文本块及元数据列表
        """
        if self.index.ntotal == 0:
            return []

        # 生成查询向量
        query_embedding = self.embeddings.embed_query(query)
        query_vector = np.array([query_embedding], dtype=np.float32)

        # 搜索 FAISS 索引
        distances, indices = self.index.search(query_vector, min(top_k, self.index.ntotal))

        # 获取元数据
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.metadata):
                result = self.metadata[idx].copy()
                result["score"] = float(dist)
                results.append(result)

        return results

    def delete_document(self, document_id: int):
        """从知识库删除文档

        注意：FAISS 不支持直接删除，需要重建索引
        """
        # 过滤掉该文档的所有块
        new_metadata = [m for m in self.metadata if m["document_id"] != document_id]

        if len(new_metadata) == len(self.metadata):
            return  # 没有需要删除的

        # 重建索引
        self.index = faiss.IndexFlatL2(1536)
        self.metadata = []

        # 重新添加剩余文档
        # 按 document_id 分组
        docs_to_readd = {}
        for meta in new_metadata:
            doc_id = meta["document_id"]
            if doc_id not in docs_to_readd:
                docs_to_readd[doc_id] = []
            docs_to_readd[doc_id].append(meta)

        # 重新生成向量并添加
        for _doc_id, chunks_meta in docs_to_readd.items():
            chunks = [m["content"] for m in chunks_meta]
            embeddings = self.embeddings.embed_documents(chunks)
            embeddings_array = np.array(embeddings, dtype=np.float32)

            start_id = len(self.metadata)
            self.index.add(embeddings_array)

            for i, meta in enumerate(chunks_meta):
                meta["id"] = start_id + i
                self.metadata.append(meta)

        self._save_index()

    def _save_index(self):
        """保存索引和元数据到磁盘"""
        faiss.write_index(self.index, str(self.index_path))
        with open(self.metadata_path, "wb") as f:
            pickle.dump(self.metadata, f)

    def get_stats(self) -> Dict:
        """获取知识库统计信息"""
        doc_ids = {m["document_id"] for m in self.metadata}
        return {
            "total_chunks": len(self.metadata),
            "total_documents": len(doc_ids),
            "index_size": self.index.ntotal if self.index else 0,
        }
