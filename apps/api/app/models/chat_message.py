"""
消息表模型

保存 AI 对话的消息记录
"""

import enum
import uuid
from datetime import datetime, timezone

from app.core.database import Base
from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy import Enum as SQLEnum


def enum_values(enum_cls):
    return [member.value for member in enum_cls]


class MessageRole(str, enum.Enum):
    """消息角色枚举"""

    USER = "user"  # 用户
    ASSISTANT = "assistant"  # AI 助手
    SYSTEM = "system"  # 系统


class ChatMessage(Base):
    """消息表"""

    __tablename__ = "chat_messages"

    # 主键
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 外键：所属会话
    session_id = Column(
        Uuid(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False, index=True
    )

    # 消息角色
    role = Column(
        SQLEnum(MessageRole, values_callable=enum_values, name="messagerole"),
        nullable=False,
        index=True,
    )

    # 消息内容
    content = Column(Text, nullable=False)

    # 识别的意图（仅 assistant 消息）
    intent = Column(String(64), nullable=True)

    # 附加数据（JSONB）
    extra_data = Column(JSON, nullable=False, default=dict)

    # 时间戳
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    def __repr__(self):
        return f"<ChatMessage {self.role} {self.content[:20]}>"
