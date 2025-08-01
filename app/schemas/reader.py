"""
阅读器相关数据模式
定义阅读进度、书签、阅读设置等请求和响应的数据结构
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
import uuid


# 阅读进度相关
class ReadingProgressUpdate(BaseModel):
    """阅读进度更新请求"""
    novel_id: uuid.UUID = Field(..., description="小说ID")
    chapter_id: Optional[uuid.UUID] = Field(None, description="章节ID")
    chapter_number: int = Field(..., ge=1, description="章节号")
    position: int = Field(default=0, ge=0, description="章节内位置")
    progress: Decimal = Field(default=0, ge=0, le=1, description="整本书进度百分比")
    reading_time: Optional[int] = Field(None, ge=0, description="本次阅读时长(秒)")
    device_type: Optional[str] = Field(None, description="设备类型")

    class Config:
        schema_extra = {
            "example": {
                "novel_id": "123e4567-e89b-12d3-a456-426614174000",
                "chapter_id": "123e4567-e89b-12d3-a456-426614174001",
                "chapter_number": 10,
                "position": 500,
                "progress": 0.15,
                "reading_time": 300,
                "device_type": "mobile"
            }
        }


class ReadingProgressResponse(BaseModel):
    """阅读进度响应"""
    id: uuid.UUID = Field(..., description="进度ID")
    novel_id: uuid.UUID = Field(..., description="小说ID")
    chapter_id: Optional[uuid.UUID] = Field(None, description="当前章节ID")
    chapter_number: int = Field(..., description="章节号")
    position: int = Field(..., description="章节内位置")
    progress: Decimal = Field(..., description="整本书进度百分比")
    reading_time: int = Field(..., description="总阅读时间(分钟)")
    last_read_duration: int = Field(..., description="最后一次阅读时长")
    device_type: Optional[str] = Field(None, description="设备类型")

    # 小说信息
    novel_title: str = Field(..., description="小说标题")
    novel_cover: Optional[str] = Field(None, description="小说封面")
    total_chapters: int = Field(..., description="总章节数")

    # 章节信息
    current_chapter_title: Optional[str] = Field(None, description="当前章节标题")

    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "novel_id": "123e4567-e89b-12d3-a456-426614174001",
                "chapter_id": "123e4567-e89b-12d3-a456-426614174002",
                "chapter_number": 10,
                "position": 500,
                "progress": 0.15,
                "reading_time": 1200,
                "last_read_duration": 300,
                "device_type": "mobile",
                "novel_title": "修真世界",
                "novel_cover": "https://example.com/cover.jpg",
                "total_chapters": 100,
                "current_chapter_title": "第十章 突破",
                "created_at": "2023-01-01T12:00:00Z",
                "updated_at": "2023-01-01T12:30:00Z"
            }
        }


class ReadingProgressSyncRequest(BaseModel):
    """阅读进度同步请求"""
    progress_data: List[ReadingProgressUpdate] = Field(..., description="进度数据列表")
    device_id: Optional[str] = Field(None, description="设备ID")
    sync_timestamp: datetime = Field(..., description="同步时间戳")

    class Config:
        schema_extra = {
            "example": {
                "progress_data": [],
                "device_id": "mobile_001",
                "sync_timestamp": "2023-01-01T12:00:00Z"
            }
        }


class ReadingProgressSyncResponse(BaseModel):
    """阅读进度同步响应"""
    synced_count: int = Field(..., description="同步成功数量")
    failed_count: int = Field(..., description="同步失败数量")
    conflicts: List[Dict[str, Any]] = Field(..., description="冲突列表")
    last_sync_time: datetime = Field(..., description="最后同步时间")

    class Config:
        schema_extra = {
            "example": {
                "synced_count": 5,
                "failed_count": 0,
                "conflicts": [],
                "last_sync_time": "2023-01-01T12:00:00Z"
            }
        }


# 书签相关
class BookmarkCreateRequest(BaseModel):
    """书签创建请求"""
    novel_id: uuid.UUID = Field(..., description="小说ID")
    chapter_id: uuid.UUID = Field(..., description="章节ID")
    position: int = Field(..., ge=0, description="位置")
    title: Optional[str] = Field(None, max_length=200, description="书签标题")
    notes: Optional[str] = Field(None, max_length=500, description="书签备注")
    content_preview: Optional[str] = Field(None, max_length=200, description="内容预览")
    folder_name: str = Field(default='默认书签', max_length=100, description="文件夹名称")
    color: str = Field(default='#1890ff', description="颜色")

    @validator('color')
    def validate_color(cls, v):
        if not v.startswith('#') or len(v) != 7:
            raise ValueError('颜色必须是7位十六进制颜色代码')
        return v

    class Config:
        schema_extra = {
            "example": {
                "novel_id": "123e4567-e89b-12d3-a456-426614174000",
                "chapter_id": "123e4567-e89b-12d3-a456-426614174001",
                "position": 500,
                "title": "重要情节",
                "notes": "主角突破的关键章节",
                "content_preview": "李逍遥感受到体内真气的变化...",
                "folder_name": "重要章节",
                "color": "#ff4d4f"
            }
        }


class BookmarkUpdateRequest(BaseModel):
    """书签更新请求"""
    title: Optional[str] = Field(None, max_length=200, description="书签标题")
    notes: Optional[str] = Field(None, max_length=500, description="书签备注")
    folder_name: Optional[str] = Field(None, max_length=100, description="文件夹名称")
    color: Optional[str] = Field(None, description="颜色")

    @validator('color')
    def validate_color(cls, v):
        if v and (not v.startswith('#') or len(v) != 7):
            raise ValueError('颜色必须是7位十六进制颜色代码')
        return v

    class Config:
        schema_extra = {
            "example": {
                "title": "更新的书签标题",
                "notes": "更新的备注",
                "folder_name": "新文件夹",
                "color": "#52c41a"
            }
        }


class BookmarkResponse(BaseModel):
    """书签响应"""
    id: uuid.UUID = Field(..., description="书签ID")
    novel_id: uuid.UUID = Field(..., description="小说ID")
    chapter_id: uuid.UUID = Field(..., description="章节ID")
    position: int = Field(..., description="位置")
    title: Optional[str] = Field(None, description="书签标题")
    notes: Optional[str] = Field(None, description="书签备注")
    content_preview: Optional[str] = Field(None, description="内容预览")
    folder_name: str = Field(..., description="文件夹名称")
    color: str = Field(..., description="颜色")

    # 关联信息
    novel_title: str = Field(..., description="小说标题")
    chapter_title: str = Field(..., description="章节标题")
    chapter_number: int = Field(..., description="章节号")

    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "novel_id": "123e4567-e89b-12d3-a456-426614174001",
                "chapter_id": "123e4567-e89b-12d3-a456-426614174002",
                "position": 500,
                "title": "重要情节",
                "notes": "主角突破的关键章节",
                "content_preview": "李逍遥感受到体内真气的变化...",
                "folder_name": "重要章节",
                "color": "#ff4d4f",
                "novel_title": "修真世界",
                "chapter_title": "第十章 突破",
                "chapter_number": 10,
                "created_at": "2023-01-01T12:00:00Z",
                "updated_at": "2023-01-01T12:00:00Z"
            }
        }


class BookmarkListResponse(BaseModel):
    """书签列表响应"""
    items: List[BookmarkResponse] = Field(..., description="书签列表")
    folders: List[str] = Field(..., description="文件夹列表")
    total: int = Field(..., description="总数")
    has_more: bool = Field(..., description="是否有更多")

    class Config:
        schema_extra = {
            "example": {
                "items": [],
                "folders": ["默认书签", "重要章节", "精彩情节"],
                "total": 25,
                "has_more": True
            }
        }


# 阅读设置相关
class ReadingSettingsUpdate(BaseModel):
    """阅读设置更新请求"""
    # 外观设置
    theme: Optional[str] = Field(None, description="主题")
    font_family: Optional[str] = Field(None, description="字体")
    font_size: Optional[int] = Field(None, ge=12, le=24, description="字体大小")
    line_spacing: Optional[Decimal] = Field(None, ge=1.0, le=3.0, description="行间距")
    paragraph_spacing: Optional[Decimal] = Field(None, ge=0.5, le=2.0, description="段落间距")
    page_margin: Optional[int] = Field(None, ge=10, le=50, description="页边距")
    background_color: Optional[str] = Field(None, description="背景颜色")
    text_color: Optional[str] = Field(None, description="文字颜色")

    # 阅读行为
    auto_scroll: Optional[bool] = Field(None, description="自动滚动")
    scroll_speed: Optional[int] = Field(None, ge=1, le=10, description="滚动速度")
    page_turn_animation: Optional[bool] = Field(None, description="翻页动画")
    full_screen: Optional[bool] = Field(None, description="全屏阅读")

    # 功能设置
    show_progress: Optional[bool] = Field(None, description="显示进度")
    show_time: Optional[bool] = Field(None, description="显示时间")
    show_battery: Optional[bool] = Field(None, description="显示电量")
    vibrate_on_page_turn: Optional[bool] = Field(None, description="翻页震动")

    # 护眼设置
    night_mode: Optional[bool] = Field(None, description="夜间模式")
    blue_light_filter: Optional[bool] = Field(None, description="蓝光过滤")
    brightness: Optional[int] = Field(None, ge=0, le=100, description="亮度")

    @validator('theme')
    def validate_theme(cls, v):
        if v and v not in ['light', 'dark', 'sepia', 'green', 'custom']:
            raise ValueError('主题只能是light、dark、sepia、green或custom')
        return v

    class Config:
        schema_extra = {
            "example": {
                "theme": "dark",
                "font_size": 18,
                "line_spacing": 1.8,
                "page_margin": 25,
                "auto_scroll": False,
                "night_mode": True,
                "show_progress": True
            }
        }


class ReadingSettingsResponse(BaseModel):
    """阅读设置响应"""
    # 外观设置
    theme: str = Field(..., description="主题")
    font_family: str = Field(..., description="字体")
    font_size: int = Field(..., description="字体大小")
    line_spacing: Decimal = Field(..., description="行间距")
    paragraph_spacing: Decimal = Field(..., description="段落间距")
    page_margin: int = Field(..., description="页边距")
    background_color: str = Field(..., description="背景颜色")
    text_color: str = Field(..., description="文字颜色")

    # 阅读行为
    auto_scroll: bool = Field(..., description="自动滚动")
    scroll_speed: int = Field(..., description="滚动速度")
    page_turn_animation: bool = Field(..., description="翻页动画")
    full_screen: bool = Field(..., description="全屏阅读")

    # 功能设置
    show_progress: bool = Field(..., description="显示进度")
    show_time: bool = Field(..., description="显示时间")
    show_battery: bool = Field(..., description="显示电量")
    vibrate_on_page_turn: bool = Field(..., description="翻页震动")

    # 护眼设置
    night_mode: bool = Field(..., description="夜间模式")
    blue_light_filter: bool = Field(..., description="蓝光过滤")
    brightness: int = Field(..., description="亮度")

    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        orm_mode = True


# 阅读时长相关
class ReadingTimeUpdate(BaseModel):
    """阅读时长更新请求"""
    novel_id: uuid.UUID = Field(..., description="小说ID")
    reading_time: int = Field(..., ge=0, description="阅读时长(秒)")
    date: Optional[str] = Field(None, description="日期(YYYY-MM-DD)")

    class Config:
        schema_extra = {
            "example": {
                "novel_id": "123e4567-e89b-12d3-a456-426614174000",
                "reading_time": 1800,
                "date": "2023-01-01"
            }
        }


class ReadingStatsResponse(BaseModel):
    """阅读统计响应"""
    # 今日统计
    today_reading_time: int = Field(..., description="今日阅读时长(分钟)")
    today_chapters_read: int = Field(..., description="今日阅读章节数")
    today_words_read: int = Field(..., description="今日阅读字数")

    # 本周统计
    week_reading_time: int = Field(..., description="本周阅读时长(分钟)")
    week_chapters_read: int = Field(..., description="本周阅读章节数")
    week_words_read: int = Field(..., description="本周阅读字数")

    # 本月统计
    month_reading_time: int = Field(..., description="本月阅读时长(分钟)")
    month_chapters_read: int = Field(..., description="本月阅读章节数")
    month_words_read: int = Field(..., description="本月阅读字数")

    # 总体统计
    total_reading_time: int = Field(..., description="总阅读时长(分钟)")
    total_chapters_read: int = Field(..., description="总阅读章节数")
    total_words_read: int = Field(..., description="总阅读字数")
    total_books_finished: int = Field(..., description="读完的书籍数")

    # 连续统计
    streak_days: int = Field(..., description="连续阅读天数")
    max_streak_days: int = Field(..., description="最长连续阅读天数")

    # 阅读习惯
    favorite_reading_time: Optional[str] = Field(None, description="最喜欢的阅读时段")
    average_daily_time: int = Field(..., description="日平均阅读时长(分钟)")
    reading_speed: int = Field(..., description="阅读速度(字/分钟)")

    # 偏好分析
    favorite_genres: List[Dict[str, Any]] = Field(..., description="喜爱的类型")
    reading_history_chart: List[Dict[str, Any]] = Field(..., description="阅读历史图表数据")

    class Config:
        schema_extra = {
            "example": {
                "today_reading_time": 120,
                "today_chapters_read": 5,
                "today_words_read": 15000,
                "week_reading_time": 600,
                "week_chapters_read": 25,
                "week_words_read": 75000,
                "total_reading_time": 18000,
                "total_chapters_read": 1500,
                "total_words_read": 4500000,
                "total_books_finished": 15,
                "streak_days": 7,
                "max_streak_days": 30,
                "favorite_reading_time": "晚上9-11点",
                "average_daily_time": 90,
                "reading_speed": 250,
                "favorite_genres": [
                    {"genre": "玄幻", "count": 8, "percentage": 53.3},
                    {"genre": "都市", "count": 4, "percentage": 26.7}
                ],
                "reading_history_chart": []
            }
        }


# 章节购买相关
class ChapterPurchaseRequest(BaseModel):
    """章节购买请求"""
    novel_id: uuid.UUID = Field(..., description="小说ID")
    chapter_id: uuid.UUID = Field(..., description="章节ID")
    payment_method: Optional[str] = Field(None, description="支付方式")

    class Config:
        schema_extra = {
            "example": {
                "novel_id": "123e4567-e89b-12d3-a456-426614174000",
                "chapter_id": "123e4567-e89b-12d3-a456-426614174001",
                "payment_method": "coins"
            }
        }


class ChapterPurchaseResponse(BaseModel):
    """章节购买响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    transaction_id: Optional[str] = Field(None, description="交易ID")
    coins_spent: int = Field(..., description="消耗金币")
    remaining_coins: int = Field(..., description="剩余金币")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "章节购买成功",
                "transaction_id": "tx_123456789",
                "coins_spent": 5,
                "remaining_coins": 95
            }
        }


class ChapterPurchaseStatusResponse(BaseModel):
    """章节购买状态响应"""
    purchased: bool = Field(..., description="是否已购买")
    can_read: bool = Field(..., description="是否可以阅读")
    price: Decimal = Field(..., description="章节价格")
    is_free: bool = Field(..., description="是否免费")
    is_vip: bool = Field(..., description="是否VIP章节")
    user_coins: Optional[int] = Field(None, description="用户金币")

    class Config:
        schema_extra = {
            "example": {
                "purchased": False,
                "can_read": False,
                "price": 5,
                "is_free": False,
                "is_vip": True,
                "user_coins": 100
            }
        }