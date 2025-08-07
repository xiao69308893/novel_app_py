# app/models/__init__.py
# -*- coding: utf-8 -*-
"""
数据模型模块
"""

from .base import Base, BaseModel, TimestampMixin, UUIDMixin
from .user import User, UserProfile, UserSettings, UserStatistics, LoginLog
from .novel import Novel, Category, Tag, NovelTag, Author, NovelRating
from .chapter import Chapter, ReadingProgress, ChapterPurchase, UserFavorite, Bookmark
from .comment import Comment, CommentLike
from .translation import (
    AIModel, TranslationConfig, TranslationProject,
    TranslatedNovel, TranslatedChapter, CharacterMapping,
    TranslationTask
)

__all__ = [
    "Base", "BaseModel", "TimestampMixin", "UUIDMixin",
    "User", "UserProfile", "UserSettings", "UserStatistics", "LoginLog",
    "Novel", "Category", "Tag", "NovelTag", "Author", "NovelRating",
    "Chapter", "ReadingProgress", "ChapterPurchase", "UserFavorite",
    "Bookmark",
    "Comment", "CommentLike",
    "AIModel", "TranslationConfig", "TranslationProject",
    "TranslatedNovel", "TranslatedChapter", "CharacterMapping",
    "TranslationTask"
]






