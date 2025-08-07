

# app/config/ai_config.py
# -*- coding: utf-8 -*-
"""
AI模型配置和管理
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum

from .settings import settings


class AIProvider(str, Enum):
    """AI提供商枚举"""
    DEEPSEEK = "deepseek"
    ZHIPU = "zhipu"
    OLLAMA = "ollama"
    OPENAI = "openai"
    CLAUDE = "claude"


class AICapability(str, Enum):
    """AI能力枚举"""
    TRANSLATION = "translation"
    OUTLINE_GENERATION = "outline_generation"
    CHARACTER_ANALYSIS = "character_analysis"
    QUALITY_CHECK = "quality_check"
    SUMMARY = "summary"


class AIModelConfig(BaseModel):
    """AI模型配置"""

    name: str = Field(description="模型名称")
    display_name: str = Field(description="显示名称")
    provider: AIProvider = Field(description="提供商")
    model_id: str = Field(description="模型ID")
    version: Optional[str] = Field(default=None, description="模型版本")

    # 模型能力
    capabilities: List[AICapability] = Field(default=[], description="模型能力")
    supported_languages: List[str] = Field(default=["zh-CN", "en-US"], description="支持的语言")

    # 性能参数
    max_tokens: int = Field(default=4000, description="最大token数")
    max_requests_per_minute: int = Field(default=60, description="每分钟最大请求数")
    max_requests_per_day: int = Field(default=10000, description="每日最大请求数")
    max_concurrent_requests: int = Field(default=5, description="最大并发请求数")

    # API配置
    api_endpoint: Optional[str] = Field(default=None, description="API端点")
    api_key: Optional[str] = Field(default=None, description="API密钥")
    api_version: Optional[str] = Field(default=None, description="API版本")
    timeout_seconds: int = Field(default=30, description="请求超时时间")

    # 成本配置
    cost_per_1k_input_tokens: float = Field(default=0.0, description="每1K输入token成本")
    cost_per_1k_output_tokens: float = Field(default=0.0, description="每1K输出token成本")

    # 质量配置
    default_temperature: float = Field(default=0.7, description="默认温度参数")
    default_top_p: float = Field(default=0.9, description="默认top_p参数")
    default_max_tokens: int = Field(default=2000, description="默认最大输出token")

    # 状态管理
    is_active: bool = Field(default=True, description="是否激活")
    is_default: bool = Field(default=False, description="是否为默认模型")
    priority: int = Field(default=1, description="优先级，数字越小优先级越高")


class AIModelsConfig:
    """AI模型配置管理器"""

    def __init__(self):
        self._models: Dict[str, AIModelConfig] = {}
        self._initialize_default_models()

    def _initialize_default_models(self):
        """初始化默认模型配置"""

        # DeepSeek模型配置
        if settings.DEEPSEEK_API_KEY:
            deepseek_config = AIModelConfig(
                name="deepseek-chat",
                display_name="DeepSeek Chat",
                provider=AIProvider.DEEPSEEK,
                model_id="deepseek-chat",
                capabilities=[
                    AICapability.TRANSLATION,
                    AICapability.OUTLINE_GENERATION,
                    AICapability.CHARACTER_ANALYSIS,
                    AICapability.SUMMARY
                ],
                supported_languages=["zh-CN", "en-US", "ja-JP"],
                max_tokens=4000,
                api_endpoint=f"{settings.DEEPSEEK_BASE_URL}/v1/chat/completions",
                api_key=settings.DEEPSEEK_API_KEY,
                cost_per_1k_input_tokens=0.0014,
                cost_per_1k_output_tokens=0.0028,
                is_default=True,
                priority=1
            )
            self._models["deepseek-chat"] = deepseek_config

        # 智谱AI模型配置
        if settings.ZHIPU_API_KEY:
            zhipu_config = AIModelConfig(
                name="glm-4",
                display_name="智谱 GLM-4",
                provider=AIProvider.ZHIPU,
                model_id="glm-4",
                capabilities=[
                    AICapability.TRANSLATION,
                    AICapability.QUALITY_CHECK,
                    AICapability.SUMMARY
                ],
                supported_languages=["zh-CN", "en-US"],
                max_tokens=8000,
                api_endpoint=f"{settings.ZHIPU_BASE_URL}chat/completions",
                api_key=settings.ZHIPU_API_KEY,
                cost_per_1k_input_tokens=0.005,
                cost_per_1k_output_tokens=0.015,
                priority=2
            )
            self._models["glm-4"] = zhipu_config

        # Ollama本地模型配置
        ollama_config = AIModelConfig(
            name="llama3.1-8b",
            display_name="Llama 3.1 8B",
            provider=AIProvider.OLLAMA,
            model_id="llama3.1:8b",
            capabilities=[
                AICapability.TRANSLATION,
                AICapability.OUTLINE_GENERATION
            ],
            supported_languages=["zh-CN", "en-US"],
            max_tokens=4096,
            api_endpoint=f"{settings.OLLAMA_BASE_URL}/api/chat",
            cost_per_1k_input_tokens=0.0,  # 本地模型无成本
            cost_per_1k_output_tokens=0.0,
            priority=3
        )
        self._models["llama3.1-8b"] = ollama_config

    def get_model(self, name: str) -> Optional[AIModelConfig]:
        """获取指定模型配置"""
        return self._models.get(name)

    def get_models_by_capability(self, capability: AICapability) -> List[AIModelConfig]:
        """根据能力获取模型列表"""
        return [
            model for model in self._models.values()
            if capability in model.capabilities and model.is_active
        ]

    def get_default_model(self, capability: AICapability) -> Optional[AIModelConfig]:
        """获取指定能力的默认模型"""
        models = self.get_models_by_capability(capability)

        # 优先返回标记为默认的模型
        default_models = [m for m in models if m.is_default]
        if default_models:
            return min(default_models, key=lambda x: x.priority)

        # 如果没有默认模型，返回优先级最高的模型
        if models:
            return min(models, key=lambda x: x.priority)

        return None

    def get_all_models(self) -> Dict[str, AIModelConfig]:
        """获取所有模型配置"""
        return self._models.copy()

    def add_model(self, model: AIModelConfig) -> None:
        """添加模型配置"""
        self._models[model.name] = model

    def remove_model(self, name: str) -> bool:
        """移除模型配置"""
        if name in self._models:
            del self._models[name]
            return True
        return False

    def update_model(self, name: str, updates: Dict[str, Any]) -> bool:
        """更新模型配置"""
        if name in self._models:
            model_dict = self._models[name].dict()
            model_dict.update(updates)
            self._models[name] = AIModelConfig(**model_dict)
            return True
        return False


# 创建全局AI模型配置实例
ai_models_config = AIModelsConfig()