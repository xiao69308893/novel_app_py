"""
书架相关的Pydantic模型
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BookshelfItemResponse(BaseModel):
    """书架项目响应模型"""
    id: UUID
    novel_id: UUID
    novel_title: str
    novel_cover_url: Optional[str] = None
    author_name: str
    last_read_chapter_id: Optional[UUID] = None
    last_read_chapter_title: Optional[str] = None
    reading_progress: float = Field(default=0.0, ge=0.0, le=1.0)
    last_read_at: Optional[datetime] = None
    added_at: datetime
    is_favorite: bool = False
    
    class Config:
        from_attributes = True


class BookshelfResponse(BaseModel):
    """书架响应模型"""
    items: List[BookshelfItemResponse]
    total: int
    page: int
    page_size: int
    
    class Config:
        from_attributes = True


class AddToBookshelfRequest(BaseModel):
    """添加到书架请求模型"""
    novel_id: UUID


class RemoveFromBookshelfRequest(BaseModel):
    """从书架移除请求模型"""
    novel_id: UUID


class BookshelfSortRequest(BaseModel):
    """书架排序请求模型"""
    sort_by: str = Field(default="last_read_at", description="排序字段")
    sort_order: str = Field(default="desc", description="排序顺序: asc/desc")


class ReadingHistoryResponse(BaseModel):
    """阅读历史响应模型"""
    id: UUID
    novel_id: UUID
    novel_title: str
    novel_cover_url: Optional[str] = None
    chapter_id: UUID
    chapter_title: str
    chapter_number: int
    read_at: datetime
    reading_duration: Optional[int] = None  # 阅读时长（秒）
    
    class Config:
        from_attributes = True


class ReadingHistoryListResponse(BaseModel):
    """阅读历史列表响应模型"""
    items: List[ReadingHistoryResponse]
    total: int
    page: int
    page_size: int
    
    class Config:
        from_attributes = True


class BookshelfCreateRequest(BaseModel):
    """创建书架请求模型"""
    name: str = Field(..., min_length=1, max_length=50, description="书架名称")
    description: Optional[str] = Field(None, max_length=200, description="书架描述")
    is_public: bool = Field(default=False, description="是否公开")


class BookshelfUpdateRequest(BaseModel):
    """更新书架请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="书架名称")
    description: Optional[str] = Field(None, max_length=200, description="书架描述")
    is_public: Optional[bool] = Field(None, description="是否公开")


class FavoriteResponse(BaseModel):
    """收藏响应模型"""
    id: UUID
    novel_id: UUID
    novel_title: str
    novel_cover_url: Optional[str] = None
    author_name: str
    favorited_at: datetime
    
    class Config:
        from_attributes = True


class FavoriteCreateRequest(BaseModel):
    """添加收藏请求模型"""
    novel_id: UUID


class BookshelfNovelResponse(BaseModel):
    """书架小说响应模型"""
    id: UUID
    novel_id: UUID
    novel_title: str
    novel_cover_url: Optional[str] = None
    author_name: str
    added_at: datetime
    last_read_chapter_id: Optional[UUID] = None
    last_read_chapter_title: Optional[str] = None
    reading_progress: float = Field(default=0.0, ge=0.0, le=1.0)
    
    class Config:
        from_attributes = True