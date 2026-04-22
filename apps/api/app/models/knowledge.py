"""知识库数据模型"""

import enum
from datetime import datetime

from app.core.database import Base
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship


class DocumentType(str, enum.Enum):
    """文档类型枚举"""

    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"
    MD = "md"
    TXT = "txt"


class KnowledgeDocument(Base):
    """知识文档模型"""

    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=True)  # 钱包地址或用户标识，NULL = 系统文档
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=True)  # 向量化后可删除原文件
    file_type = Column(Enum(DocumentType), nullable=False)
    file_size = Column(Integer, nullable=False)  # 字节
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")


class KnowledgeChunk(Base):
    """知识片段模型（文档的文本分块）"""

    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)  # 在文档中的顺序
    content = Column(Text, nullable=False)
    embedding_id = Column(String(64), nullable=True)  # FAISS 向量 ID
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    document = relationship("KnowledgeDocument", back_populates="chunks")
