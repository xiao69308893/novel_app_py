# app/ai/__init__.py
# -*- coding: utf-8 -*-
"""
AI服务模块
"""

from .base import (
    AIServiceManager,
    AIServiceFactory,
    AIProvider,
    AIModelType,
    AIResponse
)

# 导入具体的AI服务实现
from .novel_ai import (
    NovelContentGenerator,
    NovelRecommendationEngine,
    NovelContentAnalyzer
)

from .translation_ai import (
    MultiLanguageTranslator,
    NovelTranslationManager
)

from .moderation_ai import (
    ContentModerator,
    NovelContentModerator,
    RiskLevel,
    ViolationType
)

__all__ = [
    # 基础类
    "AIServiceManager",
    "AIServiceFactory", 
    "AIProvider",
    "AIModelType",
    "AIResponse",
    
    # 小说AI服务
    "NovelContentGenerator",
    "NovelRecommendationEngine", 
    "NovelContentAnalyzer",
    
    # 翻译服务
    "MultiLanguageTranslator",
    "NovelTranslationManager",
    
    # 内容审核服务
    "ContentModerator",
    "NovelContentModerator",
    "RiskLevel",
    "ViolationType"
]