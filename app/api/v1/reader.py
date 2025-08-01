
# app/api/v1/reader.py
# -*- coding: utf-8 -*-
"""
阅读器相关API接口
处理阅读进度、书签等功能
"""

from typing import Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_db
from app.core.deps import get_current_active_user, get_pagination_params
from app.schemas.base import BaseResponse, ListResponse, SuccessResponse
from app.services.reader_service import ReaderService
from app.models.user import User

# 创建路由器
router = APIRouter()


# 依赖注入
def get_reader_service(db: AsyncSession = Depends(get_db)) -> ReaderService:
    """获取阅读器服务"""
    return ReaderService(db)


@router.get("/progress/{novel_id}", response_model=BaseResponse[dict], summary="获取阅读进度")
async def get_reading_progress(
        novel_id: str,
        current_user: User = Depends(get_current_active_user),
        reader_service: ReaderService = Depends(get_reader_service)
) -> Any:
    """获取用户在指定小说的阅读进度"""

    progress = await reader_service.get_reading_progress(
        user_id=current_user.id,
        novel_id=novel_id
    )

    return BaseResponse(
        data=progress,
        message="获取阅读进度成功"
    )


@router.post("/progress", response_model=BaseResponse[dict], summary="保存阅读进度")
async def save_reading_progress(
        progress_data: dict,
        current_user: User = Depends(get_current_active_user),
        reader_service: ReaderService = Depends(get_reader_service)
) -> Any:
    """保存用户阅读进度"""

    progress = await reader_service.save_reading_progress(
        user_id=current_user.id,
        **progress_data
    )

    return BaseResponse(
        data=progress,
        message="阅读进度保存成功"
    )


@router.get("/bookmarks", response_model=ListResponse[dict], summary="获取书签列表")
async def get_bookmarks(
        novel_id: Optional[str] = Query(None, description="小说ID"),
        pagination: dict = Depends(get_pagination_params),
        current_user: User = Depends(get_current_active_user),
        reader_service: ReaderService = Depends(get_reader_service)
) -> Any:
    """获取用户书签列表"""

    bookmarks, total = await reader_service.get_user_bookmarks(
        user_id=current_user.id,
        novel_id=novel_id,
        **pagination
    )

    return ListResponse(
        data=bookmarks,
        pagination={
            "page": pagination["page"],
            "page_size": pagination["page_size"],
            "total": total,
            "total_pages": (total + pagination["page_size"] - 1) // pagination["page_size"],
            "has_more": total > pagination["offset"] + len(bookmarks),
            "has_next_page": pagination["page"] * pagination["page_size"] < total,
            "has_previous_page": pagination["page"] > 1
        },
        message="获取书签列表成功"
    )


@router.post("/bookmarks", response_model=BaseResponse[dict], summary="添加书签")
async def create_bookmark(
        bookmark_data: dict,
        current_user: User = Depends(get_current_active_user),
        reader_service: ReaderService = Depends(get_reader_service)
) -> Any:
    """添加阅读书签"""

    bookmark = await reader_service.create_bookmark(
        user_id=current_user.id,
        **bookmark_data
    )

    return BaseResponse(
        data=bookmark,
        message="书签添加成功"
    )


@router.delete("/bookmarks/{bookmark_id}", response_model=SuccessResponse, summary="删除书签")
async def delete_bookmark(
        bookmark_id: str,
        current_user: User = Depends(get_current_active_user),
        reader_service: ReaderService = Depends(get_reader_service)
) -> Any:
    """删除指定书签"""

    await reader_service.delete_bookmark(
        user_id=current_user.id,
        bookmark_id=bookmark_id
    )

    return SuccessResponse(message="书签删除成功")


@router.get("/stats", response_model=BaseResponse[dict], summary="获取阅读统计")
async def get_reading_stats(
        current_user: User = Depends(get_current_active_user),
        reader_service: ReaderService = Depends(get_reader_service)
) -> Any:
    """获取用户阅读统计数据"""

    stats = await reader_service.get_reading_statistics(current_user.id)

    return BaseResponse(
        data=stats,
        message="获取阅读统计成功"
    )

