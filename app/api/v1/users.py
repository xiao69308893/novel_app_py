# app/api/v1/users.py
# -*- coding: utf-8 -*-
"""
用户管理API接口
处理用户资料、设置、统计等功能
"""

from typing import Any
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_db
from app.core.deps import get_current_active_user, get_pagination_params
from app.schemas.base import BaseResponse, SuccessResponse, ListResponse
from app.schemas.user import (
    UserResponse, UserProfileResponse, UserSettingsResponse,
    UserStatsResponse, UserUpdateRequest
)
from app.services.user_service import UserService
from app.models.user import User

# 创建路由器
router = APIRouter()


# 依赖注入
def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """获取用户服务"""
    return UserService(db)


@router.get("/profile", response_model=BaseResponse[UserProfileResponse], summary="获取用户资料")
async def get_user_profile(
        current_user: User = Depends(get_current_active_user),
        user_service: UserService = Depends(get_user_service)
) -> Any:
    """获取当前用户的详细资料"""

    profile = await user_service.get_user_profile(current_user.id)

    return BaseResponse(
        data=profile,
        message="获取用户资料成功"
    )


@router.put("/profile", response_model=BaseResponse[UserProfileResponse], summary="更新用户资料")
async def update_user_profile(
        profile_data: UserUpdateRequest,
        current_user: User = Depends(get_current_active_user),
        user_service: UserService = Depends(get_user_service)
) -> Any:
    """更新用户资料"""

    profile = await user_service.update_user_profile(
        user_id=current_user.id,
        profile_data=profile_data.model_dump(exclude_unset=True)
    )

    return BaseResponse(
        data=profile,
        message="用户资料更新成功"
    )


@router.post("/avatar", response_model=BaseResponse[dict], summary="上传用户头像")
async def upload_avatar(
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_active_user),
        user_service: UserService = Depends(get_user_service)
) -> Any:
    """上传用户头像"""

    avatar_url = await user_service.upload_avatar(current_user.id, file)

    return BaseResponse(
        data={"avatar_url": avatar_url},
        message="头像上传成功"
    )


@router.get("/settings", response_model=BaseResponse[UserSettingsResponse], summary="获取用户设置")
async def get_user_settings(
        current_user: User = Depends(get_current_active_user),
        user_service: UserService = Depends(get_user_service)
) -> Any:
    """获取用户设置"""

    settings = await user_service.get_user_settings(current_user.id)

    return BaseResponse(
        data=settings,
        message="获取用户设置成功"
    )


@router.put("/settings", response_model=BaseResponse[UserSettingsResponse], summary="更新用户设置")
async def update_user_settings(
        settings_data: dict,
        current_user: User = Depends(get_current_active_user),
        user_service: UserService = Depends(get_user_service)
) -> Any:
    """更新用户设置"""

    settings = await user_service.update_user_settings(
        user_id=current_user.id,
        settings_data=settings_data
    )

    return BaseResponse(
        data=settings,
        message="用户设置更新成功"
    )


@router.get("/stats", response_model=BaseResponse[UserStatsResponse], summary="获取用户统计")
async def get_user_stats(
        current_user: User = Depends(get_current_active_user),
        user_service: UserService = Depends(get_user_service)
) -> Any:
    """获取用户统计信息"""

    stats = await user_service.get_user_statistics(current_user.id)

    return BaseResponse(
        data=stats,
        message="获取用户统计成功"
    )


@router.post("/checkin", response_model=BaseResponse[dict], summary="用户签到")
async def user_checkin(
        current_user: User = Depends(get_current_active_user),
        user_service: UserService = Depends(get_user_service)
) -> Any:
    """用户每日签到"""

    result = await user_service.user_checkin(current_user.id)

    return BaseResponse(
        data=result,
        message="签到成功"
    )


@router.get("/checkin/status", response_model=BaseResponse[dict], summary="获取签到状态")
async def get_checkin_status(
        current_user: User = Depends(get_current_active_user),
        user_service: UserService = Depends(get_user_service)
) -> Any:
    """获取用户签到状态"""

    status = await user_service.get_checkin_status(current_user.id)

    return BaseResponse(
        data=status,
        message="获取签到状态成功"
    )


