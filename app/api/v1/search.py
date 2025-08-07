# app/api/v1/search.py
# -*- coding: utf-8 -*-
"""
搜索相关API接口
提供全文搜索、智能推荐等功能
"""

from typing import Any, Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_db
from app.core.deps import get_current_user_optional, get_pagination_params
from app.schemas.base import BaseResponse, ListResponse
from app.schemas.search import (
    SearchResponse, SearchSuggestionResponse, SearchHistoryResponse,
    HotSearchResponse, SearchStatsResponse
)
from app.schemas.novel import NovelBasicResponse
from app.schemas.user import UserResponse
from app.services.search_service import SearchService
from app.models.user import User

# 创建路由器
router = APIRouter()


# 依赖注入
def get_search_service(db: AsyncSession = Depends(get_db)) -> SearchService:
    """获取搜索服务"""
    return SearchService(db)


@router.get("/novels", response_model=ListResponse[NovelBasicResponse], summary="搜索小说")
async def search_novels(
        q: str = Query(..., description="搜索关键词"),
        category_id: Optional[str] = Query(None, description="分类ID"),
        status: Optional[str] = Query(None, description="小说状态"),
        author: Optional[str] = Query(None, description="作者名"),
        tags: Optional[List[str]] = Query(None, description="标签列表"),
        word_count_min: Optional[int] = Query(None, description="最小字数"),
        word_count_max: Optional[int] = Query(None, description="最大字数"),
        rating_min: Optional[float] = Query(None, description="最低评分"),
        sort_by: str = Query("relevance", description="排序字段"),
        sort_order: str = Query("desc", description="排序方向"),
        pagination: dict = Depends(get_pagination_params),
        current_user: Optional[User] = Depends(get_current_user_optional),
        search_service: SearchService = Depends(get_search_service)
) -> Any:
    """搜索小说"""
    
    # 记录搜索历史
    if current_user:
        await search_service.save_search_history(
            user_id=current_user.id,
            keyword=q,
            search_type="novel"
        )
    
    novels, total = await search_service.search_novels(
        keyword=q,
        category_id=category_id,
        status=status,
        author=author,
        tags=tags,
        word_count_min=word_count_min,
        word_count_max=word_count_max,
        rating_min=rating_min,
        sort_by=sort_by,
        sort_order=sort_order,
        user_id=current_user.id if current_user else None,
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


@router.get("/authors", response_model=ListResponse[UserResponse], summary="搜索作者")
async def search_authors(
        q: str = Query(..., description="搜索关键词"),
        sort_by: str = Query("relevance", description="排序字段"),
        sort_order: str = Query("desc", description="排序方向"),
        pagination: dict = Depends(get_pagination_params),
        current_user: Optional[User] = Depends(get_current_user_optional),
        search_service: SearchService = Depends(get_search_service)
) -> Any:
    """搜索作者"""
    
    # 记录搜索历史
    if current_user:
        await search_service.save_search_history(
            user_id=current_user.id,
            keyword=q,
            search_type="author"
        )
    
    authors, total = await search_service.search_authors(
        keyword=q,
        sort_by=sort_by,
        sort_order=sort_order,
        **pagination
    )
    
    return ListResponse(
        data=authors,
        pagination={
            "page": pagination["page"],
            "page_size": pagination["page_size"],
            "total": total,
            "total_pages": (total + pagination["page_size"] - 1) // pagination["page_size"],
            "has_more": total > pagination["offset"] + len(authors),
            "has_next_page": pagination["page"] * pagination["page_size"] < total,
            "has_previous_page": pagination["page"] > 1
        },
        message="搜索作者成功"
    )


@router.get("/comprehensive", response_model=BaseResponse[SearchResponse], summary="综合搜索")
async def comprehensive_search(
        q: str = Query(..., description="搜索关键词"),
        current_user: Optional[User] = Depends(get_current_user_optional),
        search_service: SearchService = Depends(get_search_service)
) -> Any:
    """综合搜索（包含小说、作者、标签等）"""
    
    # 记录搜索历史
    if current_user:
        await search_service.save_search_history(
            user_id=current_user.id,
            keyword=q,
            search_type="comprehensive"
        )
    
    result = await search_service.comprehensive_search(
        keyword=q,
        user_id=current_user.id if current_user else None
    )
    
    return BaseResponse(
        data=result,
        message="综合搜索成功"
    )


@router.get("/suggestions", response_model=ListResponse[SearchSuggestionResponse], summary="搜索建议")
async def get_search_suggestions(
        q: str = Query(..., description="搜索关键词"),
        limit: int = Query(10, ge=1, le=20, description="返回数量"),
        search_service: SearchService = Depends(get_search_service)
) -> Any:
    """获取搜索建议"""
    
    suggestions = await search_service.get_search_suggestions(q, limit)
    
    return ListResponse(
        data=suggestions,
        message="获取搜索建议成功"
    )


@router.get("/hot", response_model=ListResponse[HotSearchResponse], summary="热门搜索")
async def get_hot_searches(
        time_range: str = Query("7d", description="时间范围"),
        limit: int = Query(20, ge=1, le=50, description="返回数量"),
        search_service: SearchService = Depends(get_search_service)
) -> Any:
    """获取热门搜索关键词"""
    
    hot_searches = await search_service.get_hot_searches(time_range, limit)
    
    return ListResponse(
        data=hot_searches,
        message="获取热门搜索成功"
    )


@router.get("/history", response_model=ListResponse[SearchHistoryResponse], summary="搜索历史")
async def get_search_history(
        search_type: Optional[str] = Query(None, description="搜索类型"),
        pagination: dict = Depends(get_pagination_params),
        current_user: User = Depends(get_current_user_optional),
        search_service: SearchService = Depends(get_search_service)
) -> Any:
    """获取用户搜索历史"""
    
    if not current_user:
        return ListResponse(
            data=[],
            pagination={
                "page": 1,
                "page_size": pagination["page_size"],
                "total": 0,
                "total_pages": 0,
                "has_more": False,
                "has_next_page": False,
                "has_previous_page": False
            },
            message="请先登录"
        )
    
    history, total = await search_service.get_search_history(
        user_id=current_user.id,
        search_type=search_type,
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
        message="获取搜索历史成功"
    )


@router.delete("/history", response_model=BaseResponse[dict], summary="清空搜索历史")
async def clear_search_history(
        search_type: Optional[str] = Query(None, description="搜索类型"),
        current_user: User = Depends(get_current_user_optional),
        search_service: SearchService = Depends(get_search_service)
) -> Any:
    """清空用户搜索历史"""
    
    if not current_user:
        return BaseResponse(
            data={"cleared": 0},
            message="请先登录"
        )
    
    cleared_count = await search_service.clear_search_history(
        user_id=current_user.id,
        search_type=search_type
    )
    
    return BaseResponse(
        data={"cleared": cleared_count},
        message="搜索历史清空成功"
    )


@router.delete("/history/{history_id}", response_model=BaseResponse[dict], summary="删除搜索历史")
async def delete_search_history(
        history_id: str,
        current_user: User = Depends(get_current_user_optional),
        search_service: SearchService = Depends(get_search_service)
) -> Any:
    """删除单条搜索历史"""
    
    if not current_user:
        return BaseResponse(
            data={"deleted": False},
            message="请先登录"
        )
    
    deleted = await search_service.delete_search_history(
        history_id=history_id,
        user_id=current_user.id
    )
    
    return BaseResponse(
        data={"deleted": deleted},
        message="搜索历史删除成功" if deleted else "搜索历史删除失败"
    )


@router.get("/stats", response_model=BaseResponse[SearchStatsResponse], summary="搜索统计")
async def get_search_stats(
        time_range: str = Query("7d", description="时间范围"),
        search_service: SearchService = Depends(get_search_service)
) -> Any:
    """获取搜索统计信息"""
    
    stats = await search_service.get_search_stats(time_range)
    
    return BaseResponse(
        data=stats,
        message="获取搜索统计成功"
    )


@router.get("/trending", response_model=ListResponse[dict], summary="搜索趋势")
async def get_search_trends(
        time_range: str = Query("7d", description="时间范围"),
        limit: int = Query(20, ge=1, le=50, description="返回数量"),
        search_service: SearchService = Depends(get_search_service)
) -> Any:
    """获取搜索趋势"""
    
    trends = await search_service.get_search_trends(time_range, limit)
    
    return ListResponse(
        data=trends,
        message="获取搜索趋势成功"
    )


@router.get("/related", response_model=ListResponse[str], summary="相关搜索")
async def get_related_searches(
        q: str = Query(..., description="搜索关键词"),
        limit: int = Query(10, ge=1, le=20, description="返回数量"),
        search_service: SearchService = Depends(get_search_service)
) -> Any:
    """获取相关搜索关键词"""
    
    related = await search_service.get_related_searches(q, limit)
    
    return ListResponse(
        data=related,
        message="获取相关搜索成功"
    )


@router.post("/feedback", response_model=BaseResponse[dict], summary="搜索反馈")
async def submit_search_feedback(
        keyword: str,
        search_type: str,
        feedback_type: str,
        description: Optional[str] = None,
        current_user: Optional[User] = Depends(get_current_user_optional),
        search_service: SearchService = Depends(get_search_service)
) -> Any:
    """提交搜索反馈"""
    
    result = await search_service.submit_search_feedback(
        keyword=keyword,
        search_type=search_type,
        feedback_type=feedback_type,
        description=description,
        user_id=current_user.id if current_user else None
    )
    
    return BaseResponse(
        data=result,
        message="搜索反馈提交成功"
    )


@router.get("/autocomplete", response_model=ListResponse[str], summary="自动补全")
async def get_autocomplete(
        q: str = Query(..., description="搜索关键词"),
        search_type: str = Query("novel", description="搜索类型"),
        limit: int = Query(10, ge=1, le=20, description="返回数量"),
        search_service: SearchService = Depends(get_search_service)
) -> Any:
    """获取自动补全建议"""
    
    suggestions = await search_service.get_autocomplete(q, search_type, limit)
    
    return ListResponse(
        data=suggestions,
        message="获取自动补全成功"
    )


@router.get("/filters", response_model=BaseResponse[dict], summary="搜索过滤器")
async def get_search_filters(
        search_type: str = Query("novel", description="搜索类型"),
        search_service: SearchService = Depends(get_search_service)
) -> Any:
    """获取搜索过滤器选项"""
    
    filters = await search_service.get_search_filters(search_type)
    
    return BaseResponse(
        data=filters,
        message="获取搜索过滤器成功"
    )