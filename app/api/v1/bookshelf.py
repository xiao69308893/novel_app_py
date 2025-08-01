
# app/api/v1/bookshelf.py
# -*- coding: utf-8 -*-
"""
书架相关API接口
处理用户收藏、阅读历史等功能
"""

from typing import Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_db
from app.core.deps import get_current_active_user, get_pagination_params
from app.schemas.base import BaseResponse, ListResponse, SuccessResponse
from app.schemas.novel import NovelResponse
from app.services.bookshelf_service import BookshelfService
from app.models.user import User

# 创建路由器
router = APIRouter()


# 依赖注入
def get_bookshelf_service(db: AsyncSession = Depends(get_db)) -> BookshelfService:
    """获取书架服务"""
    return BookshelfService(db)


@router.get("/favorites", response_model=ListResponse[NovelResponse], summary="获取收藏列表")
async def get_favorites(
        sort_by: str = Query("created_at", description="排序字段"),
        sort_order: str = Query("desc", description="排序方向"),
        pagination: dict = Depends(get_pagination_params),
        current_user: User = Depends(get_current_active_user),
        bookshelf_service: BookshelfService = Depends(get_bookshelf_service)
) -> Any:
    """获取用户收藏的小说列表"""

    novels, total = await bookshelf_service.get_user_favorites(
        user_id=current_user.id,
        sort_by=sort_by,
        sort_order=sort_order,
        **pagination
    )

    return ListResponse(
        data=novels,
        pagination={
            "page": pagination["page"],
            "page_size": pagination["page_size"],
            "total": total,
            "total_pages": (total + pagination["page_size"] - 1) // pagination["page_size"],
            "has_more": total > pagination["offset"] + len(novels),
            "has_next_page": pagination["page"] * pagination["page_size"] < total,
            "has_previous_page": pagination["page"] > 1
        },
        message="获取收藏列表成功"
    )


@router.get("/reading-history", response_model=ListResponse[dict], summary="获取阅读历史")
async def get_reading_history(
        pagination: dict = Depends(get_pagination_params),
        current_user: User = Depends(get_current_active_user),
        bookshelf_service: BookshelfService = Depends(get_bookshelf_service)
) -> Any:
    """获取用户阅读历史"""

    history, total = await bookshelf_service.get_reading_history(
        user_id=current_user.id,
        **pagination
    )

    return ListResponse(
        data=history,
        pagination={
            "page": pagination["page"],
            "page_size": pagination["page_size"],
            "total": total,
            "total_pages": (total + pagination["page_size"] - 1) // pagination["page_size"],
            "has_more": total > pagination["offset"] + len(history),
            "has_next_page": pagination["page"] * pagination["page_size"] < total,
            "has_previous_page": pagination["page"] > 1
        },
        message="获取阅读历史成功"
    )


@router.get("/recently-read", response_model=ListResponse[dict], summary="获取最近阅读")
async def get_recently_read(
        limit: int = Query(10, ge=1, le=50, description="返回数量"),
        current_user: User = Depends(get_current_active_user),
        bookshelf_service: BookshelfService = Depends(get_bookshelf_service)
) -> Any:
    """获取最近阅读的小说"""

    novels = await bookshelf_service.get_recently_read(
        user_id=current_user.id,
        limit=limit
    )

    return ListResponse(
        data=novels,
        message="获取最近阅读成功"
    )


@router.delete("/reading-history", response_model=SuccessResponse, summary="清理阅读历史")
async def clear_reading_history(
        novel_ids: Optional[list] = None,
        current_user: User = Depends(get_current_active_user),
        bookshelf_service: BookshelfService = Depends(get_bookshelf_service)
) -> Any:
    """清理阅读历史"""

    await bookshelf_service.clear_reading_history(
        user_id=current_user.id,
        novel_ids=novel_ids
    )

    return SuccessResponse(message="阅读历史清理成功")


