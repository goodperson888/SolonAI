"""
数据库初始化脚本

创建所有表
"""

import asyncio
import os

from app.core.database import Base, engine
from app.models import ChatMessage, ChatSession, Strategy, Transaction, User  # noqa: F401
from app.models.knowledge import KnowledgeDocument, KnowledgeChunk  # noqa: F401


def should_reset_db() -> bool:
    return os.getenv("INIT_DB_RESET", "").lower() in {"1", "true", "yes"}


async def init_db(reset: bool = False):
    """初始化数据库"""
    async with engine.begin() as conn:
        if reset:
            # Only drop tables when explicitly requested.
            await conn.run_sync(Base.metadata.drop_all)
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
    print(f"✅ 数据库初始化完成 reset={reset}")


if __name__ == "__main__":
    asyncio.run(init_db(reset=should_reset_db()))
