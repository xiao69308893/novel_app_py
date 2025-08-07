# app/api/v1/recommendations.py
# -*- coding: utf-8 -*-
"""
推荐系统API接口
提供个性化推荐、热门推荐等功能
"""

from typing import Any, Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_db
from app.core.deps import get_current_user_optional, get_pagination_params
from app.schemas.base import BaseResponse, ListResponse
from app.schemas.novel import NovelBasicResponse
from app.schemas.recommendation import (
    RecommendationResponse, RecommendationReasonResponse,
    UserPreferenceResponse, RecommendationStatsResponse
)
from app.services.recommendation_service import RecommendationService
from app.models.user import User

# 创建路由器
router = APIRouter()


# 依赖注入
def get_recommendation_service(db: AsyncSession = Depends(get_db)) -> RecommendationService:
    """获取推荐服务"""
    return RecommendationService(db)


@router.get("/personalized", response_model=ListResponse[RecommendationResponse], summary="个性化推荐")
async def get_personalized_recommendations(
        algorithm: str = Query("hybrid", description="推荐算法"),
        limit: int = Query(20, ge=1, le=100, description="推荐数量"),
        exclude_read: bool = Query(True, description="排除已读小说"),
        exclude_bookshelf: bool = Query(False, description="排除书架小说"),
        current_user: Optional[User] = Depends(get_current_user_optional),
        recommendation_service: RecommendationService = Depends(get_recommendation_service)
) -> Any:
    """获取个性化推荐"""
    
    if not current_user:
        # 未登录用户返回热门推荐
        recommendations = await recommendation_service.get_popular_recommendations(limit)
    else:
        recommendations = await recommendation_service.get_personalized_recommendations(
            user_id=current_user.id,
            algorithm=algorithm,
            limit=limit,
            exclude_read=exclude_read,
            exclude_bookshelf=exclude_bookshelf
        )
    
    return ListResponse(
        data=recommendations,
        message="获取个性化推荐成功"
    )


@router.get("/similar/{novel_id}", response_model=ListResponse[RecommendationResponse], summary="相似小说推荐")
async def get_similar_novels(
        novel_id: str,
        limit: int = Query(20, ge=1, le=50, description="推荐数量"),
        algorithm: str = Query("content_based", description="推荐算法"),
        current_user: Optional[User] = Depends(get_current_user_optional),
        recommendation_service: RecommendationService = Depends(get_recommendation_service)
) -> Any:
    """获取相似小说推荐"""
    
    recommendations = await recommendation_service.get_similar_novels(
        novel_id=novel_id,
        user_id=current_user.id if current_user else None,
        algorithm=algorithm,
        limit=limit
    )
    
    return ListResponse(
        data=recommendations,
        message="获取相似小说推荐成功"
    )


@router.get("/hot", response_model=ListResponse[NovelResponse], summary="热门推荐")
async def get_hot_recommendations(
        time_range: str = Query("7d", description="时间范围"),
        category_id: Optional[str] = Query(None, description="分类ID"),
        limit: int = Query(20, ge=1, le=100, description="推荐数量"),
        recommendation_service: RecommendationService = Depends(get_recommendation_service)
) -> Any:
    """获取热门推荐"""
    
    recommendations = await recommendation_service.get_hot_recommendations(
        time_range=time_range,
        category_id=category_id,
        limit=limit
    )
    
    return ListResponse(
        data=recommendations,
        message="获取热门推荐成功"
    )


@router.get("/trending", response_model=ListResponse[NovelResponse], summary="趋势推荐")
async def get_trending_recommendations(
        time_range: str = Query("24h", description="时间范围"),
        category_id: Optional[str] = Query(None, description="分类ID"),
        limit: int = Query(20, ge=1, le=100, description="推荐数量"),
        recommendation_service: RecommendationService = Depends(get_recommendation_service)
) -> Any:
    """获取趋势推荐"""
    
    recommendations = await recommendation_service.get_trending_recommendations(
        time_range=time_range,
        category_id=category_id,
        limit=limit
    )
    
    return ListResponse(
        data=recommendations,
        message="获取趋势推荐成功"
    )


@router.get("/new", response_model=ListResponse[NovelResponse], summary="新书推荐")
async def get_new_recommendations(
        category_id: Optional[str] = Query(None, description="分类ID"),
        days: int = Query(30, ge=1, le=365, description="新书天数"),
        limit: int = Query(20, ge=1, le=100, description="推荐数量"),
        recommendation_service: RecommendationService = Depends(get_recommendation_service)
) -> Any:
    """获取新书推荐"""
    
    recommendations = await recommendation_service.get_new_recommendations(
        category_id=category_id,
        days=days,
        limit=limit
    )
    
    return ListResponse(
        data=recommendations,
        message="获取新书推荐成功"
    )


@router.get("/category/{category_id}", response_model=ListResponse[RecommendationResponse], summary="分类推荐")
async def get_category_recommendations(
        category_id: str,
        algorithm: str = Query("popularity", description="推荐算法"),
        limit: int = Query(20, ge=1, le=100, description="推荐数量"),
        current_user: Optional[User] = Depends(get_current_user_optional),
        recommendation_service: RecommendationService = Depends(get_recommendation_service)
) -> Any:
    """获取分类推荐"""
    
    recommendations = await recommendation_service.get_category_recommendations(
        category_id=category_id,
        user_id=current_user.id if current_user else None,
        algorithm=algorithm,
        limit=limit
    )
    
    return ListResponse(
        data=recommendations,
        message="获取分类推荐成功"
    )


@router.get("/author/{author_id}", response_model=ListResponse[NovelResponse], summary="作者推荐")
async def get_author_recommendations(
        author_id: str,
        exclude_novel_id: Optional[str] = Query(None, description="排除的小说ID"),
        limit: int = Query(20, ge=1, le=50, description="推荐数量"),
        recommendation_service: RecommendationService = Depends(get_recommendation_service)
) -> Any:
    """获取作者其他作品推荐"""
    
    recommendations = await recommendation_service.get_author_recommendations(
        author_id=author_id,
        exclude_novel_id=exclude_novel_id,
        limit=limit
    )
    
    return ListResponse(
        data=recommendations,
        message="获取作者推荐成功"
    )


@router.get("/collaborative", response_model=ListResponse[RecommendationResponse], summary="协同过滤推荐")
async def get_collaborative_recommendations(
        limit: int = Query(20, ge=1, le=100, description="推荐数量"),
        min_similarity: float = Query(0.1, ge=0.0, le=1.0, description="最小相似度"),
        current_user: User = Depends(get_current_user_optional),
        recommendation_service: RecommendationService = Depends(get_recommendation_service)
) -> Any:
    """获取协同过滤推荐"""
    
    if not current_user:
        return ListResponse(
            data=[],
            message="请先登录"
        )
    
    recommendations = await recommendation_service.get_collaborative_recommendations(
        user_id=current_user.id,
        limit=limit,
        min_similarity=min_similarity
    )
    
    return ListResponse(
        data=recommendations,
        message="获取协同过滤推荐成功"
    )


@router.get("/content_based", response_model=ListResponse[RecommendationResponse], summary="基于内容推荐")
async def get_content_based_recommendations(
        limit: int = Query(20, ge=1, le=100, description="推荐数量"),
        weight_category: float = Query(0.3, ge=0.0, le=1.0, description="分类权重"),
        weight_tags: float = Query(0.3, ge=0.0, le=1.0, description="标签权重"),
        weight_author: float = Query(0.2, ge=0.0, le=1.0, description="作者权重"),
        weight_rating: float = Query(0.2, ge=0.0, le=1.0, description="评分权重"),
        current_user: User = Depends(get_current_user_optional),
        recommendation_service: RecommendationService = Depends(get_recommendation_service)
) -> Any:
    """获取基于内容的推荐"""
    
    if not current_user:
        return ListResponse(
            data=[],
            message="请先登录"
        )
    
    recommendations = await recommendation_service.get_content_based_recommendations(
        user_id=current_user.id,
        limit=limit,
        weights={
            "category": weight_category,
            "tags": weight_tags,
            "author": weight_author,
            "rating": weight_rating
        }
    )
    
    return ListResponse(
        data=recommendations,
        message="获取基于内容推荐成功"
    )


@router.get("/reasons/{novel_id}", response_model=BaseResponse[RecommendationReasonResponse], summary="推荐理由")
async def get_recommendation_reasons(
        novel_id: str,
        current_user: Optional[User] = Depends(get_current_user_optional),
        recommendation_service: RecommendationService = Depends(get_recommendation_service)
) -> Any:
    """获取推荐理由"""
    
    reasons = await recommendation_service.get_recommendation_reasons(
        novel_id=novel_id,
        user_id=current_user.id if current_user else None
    )
    
    return BaseResponse(
        data=reasons,
        message="获取推荐理由成功"
    )


@router.post("/feedback", response_model=BaseResponse[dict], summary="推荐反馈")
async def submit_recommendation_feedback(
        novel_id: str,
        feedback_type: str,  # like, dislike, not_interested, inappropriate
        reason: Optional[str] = None,
        current_user: User = Depends(get_current_user_optional),
        recommendation_service: RecommendationService = Depends(get_recommendation_service)
) -> Any:
    """提交推荐反馈"""
    
    if not current_user:
        return BaseResponse(
            data={"success": False},
            message="请先登录"
        )
    
    result = await recommendation_service.submit_recommendation_feedback(
        user_id=current_user.id,
        novel_id=novel_id,
        feedback_type=feedback_type,
        reason=reason
    )
    
    return BaseResponse(
        data=result,
        message="推荐反馈提交成功"
    )


@router.get("/preferences", response_model=BaseResponse[UserPreferenceResponse], summary="用户偏好")
async def get_user_preferences(
        current_user: User = Depends(get_current_user_optional),
        recommendation_service: RecommendationService = Depends(get_recommendation_service)
) -> Any:
    """获取用户偏好分析"""
    
    if not current_user:
        return BaseResponse(
            data=None,
            message="请先登录"
        )
    
    preferences = await recommendation_service.get_user_preferences(current_user.id)
    
    return BaseResponse(
        data=preferences,
        message="获取用户偏好成功"
    )


@router.put("/preferences", response_model=BaseResponse[dict], summary="更新用户偏好")
async def update_user_preferences(
        categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        authors: Optional[List[str]] = None,
        exclude_categories: Optional[List[str]] = None,
        exclude_tags: Optional[List[str]] = None,
        min_rating: Optional[float] = None,
        max_word_count: Optional[int] = None,
        min_word_count: Optional[int] = None,
        current_user: User = Depends(get_current_user_optional),
        recommendation_service: RecommendationService = Depends(get_recommendation_service)
) -> Any:
    """更新用户偏好设置"""
    
    if not current_user:
        return BaseResponse(
            data={"success": False},
            message="请先登录"
        )
    
    result = await recommendation_service.update_user_preferences(
        user_id=current_user.id,
        preferences={
            "categories": categories,
            "tags": tags,
            "authors": authors,
            "exclude_categories": exclude_categories,
            "exclude_tags": exclude_tags,
            "min_rating": min_rating,
            "max_word_count": max_word_count,
            "min_word_count": min_word_count
        }
    )
    
    return BaseResponse(
        data=result,
        message="用户偏好更新成功"
    )


@router.get("/stats", response_model=BaseResponse[RecommendationStatsResponse], summary="推荐统计")
async def get_recommendation_stats(
        time_range: str = Query("7d", description="时间范围"),
        current_user: Optional[User] = Depends(get_current_user_optional),
        recommendation_service: RecommendationService = Depends(get_recommendation_service)
) -> Any:
    """获取推荐统计信息"""
    
    stats = await recommendation_service.get_recommendation_stats(
        user_id=current_user.id if current_user else None,
        time_range=time_range
    )
    
    return BaseResponse(
        data=stats,
        message="获取推荐统计成功"
    )


@router.get("/diversity", response_model=ListResponse[RecommendationResponse], summary="多样化推荐")
async def get_diverse_recommendations(
        limit: int = Query(20, ge=1, le=100, description="推荐数量"),
        diversity_factor: float = Query(0.5, ge=0.0, le=1.0, description="多样性因子"),
        current_user: Optional[User] = Depends(get_current_user_optional),
        recommendation_service: RecommendationService = Depends(get_recommendation_service)
) -> Any:
    """获取多样化推荐"""
    
    recommendations = await recommendation_service.get_diverse_recommendations(
        user_id=current_user.id if current_user else None,
        limit=limit,
        diversity_factor=diversity_factor
    )
    
    return ListResponse(
        data=recommendations,
        message="获取多样化推荐成功"
    )


@router.get("/cold_start", response_model=ListResponse[NovelResponse], summary="冷启动推荐")
async def get_cold_start_recommendations(
        limit: int = Query(20, ge=1, le=100, description="推荐数量"),
        recommendation_service: RecommendationService = Depends(get_recommendation_service)
) -> Any:
    """获取冷启动推荐（新用户推荐）"""
    
    recommendations = await recommendation_service.get_cold_start_recommendations(limit)
    
    return ListResponse(
        data=recommendations,
        message="获取冷启动推荐成功"
    )


@router.post("/refresh", response_model=BaseResponse[dict], summary="刷新推荐")
async def refresh_recommendations(
        current_user: User = Depends(get_current_user_optional),
        recommendation_service: RecommendationService = Depends(get_recommendation_service)
) -> Any:
    """刷新用户推荐缓存"""
    
    if not current_user:
        return BaseResponse(
            data={"success": False},
            message="请先登录"
        )
    
    result = await recommendation_service.refresh_user_recommendations(current_user.id)
    
    return BaseResponse(
        data=result,
        message="推荐缓存刷新成功"
    )