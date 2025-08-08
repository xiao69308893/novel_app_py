# app/schemas/__init__.py
# -*- coding: utf-8 -*-
"""
Pydantic模式模块
定义请求和响应的数据结构
"""

from .base import BaseResponse, ListResponse, PaginationInfo, ErrorResponse
from .auth import (
    LoginRequest, RegisterRequest, TokenResponse,
    PasswordChangeRequest, SMSCodeRequest, EmailCodeRequest
)
from .user import (
    UserProfileResponse, UserSettingsResponse,
    UserStatisticsResponse, UserProfileUpdate
)
from .novel import (
    NovelBasicResponse, NovelDetailResponse, NovelListResponse, 
    ChapterBasicResponse, ChapterDetailResponse, ChapterListResponse, 
    CommentResponse, CommentCreateRequest, NovelSearchRequest,
    CategoryResponse, TagResponse, AuthorResponse
)
from .analytics import (
    UserAnalyticsOverviewResponse, ReadingStatsResponse, ReadingHabitsResponse,
    ReadingPreferencesResponse, NovelStatsResponse, AuthorStatsResponse,
    CategoryStatsResponse, RevenueStatsResponse, BehaviorAnalysisResponse, HotTrendResponse, NovelComparisonResponse,
    AuthorComparisonResponse, ReadingHeatmapResponse, ReadingFunnelResponse,
    UserRetentionResponse, UserSegmentResponse, DashboardSummaryResponse,
    AnalyticsRequest, ComparisonRequest
)

__all__ = [
    "BaseResponse", "ListResponse", "PaginationInfo", "ErrorResponse",
    "LoginRequest", "RegisterRequest", "TokenResponse",
    "PasswordChangeRequest", "SMSCodeRequest", "EmailCodeRequest",
    "UserProfileResponse", "UserSettingsResponse",
    "UserStatisticsResponse", "UserProfileUpdate",
    "NovelBasicResponse", "NovelDetailResponse", "NovelListResponse",
    "ChapterBasicResponse", "ChapterDetailResponse", "ChapterListResponse", 
    "CommentResponse", "CommentCreateRequest", "NovelSearchRequest",
    "CategoryResponse", "TagResponse", "AuthorResponse",
    "UserAnalyticsOverviewResponse", "ReadingStatsResponse", "ReadingHabitsResponse",
    "ReadingPreferencesResponse", "NovelStatsResponse", "AuthorStatsResponse",
    "CategoryStatsResponse", "RevenueStatsResponse", "BehaviorAnalysisResponse",
    "ReadingTrendResponse", "HotTrendResponse", "NovelComparisonResponse",
    "AuthorComparisonResponse", "ReadingHeatmapResponse", "ReadingFunnelResponse",
    "UserRetentionResponse", "UserSegmentResponse", "DashboardSummaryResponse",
    "AnalyticsRequest", "ComparisonRequest"
]


