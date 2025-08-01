"""
用户相关数据模式
定义用户资料、设置、统计等请求和响应的数据结构
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from decimal import Decimal
import uuid


# 用户资料相关
class UserProfileUpdate(BaseModel):
    """用户资料更新请求"""
    nickname: Optional[str] = Field(None, max_length=100, description="昵称")
    avatar_url: Optional[str] = Field(None, max_length=500, description="头像URL")
    gender: Optional[str] = Field(None, description="性别")
    birthday: Optional[date] = Field(None, description="生日")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")
    real_name: Optional[str] = Field(None, max_length=100, description="真实姓名")
    city: Optional[str] = Field(None, max_length=100, description="城市")
    country: Optional[str] = Field(None, max_length=100, description="国家")
    website: Optional[str] = Field(None, max_length=500, description="个人网站")

    @validator('gender')
    def validate_gender(cls, v):
        if v and v not in ['male', 'female', 'other']:
            raise ValueError('性别只能是male、female或other')
        return v

    class Config:
        schema_extra = {
            "example": {
                "nickname": "小说爱好者",
                "gender": "male",
                "birthday": "1990-01-01",
                "bio": "热爱阅读各种类型的小说",
                "city": "北京",
                "country": "中国"
            }
        }


class UserProfileResponse(BaseModel):
    """用户资料响应"""
    id: uuid.UUID = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: Optional[str] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, description="手机号")
    nickname: Optional[str] = Field(None, description="昵称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    gender: Optional[str] = Field(None, description="性别")
    birthday: Optional[date] = Field(None, description="生日")
    bio: Optional[str] = Field(None, description="个人简介")
    level: int = Field(..., description="用户等级")
    vip_level: int = Field(..., description="VIP等级")
    points: int = Field(..., description="积分")
    coins: int = Field(..., description="金币")
    experience: int = Field(..., description="经验值")
    is_verified: bool = Field(..., description="是否已验证")
    email_verified: bool = Field(..., description="邮箱是否已验证")
    phone_verified: bool = Field(..., description="手机号是否已验证")
    created_at: datetime = Field(..., description="注册时间")

    # 扩展资料
    real_name: Optional[str] = Field(None, description="真实姓名")
    city: Optional[str] = Field(None, description="城市")
    country: Optional[str] = Field(None, description="国家")
    timezone: Optional[str] = Field(None, description="时区")
    language: Optional[str] = Field(None, description="语言")
    website: Optional[str] = Field(None, description="个人网站")

    class Config:
        orm_mode = True


# 用户设置相关
class UserSettingsUpdate(BaseModel):
    """用户设置更新请求"""
    # 阅读设置
    reader_theme: Optional[str] = Field(None, description="阅读主题")
    font_size: Optional[int] = Field(None, ge=12, le=24, description="字体大小")
    line_spacing: Optional[Decimal] = Field(None, ge=1.0, le=3.0, description="行间距")
    page_margin: Optional[int] = Field(None, ge=10, le=50, description="页边距")
    auto_scroll: Optional[bool] = Field(None, description="自动滚动")

    # 通知设置
    email_notifications: Optional[bool] = Field(None, description="邮件通知")
    push_notifications: Optional[bool] = Field(None, description="推送通知")
    sms_notifications: Optional[bool] = Field(None, description="短信通知")

    # 隐私设置
    profile_public: Optional[bool] = Field(None, description="资料公开")
    reading_history_public: Optional[bool] = Field(None, description="阅读历史公开")
    allow_friend_requests: Optional[bool] = Field(None, description="允许好友请求")

    class Config:
        schema_extra = {
            "example": {
                "reader_theme": "dark",
                "font_size": 18,
                "line_spacing": 1.8,
                "page_margin": 25,
                "auto_scroll": False,
                "email_notifications": True,
                "push_notifications": True,
                "profile_public": True
            }
        }


class UserSettingsResponse(BaseModel):
    """用户设置响应"""
    # 阅读设置
    reader_theme: str = Field(..., description="阅读主题")
    font_size: int = Field(..., description="字体大小")
    line_spacing: Decimal = Field(..., description="行间距")
    page_margin: int = Field(..., description="页边距")
    auto_scroll: bool = Field(..., description="自动滚动")

    # 通知设置
    email_notifications: bool = Field(..., description="邮件通知")
    push_notifications: bool = Field(..., description="推送通知")
    sms_notifications: bool = Field(..., description="短信通知")

    # 隐私设置
    profile_public: bool = Field(..., description="资料公开")
    reading_history_public: bool = Field(..., description="阅读历史公开")
    allow_friend_requests: bool = Field(..., description="允许好友请求")

    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        orm_mode = True


# 用户统计相关
class UserStatisticsResponse(BaseModel):
    """用户统计响应"""
    # 阅读统计
    total_reading_time: int = Field(..., description="总阅读时间(分钟)")
    books_read: int = Field(..., description="已读完书籍数")
    chapters_read: int = Field(..., description="已读章节数")
    words_read: int = Field(..., description="已读字数")

    # 收藏统计
    favorites_count: int = Field(..., description="收藏数")
    bookmarks_count: int = Field(..., description="书签数")

    # 社交统计
    comments_count: int = Field(..., description="评论数")
    likes_received: int = Field(..., description="获得点赞数")

    # 翻译统计
    translations_created: int = Field(..., description="创建翻译数")
    translation_words: int = Field(..., description="翻译字数")

    # 日期统计
    streak_days: int = Field(..., description="连续签到天数")
    last_read_date: Optional[date] = Field(None, description="最后阅读日期")
    last_checkin_date: Optional[date] = Field(None, description="最后签到日期")

    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        orm_mode = True


# 签到相关
class CheckinResponse(BaseModel):
    """签到响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="签到消息")
    points_earned: int = Field(..., description="获得积分")
    streak_days: int = Field(..., description="连续签到天数")
    next_checkin_time: datetime = Field(..., description="下次签到时间")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "签到成功！连续签到7天",
                "points_earned": 10,
                "streak_days": 7,
                "next_checkin_time": "2023-01-02T00:00:00Z"
            }
        }


class CheckinStatusResponse(BaseModel):
    """签到状态响应"""
    can_checkin: bool = Field(..., description="是否可以签到")
    streak_days: int = Field(..., description="连续签到天数")
    last_checkin_date: Optional[date] = Field(None, description="最后签到日期")
    next_checkin_time: Optional[datetime] = Field(None, description="下次签到时间")
    checkin_rewards: List[Dict[str, Any]] = Field(..., description="签到奖励列表")

    class Config:
        schema_extra = {
            "example": {
                "can_checkin": True,
                "streak_days": 6,
                "last_checkin_date": "2023-01-01",
                "next_checkin_time": "2023-01-02T00:00:00Z",
                "checkin_rewards": [
                    {"day": 1, "points": 5, "coins": 0},
                    {"day": 7, "points": 10, "coins": 5}
                ]
            }
        }


# 阅读历史相关
class ReadingHistoryItem(BaseModel):
    """阅读历史项"""
    novel_id: uuid.UUID = Field(..., description="小说ID")
    novel_title: str = Field(..., description="小说标题")
    novel_cover: Optional[str] = Field(None, description="小说封面")
    chapter_id: Optional[uuid.UUID] = Field(None, description="章节ID")
    chapter_title: Optional[str] = Field(None, description="章节标题")
    chapter_number: Optional[int] = Field(None, description="章节号")
    reading_time: int = Field(..., description="阅读时长(分钟)")
    last_read_at: datetime = Field(..., description="最后阅读时间")

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "novel_id": "123e4567-e89b-12d3-a456-426614174000",
                "novel_title": "测试小说",
                "novel_cover": "https://example.com/cover.jpg",
                "chapter_id": "123e4567-e89b-12d3-a456-426614174001",
                "chapter_title": "第一章 开始",
                "chapter_number": 1,
                "reading_time": 30,
                "last_read_at": "2023-01-01T12:00:00Z"
            }
        }


class ReadingHistoryResponse(BaseModel):
    """阅读历史响应"""
    items: List[ReadingHistoryItem] = Field(..., description="阅读历史列表")
    total: int = Field(..., description="总数")
    has_more: bool = Field(..., description="是否有更多")

    class Config:
        schema_extra = {
            "example": {
                "items": [],
                "total": 50,
                "has_more": True
            }
        }


class AddReadingHistoryRequest(BaseModel):
    """添加阅读历史请求"""
    novel_id: uuid.UUID = Field(..., description="小说ID")
    chapter_id: Optional[uuid.UUID] = Field(None, description="章节ID")
    reading_time: int = Field(..., ge=0, description="阅读时长(秒)")
    last_position: Optional[str] = Field(None, description="最后阅读位置")

    class Config:
        schema_extra = {
            "example": {
                "novel_id": "123e4567-e89b-12d3-a456-426614174000",
                "chapter_id": "123e4567-e89b-12d3-a456-426614174001",
                "reading_time": 1800,
                "last_position": "100"
            }
        }


# 最近阅读
class RecentlyReadItem(BaseModel):
    """最近阅读项"""
    novel_id: uuid.UUID = Field(..., description="小说ID")
    novel_title: str = Field(..., description="小说标题")
    novel_cover: Optional[str] = Field(None, description="小说封面")
    author_name: str = Field(..., description="作者名")
    current_chapter: Optional[int] = Field(None, description="当前章节")
    total_chapters: int = Field(..., description="总章节数")
    progress: Decimal = Field(..., description="阅读进度")
    last_read_at: datetime = Field(..., description="最后阅读时间")

    class Config:
        orm_mode = True


# 数据导入导出
class DataExportResponse(BaseModel):
    """数据导出响应"""
    download_url: str = Field(..., description="下载链接")
    expires_at: datetime = Field(..., description="链接过期时间")
    file_size: int = Field(..., description="文件大小(字节)")

    class Config:
        schema_extra = {
            "example": {
                "download_url": "https://example.com/export/user_data.zip",
                "expires_at": "2023-01-02T00:00:00Z",
                "file_size": 1048576
            }
        }


class DataImportRequest(BaseModel):
    """数据导入请求"""
    data_path: str = Field(..., description="数据文件路径")
    options: Optional[Dict[str, Any]] = Field(None, description="导入选项")

    class Config:
        schema_extra = {
            "example": {
                "data_path": "/tmp/user_data.zip",
                "options": {
                    "overwrite": False,
                    "merge_duplicates": True
                }
            }
        }


class DataSyncResponse(BaseModel):
    """数据同步响应"""
    synced_items: int = Field(..., description="同步项目数")
    conflicts: int = Field(..., description="冲突数")
    last_sync_time: datetime = Field(..., description="最后同步时间")

    class Config:
        schema_extra = {
            "example": {
                "synced_items": 25,
                "conflicts": 2,
                "last_sync_time": "2023-01-01T12:00:00Z"
            }
        }


# 用户搜索
class UserSearchRequest(BaseModel):
    """用户搜索请求"""
    keyword: str = Field(..., min_length=1, description="搜索关键词")
    type: Optional[str] = Field(None, description="搜索类型")

    class Config:
        schema_extra = {
            "example": {
                "keyword": "科幻小说",
                "type": "favorites"
            }
        }