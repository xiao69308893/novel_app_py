# app/api/v1/__init__.py
# -*- coding: utf-8 -*-
"""
API v1路由集合
"""

from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router
from .novels import router as novels_router
from .chapters import router as chapters_router
from .bookshelf import router as bookshelf_router
from .reader import router as reader_router
from .translation import router as translation_router
from .admin import router as admin_router
from .comments import router as comments_router
from .search import router as search_router
from .recommendations import router as recommendations_router
from .analytics import router as analytics_router

# 创建API路由器
api_router = APIRouter()

# 注册各个模块的路由
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["认证"]
)

api_router.include_router(
    users_router,
    prefix="/user",
    tags=["用户"]
)

api_router.include_router(
    novels_router,
    prefix="/novels",
    tags=["小说"]
)

api_router.include_router(
    chapters_router,
    prefix="/chapters",
    tags=["章节"]
)

api_router.include_router(
    bookshelf_router,
    prefix="/bookshelf",
    tags=["书架"]
)

api_router.include_router(
    reader_router,
    prefix="/reader",
    tags=["阅读器"]
)

# api_router.include_router(
#     translation_router,
#     prefix="/translation",
#     tags=["翻译"]
# )
#
# api_router.include_router(
#     admin_router,
#     prefix="/admin",
#     tags=["管理员"]
# )
#
# api_router.include_router(
#     comments_router,
#     prefix="/comments",
#     tags=["评论"]
# )
#
# api_router.include_router(
#     search_router,
#     prefix="/search",
#     tags=["搜索"]
# )
#
# api_router.include_router(
#     recommendations_router,
#     prefix="/recommendations",
#     tags=["推荐"]
# )
#
# api_router.include_router(
#     analytics_router,
#     prefix="/analytics",
#     tags=["数据分析"]
# )
