"""
交易表模型

保存策略执行过程中的交易草稿、签名、提交结果与链上确认状态
"""

import enum
import uuid
from datetime import datetime

from app.core.database import Base
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID

class TransactionStatus(str, enum.Enum):
    """交易状态枚举"""

    DRAFT = "draft"  # 草稿
    PREPARED = "prepared"  # 已准备
    SIGNED = "signed"  # 已签名
    SUBMITTED = "submitted"  # 已提交
    CONFIRMED = "confirmed"  # 已确认
    FAILED = "failed"  # 失败
    EXPIRED = "expired"  # 已过期


class TransactionType(str, enum.Enum):
    """交易类型枚举"""

    SWAP = "swap"  # 交换
    LEND = "lend"  # 借出
    WITHDRAW = "withdraw"  # 提取
    STAKE = "stake"  # 质押
    UNSTAKE = "unstake"  # 解除质押
    REBALANCE = "rebalance"  # 再平衡


class Transaction(Base):
    """交易表"""

    __tablename__ = "transactions"

    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 外键
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    strategy_id = Column(
        UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=False, index=True
    )

    # 链上签名（唯一）
    signature = Column(String(128), unique=True, nullable=True, index=True)

    # 交易状态
    status = Column(
        SQLEnum(TransactionStatus),
        nullable=False,
        default=TransactionStatus.DRAFT,
        index=True,
    )

    # 交易类型
    tx_type = Column(
        SQLEnum(TransactionType),
        nullable=False,
        index=True,
    )

    # 链标识
    chain = Column(String(16), nullable=False, default="solana")

    # 代币信息
    from_token = Column(String(32), nullable=True)
    to_token = Column(String(32), nullable=True)
    amount = Column(Numeric(38, 18), nullable=True)

    # 滑点（基点）
    slippage_bps = Column(Integer, nullable=True)

    # 交易构建结果（JSONB）
    tx_payload = Column(JSON, nullable=False, default=dict)

    # 模拟执行结果（JSONB）
    simulation_result = Column(JSON, nullable=False, default=dict)

    # 错误信息
    error_message = Column(Text, nullable=True)

    # 时间戳
    submitted_at = Column(DateTime, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Transaction {self.tx_type} {self.status}>"
