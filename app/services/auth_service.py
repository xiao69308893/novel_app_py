
# app/services/auth_service.py
# -*- coding: utf-8 -*-
"""
认证服务
处理用户认证、注册、密码重置等业务逻辑
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.core.security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token,
    generate_verification_code
)
from app.core.exceptions import (
    AuthenticationException, ValidationException,
    ConflictException, NotFoundException
)
from app.models.user import User
from app.schemas.auth import TokenResponse
from .base import BaseService


class AuthService(BaseService):
    """认证服务类"""

    async def authenticate_user(
            self,
            username: str,
            password: str
    ) -> TokenResponse:
        """
        用户名密码认证

        Args:
            username: 用户名（支持用户名、邮箱、手机号）
            password: 密码

        Returns:
            TokenResponse: 认证结果

        Raises:
            AuthenticationException: 认证失败
        """

        try:
            # 查找用户（支持用户名、邮箱、手机号登录）
            stmt = select(User).where(
                (User.username == username) |
                (User.email == username) |
                (User.phone == username)
            )
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                raise AuthenticationException("用户不存在")

            # 验证密码
            if not verify_password(password, user.password_hash):
                # 记录失败次数
                await self._record_login_failure(user)
                raise AuthenticationException("密码错误")

            # 检查用户状态
            if user.status != "active":
                raise AuthenticationException("账户已被禁用")

            # 检查是否被锁定
            if user.locked_until and user.locked_until > datetime.utcnow():
                raise AuthenticationException("账户已被锁定，请稍后重试")

            # 生成tokens
            access_token = create_access_token(subject=str(user.id))
            refresh_token = create_refresh_token(subject=str(user.id))

            # 更新登录信息
            await self._update_login_info(user)

            # 记录登录日志
            await self._record_login_success(user)

            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="Bearer",
                expires_in=60 * 60 * 24,  # 24小时
                user={
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "avatar": user.avatar_url
                }
            )

        except AuthenticationException:
            raise
        except Exception as e:
            logger.error(f"用户认证失败: {e}")
            raise AuthenticationException("认证服务异常")

    async def authenticate_by_phone(
            self,
            phone: str,
            verification_code: str
    ) -> TokenResponse:
        """
        手机验证码认证

        Args:
            phone: 手机号
            verification_code: 验证码

        Returns:
            TokenResponse: 认证结果
        """

        # 验证验证码
        if not await self._verify_sms_code(phone, verification_code, "login"):
            raise AuthenticationException("验证码错误或已过期")

        # 查找用户
        stmt = select(User).where(User.phone == phone)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise AuthenticationException("手机号未注册")

        if user.status != "active":
            raise AuthenticationException("账户已被禁用")

        # 生成tokens
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))

        # 更新登录信息
        await self._update_login_info(user)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=60 * 60 * 24,
            user={
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "avatar": user.avatar_url
            }
        )

    async def register_user(
            self,
            username: str,
            password: str,
            email: Optional[str] = None,
            phone: Optional[str] = None,
            invite_code: Optional[str] = None
    ) -> TokenResponse:
        """
        用户注册

        Args:
            username: 用户名
            password: 密码
            email: 邮箱
            phone: 手机号
            invite_code: 邀请码

        Returns:
            TokenResponse: 注册结果
        """

        # 检查用户名是否已存在
        if await self.exists(User, {"username": username}):
            raise ConflictException("用户名已存在")

        # 检查邮箱是否已存在
        if email and await self.exists(User, {"email": email}):
            raise ConflictException("邮箱已存在")

        # 检查手机号是否已存在
        if phone and await self.exists(User, {"phone": phone}):
            raise ConflictException("手机号已存在")

        # 验证邀请码
        if invite_code:
            if not await self._validate_invite_code(invite_code):
                raise ValidationException("邀请码无效")

        # 创建用户
        user_data = {
            "username": username,
            "password_hash": get_password_hash(password),
            "salt": generate_verification_code(32),
            "email": email,
            "phone": phone,
            "status": "active"
        }

        user = await self.create(User, user_data)

        # 生成tokens
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))

        logger.info(f"用户注册成功: {username}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=60 * 60 * 24,
            user={
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "avatar": user.avatar_url
            }
        )

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """
        刷新访问token

        Args:
            refresh_token: 刷新token

        Returns:
            TokenResponse: 新的token
        """

        # TODO: 实现token刷新逻辑
        # 1. 验证refresh_token
        # 2. 生成新的access_token
        # 3. 返回新的token对

        raise NotImplementedError("Token刷新功能待实现")

    async def send_sms_verification_code(
            self,
            phone: str,
            code_type: str
    ) -> bool:
        """
        发送短信验证码

        Args:
            phone: 手机号
            code_type: 验证码类型

        Returns:
            bool: 发送成功
        """

        # 生成验证码
        code = generate_verification_code(6)

        # 存储到缓存
        cache_key = f"sms_code:{phone}:{code_type}"
        await self.cache_set(cache_key, code, ttl=300)  # 5分钟过期

        # TODO: 调用短信服务发送验证码
        logger.info(f"发送短信验证码到 {phone}: {code}")

        return True

    async def send_email_verification_code(
            self,
            email: str,
            code_type: str
    ) -> bool:
        """
        发送邮箱验证码

        Args:
            email: 邮箱
            code_type: 验证码类型

        Returns:
            bool: 发送成功
        """

        # 生成验证码
        code = generate_verification_code(6)

        # 存储到缓存
        cache_key = f"email_code:{email}:{code_type}"
        await self.cache_set(cache_key, code, ttl=300)  # 5分钟过期

        # TODO: 调用邮件服务发送验证码
        logger.info(f"发送邮件验证码到 {email}: {code}")

        return True

    async def _verify_sms_code(
            self,
            phone: str,
            code: str,
            code_type: str
    ) -> bool:
        """验证短信验证码"""

        cache_key = f"sms_code:{phone}:{code_type}"
        cached_code = await self.cache_get(cache_key)

        if cached_code and cached_code == code:
            # 验证成功后删除验证码
            await self.cache_delete(cache_key)
            return True

        return False

    async def _record_login_failure(self, user: User) -> None:
        """记录登录失败"""

        user.failed_login_attempts += 1

        # 如果失败次数过多，锁定账户
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=30)

        await self.db.commit()

    async def _record_login_success(self, user: User) -> None:
        """记录登录成功"""

        # TODO: 创建登录日志记录
        pass

    async def _update_login_info(self, user: User) -> None:
        """更新登录信息"""

        user.last_login_at = datetime.utcnow()
        user.failed_login_attempts = 0
        user.locked_until = None

        await self.db.commit()

    async def _validate_invite_code(self, invite_code: str) -> bool:
        """验证邀请码"""

        # TODO: 实现邀请码验证逻辑
        return True


