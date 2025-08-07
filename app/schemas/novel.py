"""
小说相关的响应模型 - 最小化版本
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
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


class NovelDetailResponse(BaseModel):
    """小说详情响应模型"""
    id: str = Field(..., description="小说ID")
    title: str = Field(..., description="小说标题")
    description: str = Field(..., description="小说描述")
    author_name: str = Field(..., description="作者名称")
    category_name: str = Field(..., description="分类名称")
    status: str = Field(..., description="小说状态")
    created_at: datetime = Field(..., description="创建时间")


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
    keyword: str = Field(..., min_length=1, max_length=100, description="搜索关键词")
    category_id: Optional[str] = Field(None, description="分类ID")
    status: Optional[str] = Field(None, description="小说状态")
    is_free: Optional[bool] = Field(None, description="是否免费")
    sort_by: Optional[str] = Field(None, description="排序方式")
    sort_order: Optional[str] = Field(None, description="排序顺序")