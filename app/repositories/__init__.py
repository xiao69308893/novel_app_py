# app/repositories/__init__.py
# -*- coding: utf-8 -*-
"""
数据访问层
"""

from .base import BaseRepository
from .user_repo import UserRepository
from .novel_repo import NovelRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "NovelRepository"
]