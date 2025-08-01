
# app/utils/pagination.py
# -*- coding: utf-8 -*-
"""
分页工具
提供查询分页功能
"""

from typing import List, TypeVar, Tuple, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.schemas.base import PaginationInfo

T = TypeVar('T')


async def paginate_query(
        db: AsyncSession,
        query: Select,
        page: int = 1,
        page_size: int = 20,
        max_page_size: int = 100
) -> Tuple[List[T], PaginationInfo]:
    """
    分页查询

    Args:
        db: 数据库会话
        query: SQLAlchemy查询对象
        page: 页码（从1开始）
        page_size: 每页数量
        max_page_size: 最大页面大小

    Returns:
        Tuple[List[T], PaginationInfo]: (数据列表, 分页信息)
    """

    # 参数验证
    page = max(1, page)
    page_size = min(max(1, page_size), max_page_size)

    # 计算偏移量
    offset = (page - 1) * page_size

    # 获取总数（从原查询中提取count）
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 添加分页到原查询
    paginated_query = query.offset(offset).limit(page_size)

    # 执行查询
    result = await db.execute(paginated_query)
    items = result.scalars().all()

    # 计算分页信息
    total_pages = (total + page_size - 1) // page_size
    has_more = total > offset + len(items)
    has_next_page = page < total_pages
    has_previous_page = page > 1

    pagination_info = PaginationInfo(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        has_more=has_more,
        has_next_page=has_next_page,
        has_previous_page=has_previous_page
    )

    return list(items), pagination_info


def create_pagination_response(
        data: List[T],
        pagination: PaginationInfo,
        message: str = "获取成功"
) -> Dict[str, Any]:
    """
    创建分页响应

    Args:
        data: 数据列表
        pagination: 分页信息
        message: 响应消息

    Returns:
        Dict[str, Any]: 分页响应
    """

    return {
        "success": True,
        "code": 200,
        "message": message,
        "data": data,
        "pagination": pagination.model_dump(),
        "timestamp": None  # 会在序列化时自动填充
    }

