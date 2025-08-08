# app/schemas/admin.py
"""
管理员相关的Pydantic模型
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class AdminUserResponse(BaseModel):
    """管理员用户响应模型"""
    id: uuid.UUID
    username: str
    email: str
    role: str
    status: str
    created_at: datetime
    last_login_at: Optional[datetime] = None
    permissions: List[str] = []

    class Config:
        from_attributes = True


class AdminUserCreate(BaseModel):
    """创建管理员用户请求模型"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=6)
    role: str = Field(default="admin")
    permissions: List[str] = []


class AdminUserUpdate(BaseModel):
    """更新管理员用户请求模型"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = Field(None, pattern=r'^[^@]+@[^@]+\.[^@]+$')
    role: Optional[str] = None
    status: Optional[str] = None
    permissions: Optional[List[str]] = None


class SystemStatsResponse(BaseModel):
    """系统统计响应模型"""
    total_users: int
    active_users: int
    total_novels: int
    published_novels: int
    total_chapters: int
    total_views: int
    total_revenue: float
    server_uptime: str
    database_size: str
    cache_hit_rate: float
    api_requests_today: int
    error_rate: float

    class Config:
        from_attributes = True


class UserStatsResponse(BaseModel):
    """用户统计响应模型"""
    new_users_count: int
    active_users_count: int
    vip_users_count: int
    banned_users_count: int
    user_growth_rate: float
    retention_rate: float
    daily_active_users: List[Dict[str, Any]]
    user_distribution_by_region: Dict[str, int]
    user_age_distribution: Dict[str, int]

    class Config:
        from_attributes = True


class NovelStatsResponse(BaseModel):
    """小说统计响应模型"""
    new_novels_count: int
    published_novels_count: int
    total_chapters_count: int
    total_words_count: int
    average_rating: float
    popular_categories: List[Dict[str, Any]]
    top_authors: List[Dict[str, Any]]
    reading_trends: List[Dict[str, Any]]
    completion_rate: float

    class Config:
        from_attributes = True


class RevenueStatsResponse(BaseModel):
    """收入统计响应模型"""
    total_revenue: float
    subscription_revenue: float
    purchase_revenue: float
    ad_revenue: float
    revenue_growth_rate: float
    average_revenue_per_user: float
    daily_revenue: List[Dict[str, Any]]
    revenue_by_source: Dict[str, float]
    top_paying_users: List[Dict[str, Any]]

    class Config:
        from_attributes = True


class AdminLogResponse(BaseModel):
    """管理员日志响应模型"""
    id: uuid.UUID
    admin_id: uuid.UUID
    admin_username: str
    action: str
    target_type: str
    target_id: Optional[str] = None
    details: Dict[str, Any]
    ip_address: str
    user_agent: str
    created_at: datetime

    class Config:
        from_attributes = True


class AdminLogCreate(BaseModel):
    """创建管理员日志请求模型"""
    action: str
    target_type: str
    target_id: Optional[str] = None
    details: Dict[str, Any] = {}


class UserStatusUpdate(BaseModel):
    """用户状态更新请求模型"""
    status: str = Field(..., pattern="^(active|banned|suspended)$")
    reason: Optional[str] = None


class NovelStatusUpdate(BaseModel):
    """小说状态更新请求模型"""
    status: str = Field(..., pattern="^(draft|reviewing|published|rejected|banned)$")
    reason: Optional[str] = None


class ContentModerationRequest(BaseModel):
    """内容审核请求模型"""
    content_type: str = Field(..., pattern="^(novel|chapter|comment|review)$")
    content_id: str
    action: str = Field(..., pattern="^(approve|reject|ban)$")
    reason: Optional[str] = None


class SystemConfigUpdate(BaseModel):
    """系统配置更新请求模型"""
    config_key: str
    config_value: Any
    description: Optional[str] = None


class BackupRequest(BaseModel):
    """备份请求模型"""
    backup_type: str = Field(..., pattern="^(full|incremental|database|files)$")
    description: Optional[str] = None


class MaintenanceRequest(BaseModel):
    """维护请求模型"""
    maintenance_type: str = Field(..., pattern="^(scheduled|emergency|update)$")
    start_time: datetime
    estimated_duration: int  # 分钟
    description: str
    notify_users: bool = True


class AnnouncementCreate(BaseModel):
    """公告创建请求模型"""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    type: str = Field(..., pattern="^(info|warning|maintenance|update)$")
    priority: int = Field(default=1, ge=1, le=5)
    target_audience: str = Field(default="all", pattern="^(all|vip|admin)$")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_popup: bool = False


class AnnouncementUpdate(BaseModel):
    """公告更新请求模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    type: Optional[str] = Field(None, pattern="^(info|warning|maintenance|update)$")
    priority: Optional[int] = Field(None, ge=1, le=5)
    target_audience: Optional[str] = Field(None, pattern="^(all|vip|admin)$")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_popup: Optional[bool] = None
    is_active: Optional[bool] = None


class AnnouncementResponse(BaseModel):
    """公告响应模型"""
    id: uuid.UUID
    title: str
    content: str
    type: str
    priority: int
    target_audience: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    is_popup: bool
    is_active: bool
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True