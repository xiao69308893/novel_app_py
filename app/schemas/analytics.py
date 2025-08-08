# app/schemas/analytics.py
# -*- coding: utf-8 -*-
"""
数据分析相关的Pydantic模式
定义分析数据的请求和响应结构
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime
from pydantic import BaseModel, Field


# 用户分析概览
class UserAnalyticsOverviewResponse(BaseModel):
    """用户分析概览响应"""
    user_id: str = Field(..., description="用户ID")
    registration_date: date = Field(..., description="注册日期")
    days_since_registration: int = Field(..., description="注册天数")
    books_read: int = Field(..., description="已读书籍数")
    total_reading_time: int = Field(..., description="总阅读时间(分钟)")
    average_reading_progress: float = Field(..., description="平均阅读进度")
    favorite_count: int = Field(..., description="收藏数")
    comment_count: int = Field(..., description="评论数")
    purchase_count: int = Field(..., description="购买次数")
    total_spent: float = Field(..., description="总消费金额")
    last_active_date: Optional[date] = Field(None, description="最后活跃日期")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "registration_date": "2024-01-01",
                "days_since_registration": 30,
                "books_read": 15,
                "total_reading_time": 1800,
                "average_reading_progress": 0.75,
                "favorite_count": 25,
                "comment_count": 50,
                "purchase_count": 10,
                "total_spent": 99.99,
                "last_active_date": "2024-01-30"
            }
        }


# 阅读统计
class ReadingStatsResponse(BaseModel):
    """阅读统计响应"""
    period: str = Field(..., description="统计周期")
    total_reading_time: int = Field(..., description="总阅读时间(分钟)")
    books_read: int = Field(..., description="阅读书籍数")
    chapters_read: int = Field(..., description="阅读章节数")
    average_daily_time: float = Field(..., description="日均阅读时间(分钟)")
    reading_trend: List[Dict[str, Any]] = Field(..., description="阅读趋势")

    class Config:
        json_schema_extra = {
            "example": {
                "period": "30d",
                "total_reading_time": 1800,
                "books_read": 15,
                "chapters_read": 150,
                "average_daily_time": 60.0,
                "reading_trend": [
                    {"date": "2024-01-01", "reading_time": 120},
                    {"date": "2024-01-02", "reading_time": 90}
                ]
            }
        }


# 阅读习惯
class ReadingHabitsResponse(BaseModel):
    """阅读习惯响应"""
    hour_distribution: List[Dict[str, Any]] = Field(..., description="小时分布")
    weekday_distribution: List[Dict[str, Any]] = Field(..., description="星期分布")
    average_session_duration: float = Field(..., description="平均会话时长(分钟)")
    longest_session_duration: float = Field(..., description="最长会话时长(分钟)")
    total_reading_sessions: int = Field(..., description="总阅读会话数")
    most_active_hour: int = Field(..., description="最活跃小时")
    most_active_weekday: int = Field(..., description="最活跃星期")

    class Config:
        json_schema_extra = {
            "example": {
                "hour_distribution": [
                    {"hour": 9, "count": 15},
                    {"hour": 21, "count": 25}
                ],
                "weekday_distribution": [
                    {"weekday": 0, "count": 10},
                    {"weekday": 6, "count": 20}
                ],
                "average_session_duration": 45.5,
                "longest_session_duration": 180.0,
                "total_reading_sessions": 100,
                "most_active_hour": 21,
                "most_active_weekday": 6
            }
        }


# 阅读偏好
class ReadingPreferencesResponse(BaseModel):
    """阅读偏好响应"""
    category_preferences: List[Dict[str, Any]] = Field(..., description="分类偏好")
    author_preferences: List[Dict[str, Any]] = Field(..., description="作者偏好")
    tag_preferences: List[Dict[str, Any]] = Field(..., description="标签偏好")
    average_book_length: int = Field(..., description="平均书籍长度")
    preferred_length_range: Dict[str, int] = Field(..., description="偏好长度范围")

    class Config:
        json_schema_extra = {
            "example": {
                "category_preferences": [
                    {"category": "玄幻", "count": 10, "avg_progress": 0.8},
                    {"category": "都市", "count": 5, "avg_progress": 0.9}
                ],
                "author_preferences": [
                    {"author": "作者A", "count": 8},
                    {"author": "作者B", "count": 6}
                ],
                "tag_preferences": [
                    {"tag": "修仙", "count": 12},
                    {"tag": "爱情", "count": 8}
                ],
                "average_book_length": 500000,
                "preferred_length_range": {"min": 200000, "max": 800000}
            }
        }


# 小说统计
class NovelStatsResponse(BaseModel):
    """小说统计响应"""
    novel_id: str = Field(..., description="小说ID")
    title: str = Field(..., description="小说标题")
    author: str = Field(..., description="作者")
    period: str = Field(..., description="统计周期")
    unique_readers: int = Field(..., description="独立读者数")
    total_reading_time: int = Field(..., description="总阅读时间(分钟)")
    average_progress: float = Field(..., description="平均阅读进度")
    new_favorites: int = Field(..., description="新增收藏数")
    new_comments: int = Field(..., description="新增评论数")
    reading_trend: List[Dict[str, Any]] = Field(..., description="阅读趋势")
    total_views: int = Field(..., description="总浏览量")
    rating: float = Field(..., description="评分")

    class Config:
        json_schema_extra = {
            "example": {
                "novel_id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "修仙传说",
                "author": "作者A",
                "period": "30d",
                "unique_readers": 500,
                "total_reading_time": 15000,
                "average_progress": 0.65,
                "new_favorites": 50,
                "new_comments": 25,
                "reading_trend": [
                    {"date": "2024-01-01", "readers": 20},
                    {"date": "2024-01-02", "readers": 25}
                ],
                "total_views": 10000,
                "rating": 4.5
            }
        }


# 作者统计
class AuthorStatsResponse(BaseModel):
    """作者统计响应"""
    author: str = Field(..., description="作者名称")
    period: str = Field(..., description="统计周期")
    novel_count: int = Field(..., description="小说数量")
    total_views: int = Field(..., description="总浏览量")
    average_rating: float = Field(..., description="平均评分")
    total_words: int = Field(..., description="总字数")
    unique_readers: int = Field(..., description="独立读者数")
    total_reading_time: int = Field(..., description="总阅读时间(分钟)")
    total_favorites: int = Field(..., description="总收藏数")

    class Config:
        json_schema_extra = {
            "example": {
                "author": "作者A",
                "period": "30d",
                "novel_count": 5,
                "total_views": 50000,
                "average_rating": 4.3,
                "total_words": 2500000,
                "unique_readers": 1200,
                "total_reading_time": 75000,
                "total_favorites": 300
            }
        }


# 分类统计
class CategoryStatsResponse(BaseModel):
    """分类统计响应"""
    category: str = Field(..., description="分类名称")
    novel_count: int = Field(..., description="小说数量")
    total_views: int = Field(..., description="总浏览量")
    average_rating: float = Field(..., description="平均评分")
    unique_readers: int = Field(..., description="独立读者数")
    period: str = Field(..., description="统计周期")

    class Config:
        json_schema_extra = {
            "example": {
                "category": "玄幻",
                "novel_count": 100,
                "total_views": 500000,
                "average_rating": 4.2,
                "unique_readers": 5000,
                "period": "30d"
            }
        }


# 收入统计
class RevenueStatsResponse(BaseModel):
    """收入统计响应"""
    period: str = Field(..., description="统计周期")
    total_revenue: float = Field(..., description="总收入")
    total_transactions: int = Field(..., description="总交易数")
    paying_users: int = Field(..., description="付费用户数")
    average_transaction: float = Field(..., description="平均交易金额")
    revenue_trend: List[Dict[str, Any]] = Field(..., description="收入趋势")

    class Config:
        json_schema_extra = {
            "example": {
                "period": "30d",
                "total_revenue": 5000.0,
                "total_transactions": 200,
                "paying_users": 150,
                "average_transaction": 25.0,
                "revenue_trend": [
                    {"date": "2024-01-01", "revenue": 150.0, "transactions": 6},
                    {"date": "2024-01-02", "revenue": 200.0, "transactions": 8}
                ]
            }
        }


# 行为分析
class BehaviorAnalysisResponse(BaseModel):
    """行为分析响应"""
    user_id: str = Field(..., description="用户ID")
    period: str = Field(..., description="分析周期")
    behavior_stats: Dict[str, int] = Field(..., description="行为统计")
    engagement_score: float = Field(..., description="参与度分数")
    activity_level: str = Field(..., description="活跃度等级")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "period": "30d",
                "behavior_stats": {
                    "reading_sessions": 50,
                    "books_started": 10,
                    "books_completed": 3,
                    "chapters_read": 150,
                    "comments_posted": 25,
                    "books_favorited": 8,
                    "chapters_purchased": 20
                },
                "engagement_score": 0.75,
                "activity_level": "active"
            }
        }


# 阅读趋势
# class ReadingTrendResponse(BaseModel):
#     """阅读趋势响应"""
#     date: date = Field(..., description="日期")
#     active_readers: int = Field(..., description="活跃读者数")
#     total_reading_time: int = Field(..., description="总阅读时间(分钟)")
#     reading_sessions: int = Field(..., description="阅读会话数")
#
#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "date": "2024-01-01",
#                 "active_readers": 500,
#                 "total_reading_time": 15000,
#                 "reading_sessions": 800
#             }
#         }
class HotTrendResponse(BaseModel):
    """热门趋势响应"""
    novel_id: str = Field(..., description="小说ID")
    title: str = Field(..., description="小说标题")
    author: str = Field(..., description="作者")
    category: str = Field(..., description="分类")
    readers: int = Field(..., description="读者数")
    reading_time: int = Field(..., description="阅读时间(分钟)")
    trend_score: float = Field(..., description="趋势分数")

    class Config:
        json_schema_extra = {
            "example": {
                "novel_id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "修仙传说",
                "author": "作者A",
                "category": "玄幻",
                "readers": 500,
                "reading_time": 15000,
                "trend_score": 85.5
            }
        }


# 小说对比
class NovelComparisonResponse(BaseModel):
    """小说对比响应"""
    novel_id: str = Field(..., description="小说ID")
    title: str = Field(..., description="小说标题")
    author: str = Field(..., description="作者")
    category: str = Field(..., description="分类")
    readers: int = Field(..., description="读者数")
    reading_time: int = Field(..., description="阅读时间(分钟)")
    average_progress: float = Field(..., description="平均阅读进度")
    rating: float = Field(..., description="评分")
    view_count: int = Field(..., description="浏览量")

    class Config:
        json_schema_extra = {
            "example": {
                "novel_id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "修仙传说",
                "author": "作者A",
                "category": "玄幻",
                "readers": 500,
                "reading_time": 15000,
                "average_progress": 0.65,
                "rating": 4.5,
                "view_count": 10000
            }
        }


# 作者对比
class AuthorComparisonResponse(BaseModel):
    """作者对比响应"""
    author: str = Field(..., description="作者名称")
    novel_count: int = Field(..., description="小说数量")
    total_views: int = Field(..., description="总浏览量")
    average_rating: float = Field(..., description="平均评分")
    readers: int = Field(..., description="读者数")

    class Config:
        json_schema_extra = {
            "example": {
                "author": "作者A",
                "novel_count": 5,
                "total_views": 50000,
                "average_rating": 4.3,
                "readers": 1200
            }
        }


# 阅读热力图
class ReadingHeatmapResponse(BaseModel):
    """阅读热力图响应"""
    user_id: Optional[str] = Field(None, description="用户ID")
    period: str = Field(..., description="统计周期")
    heatmap_data: List[Dict[str, Any]] = Field(..., description="热力图数据")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "period": "30d",
                "heatmap_data": [
                    {"hour": 9, "weekday": 1, "activity": 15},
                    {"hour": 21, "weekday": 6, "activity": 25}
                ]
            }
        }


# 阅读漏斗
class ReadingFunnelResponse(BaseModel):
    """阅读漏斗响应"""
    period: str = Field(..., description="统计周期")
    funnel_steps: List[Dict[str, Any]] = Field(..., description="漏斗步骤")
    overall_conversion_rate: float = Field(..., description="总转化率")

    class Config:
        json_schema_extra = {
            "example": {
                "period": "30d",
                "funnel_steps": [
                    {"step": "访问", "users": 10000, "conversion_rate": 1.0},
                    {"step": "开始阅读", "users": 5000, "conversion_rate": 0.5},
                    {"step": "完成第一章", "users": 3000, "conversion_rate": 0.6},
                    {"step": "收藏", "users": 1500, "conversion_rate": 0.5},
                    {"step": "付费", "users": 300, "conversion_rate": 0.2}
                ],
                "overall_conversion_rate": 0.03
            }
        }


# 用户留存
class UserRetentionResponse(BaseModel):
    """用户留存响应"""
    cohort_period: str = Field(..., description="队列周期")
    cohort_size: int = Field(..., description="队列大小")
    retention_rates: Dict[str, float] = Field(..., description="留存率")

    class Config:
        json_schema_extra = {
            "example": {
                "cohort_period": "第1周",
                "cohort_size": 100,
                "retention_rates": {
                    "day_1": 0.8,
                    "day_7": 0.6,
                    "day_30": 0.4
                }
            }
        }


# 用户分群
class UserSegmentResponse(BaseModel):
    """用户分群响应"""
    segment_name: str = Field(..., description="分群名称")
    user_count: int = Field(..., description="用户数量")
    characteristics: List[str] = Field(..., description="特征描述")
    percentage: float = Field(..., description="占比")

    class Config:
        json_schema_extra = {
            "example": {
                "segment_name": "重度用户",
                "user_count": 150,
                "characteristics": ["日均阅读时间>2小时", "月阅读书籍>5本"],
                "percentage": 0.15
            }
        }


# 仪表板摘要
class DashboardSummaryResponse(BaseModel):
    """仪表板摘要响应"""
    active_users_today: int = Field(..., description="今日活跃用户")
    active_users_change: int = Field(..., description="活跃用户变化")
    total_reading_time_today: int = Field(..., description="今日总阅读时间(分钟)")
    new_users_today: int = Field(..., description="今日新增用户")
    popular_categories: List[str] = Field(..., description="热门分类")
    trending_novels: List[str] = Field(..., description="趋势小说")

    class Config:
        json_schema_extra = {
            "example": {
                "active_users_today": 1500,
                "active_users_change": 50,
                "total_reading_time_today": 45000,
                "new_users_today": 25,
                "popular_categories": ["玄幻", "都市", "历史"],
                "trending_novels": ["修仙传说", "都市之王", "历史风云"]
            }
        }


# 分析请求
class AnalyticsRequest(BaseModel):
    """分析请求"""
    period: str = Field(default="30d", description="统计周期")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")

    class Config:
        json_schema_extra = {
            "example": {
                "period": "30d",
                "start_date": "2024-01-01",
                "end_date": "2024-01-31"
            }
        }


# 对比请求
class ComparisonRequest(BaseModel):
    """对比请求"""
    items: List[str] = Field(..., description="对比项目列表")
    period: str = Field(default="30d", description="统计周期")

    class Config:
        json_schema_extra = {
            "example": {
                "items": ["123e4567-e89b-12d3-a456-426614174000", "456e7890-e89b-12d3-a456-426614174001"],
                "period": "30d"
            }
        }