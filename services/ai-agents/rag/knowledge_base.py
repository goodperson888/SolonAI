"""
Solon AI - RAG 知识库

基于 FAISS 向量数据库的 RAG 知识检索系统。
支持从 Markdown 文档加载知识，向量化存储，语义检索。

架构：
  docs/ → DocumentLoader → Embedding → FAISS Index → Retriever
                                                        ↓
                                              Agent 查询时检索相关知识
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

# 项目根目录
RAG_DIR = Path(__file__).parent
DOCS_DIR = RAG_DIR / "docs"
INDEX_DIR = RAG_DIR / "index"


class SimpleEmbedding:
    """
    基于 LLM API 的文本向量化。
    使用 OpenAI 兼容接口的 embedding 端点。
    如果 embedding 不可用，降级为 TF-IDF 方式。
    """

    def __init__(self, dim: int = 256):
        self.dim = dim
        self._vocab: Dict[str, int] = {}
        self._idf: Optional[np.ndarray] = None

    def _tokenize(self, text: str) -> List[str]:
        """简单分词：按空格和标点拆分"""
        import re

        # 中文按字拆分，英文按词拆分
        tokens = []
        for segment in re.split(r"[\s,，。！？：；、（）(){}【】\[\]\"\"''" "]+", text.lower()):
            segment = segment.strip()
            if not segment:
                continue
            # 英文单词保留
            if segment.isascii():
                tokens.append(segment)
            else:
                # 中文逐字
                for char in segment:
                    tokens.append(char)
        return tokens

    def fit(self, documents: List[str]):
        """从文档集合中构建词汇表"""
        doc_freq: Dict[str, int] = {}
        for doc in documents:
            tokens = set(self._tokenize(doc))
            for token in tokens:
                doc_freq[token] = doc_freq.get(token, 0) + 1

        # 按频率排序，取 top N
        sorted_tokens = sorted(doc_freq.items(), key=lambda x: x[1], reverse=True)
        self._vocab = {token: idx for idx, (token, _) in enumerate(sorted_tokens[: self.dim])}

        # 计算 IDF
        n_docs = len(documents)
        self._idf = np.zeros(self.dim)
        for token, idx in self._vocab.items():
            df = doc_freq.get(token, 0)
            self._idf[idx] = np.log((n_docs + 1) / (df + 1)) + 1

    def embed(self, text: str) -> np.ndarray:
        """将文本转换为向量"""
        tokens = self._tokenize(text)
        vec = np.zeros(self.dim)

        # TF
        tf: Dict[str, int] = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1

        for token, count in tf.items():
            if token in self._vocab:
                idx = self._vocab[token]
                vec[idx] = count

        # TF-IDF
        if self._idf is not None:
            vec = vec * self._idf

        # L2 归一化
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return vec.astype(np.float32)

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """批量向量化"""
        return np.array([self.embed(text) for text in texts])


class KnowledgeChunk:
    """知识片段"""

    def __init__(self, content: str, metadata: Dict[str, str] = None):
        self.content = content
        self.metadata = metadata or {}
        self.id = hashlib.md5(content.encode()).hexdigest()[:12]


class RAGKnowledgeBase:
    """
    基于 FAISS 的 RAG 知识库

    使用方法：
        kb = RAGKnowledgeBase()
        kb.load_and_index()  # 首次加载文档并建立索引
        results = kb.retrieve("Jupiter swap 是什么", top_k=3)
    """

    def __init__(self):
        self.chunks: List[KnowledgeChunk] = []
        self.embedding = SimpleEmbedding(dim=256)
        self.index = None
        self._initialized = False

    def load_documents(self) -> List[KnowledgeChunk]:
        """从 docs 目录加载所有 Markdown 文档"""
        chunks = []

        if not DOCS_DIR.exists():
            logger.warning(f"知识库文档目录不存在: {DOCS_DIR}")
            return chunks

        for md_file in sorted(DOCS_DIR.glob("*.md")):
            logger.info(f"加载知识文档: {md_file.name}")
            content = md_file.read_text(encoding="utf-8")
            file_chunks = self._split_document(content, md_file.name)
            chunks.extend(file_chunks)

        logger.info(f"共加载 {len(chunks)} 个知识片段")
        return chunks

    def _split_document(self, content: str, filename: str) -> List[KnowledgeChunk]:
        """将文档按章节拆分为知识片段"""
        chunks = []
        sections = content.split("\n## ")

        for i, section in enumerate(sections):
            if i == 0:
                # 第一段可能包含标题
                if section.startswith("# "):
                    lines = section.split("\n", 1)
                    title = lines[0].replace("# ", "").strip()
                    body = lines[1].strip() if len(lines) > 1 else ""
                else:
                    title = filename.replace(".md", "")
                    body = section.strip()
            else:
                lines = section.split("\n", 1)
                title = lines[0].strip()
                body = lines[1].strip() if len(lines) > 1 else ""

            if not body or len(body) < 20:
                continue

            # 如果段落太长，继续按子标题拆分
            sub_sections = body.split("\n### ")
            if len(sub_sections) > 1:
                for j, sub in enumerate(sub_sections):
                    if j == 0:
                        sub_text = sub.strip()
                        sub_title = title
                    else:
                        sub_lines = sub.split("\n", 1)
                        sub_title = f"{title} - {sub_lines[0].strip()}"
                        sub_text = sub_lines[1].strip() if len(sub_lines) > 1 else sub_lines[0]

                    if sub_text and len(sub_text) > 20:
                        chunks.append(
                            KnowledgeChunk(
                                content=sub_text[:1000],  # 限制长度
                                metadata={"source": filename, "title": sub_title},
                            )
                        )
            else:
                chunks.append(
                    KnowledgeChunk(
                        content=body[:1000],
                        metadata={"source": filename, "title": title},
                    )
                )

        return chunks

    def build_index(self):
        """构建 FAISS 索引"""
        import faiss

        if not self.chunks:
            logger.warning("没有知识片段，跳过索引构建")
            return

        # 训练 embedding
        texts = [chunk.content for chunk in self.chunks]
        self.embedding.fit(texts)

        # 向量化所有文档
        vectors = self.embedding.embed_batch(texts)

        # 创建 FAISS 索引
        self.index = faiss.IndexFlatIP(self.embedding.dim)  # 内积相似度（已归一化 = 余弦相似度）
        self.index.add(vectors)

        logger.info(f"FAISS 索引构建完成，共 {self.index.ntotal} 个向量")

    def save_index(self):
        """保存索引到磁盘"""
        import faiss

        INDEX_DIR.mkdir(parents=True, exist_ok=True)

        if self.index:
            faiss.write_index(self.index, str(INDEX_DIR / "knowledge.index"))

        # 保存 chunks 元数据
        meta = [{"content": c.content, "metadata": c.metadata, "id": c.id} for c in self.chunks]
        with open(INDEX_DIR / "chunks.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        # 保存 embedding 词汇表
        embed_data = {
            "vocab": self.embedding._vocab,
            "idf": self.embedding._idf.tolist() if self.embedding._idf is not None else None,
            "dim": self.embedding.dim,
        }
        with open(INDEX_DIR / "embedding.json", "w", encoding="utf-8") as f:
            json.dump(embed_data, f, ensure_ascii=False)

        logger.info(f"索引已保存到 {INDEX_DIR}")

    def load_index(self) -> bool:
        """从磁盘加载索引"""
        import faiss

        index_file = INDEX_DIR / "knowledge.index"
        chunks_file = INDEX_DIR / "chunks.json"
        embed_file = INDEX_DIR / "embedding.json"

        if not all(f.exists() for f in [index_file, chunks_file, embed_file]):
            return False

        try:
            self.index = faiss.read_index(str(index_file))

            with open(chunks_file, encoding="utf-8") as f:
                meta = json.load(f)
            self.chunks = [
                KnowledgeChunk(content=m["content"], metadata=m["metadata"]) for m in meta
            ]

            with open(embed_file, encoding="utf-8") as f:
                embed_data = json.load(f)
            self.embedding._vocab = embed_data["vocab"]
            self.embedding._idf = (
                np.array(embed_data["idf"], dtype=np.float32) if embed_data["idf"] else None
            )
            self.embedding.dim = embed_data["dim"]

            self._initialized = True
            logger.info(f"从磁盘加载索引成功，共 {len(self.chunks)} 个知识片段")
            return True
        except Exception as e:
            logger.error(f"加载索引失败: {e}")
            return False

    def load_and_index(self):
        """加载文档并建立索引（或从缓存加载）"""
        # 先尝试从缓存加载
        if self.load_index():
            self._initialized = True
            return

        # 重新构建
        self.chunks = self.load_documents()
        if self.chunks:
            self.build_index()
            self.save_index()
        self._initialized = True

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, str]]:
        """
        检索与查询最相关的知识片段

        Args:
            query: 用户查询
            top_k: 返回的结果数量

        Returns:
            [{"content": "...", "title": "...", "source": "...", "score": 0.85}]
        """
        if not self._initialized:
            self.load_and_index()

        if not self.index or self.index.ntotal == 0:
            return []

        # 向量化查询
        query_vec = self.embedding.embed(query).reshape(1, -1)

        # 搜索
        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_vec, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.chunks):
                continue
            if score < 0.05:  # 相似度太低的过滤掉
                continue
            chunk = self.chunks[idx]
            results.append(
                {
                    "content": chunk.content,
                    "title": chunk.metadata.get("title", ""),
                    "source": chunk.metadata.get("source", ""),
                    "score": float(score),
                }
            )

        return results

    def format_context(self, results: List[Dict[str, str]]) -> str:
        """将检索结果格式化为上下文字符串，供 Agent 使用"""
        if not results:
            return ""

        parts = ["以下是相关的参考知识：\n"]
        for r in results:
            parts.append(f"【{r['title']}】（来源: {r['source']}）\n{r['content']}\n")

        return "\n".join(parts)


# ===== 单例 =====

_knowledge_base: Optional[RAGKnowledgeBase] = None


def get_knowledge_base() -> RAGKnowledgeBase:
    """获取知识库单例"""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = RAGKnowledgeBase()
        _knowledge_base.load_and_index()
    return _knowledge_base


def retrieve_knowledge(query: str, top_k: int = 3) -> str:
    """
    快捷检索函数，供 Agent 直接调用

    Args:
        query: 用户查询
        top_k: 返回数量

    Returns:
        格式化的上下文字符串
    """
    kb = get_knowledge_base()
    results = kb.retrieve(query, top_k)
    return kb.format_context(results)
