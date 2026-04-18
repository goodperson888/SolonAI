"""
用户表模型

保存用户账户、登录身份、风险偏好与个性化配置
"""

import enum
import uuid
from datetime import datetime

from app.core.database import Base
from sqlalchemy import JSON, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID


class RiskLevel(str, enum.Enum):
    """风险偏好枚举"""

    CONSERVATIVE = "conservative"  # 保守型
    BALANCED = "balanced"  # 平衡型
    AGGRESSIVE = "aggressive"  # 激进型


class UserStatus(str, enum.Enum):
    """用户状态枚举"""

    ACTIVE = "active"  # 活跃
    DISABLED = "disabled"  # 禁用
    DELETED = "deleted"  # 已删除


class User(Base):
    """用户表"""

    __tablename__ = "users"

    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 钱包地址（主登录标识）
    wallet_address = Column(String(64), unique=True, nullable=False, index=True)

    # 可选邮箱登录
    email = Column(String(255), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)

    # 风险偏好
    risk_level = Column(
        SQLEnum(RiskLevel),
        nullable=False,
        default=RiskLevel.BALANCED,
        index=True,
    )

    # 用户状态
    status = Column(
        SQLEnum(UserStatus),
        nullable=False,
        default=UserStatus.ACTIVE,
        index=True,
    )

    # 个性化偏好（JSONB）
    preferences = Column(JSON, nullable=False, default=dict)

    # 最近登录时间
    last_login_at = Column(DateTime, nullable=True)

    # 时间戳
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.wallet_address}>"
