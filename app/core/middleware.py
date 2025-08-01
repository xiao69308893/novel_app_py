# app/core/middleware.py
# -*- coding: utf-8 -*-
"""
中间件集合
提供各种自定义中间件
"""

import time
import uuid
from typing import Callable, Dict, Any
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
from loguru import logger
import redis.asyncio as redis
from collections import defaultdict, deque
import asyncio

from app.config import settings


class RequestIdMiddleware(BaseHTTPMiddleware):
    """请求ID中间件，为每个请求生成唯一ID"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求，添加请求ID

        Args:
            request: 请求对象
            call_next: 下一个处理函数

        Returns:
            Response: 响应对象
        """

        # 生成或获取请求ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # 将请求ID添加到请求状态
        request.state.request_id = request_id

        # 处理请求
        response = await call_next(request)

        # 将请求ID添加到响应头
        response.headers["X-Request-ID"] = request_id

        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求，记录日志

        Args:
            request: 请求对象
            call_next: 下一个处理函数

        Returns:
            Response: 响应对象
        """

        start_time = time.time()

        # 获取请求信息
        request_id = getattr(request.state, "request_id", "unknown")
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "")

        # 记录请求开始日志
        logger.info(
            f"请求开始 | ID: {request_id} | "
            f"方法: {request.method} | "
            f"URL: {request.url} | "
            f"IP: {client_ip} | "
            f"UA: {user_agent[:100]}..."
        )

        try:
            # 处理请求
            response = await call_next(request)

            # 计算处理时间
            process_time = time.time() - start_time

            # 记录请求完成日志
            logger.info(
                f"请求完成 | ID: {request_id} | "
                f"状态: {response.status_code} | "
                f"耗时: {process_time:.3f}s"
            )

            # 添加响应头
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time

            # 记录异常日志
            logger.error(
                f"请求异常 | ID: {request_id} | "
                f"异常: {type(e).__name__} - {str(e)} | "
                f"耗时: {process_time:.3f}s"
            )

            raise

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""

        # 优先从代理头获取真实IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # 从X-Real-IP头获取
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 最后使用客户端IP
        return request.client.host if request.client else "unknown"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求，添加安全头

        Args:
            request: 请求对象
            call_next: 下一个处理函数

        Returns:
            Response: 响应对象
        """

        response = await call_next(request)

        # 添加安全头
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }

        for header, value in security_headers.items():
            response.headers[header] = value

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""

    def __init__(self, app, calls: int = 100, period: int = 60):
        """
        初始化限流中间件

        Args:
            app: ASGI应用
            calls: 时间窗口内允许的调用次数
            period: 时间窗口大小（秒）
        """

        super().__init__(app)
        self.calls = calls
        self.period = period
        self.client_requests: Dict[str, deque] = defaultdict(deque)
        self.redis_client = None

        # 尝试连接Redis
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )
        except Exception:
            logger.warning("Redis连接失败，使用内存限流")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求，执行限流

        Args:
            request: 请求对象
            call_next: 下一个处理函数

        Returns:
            Response: 响应对象
        """

        # 获取客户端标识
        client_id = self._get_client_id(request)

        # 检查限流
        if await self._is_rate_limited(client_id):
            return JSONResponse(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "code": HTTP_429_TOO_MANY_REQUESTS,
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "message": f"请求过于频繁，请在{self.period}秒后重试",
                    "retry_after": self.period
                }
            )

        # 记录请求
        await self._record_request(client_id)

        return await call_next(request)

    def _get_client_id(self, request: Request) -> str:
        """
        获取客户端标识

        Args:
            request: 请求对象

        Returns:
            str: 客户端标识
        """

        # 优先使用用户ID（如果已认证）
        if hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"

        # 使用IP地址
        client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if not client_ip:
            client_ip = request.headers.get("X-Real-IP", "")
        if not client_ip:
            client_ip = request.client.host if request.client else "unknown"

        return f"ip:{client_ip}"

    async def _is_rate_limited(self, client_id: str) -> bool:
        """
        检查是否被限流

        Args:
            client_id: 客户端标识

        Returns:
            bool: 是否被限流
        """

        current_time = time.time()

        if self.redis_client:
            # 使用Redis限流
            return await self._redis_rate_limit(client_id, current_time)
        else:
            # 使用内存限流
            return self._memory_rate_limit(client_id, current_time)

    async def _redis_rate_limit(self, client_id: str, current_time: float) -> bool:
        """
        Redis限流检查

        Args:
            client_id: 客户端标识
            current_time: 当前时间

        Returns:
            bool: 是否被限流
        """

        try:
            key = f"rate_limit:{client_id}"

            # 使用滑动窗口算法
            async with self.redis_client.pipeline() as pipe:
                # 移除过期的请求记录
                await pipe.zremrangebyscore(
                    key,
                    0,
                    current_time - self.period
                )

                # 获取当前窗口内的请求数
                count = await pipe.zcard(key)

                # 检查是否超过限制
                if count >= self.calls:
                    return True

                # 记录当前请求
                await pipe.zadd(key, {str(current_time): current_time})
                await pipe.expire(key, self.period)
                await pipe.execute()

            return False

        except Exception as e:
            logger.warning(f"Redis限流检查失败: {e}")
            return False

    def _memory_rate_limit(self, client_id: str, current_time: float) -> bool:
        """
        内存限流检查

        Args:
            client_id: 客户端标识
            current_time: 当前时间

        Returns:
            bool: 是否被限流
        """

        requests = self.client_requests[client_id]

        # 清理过期的请求记录
        while requests and requests[0] < current_time - self.period:
            requests.popleft()

        # 检查是否超过限制
        if len(requests) >= self.calls:
            return True

        return False

    async def _record_request(self, client_id: str) -> None:
        """
        记录请求

        Args:
            client_id: 客户端标识
        """

        current_time = time.time()

        if not self.redis_client:
            # 内存记录
            self.client_requests[client_id].append(current_time)


class CompressionMiddleware(BaseHTTPMiddleware):
    """响应压缩中间件"""

    def __init__(self, app, minimum_size: int = 1024):
        """
        初始化压缩中间件

        Args:
            app: ASGI应用
            minimum_size: 最小压缩大小
        """

        super().__init__(app)
        self.minimum_size = minimum_size

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求，压缩响应

        Args:
            request: 请求对象
            call_next: 下一个处理函数

        Returns:
            Response: 响应对象
        """

        response = await call_next(request)

        # 检查是否支持压缩
        accept_encoding = request.headers.get("Accept-Encoding", "")
        if "gzip" not in accept_encoding:
            return response

        # 检查响应类型
        content_type = response.headers.get("Content-Type", "")
        if not self._should_compress(content_type):
            return response

        # 检查响应大小
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) < self.minimum_size:
            return response

        # TODO: 实现GZIP压缩
        # 这里可以添加实际的压缩逻辑

        return response

    def _should_compress(self, content_type: str) -> bool:
        """
        判断是否应该压缩

        Args:
            content_type: 内容类型

        Returns:
            bool: 是否应该压缩
        """

        compressible_types = [
            "application/json",
            "text/html",
            "text/css",
            "text/javascript",
            "application/javascript",
            "text/plain",
            "application/xml",
            "text/xml"
        ]

        return any(ct in content_type for ct in compressible_types)
