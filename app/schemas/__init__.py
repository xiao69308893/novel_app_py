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
    UserResponse, UserProfileResponse, UserSettingsResponse,
    UserStatsResponse, UserUpdateRequest
)
from .novel import (
    NovelResponse, NovelListResponse, ChapterResponse,
    ChapterListResponse, CommentResponse, CommentCreateRequest
)

__all__ = [
    "BaseResponse", "ListResponse", "PaginationInfo", "ErrorResponse",
    "LoginRequest", "RegisterRequest", "TokenResponse",
    "PasswordChangeRequest", "SMSCodeRequest", "EmailCodeRequest",
    "UserResponse", "UserProfileResponse", "UserSettingsResponse",
    "UserStatsResponse", "UserUpdateRequest",
    "NovelResponse", "NovelListResponse", "ChapterResponse",
    "ChapterListResponse", "CommentResponse", "CommentCreateRequest"
]


