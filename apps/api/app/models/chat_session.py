"""
会话表模型

保存 AI 对话的会话信息
"""

import uuid
from datetime import datetime

from app.core.database import Base
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID


class ChatSession(Base):
    """会话表"""

    __tablename__ = "chat_sessions"

    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 外键：所属用户
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # 会话 ID（用于前端标识）
    session_id = Column(String(64), unique=True, nullable=False, index=True)

    # 会话标题
    title = Column(String(255), nullable=True)

    # 时间戳
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ChatSession {self.session_id}>"
