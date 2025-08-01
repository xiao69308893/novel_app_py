
# app/api/v1/auth.py
# -*- coding: utf-8 -*-
"""
认证相关API接口
处理用户登录、注册、token刷新等认证功能
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_db
from app.core.deps import get_current_active_user
from app.schemas.auth import (
    LoginRequest, RegisterRequest, TokenResponse,
    PasswordChangeRequest, SMSCodeRequest, EmailCodeRequest
)
from app.schemas.base import BaseResponse, SuccessResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.models.user import User

# 创建路由器
router = APIRouter()


# 依赖注入
def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """获取认证服务"""
    return AuthService(db)


@router.post("/login", response_model=BaseResponse[TokenResponse], summary="用户登录")
async def login(
        login_data: LoginRequest,
        auth_service: AuthService = Depends(get_auth_service)
) -> Any:
    """
    用户登录

    支持用户名、邮箱、手机号登录
    """

    result = await auth_service.authenticate_user(
        username=login_data.username,
        password=login_data.password
    )

    return BaseResponse(
        data=result,
        message="登录成功"
    )


@router.post("/login/phone", response_model=BaseResponse[TokenResponse], summary="手机验证码登录")
async def login_by_phone(
        phone_data: SMSCodeRequest,
        auth_service: AuthService = Depends(get_auth_service)
) -> Any:
    """
    手机验证码登录
    """

    result = await auth_service.authenticate_by_phone(
        phone=phone_data.phone,
        verification_code=phone_data.verification_code
    )

    return BaseResponse(
        data=result,
        message="登录成功"
    )


@router.post("/register", response_model=BaseResponse[TokenResponse], summary="用户注册")
async def register(
        register_data: RegisterRequest,
        auth_service: AuthService = Depends(get_auth_service)
) -> Any:
    """
    用户注册
    """

    result = await auth_service.register_user(
        username=register_data.username,
        password=register_data.password,
        email=register_data.email,
        phone=register_data.phone,
        invite_code=register_data.invite_code
    )

    return BaseResponse(
        data=result,
        message="注册成功"
    )


@router.post("/refresh", response_model=BaseResponse[TokenResponse], summary="刷新Token")
async def refresh_token(
        refresh_token: str,
        auth_service: AuthService = Depends(get_auth_service)
) -> Any:
    """
    刷新访问token
    """

    result = await auth_service.refresh_access_token(refresh_token)

    return BaseResponse(
        data=result,
        message="Token刷新成功"
    )


@router.post("/logout", response_model=SuccessResponse, summary="用户登出")
async def logout(
        current_user: User = Depends(get_current_active_user),
        auth_service: AuthService = Depends(get_auth_service)
) -> Any:
    """
    用户登出
    """

    await auth_service.logout_user(current_user.id)

    return SuccessResponse(message="登出成功")


@router.get("/user", response_model=BaseResponse[UserResponse], summary="获取当前用户信息")
async def get_current_user_info(
        current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    获取当前认证用户的信息
    """

    return BaseResponse(
        data=UserResponse.model_validate(current_user),
        message="获取用户信息成功"
    )


@router.put("/password/change", response_model=SuccessResponse, summary="修改密码")
async def change_password(
        password_data: PasswordChangeRequest,
        current_user: User = Depends(get_current_active_user),
        auth_service: AuthService = Depends(get_auth_service)
) -> Any:
    """
    修改用户密码
    """

    await auth_service.change_password(
        user_id=current_user.id,
        old_password=password_data.old_password,
        new_password=password_data.new_password
    )

    return SuccessResponse(message="密码修改成功")


@router.post("/password/forgot", response_model=SuccessResponse, summary="忘记密码")
async def forgot_password(
        account: str,
        verification_code: str,
        new_password: str,
        auth_service: AuthService = Depends(get_auth_service)
) -> Any:
    """
    忘记密码重置
    """

    await auth_service.reset_password(
        account=account,
        verification_code=verification_code,
        new_password=new_password
    )

    return SuccessResponse(message="密码重置成功")


@router.post("/sms/send", response_model=SuccessResponse, summary="发送短信验证码")
async def send_sms_code(
        sms_data: SMSCodeRequest,
        auth_service: AuthService = Depends(get_auth_service)
) -> Any:
    """
    发送短信验证码
    """

    await auth_service.send_sms_verification_code(
        phone=sms_data.phone,
        code_type=sms_data.type
    )

    return SuccessResponse(message="验证码发送成功")


@router.post("/email/send", response_model=SuccessResponse, summary="发送邮箱验证码")
async def send_email_code(
        email_data: EmailCodeRequest,
        auth_service: AuthService = Depends(get_auth_service)
) -> Any:
    """
    发送邮箱验证码
    """

    await auth_service.send_email_verification_code(
        email=email_data.email,
        code_type=email_data.type
    )

    return SuccessResponse(message="验证码发送成功")


@router.post("/phone/bind", response_model=SuccessResponse, summary="绑定手机号")
async def bind_phone(
        phone_data: SMSCodeRequest,
        current_user: User = Depends(get_current_active_user),
        auth_service: AuthService = Depends(get_auth_service)
) -> Any:
    """
    绑定手机号
    """

    await auth_service.bind_phone(
        user_id=current_user.id,
        phone=phone_data.phone,
        verification_code=phone_data.verification_code
    )

    return SuccessResponse(message="手机号绑定成功")


@router.post("/email/bind", response_model=SuccessResponse, summary="绑定邮箱")
async def bind_email(
        email_data: EmailCodeRequest,
        current_user: User = Depends(get_current_active_user),
        auth_service: AuthService = Depends(get_auth_service)
) -> Any:
    """
    绑定邮箱
    """

    await auth_service.bind_email(
        user_id=current_user.id,
        email=email_data.email,
        verification_code=email_data.verification_code
    )

    return SuccessResponse(message="邮箱绑定成功")


@router.delete("/account", response_model=SuccessResponse, summary="删除账户")
async def delete_account(
        password: str,
        current_user: User = Depends(get_current_active_user),
        auth_service: AuthService = Depends(get_auth_service)
) -> Any:
    """
    删除用户账户
    """

    await auth_service.delete_account(
        user_id=current_user.id,
        password=password
    )

    return SuccessResponse(message="账户删除成功")



