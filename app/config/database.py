
# app/config/database.py
# -*- coding: utf-8 -*-
"""
数据库连接和会话管理
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool
import logging

from .settings import settings

# 创建异步数据库引擎
if "sqlite" in settings.DATABASE_URL:
    # SQLite配置
    engine = create_async_engine(
        url=settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        future=True
    )
else:
    # PostgreSQL配置
    engine = create_async_engine(
        url=settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_timeout=settings.DATABASE_POOL_TIMEOUT,
        pool_recycle=settings.DATABASE_POOL_RECYCLE,
        pool_pre_ping=True,  # 连接前检查连接有效性
        future=True
    )

# 创建异步会话工厂
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)


class Base(DeclarativeBase):
    """SQLAlchemy基类"""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话的依赖注入函数

    Yields:
        AsyncSession: 异步数据库会话
    """
    async with SessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logging.error(f"数据库会话错误: {e}")
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """初始化数据库"""
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """关闭数据库连接"""
    await engine.dispose()


async def check_db_connection() -> bool:
    """
    检查数据库连接状态

    Returns:
        bool: 连接状态
    """
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logging.error(f"数据库连接检查失败: {e}")
        return False
