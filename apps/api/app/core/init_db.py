"""
数据库初始化脚本

创建所有表
"""

import asyncio

from app.core.database import Base, engine
from app.models import ChatMessage, ChatSession, Strategy, Transaction, User  # noqa: F401


async def init_db():
    """初始化数据库"""
    async with engine.begin() as conn:
        # 删除所有表（开发环境）
        await conn.run_sync(Base.metadata.drop_all)
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据库初始化完成")


if __name__ == "__main__":
    asyncio.run(init_db())
