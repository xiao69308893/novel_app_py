# app/ai/base.py
# -*- coding: utf-8 -*-
"""
AI服务基础类
定义AI功能的通用接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AIModelType(Enum):
    """AI模型类型"""
    TEXT_GENERATION = "text_generation"
    TEXT_CLASSIFICATION = "text_classification"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    CONTENT_MODERATION = "content_moderation"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    RECOMMENDATION = "recommendation"


class AIProvider(Enum):
    """AI服务提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    BAIDU = "baidu"
    ALIBABA = "alibaba"
    TENCENT = "tencent"
    LOCAL = "local"


class AIResponse:
    """AI响应结果"""
    
    def __init__(
        self,
        success: bool,
        data: Any = None,
        error: str = None,
        model: str = None,
        usage: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ):
        self.success = success
        self.data = data
        self.error = error
        self.model = model
        self.usage = usage or {}
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "model": self.model,
            "usage": self.usage,
            "metadata": self.metadata
        }


class BaseAIService(ABC):
    """AI服务基础类"""
    
    def __init__(
        self,
        provider: AIProvider,
        model_name: str,
        api_key: str = None,
        api_base: str = None,
        **kwargs
    ):
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key
        self.api_base = api_base
        self.config = kwargs
        self._client = None
    
    @abstractmethod
    async def initialize(self) -> bool:
        """初始化AI服务"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass
    
    @abstractmethod
    async def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        pass
    
    def _create_response(
        self,
        success: bool,
        data: Any = None,
        error: str = None,
        usage: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ) -> AIResponse:
        """创建响应对象"""
        return AIResponse(
            success=success,
            data=data,
            error=error,
            model=self.model_name,
            usage=usage,
            metadata=metadata
        )


class TextGenerationService(BaseAIService):
    """文本生成服务"""
    
    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> AIResponse:
        """生成文本"""
        pass
    
    @abstractmethod
    async def complete_text(
        self,
        text: str,
        max_tokens: int = 500,
        **kwargs
    ) -> AIResponse:
        """文本补全"""
        pass


class TextClassificationService(BaseAIService):
    """文本分类服务"""
    
    @abstractmethod
    async def classify_text(
        self,
        text: str,
        categories: List[str] = None,
        **kwargs
    ) -> AIResponse:
        """文本分类"""
        pass
    
    @abstractmethod
    async def analyze_sentiment(
        self,
        text: str,
        **kwargs
    ) -> AIResponse:
        """情感分析"""
        pass


class ContentModerationService(BaseAIService):
    """内容审核服务"""
    
    @abstractmethod
    async def moderate_content(
        self,
        content: str,
        content_type: str = "text",
        **kwargs
    ) -> AIResponse:
        """内容审核"""
        pass
    
    @abstractmethod
    async def detect_sensitive_content(
        self,
        content: str,
        **kwargs
    ) -> AIResponse:
        """敏感内容检测"""
        pass


class TranslationService(BaseAIService):
    """翻译服务"""
    
    @abstractmethod
    async def translate_text(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        **kwargs
    ) -> AIResponse:
        """文本翻译"""
        pass
    
    @abstractmethod
    async def detect_language(
        self,
        text: str,
        **kwargs
    ) -> AIResponse:
        """语言检测"""
        pass


class SummarizationService(BaseAIService):
    """摘要生成服务"""
    
    @abstractmethod
    async def summarize_text(
        self,
        text: str,
        max_length: int = 200,
        **kwargs
    ) -> AIResponse:
        """文本摘要"""
        pass
    
    @abstractmethod
    async def extract_keywords(
        self,
        text: str,
        max_keywords: int = 10,
        **kwargs
    ) -> AIResponse:
        """关键词提取"""
        pass


class RecommendationService(BaseAIService):
    """推荐服务"""
    
    @abstractmethod
    async def get_content_recommendations(
        self,
        user_id: int,
        content_type: str,
        limit: int = 10,
        **kwargs
    ) -> AIResponse:
        """内容推荐"""
        pass
    
    @abstractmethod
    async def get_similar_content(
        self,
        content_id: int,
        content_type: str,
        limit: int = 10,
        **kwargs
    ) -> AIResponse:
        """相似内容推荐"""
        pass


class AIServiceFactory:
    """AI服务工厂"""
    
    _services = {}
    
    @classmethod
    def register_service(
        cls,
        service_type: AIModelType,
        provider: AIProvider,
        service_class: type
    ):
        """注册服务"""
        key = f"{service_type.value}_{provider.value}"
        cls._services[key] = service_class
    
    @classmethod
    def create_service(
        cls,
        service_type: AIModelType,
        provider: AIProvider,
        **kwargs
    ) -> Optional[BaseAIService]:
        """创建服务实例"""
        key = f"{service_type.value}_{provider.value}"
        service_class = cls._services.get(key)
        
        if not service_class:
            logger.error(f"未找到服务: {key}")
            return None
        
        try:
            return service_class(provider=provider, **kwargs)
        except Exception as e:
            logger.error(f"创建服务失败: {e}")
            return None
    
    @classmethod
    def get_available_services(cls) -> List[str]:
        """获取可用服务列表"""
        return list(cls._services.keys())


class AIServiceManager:
    """AI服务管理器"""
    
    def __init__(self):
        self._services: Dict[str, BaseAIService] = {}
        self._initialized = False
    
    async def initialize(self, config: Dict[str, Any]):
        """初始化所有服务"""
        try:
            for service_name, service_config in config.items():
                service = AIServiceFactory.create_service(**service_config)
                if service:
                    await service.initialize()
                    self._services[service_name] = service
                    logger.info(f"AI服务初始化成功: {service_name}")
            
            self._initialized = True
            logger.info("AI服务管理器初始化完成")
        except Exception as e:
            logger.error(f"AI服务管理器初始化失败: {e}")
    
    def get_service(self, service_name: str) -> Optional[BaseAIService]:
        """获取服务实例"""
        return self._services.get(service_name)
    
    async def health_check_all(self) -> Dict[str, bool]:
        """检查所有服务健康状态"""
        results = {}
        for name, service in self._services.items():
            try:
                results[name] = await service.health_check()
            except Exception as e:
                logger.error(f"服务健康检查失败 {name}: {e}")
                results[name] = False
        return results
    
    def get_service_list(self) -> List[str]:
        """获取服务列表"""
        return list(self._services.keys())
    
    @property
    def is_initialized(self) -> bool:
        """是否已初始化"""
        return self._initialized


# 全局AI服务管理器实例
ai_service_manager = AIServiceManager()