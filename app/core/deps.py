
# app/core/deps.py
# -*- coding: utf-8 -*-
"""
依赖注入管理
提供通用的依赖注入函数
"""

from typing import AsyncGenerator, Optional, Any
from fastapi import Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt
from pydantic import ValidationError
import redis.asyncio as redis

from app.config import settings, SessionLocal
from app.core.exceptions import AuthenticationException, PermissionException
from app.models.user import User

# JWT Bearer 认证
security = HTTPBearer()

# Redis连接池（稍后初始化）
redis_pool: Optional[redis.ConnectionPool] = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话的依赖注入函数

    Yields:
        AsyncSession: 异步数据库会话
    """
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    """
    获取Redis连接的依赖注入函数

    Yields:
        redis.Redis: Redis连接实例
    """
    global redis_pool

    if redis_pool is None:
        redis_pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=settings.REDIS_DECODE_RESPONSES,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
            max_connections=settings.REDIS_CONNECTION_POOL_MAX
        )

    redis_client = redis.Redis(connection_pool=redis_pool)
    try:
        yield redis_client
    finally:
        await redis_client.close()


async def get_current_user_token(
        credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    从请求头中提取JWT token

    Args:
        credentials: HTTP认证凭据

    Returns:
        str: JWT token

    Raises:
        AuthenticationException: 认证失败
    """
    if not credentials:
        raise AuthenticationException("缺少认证凭据")

    return credentials.credentials


async def get_current_user(
        db: AsyncSession = Depends(get_db),
        token: str = Depends(get_current_user_token)
) -> User:
    """
    获取当前认证用户

    Args:
        db: 数据库会话
        token: JWT token

    Returns:
        User: 当前用户对象

    Raises:
        AuthenticationException: 认证失败
    """

    try:
        # 解码JWT token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # 提取用户ID
        user_id: str = payload.get("sub")
        if user_id is None:
            raise AuthenticationException("Token无效")

        # 检查token类型
        token_type: str = payload.get("type")
        if token_type != "access":
            raise AuthenticationException("Token类型错误")

    except JWTError:
        raise AuthenticationException("Token解析失败")

    # 查询用户
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise AuthenticationException("用户不存在")

    return user


async def get_current_user_optional(
        db: AsyncSession = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))
) -> Optional[User]:
    """
    获取当前用户（可选，不抛出异常）

    Args:
        db: 数据库会话
        credentials: 认证凭据（可选）

    Returns:
        Optional[User]: 当前用户对象或None
    """
    if not credentials:
        return None

    try:
        # 解码JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # 提取用户ID
        user_id: str = payload.get("sub")
        if user_id is None:
            return None

        # 检查token类型
        token_type: str = payload.get("type")
        if token_type != "access":
            return None

        # 查询用户
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user and user.status == "active":
            return user

    except JWTError:
        pass

    return None


async def get_current_active_user(
        current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前活跃用户（状态检查）

    Args:
        current_user: 当前用户

    Returns:
        User: 活跃用户对象

    Raises:
        AuthenticationException: 用户状态异常
    """

    if current_user.status != "active":
        raise AuthenticationException("用户账号已被禁用")

    return current_user


async def get_current_vip_user(
        current_user: User = Depends(get_current_active_user)
) -> User:
    """
    获取当前VIP用户

    Args:
        current_user: 当前活跃用户

    Returns:
        User: VIP用户对象

    Raises:
        PermissionException: 权限不足
    """

    if current_user.vip_level <= 0:
        raise PermissionException("需要VIP权限")

    return current_user


async def get_current_admin_user(
        current_user: User = Depends(get_current_active_user)
) -> User:
    """
    获取当前管理员用户

    Args:
        current_user: 当前活跃用户

    Returns:
        User: 管理员用户对象

    Raises:
        PermissionException: 权限不足
    """

    if current_user.role != "admin":
        raise PermissionException("需要管理员权限")

    return current_user


def get_pagination_params(
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量")
) -> dict:
    """
    获取分页参数

    Args:
        page: 页码，从1开始
        page_size: 每页数量，1-100

    Returns:
        dict: 分页参数字典
    """

    return {
        "page": page,
        "page_size": page_size,
        "offset": (page - 1) * page_size,
        "limit": page_size
    }


def get_sort_params(
        sort_by: str = Query("created_at", description="排序字段"),
        sort_order: str = Query("desc", pattern="^(asc|desc)$", description="排序方向")
) -> dict:
    """
    获取排序参数

    Args:
        sort_by: 排序字段
        sort_order: 排序方向 asc/desc

    Returns:
        dict: 排序参数字典
    """

    return {
        "sort_by": sort_by,
        "sort_order": sort_order,
        "ascending": sort_order == "asc"
    }


async def require_permission(
        required_permissions: list[str],
        current_user: User = Depends(get_current_active_user)
) -> User:
    """
    权限验证依赖

    Args:
        required_permissions: 必需的权限列表
        current_user: 当前用户

    Returns:
        User: 有权限的用户

    Raises:
        PermissionException: 权限不足
    """

    # TODO: 实现权限验证逻辑
    # 这里可以根据用户角色、权限表等进行验证

    return current_user


class RequirePermissions:
    """权限验证类，用于创建权限依赖"""

    def __init__(self, *permissions: str):
        self.permissions = list(permissions)

    async def __call__(
            self,
            current_user: User = Depends(get_current_active_user)
    ) -> User:
        """
        权限验证调用

        Args:
            current_user: 当前用户

        Returns:
            User: 有权限的用户

        Raises:
            PermissionException: 权限不足
        """

        return await require_permission(self.permissions, current_user)


async def get_request_info(request: Request) -> dict:
    """
    获取请求信息

    Args:
        request: FastAPI请求对象

    Returns:
        dict: 请求信息字典
    """

    # 获取真实IP（考虑代理）
    real_ip = request.headers.get('X-Real-IP')
    forwarded_for = request.headers.get('X-Forwarded-For')

    if real_ip:
        client_ip = real_ip
    elif forwarded_for:
        client_ip = forwarded_for.split(',')[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"

    return {
        "ip": client_ip,
        "user_agent": request.headers.get("User-Agent", ""),
        "referer": request.headers.get("Referer", ""),
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers)
    }

