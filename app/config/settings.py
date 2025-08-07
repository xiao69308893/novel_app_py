# app/config/settings.py
# -*- coding: utf-8 -*-
"""
应用核心配置管理
使用Pydantic Settings进行环境变量读取和验证
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import AnyHttpUrl, BaseConfig, EmailStr, validator, Field
import secrets
import os
from pathlib import Path


class Settings(BaseConfig):
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
        default="postgresql+asyncpg://postgres:123456@localhost:5432/novel_db",
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
