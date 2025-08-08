# app/schemas/comment.py
# -*- coding: utf-8 -*-
"""
评论相关的Pydantic模型
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class CommentBase(BaseModel):
    """评论基础模型"""
    content: str = Field(..., min_length=1, max_length=2000, description="评论内容")
    rating: Optional[int] = Field(None, ge=1, le=5, description="评分（1-5星）")
    spoiler: bool = Field(False, description="是否包含剧透")


class CommentCreate(CommentBase):
    """创建评论模型"""
    pass


class CommentCreateRequest(CommentBase):
    """创建评论请求模型"""
    target_type: str = Field(..., description="目标类型")
    target_id: str = Field(..., description="目标ID")
    parent_id: Optional[str] = Field(None, description="父评论ID")
    is_spoiler: bool = Field(False, description="是否包含剧透")


class CommentUpdate(BaseModel):
    """更新评论模型"""
    content: Optional[str] = Field(None, min_length=1, max_length=2000, description="评论内容")
    rating: Optional[int] = Field(None, ge=1, le=5, description="评分（1-5星）")
    spoiler: Optional[bool] = Field(None, description="是否包含剧透")


class CommentUpdateRequest(BaseModel):
    """更新评论请求模型"""
    content: Optional[str] = Field(None, min_length=1, max_length=2000, description="评论内容")
    is_spoiler: Optional[bool] = Field(None, description="是否包含剧透")


class CommentResponse(CommentBase):
    """评论响应模型"""
    id: str = Field(..., description="评论ID")
    user_id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    user_avatar: Optional[str] = Field(None, description="用户头像")
    novel_id: Optional[str] = Field(None, description="小说ID")
    chapter_id: Optional[str] = Field(None, description="章节ID")
    parent_id: Optional[str] = Field(None, description="父评论ID")
    like_count: int = Field(0, description="点赞数")
    reply_count: int = Field(0, description="回复数")
    is_liked: bool = Field(False, description="当前用户是否已点赞")
    is_author: bool = Field(False, description="是否为当前用户的评论")
    status: str = Field("active", description="评论状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class CommentReplyBase(BaseModel):
    """评论回复基础模型"""
    content: str = Field(..., min_length=1, max_length=1000, description="回复内容")


class CommentReplyCreate(CommentReplyBase):
    """创建评论回复模型"""
    pass


class CommentReplyResponse(CommentReplyBase):
    """评论回复响应模型"""
    id: str = Field(..., description="回复ID")
    comment_id: str = Field(..., description="评论ID")
    user_id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    user_avatar: Optional[str] = Field(None, description="用户头像")
    reply_to_user_id: Optional[str] = Field(None, description="回复目标用户ID")
    reply_to_username: Optional[str] = Field(None, description="回复目标用户名")
    like_count: int = Field(0, description="点赞数")
    is_liked: bool = Field(False, description="当前用户是否已点赞")
    is_author: bool = Field(False, description="是否为当前用户的回复")
    status: str = Field("active", description="回复状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class CommentLikeResponse(BaseModel):
    """评论点赞响应模型"""
    is_liked: bool = Field(..., description="是否已点赞")
    like_count: int = Field(..., description="点赞数")


class CommentStatsResponse(BaseModel):
    """评论统计响应模型"""
    total_comments: int = Field(0, description="总评论数")
    total_replies: int = Field(0, description="总回复数")
    average_rating: Optional[float] = Field(None, description="平均评分")
    rating_distribution: dict = Field(default_factory=dict, description="评分分布")


class CommentListResponse(BaseModel):
    """评论列表响应模型"""
    comments: List[CommentResponse] = Field(..., description="评论列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    page_size: int = Field(..., description="每页大小")
    total_pages: int = Field(..., description="总页数")


class CommentListFilter(BaseModel):
    """评论列表过滤模型"""
    novel_id: Optional[str] = Field(None, description="小说ID")
    chapter_id: Optional[str] = Field(None, description="章节ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    rating: Optional[int] = Field(None, ge=1, le=5, description="评分筛选")
    has_spoiler: Optional[bool] = Field(None, description="是否包含剧透")
    status: Optional[str] = Field(None, description="评论状态")
    sort_by: str = Field("created_at", description="排序字段")
    sort_order: str = Field("desc", description="排序方向")