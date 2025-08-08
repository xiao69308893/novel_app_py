"""
小说相关的响应模型 - 最小化版本
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
import uuid


# 基础响应类
class CategoryResponse(BaseModel):
    """分类响应模型"""
    id: str = Field(..., description="分类ID")
    name: str = Field(..., description="分类名称")


class TagResponse(BaseModel):
    """标签响应模型"""
    id: str = Field(..., description="标签ID")
    name: str = Field(..., description="标签名称")


class AuthorResponse(BaseModel):
    """作者响应模型"""
    id: str = Field(..., description="作者ID")
    name: str = Field(..., description="作者名称")


class NovelBasicResponse(BaseModel):
    """小说基础响应模型"""
    id: str = Field(..., description="小说ID")
    title: str = Field(..., description="小说标题")
    author_name: str = Field(..., description="作者名称")
    status: str = Field(..., description="小说状态")


class NovelResponse(BaseModel):
    """小说基础响应"""
    id: uuid.UUID = Field(..., description="小说ID")
    title: str = Field(..., description="小说标题")
    author_name: str = Field(..., description="作者名称")
    description: str = Field(..., description="小说简介")
    cover_url: Optional[str] = Field(None, description="封面图片URL")
    category: str = Field(..., description="分类")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    status: str = Field(..., description="连载状态")
    word_count: int = Field(..., description="总字数")
    chapter_count: int = Field(..., description="章节数")
    rating: float = Field(..., description="评分")
    view_count: int = Field(..., description="浏览量")
    favorite_count: int = Field(..., description="收藏数")
    is_vip: bool = Field(..., description="是否VIP小说")
    is_finished: bool = Field(..., description="是否完结")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class NovelDetailResponse(BaseModel):
    """小说详情响应"""
    id: uuid.UUID = Field(..., description="小说ID")
    title: str = Field(..., description="小说标题")
    author_name: str = Field(..., description="作者名称")
    description: str = Field(..., description="小说简介")
    cover_url: Optional[str] = Field(None, description="封面图片URL")
    category: str = Field(..., description="分类")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    status: str = Field(..., description="连载状态")
    word_count: int = Field(..., description="总字数")
    chapter_count: int = Field(..., description="章节数")
    rating: float = Field(..., description="评分")
    rating_count: int = Field(..., description="评分人数")
    view_count: int = Field(..., description="浏览量")
    favorite_count: int = Field(..., description="收藏数")
    is_vip: bool = Field(..., description="是否VIP小说")
    is_finished: bool = Field(..., description="是否完结")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    last_chapter_title: Optional[str] = Field(None, description="最新章节标题")
    last_chapter_updated_at: Optional[datetime] = Field(None, description="最新章节更新时间")
    is_favorited: bool = Field(False, description="是否已收藏")
    user_rating: Optional[int] = Field(None, description="用户评分")

    class Config:
        from_attributes = True


class ChapterBasicResponse(BaseModel):
    """章节基础响应模型"""
    id: str = Field(..., description="章节ID")
    title: str = Field(..., description="章节标题")
    chapter_number: int = Field(..., description="章节序号")


class ChapterDetailResponse(BaseModel):
    """章节详情响应模型"""
    id: str = Field(..., description="章节ID")
    title: str = Field(..., description="章节标题")
    content: str = Field(..., description="章节内容")
    chapter_number: int = Field(..., description="章节序号")
    created_at: datetime = Field(..., description="创建时间")


class CommentResponse(BaseModel):
    """评论响应模型"""
    id: str = Field(..., description="评论ID")
    content: str = Field(..., description="评论内容")
    user_id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    created_at: datetime = Field(..., description="创建时间")


class NovelListResponse(BaseModel):
    """小说列表响应"""
    total: int = Field(..., description="总数")
    has_more: bool = Field(..., description="是否有更多")


class ChapterListResponse(BaseModel):
    """章节列表响应"""
    total: int = Field(..., description="总数")
    has_more: bool = Field(..., description="是否有更多")


class CommentCreateRequest(BaseModel):
    """评论创建请求"""
    content: str = Field(..., min_length=1, max_length=1000, description="评论内容")
    novel_id: str = Field(..., description="小说ID")
    chapter_id: Optional[str] = Field(None, description="章节ID")
    parent_id: Optional[str] = Field(None, description="父评论ID")


class NovelSearchRequest(BaseModel):
    """小说搜索请求"""
    keyword: Optional[str] = Field(None, min_length=1, max_length=100, description="搜索关键词")
    category_id: Optional[str] = Field(None, description="分类ID")
    status: Optional[str] = Field(None, description="小说状态")
    language: Optional[str] = Field(None, description="语言")
    is_free: Optional[bool] = Field(None, description="是否免费")
    word_count_min: Optional[int] = Field(None, description="最小字数")
    word_count_max: Optional[int] = Field(None, description="最大字数")
    rating_min: Optional[float] = Field(None, description="最低评分")
    tags: Optional[list] = Field(None, description="标签列表")
    sort_by: Optional[str] = Field(None, description="排序方式")
    sort_order: Optional[str] = Field(None, description="排序顺序")


class NovelRatingRequest(BaseModel):
    """小说评分请求"""
    novel_id: str = Field(..., description="小说ID")
    rating: float = Field(..., ge=1.0, le=5.0, description="评分(1-5)")
    comment: Optional[str] = Field(None, max_length=500, description="评价内容")


class AdjacentChaptersResponse(BaseModel):
    """相邻章节响应"""
    previous: Optional[ChapterBasicResponse] = Field(None, description="上一章")
    next: Optional[ChapterBasicResponse] = Field(None, description="下一章")