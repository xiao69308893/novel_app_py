
# app/api/v1/chapters.py
# -*- coding: utf-8 -*-
"""
章节相关API接口
处理章节内容、评论等功能
"""

from typing import Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_db
from app.core.deps import get_current_active_user, get_pagination_params
from app.schemas.base import BaseResponse, ListResponse
from app.schemas.novel import ChapterBasicResponse, ChapterDetailResponse, CommentResponse, CommentCreateRequest
from app.services.chapter_service import ChapterService
from app.models.user import User

# 创建路由器
router = APIRouter()


# 依赖注入
def get_chapter_service(db: AsyncSession = Depends(get_db)) -> ChapterService:
    """获取章节服务"""
    return ChapterService(db)


@router.get("/novels/{novel_id}/chapters", response_model=ListResponse[ChapterBasicResponse], summary="获取章节列表")
async def get_novel_chapters(
        novel_id: str,
        pagination: dict = Depends(get_pagination_params),
        chapter_service: ChapterService = Depends(get_chapter_service)
) -> Any:
    """获取小说章节列表"""

    chapters, total = await chapter_service.get_novel_chapters(
        novel_id=novel_id,
        **pagination
    )

    return ListResponse(
        data=chapters,
        pagination={
            "page": pagination["page"],
            "page_size": pagination["page_size"],
            "total": total,
            "total_pages": (total + pagination["page_size"] - 1) // pagination["page_size"],
            "has_more": total > pagination["offset"] + len(chapters),
            "has_next_page": pagination["page"] * pagination["page_size"] < total,
            "has_previous_page": pagination["page"] > 1
        },
        message="获取章节列表成功"
    )


@router.get("/{chapter_id}", response_model=BaseResponse[ChapterDetailResponse], summary="获取章节详情")
async def get_chapter_detail(
        chapter_id: str,
        current_user: Optional[User] = Depends(get_current_active_user),
        chapter_service: ChapterService = Depends(get_chapter_service)
) -> Any:
    """获取章节详情和内容"""

    chapter = await chapter_service.get_chapter_detail(
        chapter_id=chapter_id,
        user_id=current_user.id if current_user else None
    )

    return BaseResponse(
        data=chapter,
        message="获取章节详情成功"
    )


@router.get("/{chapter_id}/adjacent", response_model=BaseResponse[dict], summary="获取相邻章节")
async def get_adjacent_chapters(
        chapter_id: str,
        chapter_service: ChapterService = Depends(get_chapter_service)
) -> Any:
    """获取上一章和下一章信息"""

    result = await chapter_service.get_adjacent_chapters(chapter_id)

    return BaseResponse(
        data=result,
        message="获取相邻章节成功"
    )


@router.get("/{chapter_id}/comments", response_model=ListResponse[CommentResponse], summary="获取章节评论")
async def get_chapter_comments(
        chapter_id: str,
        pagination: dict = Depends(get_pagination_params),
        chapter_service: ChapterService = Depends(get_chapter_service)
) -> Any:
    """获取章节评论列表"""

    comments, total = await chapter_service.get_chapter_comments(
        chapter_id=chapter_id,
        **pagination
    )

    return ListResponse(
        data=comments,
        pagination={
            "page": pagination["page"],
            "page_size": pagination["page_size"],
            "total": total,
            "total_pages": (total + pagination["page_size"] - 1) // pagination["page_size"],
            "has_more": total > pagination["offset"] + len(comments),
            "has_next_page": pagination["page"] * pagination["page_size"] < total,
            "has_previous_page": pagination["page"] > 1
        },
        message="获取章节评论成功"
    )


@router.post("/{chapter_id}/comments", response_model=BaseResponse[CommentResponse], summary="发表章节评论")
async def create_chapter_comment(
        chapter_id: str,
        comment_data: CommentCreateRequest,
        current_user: User = Depends(get_current_active_user),
        chapter_service: ChapterService = Depends(get_chapter_service)
) -> Any:
    """发表章节评论"""

    comment = await chapter_service.create_comment(
        user_id=current_user.id,
        chapter_id=chapter_id,
        content=comment_data.content,
        parent_id=comment_data.parent_id
    )

    return BaseResponse(
        data=comment,
        message="评论发表成功"
    )


@router.post("/{chapter_id}/purchase", response_model=BaseResponse[dict], summary="购买章节")
async def purchase_chapter(
        chapter_id: str,
        current_user: User = Depends(get_current_active_user),
        chapter_service: ChapterService = Depends(get_chapter_service)
) -> Any:
    """购买VIP章节"""

    result = await chapter_service.purchase_chapter(
        user_id=current_user.id,
        chapter_id=chapter_id
    )

    return BaseResponse(
        data=result,
        message="章节购买成功"
    )

