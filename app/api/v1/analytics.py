# app/api/v1/analytics.py
# -*- coding: utf-8 -*-
"""
数据分析API接口
提供用户行为分析、阅读统计等功能
"""

from typing import Any, Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_db
from app.core.deps import get_current_user_optional, get_pagination_params
from app.schemas.base import BaseResponse, ListResponse
from app.schemas.analytics import (
    UserAnalyticsResponse, ReadingAnalyticsResponse, NovelAnalyticsResponse,
    AuthorAnalyticsResponse, CategoryAnalyticsResponse, RevenueAnalyticsResponse,
    BehaviorAnalyticsResponse, TrendAnalyticsResponse, ComparisonAnalyticsResponse
)
from app.services.analytics_service import AnalyticsService
from app.models.user import User

# 创建路由器
router = APIRouter()


# 依赖注入
def get_analytics_service(db: AsyncSession = Depends(get_db)) -> AnalyticsService:
    """获取分析服务"""
    return AnalyticsService(db)


@router.get("/user/overview", response_model=BaseResponse[UserAnalyticsResponse], summary="用户分析概览")
async def get_user_analytics_overview(
        time_range: str = Query("30d", description="时间范围"),
        current_user: User = Depends(get_current_user_optional),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Any:
    """获取用户分析概览"""
    
    if not current_user:
        return BaseResponse(
            data=None,
            message="请先登录"
        )
    
    analytics = await analytics_service.get_user_analytics_overview(
        user_id=current_user.id,
        time_range=time_range
    )
    
    return BaseResponse(
        data=analytics,
        message="获取用户分析概览成功"
    )


@router.get("/reading/stats", response_model=BaseResponse[ReadingAnalyticsResponse], summary="阅读统计")
async def get_reading_analytics(
        time_range: str = Query("30d", description="时间范围"),
        group_by: str = Query("day", description="分组方式"),
        current_user: User = Depends(get_current_user_optional),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Any:
    """获取阅读统计分析"""
    
    if not current_user:
        return BaseResponse(
            data=None,
            message="请先登录"
        )
    
    analytics = await analytics_service.get_reading_analytics(
        user_id=current_user.id,
        time_range=time_range,
        group_by=group_by
    )
    
    return BaseResponse(
        data=analytics,
        message="获取阅读统计成功"
    )


@router.get("/reading/habits", response_model=BaseResponse[dict], summary="阅读习惯分析")
async def get_reading_habits(
        time_range: str = Query("30d", description="时间范围"),
        current_user: User = Depends(get_current_user_optional),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Any:
    """获取阅读习惯分析"""
    
    if not current_user:
        return BaseResponse(
            data=None,
            message="请先登录"
        )
    
    habits = await analytics_service.get_reading_habits(
        user_id=current_user.id,
        time_range=time_range
    )
    
    return BaseResponse(
        data=habits,
        message="获取阅读习惯分析成功"
    )


@router.get("/reading/preferences", response_model=BaseResponse[dict], summary="阅读偏好分析")
async def get_reading_preferences(
        current_user: User = Depends(get_current_user_optional),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Any:
    """获取阅读偏好分析"""
    
    if not current_user:
        return BaseResponse(
            data=None,
            message="请先登录"
        )
    
    preferences = await analytics_service.get_reading_preferences(current_user.id)
    
    return BaseResponse(
        data=preferences,
        message="获取阅读偏好分析成功"
    )


@router.get("/novel/{novel_id}/stats", response_model=BaseResponse[NovelAnalyticsResponse], summary="小说统计")
async def get_novel_analytics(
        novel_id: str,
        time_range: str = Query("30d", description="时间范围"),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Any:
    """获取小说统计分析"""
    
    analytics = await analytics_service.get_novel_analytics(
        novel_id=novel_id,
        time_range=time_range
    )
    
    return BaseResponse(
        data=analytics,
        message="获取小说统计成功"
    )


@router.get("/author/{author_id}/stats", response_model=BaseResponse[AuthorAnalyticsResponse], summary="作者统计")
async def get_author_analytics(
        author_id: str,
        time_range: str = Query("30d", description="时间范围"),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Any:
    """获取作者统计分析"""
    
    analytics = await analytics_service.get_author_analytics(
        author_id=author_id,
        time_range=time_range
    )
    
    return BaseResponse(
        data=analytics,
        message="获取作者统计成功"
    )


@router.get("/category/{category_id}/stats", response_model=BaseResponse[CategoryAnalyticsResponse], summary="分类统计")
async def get_category_analytics(
        category_id: str,
        time_range: str = Query("30d", description="时间范围"),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Any:
    """获取分类统计分析"""
    
    analytics = await analytics_service.get_category_analytics(
        category_id=category_id,
        time_range=time_range
    )
    
    return BaseResponse(
        data=analytics,
        message="获取分类统计成功"
    )


@router.get("/revenue/stats", response_model=BaseResponse[RevenueAnalyticsResponse], summary="收入统计")
async def get_revenue_analytics(
        time_range: str = Query("30d", description="时间范围"),
        group_by: str = Query("day", description="分组方式"),
        current_user: User = Depends(get_current_user_optional),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Any:
    """获取收入统计分析"""
    
    if not current_user:
        return BaseResponse(
            data=None,
            message="请先登录"
        )
    
    analytics = await analytics_service.get_revenue_analytics(
        user_id=current_user.id,
        time_range=time_range,
        group_by=group_by
    )
    
    return BaseResponse(
        data=analytics,
        message="获取收入统计成功"
    )


@router.get("/behavior/analysis", response_model=BaseResponse[BehaviorAnalyticsResponse], summary="行为分析")
async def get_behavior_analytics(
        time_range: str = Query("30d", description="时间范围"),
        behavior_types: Optional[List[str]] = Query(None, description="行为类型"),
        current_user: User = Depends(get_current_user_optional),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Any:
    """获取用户行为分析"""
    
    if not current_user:
        return BaseResponse(
            data=None,
            message="请先登录"
        )
    
    analytics = await analytics_service.get_behavior_analytics(
        user_id=current_user.id,
        time_range=time_range,
        behavior_types=behavior_types
    )
    
    return BaseResponse(
        data=analytics,
        message="获取行为分析成功"
    )


@router.get("/trends/reading", response_model=BaseResponse[TrendAnalyticsResponse], summary="阅读趋势")
async def get_reading_trends(
        time_range: str = Query("30d", description="时间范围"),
        metric: str = Query("reading_time", description="指标类型"),
        group_by: str = Query("day", description="分组方式"),
        current_user: Optional[User] = Depends(get_current_user_optional),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Any:
    """获取阅读趋势分析"""
    
    trends = await analytics_service.get_reading_trends(
        user_id=current_user.id if current_user else None,
        time_range=time_range,
        metric=metric,
        group_by=group_by
    )
    
    return BaseResponse(
        data=trends,
        message="获取阅读趋势成功"
    )


@router.get("/trends/popular", response_model=BaseResponse[TrendAnalyticsResponse], summary="热门趋势")
async def get_popular_trends(
        time_range: str = Query("7d", description="时间范围"),
        category_id: Optional[str] = Query(None, description="分类ID"),
        limit: int = Query(20, ge=1, le=100, description="返回数量"),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Any:
    """获取热门趋势分析"""
    
    trends = await analytics_service.get_popular_trends(
        time_range=time_range,
        category_id=category_id,
        limit=limit
    )
    
    return BaseResponse(
        data=trends,
        message="获取热门趋势成功"
    )


@router.get("/comparison/novels", response_model=BaseResponse[ComparisonAnalyticsResponse], summary="小说对比")
async def get_novels_comparison(
        novel_ids: List[str] = Query(..., description="小说ID列表"),
        time_range: str = Query("30d", description="时间范围"),
        metrics: List[str] = Query(["views", "favorites", "rating"], description="对比指标"),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Any:
    """获取小说对比分析"""
    
    comparison = await analytics_service.get_novels_comparison(
        novel_ids=novel_ids,
        time_range=time_range,
        metrics=metrics
    )
    
    return BaseResponse(
        data=comparison,
        message="获取小说对比成功"
    )


@router.get("/comparison/authors", response_model=BaseResponse[ComparisonAnalyticsResponse], summary="作者对比")
async def get_authors_comparison(
        author_ids: List[str] = Query(..., description="作者ID列表"),
        time_range: str = Query("30d", description="时间范围"),
        metrics: List[str] = Query(["novels_count", "total_views", "avg_rating"], description="对比指标"),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Any:
    """获取作者对比分析"""
    
    comparison = await analytics_service.get_authors_comparison(
        author_ids=author_ids,
        time_range=time_range,
        metrics=metrics
    )
    
    return BaseResponse(
        data=comparison,
        message="获取作者对比成功"
    )


@router.get("/heatmap/reading", response_model=BaseResponse[dict], summary="阅读热力图")
async def get_reading_heatmap(
        time_range: str = Query("30d", description="时间范围"),
        granularity: str = Query("hour", description="粒度"),
        current_user: User = Depends(get_current_user_optional),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Any:
    """获取阅读热力图数据"""
    
    if not current_user:
        return BaseResponse(
            data=None,
            message="请先登录"
        )
    
    heatmap = await analytics_service.get_reading_heatmap(
        user_id=current_user.id,
        time_range=time_range,
        granularity=granularity
    )
    
    return BaseResponse(
        data=heatmap,
        message="获取阅读热力图成功"
    )


@router.get("/funnel/reading", response_model=BaseResponse[dict], summary="阅读漏斗")
async def get_reading_funnel(
        time_range: str = Query("30d", description="时间范围"),
        novel_id: Optional[str] = Query(None, description="小说ID"),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Any:
    """获取阅读漏斗分析"""
    
    funnel = await analytics_service.get_reading_funnel(
        time_range=time_range,
        novel_id=novel_id
    )
    
    return BaseResponse(
        data=funnel,
        message="获取阅读漏斗成功"
    )


@router.get("/cohort/retention", response_model=BaseResponse[dict], summary="用户留存分析")
async def get_user_retention_cohort(
        start_date: str = Query(..., description="开始日期"),
        period_type: str = Query("week", description="周期类型"),
        periods: int = Query(12, ge=1, le=52, description="周期数量"),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Any:
    """获取用户留存队列分析"""
    
    cohort = await analytics_service.get_user_retention_cohort(
        start_date=start_date,
        period_type=period_type,
        periods=periods
    )
    
    return BaseResponse(
        data=cohort,
        message="获取用户留存分析成功"
    )


@router.get("/segmentation/users", response_model=BaseResponse[dict], summary="用户分群")
async def get_user_segmentation(
        segmentation_type: str = Query("behavior", description="分群类型"),
        time_range: str = Query("30d", description="时间范围"),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Any:
    """获取用户分群分析"""
    
    segmentation = await analytics_service.get_user_segmentation(
        segmentation_type=segmentation_type,
        time_range=time_range
    )
    
    return BaseResponse(
        data=segmentation,
        message="获取用户分群成功"
    )


@router.get("/export/report", response_model=BaseResponse[dict], summary="导出分析报告")
async def export_analytics_report(
        report_type: str = Query("user_analytics", description="报告类型"),
        time_range: str = Query("30d", description="时间范围"),
        format: str = Query("excel", description="导出格式"),
        current_user: User = Depends(get_current_user_optional),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Any:
    """导出分析报告"""
    
    if not current_user:
        return BaseResponse(
            data=None,
            message="请先登录"
        )
    
    report = await analytics_service.export_analytics_report(
        user_id=current_user.id,
        report_type=report_type,
        time_range=time_range,
        format=format
    )
    
    return BaseResponse(
        data=report,
        message="分析报告导出成功"
    )


@router.get("/dashboard/summary", response_model=BaseResponse[dict], summary="仪表板摘要")
async def get_dashboard_summary(
        time_range: str = Query("7d", description="时间范围"),
        current_user: Optional[User] = Depends(get_current_user_optional),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Any:
    """获取仪表板摘要数据"""
    
    summary = await analytics_service.get_dashboard_summary(
        user_id=current_user.id if current_user else None,
        time_range=time_range
    )
    
    return BaseResponse(
        data=summary,
        message="获取仪表板摘要成功"
    )


@router.post("/track/event", response_model=BaseResponse[dict], summary="事件追踪")
async def track_analytics_event(
        event_type: str,
        event_data: dict,
        current_user: Optional[User] = Depends(get_current_user_optional),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Any:
    """追踪分析事件"""
    
    result = await analytics_service.track_analytics_event(
        user_id=current_user.id if current_user else None,
        event_type=event_type,
        event_data=event_data
    )
    
    return BaseResponse(
        data=result,
        message="事件追踪成功"
    )