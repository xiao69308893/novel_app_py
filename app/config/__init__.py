# app/config/__init__.py
# -*- coding: utf-8 -*-
"""
配置模块
"""

from .settings import settings
from .database import engine, SessionLocal, get_db
from .ai_config import ai_models_config

__all__ = [
    "settings",
    "engine",
    "SessionLocal",
    "get_db",
    "ai_models_config"
]

---

# app/config/settings.py
# -*- coding: utf-8 -*-
"""
应用核心配置管理
使用Pydantic Settings进行环境变量读取和验证
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import AnyHttpUrl, BaseSettings, EmailStr, validator, Field
import secrets
import os
from pathlib import Path


class Settings(BaseSettings):
    """应用设置类"""

    # 基础应用配置
    APP_NAME: str = "小说阅读APP"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)

    # 服务器配置
    SERVER_NAME: str = "localhost"
    SERVER_HOST: AnyHttpUrl = "http://localhost"

    # CORS配置
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:8000"
    ]

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """组装CORS源列表"""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # 数据库配置
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/novel_db",
        description="数据库连接URL"
    )
    DATABASE_ECHO: bool = Field(default=False, description="是否输出SQL日志")
    DATABASE_POOL_SIZE: int = Field(default=20, description="数据库连接池大小")
    DATABASE_MAX_OVERFLOW: int = Field(default=30, description="数据库连接池最大溢出")
    DATABASE_POOL_TIMEOUT: int = Field(default=30, description="获取连接超时时间")
    DATABASE_POOL_RECYCLE: int = Field(default=3600, description="连接回收时间")

    # Redis配置
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis连接URL")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis密码")
    REDIS_DB: int = Field(default=0, description="Redis数据库索引")
    REDIS_DECODE_RESPONSES: bool = Field(default=True, description="自动解码响应")
    REDIS_SOCKET_TIMEOUT: int = Field(default=5, description="Redis套接字超时")
    REDIS_CONNECTION_POOL_MAX: int = Field(default=100, description="Redis连接池最大连接数")

    # JWT配置
    JWT_SECRET_KEY: str = Field(default=secrets.token_urlsafe(32), description="JWT密钥")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT算法")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440, description="访问token过期时间(分钟)")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="刷新token过期时间(天)")

    # 密码配置
    PASSWORD_MIN_LENGTH: int = Field(default=8, description="密码最小长度")
    PASSWORD_HASH_ROUNDS: int = Field(default=12, description="密码哈希轮数")

    # 邮件配置
    SMTP_TLS: bool = Field(default=True, description="SMTP使用TLS")
    SMTP_PORT: Optional[int] = Field(default=587, description="SMTP端口")
    SMTP_HOST: Optional[str] = Field(default=None, description="SMTP主机")
    SMTP_USER: Optional[EmailStr] = Field(default=None, description="SMTP用户名")
    SMTP_PASSWORD: Optional[str] = Field(default=None, description="SMTP密码")
    EMAIL_FROM: Optional[EmailStr] = Field(default=None, description="发件人邮箱")
    EMAIL_FROM_NAME: Optional[str] = Field(default=None, description="发件人名称")

    @validator("EMAIL_FROM", pre=True)
    def get_email_from(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        """获取发件人邮箱"""
        if not v:
            return values.get("SMTP_USER")
        return v

    # 文件存储配置
    UPLOAD_PATH: str = Field(default="./static/uploads/", description="上传文件路径")
    MAX_UPLOAD_SIZE: int = Field(default=10 * 1024 * 1024, description="最大上传文件大小(字节)")
    ALLOWED_IMAGE_EXTENSIONS: List[str] = Field(
        default=[".jpg", ".jpeg", ".png", ".gif", ".webp"],
        description="允许的图片文件扩展名"
    )
    ALLOWED_DOCUMENT_EXTENSIONS: List[str] = Field(
        default=[".txt", ".doc", ".docx", ".pdf"],
        description="允许的文档文件扩展名"
    )

    # Celery配置
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1", description="Celery broker URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/2", description="Celery结果后端")
    CELERY_TIMEZONE: str = Field(default="Asia/Shanghai", description="Celery时区")
    CELERY_ENABLE_UTC: bool = Field(default=True, description="Celery启用UTC")

    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FILE: str = Field(default="./logs/app.log", description="日志文件路径")
    LOG_ROTATION: str = Field(default="1 week", description="日志轮转周期")
    LOG_RETENTION: str = Field(default="1 month", description="日志保留时间")
    LOG_MAX_SIZE: str = Field(default="100 MB", description="单个日志文件最大大小")

    # 限流配置
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="是否启用限流")
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="每分钟请求限制")
    RATE_LIMIT_PER_HOUR: int = Field(default=1000, description="每小时请求限制")
    RATE_LIMIT_PER_DAY: int = Field(default=10000, description="每日请求限制")

    # 缓存配置
    CACHE_TTL: int = Field(default=3600, description="缓存过期时间(秒)")
    CACHE_ENABLED: bool = Field(default=True, description="是否启用缓存")
    CACHE_KEY_PREFIX: str = Field(default="novel_app:", description="缓存键前缀")

    # AI模型基础配置
    AI_ENABLED: bool = Field(default=True, description="是否启用AI功能")
    AI_REQUEST_TIMEOUT: int = Field(default=30, description="AI请求超时时间(秒)")
    AI_MAX_RETRIES: int = Field(default=3, description="AI请求最大重试次数")
    AI_RETRY_DELAY: int = Field(default=2, description="AI请求重试延迟(秒)")

    # DeepSeek配置
    DEEPSEEK_API_KEY: Optional[str] = Field(default=None, description="DeepSeek API密钥")
    DEEPSEEK_BASE_URL: str = Field(default="https://api.deepseek.com", description="DeepSeek API基础URL")
    DEEPSEEK_MODEL: str = Field(default="deepseek-chat", description="DeepSeek默认模型")

    # 智谱AI配置
    ZHIPU_API_KEY: Optional[str] = Field(default=None, description="智谱AI API密钥")
    ZHIPU_BASE_URL: str = Field(default="https://open.bigmodel.cn/api/paas/v4/", description="智谱AI API基础URL")
    ZHIPU_MODEL: str = Field(default="glm-4", description="智谱AI默认模型")

    # Ollama配置
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", description="Ollama服务基础URL")
    OLLAMA_MODEL: str = Field(default="llama3.1:8b", description="Ollama默认模型")

    # 翻译配置
    TRANSLATION_ENABLED: bool = Field(default=True, description="是否启用翻译功能")
    TRANSLATION_DAILY_LIMIT: int = Field(default=50, description="每日翻译章节数限制")
    TRANSLATION_BATCH_SIZE: int = Field(default=5, description="批量翻译大小")
    TRANSLATION_MAX_CONCURRENT: int = Field(default=3, description="最大并发翻译任务数")
    TRANSLATION_QUALITY_THRESHOLD: float = Field(default=3.5, description="翻译质量阈值")

    # 监控配置
    SENTRY_DSN: Optional[str] = Field(default=None, description="Sentry DSN")
    PROMETHEUS_ENABLED: bool = Field(default=False, description="是否启用Prometheus监控")
    METRICS_PORT: int = Field(default=8001, description="监控指标端口")

    # 安全配置
    ALLOWED_HOSTS: List[str] = Field(default=["*"], description="允许的主机")
    TRUSTED_PROXIES: List[str] = Field(default=[], description="信任的代理")
    SECURE_COOKIES: bool = Field(default=False, description="是否启用安全Cookie")

    # 业务配置
    MAX_FAVORITE_COUNT: int = Field(default=1000, description="最大收藏数量")
    MAX_BOOKMARK_COUNT: int = Field(default=5000, description="最大书签数量")
    FREE_CHAPTER_COUNT: int = Field(default=5, description="免费章节数量")
    VIP_PRICE_PER_MONTH: float = Field(default=19.9, description="VIP月费价格")
    CHAPTER_PRICE: float = Field(default=0.1, description="章节默认价格")

    class Config:
        """Pydantic配置"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @property
    def upload_path(self) -> Path:
        """获取上传路径的Path对象"""
        path = Path(self.UPLOAD_PATH)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def log_path(self) -> Path:
        """获取日志路径的Path对象"""
        path = Path(self.LOG_FILE).parent
        path.mkdir(parents=True, exist_ok=True)
        return path


# 创建全局设置实例
settings = Settings()

---

# app/config/database.py
# -*- coding: utf-8 -*-
"""
数据库连接和会话管理
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool
import logging

from .settings import settings

# 创建异步数据库引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    pool_pre_ping=True,  # 连接前检查连接有效性
    future=True
)

# 创建异步会话工厂
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)


class Base(DeclarativeBase):
    """SQLAlchemy基类"""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话的依赖注入函数

    Yields:
        AsyncSession: 异步数据库会话
    """
    async with SessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logging.error(f"数据库会话错误: {e}")
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """初始化数据库"""
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """关闭数据库连接"""
    await engine.dispose()


async def check_db_connection() -> bool:
    """
    检查数据库连接状态

    Returns:
        bool: 连接状态
    """
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logging.error(f"数据库连接检查失败: {e}")
        return False


---

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