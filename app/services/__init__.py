# app/services/__init__.py
# -*- coding: utf-8 -*-
"""
业务逻辑层
"""

from .base import BaseService
from .auth_service import AuthService
from .user_service import UserService
from .novel_service import NovelService

__all__ = [
    "BaseService",
    "AuthService",
    "UserService",
    "NovelService"
]