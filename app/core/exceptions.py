# app/core/exceptions.py
# -*- coding: utf-8 -*-
"""
异常处理定义
定义自定义异常类和异常处理器
"""

from typing import Any, Dict, Optional, Union
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from loguru import logger
import traceback


class CustomException(Exception):
    """自定义异常基类"""

    def __init__(
            self,
            message: str,
            code: str = "CUSTOM_ERROR",
            status_code: int = status.HTTP_400_BAD_REQUEST,
            details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(CustomException):
    """验证异常"""

    def __init__(
            self,
            message: str = "数据验证失败",
            details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class AuthenticationException(CustomException):
    """认证异常"""

    def __init__(
            self,
            message: str = "认证失败",
            details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class PermissionException(CustomException):
    """权限异常"""

    def __init__(
            self,
            message: str = "权限不足",
            details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="PERMISSION_ERROR",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class NotFoundException(CustomException):
    """资源不存在异常"""

    def __init__(
            self,
            message: str = "资源不存在",
            resource_type: str = "resource",
            resource_id: Optional[str] = None
    ):
        details = {"resource_type": resource_type}
        if resource_id:
            details["resource_id"] = resource_id

        super().__init__(
            message=message,
            code="NOT_FOUND_ERROR",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class ConflictException(CustomException):
    """资源冲突异常"""

    def __init__(
            self,
            message: str = "资源冲突",
            details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="CONFLICT_ERROR",
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )


class RateLimitException(CustomException):
    """限流异常"""

    def __init__(
            self,
            message: str = "请求过于频繁",
            retry_after: Optional[int] = None
    ):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after

        super().__init__(
            message=message,
            code="RATE_LIMIT_ERROR",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details
        )


class BusinessException(CustomException):
    """业务逻辑异常"""

    def __init__(
            self,
            message: str,
            code: str = "BUSINESS_ERROR",
            details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class ExternalServiceException(CustomException):
    """外部服务异常"""

    def __init__(
            self,
            message: str = "外部服务异常",
            service_name: str = "unknown",
            details: Optional[Dict[str, Any]] = None
    ):
        if details is None:
            details = {}
        details["service_name"] = service_name

        super().__init__(
            message=message,
            code="EXTERNAL_SERVICE_ERROR",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details
        )


# 异常处理器
async def custom_exception_handler(request: Request, exc: CustomException) -> JSONResponse:
    """
    自定义异常处理器

    Args:
        request: FastAPI请求对象
        exc: 自定义异常

    Returns:
        JSONResponse: JSON响应
    """

    # 记录异常日志
    logger.warning(
        f"自定义异常: {exc.code} - {exc.message} | "
        f"URL: {request.url} | "
        f"方法: {request.method} | "
        f"详情: {exc.details}"
    )

    # 构建响应数据
    response_data = {
        "success": False,
        "code": exc.status_code,
        "error_code": exc.code,
        "message": exc.message,
        "timestamp": logger._core.now().isoformat(),
        "path": str(request.url.path)
    }

    # 添加详细信息（仅在开发环境）
    if exc.details:
        response_data["details"] = exc.details

    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    HTTP异常处理器

    Args:
        request: FastAPI请求对象
        exc: HTTP异常

    Returns:
        JSONResponse: JSON响应
    """

    # 记录异常日志
    logger.warning(
        f"HTTP异常: {exc.status_code} - {exc.detail} | "
        f"URL: {request.url} | "
        f"方法: {request.method}"
    )

    # 构建响应数据
    response_data = {
        "success": False,
        "code": exc.status_code,
        "error_code": "HTTP_ERROR",
        "message": exc.detail,
        "timestamp": logger._core.now().isoformat(),
        "path": str(request.url.path)
    }

    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    验证异常处理器

    Args:
        request: FastAPI请求对象
        exc: 请求验证异常

    Returns:
        JSONResponse: JSON响应
    """

    # 处理验证错误
    errors = []
    for error in exc.errors():
        error_info = {
            "field": ".".join(str(x) for x in error["loc"]) if error["loc"] else "root",
            "message": error["msg"],
            "type": error["type"]
        }
        errors.append(error_info)

    # 记录异常日志
    logger.warning(
        f"参数验证异常: {len(errors)}个错误 | "
        f"URL: {request.url} | "
        f"方法: {request.method} | "
        f"错误: {errors}"
    )

    # 构建响应数据
    response_data = {
        "success": False,
        "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "error_code": "VALIDATION_ERROR",
        "message": "请求参数验证失败",
        "errors": errors,
        "timestamp": logger._core.now().isoformat(),
        "path": str(request.url.path)
    }

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_data
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    通用异常处理器

    Args:
        request: FastAPI请求对象
        exc: 通用异常

    Returns:
        JSONResponse: JSON响应
    """

    # 记录详细异常信息
    logger.error(
        f"未处理异常: {type(exc).__name__} - {str(exc)} | "
        f"URL: {request.url} | "
        f"方法: {request.method} | "
        f"堆栈: {traceback.format_exc()}"
    )

    # 构建响应数据
    response_data = {
        "success": False,
        "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "error_code": "INTERNAL_SERVER_ERROR",
        "message": "服务器内部错误",
        "timestamp": logger._core.now().isoformat(),
        "path": str(request.url.path)
    }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data
    )


