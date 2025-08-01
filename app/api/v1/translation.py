
# app/api/v1/translation.py
# -*- coding: utf-8 -*-
"""
翻译相关API接口
处理AI翻译项目、配置、任务等功能
"""

from typing import Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_db
from app.core.deps import get_current_active_user, get_pagination_params
from app.schemas.base import BaseResponse, ListResponse, SuccessResponse
from app.services.translation_service import TranslationService
from app.models.user import User

# 创建路由器
router = APIRouter()


# 依赖注入
def get_translation_service(db: AsyncSession = Depends(get_db)) -> TranslationService:
    """获取翻译服务"""
    return TranslationService(db)


@router.get("/projects", response_model=ListResponse[dict], summary="获取翻译项目列表")
async def get_translation_projects(
        status: Optional[str] = Query(None, description="项目状态"),
        pagination: dict = Depends(get_pagination_params),
        current_user: User = Depends(get_current_active_user),
        translation_service: TranslationService = Depends(get_translation_service)
) -> Any:
    """获取用户的翻译项目列表"""

    projects, total = await translation_service.get_user_projects(
        user_id=current_user.id,
        status=status,
        **pagination
    )

    return ListResponse(
        data=projects,
        pagination={
            "page": pagination["page"],
            "page_size": pagination["page_size"],
            "total": total,
            "total_pages": (total + pagination["page_size"] - 1) // pagination["page_size"],
            "has_more": total > pagination["offset"] + len(projects),
            "has_next_page": pagination["page"] * pagination["page_size"] < total,
            "has_previous_page": pagination["page"] > 1
        },
        message="获取翻译项目列表成功"
    )


@router.post("/projects", response_model=BaseResponse[dict], summary="创建翻译项目")
async def create_translation_project(
        project_data: dict,
        current_user: User = Depends(get_current_active_user),
        translation_service: TranslationService = Depends(get_translation_service)
) -> Any:
    """创建新的翻译项目"""

    project = await translation_service.create_project(
        user_id=current_user.id,
        **project_data
    )

    return BaseResponse(
        data=project,
        message="翻译项目创建成功"
    )


@router.get("/projects/{project_id}", response_model=BaseResponse[dict], summary="获取翻译项目详情")
async def get_translation_project(
        project_id: str,
        current_user: User = Depends(get_current_active_user),
        translation_service: TranslationService = Depends(get_translation_service)
) -> Any:
    """获取翻译项目详情"""

    project = await translation_service.get_project_detail(
        project_id=project_id,
        user_id=current_user.id
    )

    return BaseResponse(
        data=project,
        message="获取翻译项目详情成功"
    )


@router.post("/projects/{project_id}/start", response_model=BaseResponse[dict], summary="启动翻译项目")
async def start_translation_project(
        project_id: str,
        current_user: User = Depends(get_current_active_user),
        translation_service: TranslationService = Depends(get_translation_service)
) -> Any:
    """启动翻译项目"""

    result = await translation_service.start_project(
        project_id=project_id,
        user_id=current_user.id
    )

    return BaseResponse(
        data=result,
        message="翻译项目启动成功"
    )


@router.get("/configs", response_model=ListResponse[dict], summary="获取翻译配置列表")
async def get_translation_configs(
        translation_service: TranslationService = Depends(get_translation_service)
) -> Any:
    """获取可用的翻译配置列表"""

    configs = await translation_service.get_available_configs()

    return ListResponse(
        data=configs,
        message="获取翻译配置列表成功"
    )