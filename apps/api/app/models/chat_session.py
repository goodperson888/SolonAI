"""
会话表模型

保存 AI 对话的会话信息
"""

import uuid
from datetime import datetime, timezone

from app.core.database import Base
from sqlalchemy import Column, DateTime, ForeignKey, String, Uuid


class ChatSession(Base):
    """会话表"""

    __tablename__ = "chat_sessions"

    # 主键
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 外键：所属用户
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # 会话 ID（用于前端标识）
    session_id = Column(String(64), unique=True, nullable=False, index=True)

    # 会话标题
    title = Column(String(255), nullable=True)

    # 时间戳
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f"<ChatSession {self.session_id}>"
