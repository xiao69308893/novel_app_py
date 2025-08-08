"""
章节相关的响应模型
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
import uuid


class ChapterBasicResponse(BaseModel):
    """章节基础响应模型"""
    id: uuid.UUID = Field(..., description="章节ID")
    title: str = Field(..., description="章节标题")
    chapter_number: int = Field(..., description="章节序号")
    is_vip: bool = Field(..., description="是否VIP章节")
    is_free: bool = Field(..., description="是否免费")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class ChapterResponse(BaseModel):
    """章节响应模型"""
    id: uuid.UUID = Field(..., description="章节ID")
    title: str = Field(..., description="章节标题")
    chapter_number: int = Field(..., description="章节序号")
    word_count: int = Field(..., description="字数")
    is_vip: bool = Field(..., description="是否VIP章节")
    is_free: bool = Field(..., description="是否免费")
    price: Optional[float] = Field(None, description="章节价格")
    publish_status: str = Field(..., description="发布状态")
    created_at: datetime = Field(..., description="创建时间")
    published_at: Optional[datetime] = Field(None, description="发布时间")

    class Config:
        from_attributes = True


class ChapterDetailResponse(BaseModel):
    """章节详情响应模型"""
    id: uuid.UUID = Field(..., description="章节ID")
    title: str = Field(..., description="章节标题")
    content: str = Field(..., description="章节内容")
    chapter_number: int = Field(..., description="章节序号")
    word_count: int = Field(..., description="字数")
    is_vip: bool = Field(..., description="是否VIP章节")
    is_free: bool = Field(..., description="是否免费")
    price: Optional[float] = Field(None, description="章节价格")
    publish_status: str = Field(..., description="发布状态")
    view_count: int = Field(..., description="阅读次数")
    created_at: datetime = Field(..., description="创建时间")
    published_at: Optional[datetime] = Field(None, description="发布时间")

    class Config:
        from_attributes = True


class ChapterListResponse(BaseModel):
    """章节列表响应"""
    chapters: List[ChapterResponse] = Field(..., description="章节列表")
    total: int = Field(..., description="总数")
    has_more: bool = Field(..., description="是否有更多")

    class Config:
        json_schema_extra = {
            "example": {
                "chapters": [],
                "total": 100,
                "has_more": True
            }
        }


class ChapterCreateRequest(BaseModel):
    """章节创建请求"""
    title: str = Field(..., min_length=1, max_length=200, description="章节标题")
    content: str = Field(..., min_length=1, description="章节内容")
    chapter_number: int = Field(..., ge=1, description="章节序号")
    is_vip: bool = Field(False, description="是否VIP章节")
    is_free: bool = Field(True, description="是否免费")
    price: Optional[float] = Field(None, ge=0, description="章节价格")
    publish_status: str = Field("draft", description="发布状态")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "第一章 开始",
                "content": "这是章节内容...",
                "chapter_number": 1,
                "is_vip": False,
                "is_free": True,
                "price": None,
                "publish_status": "draft"
            }
        }


class ChapterUpdateRequest(BaseModel):
    """章节更新请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="章节标题")
    content: Optional[str] = Field(None, min_length=1, description="章节内容")
    is_vip: Optional[bool] = Field(None, description="是否VIP章节")
    is_free: Optional[bool] = Field(None, description="是否免费")
    price: Optional[float] = Field(None, ge=0, description="章节价格")
    publish_status: Optional[str] = Field(None, description="发布状态")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "第一章 开始（修订版）",
                "content": "这是修订后的章节内容...",
                "publish_status": "published"
            }
        }


class BookmarkCreateRequest(BaseModel):
    """书签创建请求"""
    chapter_id: uuid.UUID = Field(..., description="章节ID")
    position: str = Field(..., description="书签位置")
    note: Optional[str] = Field(None, max_length=500, description="书签备注")

    class Config:
        json_schema_extra = {
            "example": {
                "chapter_id": "123e4567-e89b-12d3-a456-426614174000",
                "position": "100",
                "note": "重要情节"
            }
        }


class BookmarkResponse(BaseModel):
    """书签响应"""
    id: uuid.UUID = Field(..., description="书签ID")
    chapter_id: uuid.UUID = Field(..., description="章节ID")
    chapter_title: str = Field(..., description="章节标题")
    position: str = Field(..., description="书签位置")
    note: Optional[str] = Field(None, description="书签备注")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class ReadingProgressRequest(BaseModel):
    """阅读进度请求"""
    chapter_id: uuid.UUID = Field(..., description="章节ID")
    progress: float = Field(..., ge=0.0, le=1.0, description="阅读进度(0-1)")
    reading_time: int = Field(..., ge=0, description="阅读时长(秒)")

    class Config:
        json_schema_extra = {
            "example": {
                "chapter_id": "123e4567-e89b-12d3-a456-426614174000",
                "progress": 0.5,
                "reading_time": 300
            }
        }


class ReadingProgressResponse(BaseModel):
    """阅读进度响应"""
    novel_id: uuid.UUID = Field(..., description="小说ID")
    chapter_id: uuid.UUID = Field(..., description="章节ID")
    chapter_number: int = Field(..., description="章节序号")
    progress: float = Field(..., description="阅读进度")
    reading_time: int = Field(..., description="阅读时长")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True