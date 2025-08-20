# app/services/analytics_service.py
# -*- coding: utf-8 -*-
"""
数据分析业务服务
处理数据分析相关的业务逻辑，包括用户行为分析、阅读统计、趋势分析等
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func, desc, asc, text

import uuid

from ..models.user import User, UserFavorite
from ..models.novel import Novel
from ..models.chapter import Chapter, ReadingProgress, ChapterPurchase
from ..models.comment import Comment
from ..schemas.analytics import (
    UserAnalyticsOverviewResponse, ReadingStatsResponse, ReadingHabitsResponse,
    ReadingPreferencesResponse, NovelStatsResponse, AuthorStatsResponse,
    CategoryStatsResponse, RevenueStatsResponse, BehaviorAnalysisResponse,
    ReadingTrendResponse, HotTrendResponse, NovelComparisonResponse,
    AuthorComparisonResponse, ReadingHeatmapResponse, ReadingFunnelResponse,
    UserRetentionResponse, UserSegmentResponse, DashboardSummaryResponse
)
from .base import BaseService


class AnalyticsService(BaseService):
    """数据分析服务类"""

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_user_analytics_overview(
        self,
        user_id: uuid.UUID
    ) -> UserAnalyticsOverviewResponse:
        """获取用户分析概览"""
        
        # 获取用户基本信息
        user_query = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise ValueError("用户不存在")
        
        # 获取阅读统计
        reading_progress_query = select(
            func.count(ReadingProgress.id).label('books_read'),
            func.sum(ReadingProgress.progress).label('total_progress'),
            func.avg(ReadingProgress.progress).label('avg_progress')
        ).where(ReadingProgress.user_id == user_id)
        
        reading_result = await self.db.execute(reading_progress_query)
        reading_stats = reading_result.first()
        
        # 获取收藏统计
        favorite_query = select(func.count()).select_from(UserFavorite).where(
            UserFavorite.user_id == user_id
        )
        favorite_result = await self.db.execute(favorite_query)
        favorite_count = favorite_result.scalar()
        
        # 获取评论统计
        comment_query = select(func.count()).select_from(Comment).where(
            Comment.user_id == user_id
        )
        comment_result = await self.db.execute(comment_query)
        comment_count = comment_result.scalar()
        
        # 获取消费统计
        purchase_query = select(
            func.count(ChapterPurchase.id).label('purchase_count'),
            func.sum(ChapterPurchase.amount).label('total_spent')
        ).where(ChapterPurchase.user_id == user_id)
        
        purchase_result = await self.db.execute(purchase_query)
        purchase_stats = purchase_result.first()
        
        return UserAnalyticsOverviewResponse(
            user_id=str(user_id),
            registration_date=user.created_at.date(),
            days_since_registration=(datetime.now().date() - user.created_at.date()).days,
            books_read=reading_stats.books_read or 0,
            total_reading_time=int((reading_stats.total_progress or 0) * 60),  # 假设每个进度点代表1分钟
            average_reading_progress=float(reading_stats.avg_progress or 0),
            favorite_count=favorite_count,
            comment_count=comment_count,
            purchase_count=purchase_stats.purchase_count or 0,
            total_spent=float(purchase_stats.total_spent or 0),
            last_active_date=user.last_login_at.date() if user.last_login_at else None
        )

    async def get_reading_stats(
        self,
        user_id: uuid.UUID,
        period: str = "30d"
    ) -> ReadingStatsResponse:
        """获取阅读统计"""
        
        # 解析时间周期
        if period == "7d":
            start_date = datetime.now() - timedelta(days=7)
        elif period == "30d":
            start_date = datetime.now() - timedelta(days=30)
        elif period == "90d":
            start_date = datetime.now() - timedelta(days=90)
        else:
            start_date = datetime.now() - timedelta(days=30)
        
        # 获取阅读时长趋势
        reading_trend_query = select(
            func.date(ReadingProgress.updated_at).label('date'),
            func.sum(ReadingProgress.reading_time).label('reading_time')
        ).where(
            and_(
                ReadingProgress.user_id == user_id,
                ReadingProgress.updated_at >= start_date
            )
        ).group_by(
            func.date(ReadingProgress.updated_at)
        ).order_by(
            func.date(ReadingProgress.updated_at)
        )
        
        trend_result = await self.db.execute(reading_trend_query)
        reading_trend = [
            {"date": str(row.date), "reading_time": row.reading_time or 0}
            for row in trend_result
        ]
        
        # 获取总阅读时长
        total_time_query = select(func.sum(ReadingProgress.reading_time)).where(
            and_(
                ReadingProgress.user_id == user_id,
                ReadingProgress.updated_at >= start_date
            )
        )
        total_time_result = await self.db.execute(total_time_query)
        total_reading_time = total_time_result.scalar() or 0
        
        # 获取阅读书籍数
        books_query = select(func.count(func.distinct(ReadingProgress.novel_id))).where(
            and_(
                ReadingProgress.user_id == user_id,
                ReadingProgress.updated_at >= start_date
            )
        )
        books_result = await self.db.execute(books_query)
        books_read = books_result.scalar() or 0
        
        # 获取阅读章节数
        chapters_query = select(func.count(func.distinct(ReadingProgress.chapter_id))).where(
            and_(
                ReadingProgress.user_id == user_id,
                ReadingProgress.updated_at >= start_date
            )
        )
        chapters_result = await self.db.execute(chapters_query)
        chapters_read = chapters_result.scalar() or 0
        
        return ReadingStatsResponse(
            period=period,
            total_reading_time=total_reading_time,
            books_read=books_read,
            chapters_read=chapters_read,
            average_daily_time=total_reading_time / max(1, (datetime.now() - start_date).days),
            reading_trend=reading_trend
        )

    async def get_reading_habits(
        self,
        user_id: uuid.UUID
    ) -> ReadingHabitsResponse:
        """获取阅读习惯分析"""
        
        # 获取阅读时间分布（按小时）
        hour_distribution_query = select(
            func.extract('hour', ReadingProgress.updated_at).label('hour'),
            func.count().label('count')
        ).where(
            ReadingProgress.user_id == user_id
        ).group_by(
            func.extract('hour', ReadingProgress.updated_at)
        ).order_by(
            func.extract('hour', ReadingProgress.updated_at)
        )
        
        hour_result = await self.db.execute(hour_distribution_query)
        hour_distribution = [
            {"hour": int(row.hour), "count": row.count}
            for row in hour_result
        ]
        
        # 获取星期分布
        weekday_distribution_query = select(
            func.extract('dow', ReadingProgress.updated_at).label('weekday'),
            func.count().label('count')
        ).where(
            ReadingProgress.user_id == user_id
        ).group_by(
            func.extract('dow', ReadingProgress.updated_at)
        ).order_by(
            func.extract('dow', ReadingProgress.updated_at)
        )
        
        weekday_result = await self.db.execute(weekday_distribution_query)
        weekday_distribution = [
            {"weekday": int(row.weekday), "count": row.count}
            for row in weekday_result
        ]
        
        # 获取阅读会话统计
        session_query = select(
            func.avg(ReadingProgress.reading_time).label('avg_session'),
            func.max(ReadingProgress.reading_time).label('max_session'),
            func.count().label('total_sessions')
        ).where(ReadingProgress.user_id == user_id)
        
        session_result = await self.db.execute(session_query)
        session_stats = session_result.first()
        
        return ReadingHabitsResponse(
            hour_distribution=hour_distribution,
            weekday_distribution=weekday_distribution,
            average_session_duration=session_stats.avg_session or 0,
            longest_session_duration=session_stats.max_session or 0,
            total_reading_sessions=session_stats.total_sessions or 0,
            most_active_hour=max(hour_distribution, key=lambda x: x["count"])["hour"] if hour_distribution else 0,
            most_active_weekday=max(weekday_distribution, key=lambda x: x["count"])["weekday"] if weekday_distribution else 0
        )

    async def get_reading_preferences(
        self,
        user_id: uuid.UUID
    ) -> ReadingPreferencesResponse:
        """获取阅读偏好分析"""
        
        # 获取分类偏好
        category_query = select(
            Novel.category,
            func.count().label('count'),
            func.avg(ReadingProgress.progress).label('avg_progress')
        ).join(
            ReadingProgress, Novel.id == ReadingProgress.novel_id
        ).where(
            ReadingProgress.user_id == user_id
        ).group_by(
            Novel.category
        ).order_by(
            desc(func.count())
        )
        
        category_result = await self.db.execute(category_query)
        category_preferences = [
            {
                "category": row.category,
                "count": row.count,
                "avg_progress": float(row.avg_progress or 0)
            }
            for row in category_result
        ]
        
        # 获取作者偏好
        author_query = select(
            Novel.author,
            func.count().label('count')
        ).join(
            ReadingProgress, Novel.id == ReadingProgress.novel_id
        ).where(
            ReadingProgress.user_id == user_id
        ).group_by(
            Novel.author
        ).order_by(
            desc(func.count())
        ).limit(10)
        
        author_result = await self.db.execute(author_query)
        author_preferences = [
            {"author": row.author, "count": row.count}
            for row in author_result
        ]
        
        # 获取标签偏好
        tag_preferences = []  # 简化实现
        
        # 获取长度偏好
        length_query = select(
            func.avg(Novel.word_count).label('avg_length'),
            func.min(Novel.word_count).label('min_length'),
            func.max(Novel.word_count).label('max_length')
        ).join(
            ReadingProgress, Novel.id == ReadingProgress.novel_id
        ).where(ReadingProgress.user_id == user_id)
        
        length_result = await self.db.execute(length_query)
        length_stats = length_result.first()
        
        return ReadingPreferencesResponse(
            category_preferences=category_preferences,
            author_preferences=author_preferences,
            tag_preferences=tag_preferences,
            average_book_length=int(length_stats.avg_length or 0),
            preferred_length_range={
                "min": int(length_stats.min_length or 0),
                "max": int(length_stats.max_length or 0)
            }
        )

    async def get_novel_stats(
        self,
        novel_id: uuid.UUID,
        period: str = "30d"
    ) -> NovelStatsResponse:
        """获取小说统计"""
        
        # 解析时间周期
        if period == "7d":
            start_date = datetime.now() - timedelta(days=7)
        elif period == "30d":
            start_date = datetime.now() - timedelta(days=30)
        elif period == "90d":
            start_date = datetime.now() - timedelta(days=90)
        else:
            start_date = datetime.now() - timedelta(days=30)
        
        # 获取小说基本信息
        novel_query = select(Novel).where(Novel.id == novel_id)
        novel_result = await self.db.execute(novel_query)
        novel = novel_result.scalar_one_or_none()
        
        if not novel:
            raise ValueError("小说不存在")
        
        # 获取阅读统计
        reading_stats_query = select(
            func.count(func.distinct(ReadingProgress.user_id)).label('unique_readers'),
            func.sum(ReadingProgress.reading_time).label('total_reading_time'),
            func.avg(ReadingProgress.progress).label('avg_progress')
        ).where(
            and_(
                ReadingProgress.novel_id == novel_id,
                ReadingProgress.updated_at >= start_date
            )
        )
        
        reading_result = await self.db.execute(reading_stats_query)
        reading_stats = reading_result.first()
        
        # 获取收藏统计
        favorite_query = select(func.count()).select_from(UserFavorite).where(
            and_(
                UserFavorite.novel_id == novel_id,
                UserFavorite.created_at >= start_date
            )
        )
        favorite_result = await self.db.execute(favorite_query)
        new_favorites = favorite_result.scalar()
        
        # 获取评论统计
        comment_query = select(func.count()).select_from(Comment).where(
            and_(
                Comment.novel_id == novel_id,
                Comment.created_at >= start_date
            )
        )
        comment_result = await self.db.execute(comment_query)
        new_comments = comment_result.scalar()
        
        # 获取阅读趋势
        trend_query = select(
            func.date(ReadingProgress.updated_at).label('date'),
            func.count(func.distinct(ReadingProgress.user_id)).label('readers')
        ).where(
            and_(
                ReadingProgress.novel_id == novel_id,
                ReadingProgress.updated_at >= start_date
            )
        ).group_by(
            func.date(ReadingProgress.updated_at)
        ).order_by(
            func.date(ReadingProgress.updated_at)
        )
        
        trend_result = await self.db.execute(trend_query)
        reading_trend = [
            {"date": str(row.date), "readers": row.readers}
            for row in trend_result
        ]
        
        return NovelStatsResponse(
            novel_id=str(novel_id),
            title=novel.title,
            author=novel.author,
            period=period,
            unique_readers=reading_stats.unique_readers or 0,
            total_reading_time=reading_stats.total_reading_time or 0,
            average_progress=float(reading_stats.avg_progress or 0),
            new_favorites=new_favorites,
            new_comments=new_comments,
            reading_trend=reading_trend,
            total_views=novel.view_count,
            rating=novel.rating
        )

    async def get_author_stats(
        self,
        author: str,
        period: str = "30d"
    ) -> AuthorStatsResponse:
        """获取作者统计"""
        
        # 解析时间周期
        if period == "7d":
            start_date = datetime.now() - timedelta(days=7)
        elif period == "30d":
            start_date = datetime.now() - timedelta(days=30)
        elif period == "90d":
            start_date = datetime.now() - timedelta(days=90)
        else:
            start_date = datetime.now() - timedelta(days=30)
        
        # 获取作者小说统计
        novel_stats_query = select(
            func.count(Novel.id).label('novel_count'),
            func.sum(Novel.view_count).label('total_views'),
            func.avg(Novel.rating).label('avg_rating'),
            func.sum(Novel.word_count).label('total_words')
        ).where(
            and_(
                Novel.author == author,
                Novel.is_deleted == False
            )
        )
        
        novel_result = await self.db.execute(novel_stats_query)
        novel_stats = novel_result.first()
        
        # 获取阅读统计
        reading_stats_query = select(
            func.count(func.distinct(ReadingProgress.user_id)).label('unique_readers'),
            func.sum(ReadingProgress.reading_time).label('total_reading_time')
        ).join(
            Novel, ReadingProgress.novel_id == Novel.id
        ).where(
            and_(
                Novel.author == author,
                ReadingProgress.updated_at >= start_date
            )
        )
        
        reading_result = await self.db.execute(reading_stats_query)
        reading_stats = reading_result.first()
        
        # 获取收藏统计
        favorite_stats_query = select(
            func.count().label('total_favorites')
        ).select_from(UserFavorite).join(
            Novel, UserFavorite.novel_id == Novel.id
        ).where(
            and_(
                Novel.author == author,
                UserFavorite.created_at >= start_date
            )
        )
        
        favorite_result = await self.db.execute(favorite_stats_query)
        favorite_stats = favorite_result.first()
        
        return AuthorStatsResponse(
            author=author,
            period=period,
            novel_count=novel_stats.novel_count or 0,
            total_views=novel_stats.total_views or 0,
            average_rating=float(novel_stats.avg_rating or 0),
            total_words=novel_stats.total_words or 0,
            unique_readers=reading_stats.unique_readers or 0,
            total_reading_time=reading_stats.total_reading_time or 0,
            total_favorites=favorite_stats.total_favorites or 0
        )

    async def get_category_stats(
        self,
        period: str = "30d"
    ) -> List[CategoryStatsResponse]:
        """获取分类统计"""
        
        # 解析时间周期
        if period == "7d":
            start_date = datetime.now() - timedelta(days=7)
        elif period == "30d":
            start_date = datetime.now() - timedelta(days=30)
        elif period == "90d":
            start_date = datetime.now() - timedelta(days=90)
        else:
            start_date = datetime.now() - timedelta(days=30)
        
        # 获取分类统计
        category_stats_query = select(
            Novel.category,
            func.count(Novel.id).label('novel_count'),
            func.sum(Novel.view_count).label('total_views'),
            func.avg(Novel.rating).label('avg_rating'),
            func.count(func.distinct(ReadingProgress.user_id)).label('unique_readers')
        ).outerjoin(
            ReadingProgress, and_(
                Novel.id == ReadingProgress.novel_id,
                ReadingProgress.updated_at >= start_date
            )
        ).where(
            Novel.is_deleted == False
        ).group_by(
            Novel.category
        ).order_by(
            desc(func.count(Novel.id))
        )
        
        result = await self.db.execute(category_stats_query)
        categories = result.all()
        
        category_stats = [
            CategoryStatsResponse(
                category=row.category,
                novel_count=row.novel_count,
                total_views=row.total_views or 0,
                average_rating=float(row.avg_rating or 0),
                unique_readers=row.unique_readers or 0,
                period=period
            )
            for row in categories
        ]
        
        return category_stats

    async def get_revenue_stats(
        self,
        period: str = "30d"
    ) -> RevenueStatsResponse:
        """获取收入统计"""
        
        # 解析时间周期
        if period == "7d":
            start_date = datetime.now() - timedelta(days=7)
        elif period == "30d":
            start_date = datetime.now() - timedelta(days=30)
        elif period == "90d":
            start_date = datetime.now() - timedelta(days=90)
        else:
            start_date = datetime.now() - timedelta(days=30)
        
        # 获取收入趋势
        revenue_trend_query = select(
            func.date(ChapterPurchase.created_at).label('date'),
            func.sum(ChapterPurchase.amount).label('revenue'),
            func.count().label('transactions')
        ).where(
            ChapterPurchase.created_at >= start_date
        ).group_by(
            func.date(ChapterPurchase.created_at)
        ).order_by(
            func.date(ChapterPurchase.created_at)
        )
        
        trend_result = await self.db.execute(revenue_trend_query)
        revenue_trend = [
            {
                "date": str(row.date),
                "revenue": float(row.revenue or 0),
                "transactions": row.transactions
            }
            for row in trend_result
        ]
        
        # 获取总收入统计
        total_stats_query = select(
            func.sum(ChapterPurchase.amount).label('total_revenue'),
            func.count().label('total_transactions'),
            func.count(func.distinct(ChapterPurchase.user_id)).label('paying_users'),
            func.avg(ChapterPurchase.amount).label('avg_transaction')
        ).where(
            ChapterPurchase.created_at >= start_date
        )
        
        total_result = await self.db.execute(total_stats_query)
        total_stats = total_result.first()
        
        return RevenueStatsResponse(
            period=period,
            total_revenue=float(total_stats.total_revenue or 0),
            total_transactions=total_stats.total_transactions or 0,
            paying_users=total_stats.paying_users or 0,
            average_transaction=float(total_stats.avg_transaction or 0),
            revenue_trend=revenue_trend
        )

    async def get_behavior_analysis(
        self,
        user_id: uuid.UUID,
        period: str = "30d"
    ) -> BehaviorAnalysisResponse:
        """获取行为分析"""
        
        # 解析时间周期
        if period == "7d":
            start_date = datetime.now() - timedelta(days=7)
        elif period == "30d":
            start_date = datetime.now() - timedelta(days=30)
        elif period == "90d":
            start_date = datetime.now() - timedelta(days=90)
        else:
            start_date = datetime.now() - timedelta(days=30)
        
        # 获取行为统计
        behavior_stats = {
            "reading_sessions": 0,
            "books_started": 0,
            "books_completed": 0,
            "chapters_read": 0,
            "comments_posted": 0,
            "books_favorited": 0,
            "chapters_purchased": 0
        }
        
        # 阅读会话数
        session_query = select(func.count()).select_from(ReadingProgress).where(
            and_(
                ReadingProgress.user_id == user_id,
                ReadingProgress.updated_at >= start_date
            )
        )
        session_result = await self.db.execute(session_query)
        behavior_stats["reading_sessions"] = session_result.scalar() or 0
        
        # 开始阅读的书籍数
        started_query = select(func.count(func.distinct(ReadingProgress.novel_id))).where(
            and_(
                ReadingProgress.user_id == user_id,
                ReadingProgress.created_at >= start_date
            )
        )
        started_result = await self.db.execute(started_query)
        behavior_stats["books_started"] = started_result.scalar() or 0
        
        # 完成的书籍数
        completed_query = select(func.count()).select_from(ReadingProgress).where(
            and_(
                ReadingProgress.user_id == user_id,
                ReadingProgress.progress >= 1.0,
                ReadingProgress.updated_at >= start_date
            )
        )
        completed_result = await self.db.execute(completed_query)
        behavior_stats["books_completed"] = completed_result.scalar() or 0
        
        # 其他统计...
        
        return BehaviorAnalysisResponse(
            user_id=str(user_id),
            period=period,
            behavior_stats=behavior_stats,
            engagement_score=0.75,  # 简化计算
            activity_level="active"  # 简化分类
        )

    async def get_reading_trends(
        self,
        period: str = "30d"
    ) -> List[ReadingTrendResponse]:
        """获取阅读趋势"""
        
        # 解析时间周期
        if period == "7d":
            start_date = datetime.now() - timedelta(days=7)
        elif period == "30d":
            start_date = datetime.now() - timedelta(days=30)
        elif period == "90d":
            start_date = datetime.now() - timedelta(days=90)
        else:
            start_date = datetime.now() - timedelta(days=30)
        
        # 获取每日阅读趋势
        trend_query = select(
            func.date(ReadingProgress.updated_at).label('date'),
            func.count(func.distinct(ReadingProgress.user_id)).label('active_readers'),
            func.sum(ReadingProgress.reading_time).label('total_time'),
            func.count().label('reading_sessions')
        ).where(
            ReadingProgress.updated_at >= start_date
        ).group_by(
            func.date(ReadingProgress.updated_at)
        ).order_by(
            func.date(ReadingProgress.updated_at)
        )
        
        result = await self.db.execute(trend_query)
        trends = [
            ReadingTrendResponse(
                date=row.date,
                active_readers=row.active_readers,
                total_reading_time=row.total_time or 0,
                reading_sessions=row.reading_sessions
            )
            for row in result
        ]
        
        return trends

    async def get_hot_trends(
        self,
        period: str = "7d",
        limit: int = 10
    ) -> List[HotTrendResponse]:
        """获取热门趋势"""
        
        # 解析时间周期
        if period == "7d":
            start_date = datetime.now() - timedelta(days=7)
        elif period == "30d":
            start_date = datetime.now() - timedelta(days=30)
        else:
            start_date = datetime.now() - timedelta(days=7)
        
        # 获取热门小说趋势
        hot_query = select(
            Novel.id,
            Novel.title,
            Novel.author,
            Novel.category,
            func.count(func.distinct(ReadingProgress.user_id)).label('readers'),
            func.sum(ReadingProgress.reading_time).label('reading_time')
        ).join(
            ReadingProgress, Novel.id == ReadingProgress.novel_id
        ).where(
            and_(
                ReadingProgress.updated_at >= start_date,
                Novel.is_deleted == False
            )
        ).group_by(
            Novel.id, Novel.title, Novel.author, Novel.category
        ).order_by(
            desc(func.count(func.distinct(ReadingProgress.user_id)))
        ).limit(limit)
        
        result = await self.db.execute(hot_query)
        hot_trends = [
            HotTrendResponse(
                novel_id=str(row.id),
                title=row.title,
                author=row.author,
                category=row.category,
                readers=row.readers,
                reading_time=row.reading_time or 0,
                trend_score=row.readers * 1.0  # 简化的趋势分数
            )
            for row in result
        ]
        
        return hot_trends

    async def compare_novels(
        self,
        novel_ids: List[uuid.UUID],
        period: str = "30d"
    ) -> List[NovelComparisonResponse]:
        """对比小说数据"""
        
        # 解析时间周期
        if period == "7d":
            start_date = datetime.now() - timedelta(days=7)
        elif period == "30d":
            start_date = datetime.now() - timedelta(days=30)
        elif period == "90d":
            start_date = datetime.now() - timedelta(days=90)
        else:
            start_date = datetime.now() - timedelta(days=30)
        
        comparisons = []
        
        for novel_id in novel_ids:
            # 获取小说基本信息
            novel_query = select(Novel).where(Novel.id == novel_id)
            novel_result = await self.db.execute(novel_query)
            novel = novel_result.scalar_one_or_none()
            
            if not novel:
                continue
            
            # 获取统计数据
            stats_query = select(
                func.count(func.distinct(ReadingProgress.user_id)).label('readers'),
                func.sum(ReadingProgress.reading_time).label('reading_time'),
                func.avg(ReadingProgress.progress).label('avg_progress')
            ).where(
                and_(
                    ReadingProgress.novel_id == novel_id,
                    ReadingProgress.updated_at >= start_date
                )
            )
            
            stats_result = await self.db.execute(stats_query)
            stats = stats_result.first()
            
            comparisons.append(NovelComparisonResponse(
                novel_id=str(novel_id),
                title=novel.title,
                author=novel.author,
                category=novel.category,
                readers=stats.readers or 0,
                reading_time=stats.reading_time or 0,
                average_progress=float(stats.avg_progress or 0),
                rating=novel.rating,
                view_count=novel.view_count
            ))
        
        return comparisons

    async def compare_authors(
        self,
        authors: List[str],
        period: str = "30d"
    ) -> List[AuthorComparisonResponse]:
        """对比作者数据"""
        
        # 解析时间周期
        if period == "7d":
            start_date = datetime.now() - timedelta(days=7)
        elif period == "30d":
            start_date = datetime.now() - timedelta(days=30)
        elif period == "90d":
            start_date = datetime.now() - timedelta(days=90)
        else:
            start_date = datetime.now() - timedelta(days=30)
        
        comparisons = []
        
        for author in authors:
            # 获取作者统计
            stats_query = select(
                func.count(Novel.id).label('novel_count'),
                func.sum(Novel.view_count).label('total_views'),
                func.avg(Novel.rating).label('avg_rating'),
                func.count(func.distinct(ReadingProgress.user_id)).label('readers')
            ).outerjoin(
                ReadingProgress, and_(
                    Novel.id == ReadingProgress.novel_id,
                    ReadingProgress.updated_at >= start_date
                )
            ).where(
                and_(
                    Novel.author == author,
                    Novel.is_deleted == False
                )
            )
            
            result = await self.db.execute(stats_query)
            stats = result.first()
            
            comparisons.append(AuthorComparisonResponse(
                author=author,
                novel_count=stats.novel_count or 0,
                total_views=stats.total_views or 0,
                average_rating=float(stats.avg_rating or 0),
                readers=stats.readers or 0
            ))
        
        return comparisons

    async def get_reading_heatmap(
        self,
        user_id: Optional[uuid.UUID] = None,
        period: str = "30d"
    ) -> ReadingHeatmapResponse:
        """获取阅读热力图"""
        
        # 解析时间周期
        if period == "7d":
            start_date = datetime.now() - timedelta(days=7)
        elif period == "30d":
            start_date = datetime.now() - timedelta(days=30)
        elif period == "90d":
            start_date = datetime.now() - timedelta(days=90)
        else:
            start_date = datetime.now() - timedelta(days=30)
        
        # 构建查询条件
        conditions = [ReadingProgress.updated_at >= start_date]
        if user_id:
            conditions.append(ReadingProgress.user_id == user_id)
        
        # 获取热力图数据（按小时和星期）
        heatmap_query = select(
            func.extract('hour', ReadingProgress.updated_at).label('hour'),
            func.extract('dow', ReadingProgress.updated_at).label('weekday'),
            func.count().label('activity')
        ).where(
            and_(*conditions)
        ).group_by(
            func.extract('hour', ReadingProgress.updated_at),
            func.extract('dow', ReadingProgress.updated_at)
        )
        
        result = await self.db.execute(heatmap_query)
        heatmap_data = [
            {
                "hour": int(row.hour),
                "weekday": int(row.weekday),
                "activity": row.activity
            }
            for row in result
        ]
        
        return ReadingHeatmapResponse(
            user_id=str(user_id) if user_id else None,
            period=period,
            heatmap_data=heatmap_data
        )

    async def get_reading_funnel(
        self,
        period: str = "30d"
    ) -> ReadingFunnelResponse:
        """获取阅读漏斗分析"""
        
        # 解析时间周期
        if period == "7d":
            start_date = datetime.now() - timedelta(days=7)
        elif period == "30d":
            start_date = datetime.now() - timedelta(days=30)
        elif period == "90d":
            start_date = datetime.now() - timedelta(days=90)
        else:
            start_date = datetime.now() - timedelta(days=30)
        
        # 获取漏斗数据
        # 1. 访问用户数
        total_users_query = select(func.count(func.distinct(User.id))).where(
            User.last_login_at >= start_date
        )
        total_users_result = await self.db.execute(total_users_query)
        total_users = total_users_result.scalar() or 0
        
        # 2. 开始阅读用户数
        reading_users_query = select(func.count(func.distinct(ReadingProgress.user_id))).where(
            ReadingProgress.created_at >= start_date
        )
        reading_users_result = await self.db.execute(reading_users_query)
        reading_users = reading_users_result.scalar() or 0
        
        # 3. 完成第一章用户数
        first_chapter_query = select(func.count(func.distinct(ReadingProgress.user_id))).where(
            and_(
                ReadingProgress.created_at >= start_date,
                ReadingProgress.progress > 0.1
            )
        )
        first_chapter_result = await self.db.execute(first_chapter_query)
        first_chapter_users = first_chapter_result.scalar() or 0
        
        # 4. 收藏用户数
        favorite_users_query = select(func.count(func.distinct(UserFavorite.user_id))).where(
            UserFavorite.created_at >= start_date
        )
        favorite_users_result = await self.db.execute(favorite_users_query)
        favorite_users = favorite_users_result.scalar() or 0
        
        # 5. 付费用户数
        paying_users_query = select(func.count(func.distinct(ChapterPurchase.user_id))).where(
            ChapterPurchase.created_at >= start_date
        )
        paying_users_result = await self.db.execute(paying_users_query)
        paying_users = paying_users_result.scalar() or 0
        
        funnel_steps = [
            {"step": "访问", "users": total_users, "conversion_rate": 1.0},
            {"step": "开始阅读", "users": reading_users, "conversion_rate": reading_users / max(1, total_users)},
            {"step": "完成第一章", "users": first_chapter_users, "conversion_rate": first_chapter_users / max(1, reading_users)},
            {"step": "收藏", "users": favorite_users, "conversion_rate": favorite_users / max(1, first_chapter_users)},
            {"step": "付费", "users": paying_users, "conversion_rate": paying_users / max(1, favorite_users)}
        ]
        
        return ReadingFunnelResponse(
            period=period,
            funnel_steps=funnel_steps,
            overall_conversion_rate=paying_users / max(1, total_users)
        )

    async def get_user_retention(
        self,
        cohort_period: str = "weekly"
    ) -> List[UserRetentionResponse]:
        """获取用户留存分析"""
        
        # 简化实现，返回模拟数据
        retention_data = []
        
        for i in range(4):  # 4个时间段
            if cohort_period == "weekly":
                period_start = datetime.now() - timedelta(weeks=i+1)
                period_name = f"第{i+1}周"
            else:
                period_start = datetime.now() - timedelta(days=(i+1)*30)
                period_name = f"第{i+1}月"
            
            retention_data.append(UserRetentionResponse(
                cohort_period=period_name,
                cohort_size=100 - i*10,  # 模拟数据
                retention_rates={
                    "day_1": 0.8 - i*0.1,
                    "day_7": 0.6 - i*0.1,
                    "day_30": 0.4 - i*0.1
                }
            ))
        
        return retention_data

    async def get_user_segments(
        self,
        segmentation_type: str = "behavior"
    ) -> List[UserSegmentResponse]:
        """获取用户分群分析"""
        
        # 简化实现，基于阅读行为分群
        if segmentation_type == "behavior":
            segments = [
                UserSegmentResponse(
                    segment_name="重度用户",
                    user_count=150,
                    characteristics=["日均阅读时间>2小时", "月阅读书籍>5本"],
                    percentage=0.15
                ),
                UserSegmentResponse(
                    segment_name="中度用户",
                    user_count=500,
                    characteristics=["日均阅读时间30分钟-2小时", "月阅读书籍2-5本"],
                    percentage=0.50
                ),
                UserSegmentResponse(
                    segment_name="轻度用户",
                    user_count=350,
                    characteristics=["日均阅读时间<30分钟", "月阅读书籍<2本"],
                    percentage=0.35
                )
            ]
        else:
            segments = []
        
        return segments

    async def export_analytics_report(
        self,
        report_type: str,
        period: str = "30d",
        format: str = "json"
    ) -> Dict[str, Any]:
        """导出分析报告"""
        
        # 简化实现，返回基本报告数据
        report_data = {
            "report_type": report_type,
            "period": period,
            "generated_at": datetime.now().isoformat(),
            "data": {}
        }
        
        if report_type == "user_analytics":
            # 用户分析报告
            report_data["data"] = {
                "total_users": 1000,
                "active_users": 600,
                "new_users": 50
            }
        elif report_type == "reading_analytics":
            # 阅读分析报告
            report_data["data"] = {
                "total_reading_time": 50000,
                "books_read": 2000,
                "average_session": 45
            }
        
        return report_data

    async def get_dashboard_summary(
        self,
        user_id: Optional[uuid.UUID] = None
    ) -> DashboardSummaryResponse:
        """获取仪表板摘要"""
        
        # 获取关键指标
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        # 今日活跃用户
        today_active_query = select(func.count(func.distinct(ReadingProgress.user_id))).where(
            func.date(ReadingProgress.updated_at) == today
        )
        today_active_result = await self.db.execute(today_active_query)
        today_active_users = today_active_result.scalar() or 0
        
        # 昨日活跃用户
        yesterday_active_query = select(func.count(func.distinct(ReadingProgress.user_id))).where(
            func.date(ReadingProgress.updated_at) == yesterday
        )
        yesterday_active_result = await self.db.execute(yesterday_active_query)
        yesterday_active_users = yesterday_active_result.scalar() or 0
        
        # 今日阅读时长
        today_reading_query = select(func.sum(ReadingProgress.reading_time)).where(
            func.date(ReadingProgress.updated_at) == today
        )
        today_reading_result = await self.db.execute(today_reading_query)
        today_reading_time = today_reading_result.scalar() or 0
        
        # 今日新增用户
        today_new_users_query = select(func.count()).select_from(User).where(
            func.date(User.created_at) == today
        )
        today_new_users_result = await self.db.execute(today_new_users_query)
        today_new_users = today_new_users_result.scalar() or 0
        
        return DashboardSummaryResponse(
            active_users_today=today_active_users,
            active_users_change=today_active_users - yesterday_active_users,
            total_reading_time_today=today_reading_time,
            new_users_today=today_new_users,
            popular_categories=["玄幻", "都市", "历史"],  # 简化数据
            trending_novels=["小说1", "小说2", "小说3"]  # 简化数据
        )

    async def track_event(
        self,
        user_id: uuid.UUID,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> None:
        """追踪事件"""
        
        # 这里简化实现，实际项目中应该保存到事件表
        # 用于后续的行为分析
        pass