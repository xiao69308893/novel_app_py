
# app/api/v1/novels.py
# -*- coding: utf-8 -*-
"""
小说相关API接口
处理小说查询、搜索、分类等功能
"""

from typing import Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_db
from app.core.deps import get_current_active_user, get_pagination_params
from app.schemas.base import BaseResponse, ListResponse
from app.schemas.novel import NovelBasicResponse, NovelDetailResponse, NovelListResponse
from app.services.novel_service import NovelService
from app.models.user import User

# 创建路由器
router = APIRouter()


# 依赖注入
def get_novel_service(db: AsyncSession = Depends(get_db)) -> NovelService:
    """获取小说服务"""
    return NovelService(db)


@router.get("", response_model=ListResponse[NovelBasicResponse], summary="获取小说列表")
async def get_novels(
        category_id: Optional[str] = Query(None, description="分类ID"),
        status: Optional[str] = Query(None, description="小说状态"),
        sort_by: str = Query("updated_at", description="排序字段"),
        sort_order: str = Query("desc", description="排序方向"),
        pagination: dict = Depends(get_pagination_params),
        novel_service: NovelService = Depends(get_novel_service)
) -> Any:
    """获取小说列表"""

    novels, total = await novel_service.get_novels(
        category_id=category_id,
        status=status,
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
        message="获取小说列表成功"
    )


@router.get("/hot", response_model=ListResponse[NovelBasicResponse], summary="获取热门小说")
async def get_hot_novels(
        pagination: dict = Depends(get_pagination_params),
        novel_service: NovelService = Depends(get_novel_service)
) -> Any:
    """获取热门小说"""

    novels, total = await novel_service.get_hot_novels(**pagination)

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
        message="获取热门小说成功"
    )


@router.get("/new", response_model=ListResponse[NovelBasicResponse], summary="获取最新小说")
async def get_new_novels(
        pagination: dict = Depends(get_pagination_params),
        novel_service: NovelService = Depends(get_novel_service)
) -> Any:
    """获取最新小说"""

    novels, total = await novel_service.get_new_novels(**pagination)

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
        message="获取最新小说成功"
    )


@router.get("/search", response_model=ListResponse[NovelBasicResponse], summary="搜索小说")
async def search_novels(
        keyword: str = Query(..., description="搜索关键词"),
        category_id: Optional[str] = Query(None, description="分类ID"),
        status: Optional[str] = Query(None, description="小说状态"),
        sort_by: str = Query("relevance", description="排序字段"),
        pagination: dict = Depends(get_pagination_params),
        novel_service: NovelService = Depends(get_novel_service)
) -> Any:
    """搜索小说"""

    novels, total = await novel_service.search_novels(
        keyword=keyword,
        category_id=category_id,
        status=status,
        sort_by=sort_by,
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
        message="搜索小说成功"
    )


@router.get("/{novel_id}", response_model=BaseResponse[NovelDetailResponse], summary="获取小说详情")
async def get_novel_detail(
        novel_id: str,
        novel_service: NovelService = Depends(get_novel_service)
) -> Any:
    """获取小说详情"""

    novel = await novel_service.get_novel_by_id(novel_id)

    return BaseResponse(
        data=novel,
        message="获取小说详情成功"
    )


@router.get("/{novel_id}/similar", response_model=ListResponse[NovelBasicResponse], summary="获取相似小说")
async def get_similar_novels(
        novel_id: str,
        limit: int = Query(10, ge=1, le=50, description="返回数量"),
        novel_service: NovelService = Depends(get_novel_service)
) -> Any:
    """获取相似小说推荐"""

    novels = await novel_service.get_similar_novels(novel_id, limit)

    return ListResponse(
        data=novels,
        message="获取相似小说成功"
    )


@router.post("/{novel_id}/favorite", response_model=BaseResponse[dict], summary="收藏小说")
async def favorite_novel(
        novel_id: str,
        current_user: User = Depends(get_current_active_user),
        novel_service: NovelService = Depends(get_novel_service)
) -> Any:
    """收藏小说"""

    result = await novel_service.favorite_novel(current_user.id, novel_id)

    return BaseResponse(
        data=result,
        message="收藏成功"
    )


@router.delete("/{novel_id}/favorite", response_model=BaseResponse[dict], summary="取消收藏小说")
async def unfavorite_novel(
        novel_id: str,
        current_user: User = Depends(get_current_active_user),
        novel_service: NovelService = Depends(get_novel_service)
) -> Any:
    """取消收藏小说"""

    result = await novel_service.unfavorite_novel(current_user.id, novel_id)

    return BaseResponse(
        data=result,
        message="取消收藏成功"
    )


@router.post("/{novel_id}/rate", response_model=BaseResponse[dict], summary="评分小说")
async def rate_novel(
        novel_id: str,
        rating: int = Query(..., ge=1, le=5, description="评分(1-5)"),
        review: Optional[str] = Query(None, description="评价内容"),
        current_user: User = Depends(get_current_active_user),
        novel_service: NovelService = Depends(get_novel_service)
) -> Any:
    """给小说评分"""

    result = await novel_service.rate_novel(
        user_id=current_user.id,
        novel_id=novel_id,
        rating=rating,
        review=review
    )

    return BaseResponse(
        data=result,
        message="评分成功"
    )


@router.get("/categories", response_model=ListResponse[dict], summary="获取小说分类")
async def get_categories(
        novel_service: NovelService = Depends(get_novel_service)
) -> Any:
    """获取小说分类列表"""

    categories = await novel_service.get_categories()

    return ListResponse(
        data=categories,
        message="获取分类列表成功"
    )


@router.get("/tags", response_model=ListResponse[dict], summary="获取小说标签")
async def get_tags(
        novel_service: NovelService = Depends(get_novel_service)
) -> Any:
    """获取小说标签列表"""

    tags = await novel_service.get_tags()

    return ListResponse(
        data=tags,
        message="获取标签列表成功"
    )


@router.get("/rankings", response_model=ListResponse[NovelBasicResponse], summary="获取小说排行榜")
async def get_rankings(
        type: str = Query("hot", description="排行榜类型: hot, new, rating, favorite"),
        pagination: dict = Depends(get_pagination_params),
        novel_service: NovelService = Depends(get_novel_service)
) -> Any:
    """获取小说排行榜"""

    novels, total = await novel_service.get_rankings(type, **pagination)

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
        message="获取排行榜成功"
    )


@router.get("/recommendations", response_model=ListResponse[NovelBasicResponse], summary="获取推荐小说")
async def get_recommendations(
        pagination: dict = Depends(get_pagination_params),
        novel_service: NovelService = Depends(get_novel_service)
) -> Any:
    """获取推荐小说"""

    novels, total = await novel_service.get_recommendations(**pagination)

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
        message="获取推荐小说成功"
    )


@router.get("/completed", response_model=ListResponse[NovelBasicResponse], summary="获取完结小说")
async def get_completed_novels(
        pagination: dict = Depends(get_pagination_params),
        novel_service: NovelService = Depends(get_novel_service)
) -> Any:
    """获取完结小说"""

    novels, total = await novel_service.get_completed_novels(**pagination)

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
        message="获取完结小说成功"
    )


