# app/main.py
# -*- coding: utf-8 -*-
"""
FastAPI主应用入口
"""

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger
import time

from app.config import settings, init_db, close_db
from app.core.middleware import (
    LoggingMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    RequestIdMiddleware
)
from app.core.exceptions import (
    CustomException,
    validation_exception_handler,
    custom_exception_handler,
    http_exception_handler
)
from app.api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 启动时执行
    logger.info("🚀 小说阅读APP后端服务启动中...")

    try:
        # 初始化数据库
        await init_db()
        logger.info("✅ 数据库初始化完成")

        # 其他启动任务
        logger.info("✅ 应用启动完成")

        yield

    except Exception as e:
        logger.error(f"❌ 应用启动失败: {e}")
        raise
    finally:
        # 关闭时执行
        logger.info("🔄 小说阅读APP后端服务关闭中...")

        try:
            # 关闭数据库连接
            await close_db()
            logger.info("✅ 数据库连接已关闭")

            logger.info("✅ 应用已安全关闭")

        except Exception as e:
            logger.error(f"❌ 应用关闭时出错: {e}")


def create_app() -> FastAPI:
    """
    创建FastAPI应用实例

    Returns:
        FastAPI: 应用实例
    """

    # 创建FastAPI应用
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="支持AI翻译功能的小说阅读平台后端API",
        openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
        docs_url=f"{settings.API_V1_STR}/docs" if settings.DEBUG else None,
        redoc_url=f"{settings.API_V1_STR}/redoc" if settings.DEBUG else None,
        lifespan=lifespan
    )

    # 添加中间件
    setup_middleware(app)

    # 添加异常处理器
    setup_exception_handlers(app)

    # 添加路由
    setup_routes(app)

    # 挂载静态文件
    setup_static_files(app)

    return app


def setup_middleware(app: FastAPI) -> None:
    """
    设置中间件

    Args:
        app: FastAPI应用实例
    """

    # 信任主机中间件（安全）
    if settings.ALLOWED_HOSTS:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS
        )

    # CORS中间件
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # 自定义中间件
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIdMiddleware)

    if settings.RATE_LIMIT_ENABLED:
        app.add_middleware(
            RateLimitMiddleware,
            calls=settings.RATE_LIMIT_PER_MINUTE,
            period=60
        )

    app.add_middleware(LoggingMiddleware)


def setup_exception_handlers(app: FastAPI) -> None:
    """
    设置异常处理器

    Args:
        app: FastAPI应用实例
    """

    from fastapi import HTTPException
    from fastapi.exceptions import RequestValidationError

    # 自定义异常处理器
    app.add_exception_handler(CustomException, custom_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)


def setup_routes(app: FastAPI) -> None:
    """
    设置路由

    Args:
        app: FastAPI应用实例
    """

    # 健康检查端点
    @app.get("/health", tags=["健康检查"])
    async def health_check():
        """健康检查接口"""
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": settings.APP_VERSION,
            "service": settings.APP_NAME
        }

    # API路由
    app.include_router(api_router, prefix=settings.API_V1_STR)


def setup_static_files(app: FastAPI) -> None:
    """
    设置静态文件服务

    Args:
        app: FastAPI应用实例
    """

    # 挂载静态文件目录
    app.mount("/static", StaticFiles(directory="static"), name="static")


# 创建应用实例
app = create_app()

if __name__ == "__main__":
    """
    开发环境直接运行
    """
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )






