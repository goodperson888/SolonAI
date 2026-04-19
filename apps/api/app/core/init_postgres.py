"""
Postgres 初始化脚本

执行固化的 Postgres 建表 SQL。
"""

import asyncio
from pathlib import Path

import asyncpg
from app.core.config import settings


def get_postgres_dsn() -> str:
    database_url = settings.DATABASE_URL
    if not database_url.startswith("postgresql+asyncpg://"):
        raise RuntimeError("当前 DATABASE_URL 不是 Postgres 连接串")
    return database_url.replace("postgresql+asyncpg://", "postgresql://", 1)


def get_schema_sql() -> str:
    sql_path = Path(__file__).resolve().parents[2] / "sql" / "postgres_schema.sql"
    return sql_path.read_text(encoding="utf-8")


async def init_postgres() -> None:
    conn = await asyncpg.connect(get_postgres_dsn())
    try:
        await conn.execute(get_schema_sql())
    finally:
        await conn.close()
    print("✅ Postgres SQL 初始化完成")


if __name__ == "__main__":
    asyncio.run(init_postgres())
