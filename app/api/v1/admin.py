# app/api/v1/admin.py
# -*- coding: utf-8 -*-
"""
管理员API接口
处理后台管理相关功能
"""

from typing import Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_db
from app.core.deps import get_current_admin_user, get_pagination_params
from app.schemas.base import BaseResponse, ListResponse, SuccessResponse
from app.schemas.admin import (
    AdminUserResponse, AdminUserCreate, AdminUserUpdate,
    SystemStatsResponse, UserStatsResponse, NovelStatsResponse,
    RevenueStatsResponse, AdminLogResponse
)
from app.schemas.user import UserResponse
from app.schemas.novel import NovelBasicResponse
from app.services.admin_service import AdminService
from app.services.user_service import UserService
from app.services.novel_service import NovelService
from app.models.user import User

# 创建路由器
router = APIRouter()


def get_admin_service(db: AsyncSession = Depends(get_db)) -> AdminService:
    """获取管理员服务"""
    return AdminService(db)


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """获取用户服务"""
    return UserService(db)


def get_novel_service(db: AsyncSession = Depends(get_db)) -> NovelService:
    """获取小说服务"""
    return NovelService(db)


# 系统统计
@router.get("/stats/system", response_model=BaseResponse[SystemStatsResponse], summary="获取系统统计")
async def get_system_stats(
        current_admin: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> Any:
    """获取系统统计信息"""

    stats = await admin_service.get_system_stats()

    return BaseResponse(
        data=stats,
        message="获取系统统计成功"
    )


@router.get("/stats/users", response_model=BaseResponse[UserStatsResponse], summary="获取用户统计")
async def get_user_stats(
        period: str = Query("7d", description="统计周期"),
        current_admin: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> Any:
    """获取用户统计信息"""

    stats = await admin_service.get_user_stats(period)

    return BaseResponse(
        data=stats,
        message="获取用户统计成功"
    )


@router.get("/stats/novels", response_model=BaseResponse[NovelStatsResponse], summary="获取小说统计")
async def get_novel_stats(
        period: str = Query("7d", description="统计周期"),
        current_admin: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> Any:
    """获取小说统计信息"""

    stats = await admin_service.get_novel_stats(period)

    return BaseResponse(
        data=stats,
        message="获取小说统计成功"
    )


@router.get("/stats/revenue", response_model=BaseResponse[RevenueStatsResponse], summary="获取收入统计")
async def get_revenue_stats(
        period: str = Query("7d", description="统计周期"),
        current_admin: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> Any:
    """获取收入统计信息"""

    stats = await admin_service.get_revenue_stats(period)

    return BaseResponse(
        data=stats,
        message="获取收入统计成功"
    )


# 用户管理
@router.get("/users", response_model=ListResponse[UserResponse], summary="获取用户列表")
async def get_users(
        keyword: Optional[str] = Query(None, description="搜索关键词"),
        status: Optional[str] = Query(None, description="用户状态"),
        role: Optional[str] = Query(None, description="用户角色"),
        sort_by: str = Query("created_at", description="排序字段"),
        sort_order: str = Query("desc", description="排序方向"),
        pagination: dict = Depends(get_pagination_params),
        current_admin: User = Depends(get_current_admin_user),
        user_service: UserService = Depends(get_user_service)
) -> Any:
    """获取用户列表"""

    users, total = await user_service.get_users_for_admin(
        keyword=keyword,
        status=status,
        role=role,
        sort_by=sort_by,
        sort_order=sort_order,
        **pagination
    )

    return ListResponse(
        data=users,
        pagination={
            "page": pagination["page"],
            "page_size": pagination["page_size"],
            "total": total,
            "total_pages": (total + pagination["page_size"] - 1) // pagination["page_size"],
            "has_more": total > pagination["offset"] + len(users),
            "has_next_page": pagination["page"] * pagination["page_size"] < total,
            "has_previous_page": pagination["page"] > 1
        },
        message="获取用户列表成功"
    )


@router.get("/users/{user_id}", response_model=BaseResponse[UserResponse], summary="获取用户详情")
async def get_user_detail(
        user_id: str,
        current_admin: User = Depends(get_current_admin_user),
        user_service: UserService = Depends(get_user_service)
) -> Any:
    """获取用户详情"""

    user = await user_service.get_user_by_id(user_id)

    return BaseResponse(
        data=user,
        message="获取用户详情成功"
    )


@router.put("/users/{user_id}/status", response_model=SuccessResponse, summary="更新用户状态")
async def update_user_status(
        user_id: str,
        status: str,
        reason: Optional[str] = None,
        current_admin: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> Any:
    """更新用户状态（封禁/解封）"""

    await admin_service.update_user_status(
        user_id=user_id,
        status=status,
        reason=reason,
        admin_id=current_admin.id
    )

    return SuccessResponse(message="用户状态更新成功")


@router.delete("/users/{user_id}", response_model=SuccessResponse, summary="删除用户")
async def delete_user(
        user_id: str,
        current_admin: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> Any:
    """删除用户"""

    await admin_service.delete_user(user_id, current_admin.id)

    return SuccessResponse(message="用户删除成功")


# 小说管理
@router.get("/novels", response_model=ListResponse[NovelBasicResponse], summary="获取小说列表")
async def get_novels(
        keyword: Optional[str] = Query(None, description="搜索关键词"),
        status: Optional[str] = Query(None, description="小说状态"),
        category_id: Optional[str] = Query(None, description="分类ID"),
        author_id: Optional[str] = Query(None, description="作者ID"),
        sort_by: str = Query("created_at", description="排序字段"),
        sort_order: str = Query("desc", description="排序方向"),
        pagination: dict = Depends(get_pagination_params),
        current_admin: User = Depends(get_current_admin_user),
        novel_service: NovelService = Depends(get_novel_service)
) -> Any:
    """获取小说列表"""

    novels, total = await novel_service.get_novels_for_admin(
        keyword=keyword,
        status=status,
        category_id=category_id,
        author_id=author_id,
        sort_by=sort_by,
        sort_order=sort_order,
        **pagination
    )

    return ListResponse(
        data=novels,
        pagination={
            "page": pagination["page"],
            "page_size": pagination["page_size"],
            "total": total,
            "total_pages": (total + pagination["page_size"] - 1) // pagination["page_size"],
            "has_more": total > pagination["offset"] + len(novels),
            "has_next_page": pagination["page"] * pagination["page_size"] < total,
            "has_previous_page": pagination["page"] > 1
        },
        message="获取小说列表成功"
    )


@router.put("/novels/{novel_id}/status", response_model=SuccessResponse, summary="更新小说状态")
async def update_novel_status(
        novel_id: str,
        status: str,
        reason: Optional[str] = None,
        current_admin: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> Any:
    """更新小说状态（审核/下架）"""

    await admin_service.update_novel_status(
        novel_id=novel_id,
        status=status,
        reason=reason,
        admin_id=current_admin.id
    )

    return SuccessResponse(message="小说状态更新成功")


@router.delete("/novels/{novel_id}", response_model=SuccessResponse, summary="删除小说")
async def delete_novel(
        novel_id: str,
        current_admin: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> Any:
    """删除小说"""

    await admin_service.delete_novel(novel_id, current_admin.id)

    return SuccessResponse(message="小说删除成功")


# 管理员管理
@router.get("/admins", response_model=ListResponse[AdminUserResponse], summary="获取管理员列表")
async def get_admins(
        pagination: dict = Depends(get_pagination_params),
        current_admin: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> Any:
    """获取管理员列表"""

    admins, total = await admin_service.get_admins(**pagination)

    return ListResponse(
        data=admins,
        pagination={
            "page": pagination["page"],
            "page_size": pagination["page_size"],
            "total": total,
            "total_pages": (total + pagination["page_size"] - 1) // pagination["page_size"],
            "has_more": total > pagination["offset"] + len(admins),
            "has_next_page": pagination["page"] * pagination["page_size"] < total,
            "has_previous_page": pagination["page"] > 1
        },
        message="获取管理员列表成功"
    )


@router.post("/admins", response_model=BaseResponse[AdminUserResponse], summary="创建管理员")
async def create_admin(
        admin_data: AdminUserCreate,
        current_admin: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> Any:
    """创建管理员"""

    admin = await admin_service.create_admin(admin_data, current_admin.id)

    return BaseResponse(
        data=admin,
        message="管理员创建成功"
    )


@router.put("/admins/{admin_id}", response_model=BaseResponse[AdminUserResponse], summary="更新管理员")
async def update_admin(
        admin_id: str,
        admin_data: AdminUserUpdate,
        current_admin: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> Any:
    """更新管理员信息"""

    admin = await admin_service.update_admin(admin_id, admin_data, current_admin.id)

    return BaseResponse(
        data=admin,
        message="管理员更新成功"
    )


@router.delete("/admins/{admin_id}", response_model=SuccessResponse, summary="删除管理员")
async def delete_admin(
        admin_id: str,
        current_admin: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> Any:
    """删除管理员"""

    await admin_service.delete_admin(admin_id, current_admin.id)

    return SuccessResponse(message="管理员删除成功")


# 操作日志
@router.get("/logs", response_model=ListResponse[AdminLogResponse], summary="获取操作日志")
async def get_admin_logs(
        admin_id: Optional[str] = Query(None, description="管理员ID"),
        action: Optional[str] = Query(None, description="操作类型"),
        start_date: Optional[str] = Query(None, description="开始日期"),
        end_date: Optional[str] = Query(None, description="结束日期"),
        pagination: dict = Depends(get_pagination_params),
        current_admin: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> Any:
    """获取操作日志"""

    logs, total = await admin_service.get_admin_logs(
        admin_id=admin_id,
        action=action,
        start_date=start_date,
        end_date=end_date,
        **pagination
    )

    return ListResponse(
        data=logs,
        pagination={
            "page": pagination["page"],
            "page_size": pagination["page_size"],
            "total": total,
            "total_pages": (total + pagination["page_size"] - 1) // pagination["page_size"],
            "has_more": total > pagination["offset"] + len(logs),
            "has_next_page": pagination["page"] * pagination["page_size"] < total,
            "has_previous_page": pagination["page"] > 1
        },
        message="获取操作日志成功"
    )


# 内容审核
@router.get("/moderation/pending", response_model=ListResponse[dict], summary="获取待审核内容")
async def get_pending_moderation(
        content_type: Optional[str] = Query(None, description="内容类型"),
        pagination: dict = Depends(get_pagination_params),
        current_admin: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> Any:
    """获取待审核内容"""

    items, total = await admin_service.get_pending_moderation(
        content_type=content_type,
        **pagination
    )

    return ListResponse(
        data=items,
        pagination={
            "page": pagination["page"],
            "page_size": pagination["page_size"],
            "total": total,
            "total_pages": (total + pagination["page_size"] - 1) // pagination["page_size"],
            "has_more": total > pagination["offset"] + len(items),
            "has_next_page": pagination["page"] * pagination["page_size"] < total,
            "has_previous_page": pagination["page"] > 1
        },
        message="获取待审核内容成功"
    )


@router.post("/moderation/{item_id}/approve", response_model=SuccessResponse, summary="审核通过")
async def approve_content(
        item_id: str,
        content_type: str,
        current_admin: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> Any:
    """审核通过"""

    await admin_service.approve_content(
        item_id=item_id,
        content_type=content_type,
        admin_id=current_admin.id
    )

    return SuccessResponse(message="审核通过")


@router.post("/moderation/{item_id}/reject", response_model=SuccessResponse, summary="审核拒绝")
async def reject_content(
        item_id: str,
        content_type: str,
        reason: str,
        current_admin: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> Any:
    """审核拒绝"""

    await admin_service.reject_content(
        item_id=item_id,
        content_type=content_type,
        reason=reason,
        admin_id=current_admin.id
    )

    return SuccessResponse(message="审核拒绝")


# 系统配置
@router.get("/config", response_model=BaseResponse[dict], summary="获取系统配置")
async def get_system_config(
        current_admin: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> Any:
    """获取系统配置"""

    config = await admin_service.get_system_config()

    return BaseResponse(
        data=config,
        message="获取系统配置成功"
    )


@router.put("/config", response_model=SuccessResponse, summary="更新系统配置")
async def update_system_config(
        config_data: dict,
        current_admin: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> Any:
    """更新系统配置"""

    await admin_service.update_system_config(config_data, current_admin.id)

    return SuccessResponse(message="系统配置更新成功")


# 数据导出
@router.post("/export/users", response_model=BaseResponse[dict], summary="导出用户数据")
async def export_users(
        format: str = "csv",
        filters: Optional[dict] = None,
        current_admin: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> Any:
    """导出用户数据"""

    result = await admin_service.export_users(format, filters, current_admin.id)

    return BaseResponse(
        data=result,
        message="用户数据导出成功"
    )


@router.post("/export/novels", response_model=BaseResponse[dict], summary="导出小说数据")
async def export_novels(
        format: str = "csv",
        filters: Optional[dict] = None,
        current_admin: User = Depends(get_current_admin_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> Any:
    """导出小说数据"""

    result = await admin_service.export_novels(format, filters, current_admin.id)

    return BaseResponse(
        data=result,
        message="小说数据导出成功"
    )