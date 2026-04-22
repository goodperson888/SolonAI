"""
策略表模型

保存 Agent 生成的结构化策略、收益测算结果和风险审计摘要
"""

import enum
import uuid
from datetime import datetime, timezone

from app.core.database import Base
from sqlalchemy import JSON, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Numeric, String, Text, Uuid


def enum_values(enum_cls):
    return [member.value for member in enum_cls]


class StrategyStatus(str, enum.Enum):
    """策略状态枚举"""

    DRAFT = "draft"  # 草稿
    GENERATED = "generated"  # 已生成
    APPROVED = "approved"  # 已批准
    REJECTED = "rejected"  # 已拒绝
    EXPIRED = "expired"  # 已过期
    EXECUTED = "executed"  # 已执行


class Strategy(Base):
    """策略表"""

    __tablename__ = "strategies"

    # 主键
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 外键：所属用户
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # 策略类型
    strategy_type = Column(String(32), nullable=False, index=True)

    # 策略状态
    status = Column(
        SQLEnum(StrategyStatus, values_callable=enum_values, name="strategystatus"),
        nullable=False,
        default=StrategyStatus.DRAFT,
        index=True,
    )

    # 输入/输出代币
    input_token = Column(String(32), nullable=False)
    output_token = Column(String(32), nullable=True)
    input_amount = Column(Numeric(38, 18), nullable=True)

    # 预估收益
    estimated_apy = Column(Numeric(10, 4), nullable=True)

    # 风险等级
    risk_level = Column(String(32), nullable=False, index=True)

    # 主要推荐协议
    protocol_name = Column(String(64), nullable=True, index=True)

    # 策略标题和摘要
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)

    # 执行步骤（JSONB）
    steps = Column(JSON, nullable=False, default=list)

    # 完整策略结构化结果（JSONB）
    strategy_payload = Column(JSON, nullable=False, default=dict)

    # 风险审计摘要（JSONB）
    risk_assessment = Column(JSON, nullable=False, default=dict)

    # 失效时间
    expires_at = Column(DateTime(timezone=True), nullable=True)

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
        return f"<Strategy {self.title}>"
