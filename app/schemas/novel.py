"""
小说相关数据模式
定义小说、章节、评论等请求和响应的数据结构
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
import uuid


# 分类相关
class CategoryResponse(BaseModel):
    """分类响应"""
    id: uuid.UUID = Field(..., description="分类ID")
    name: str = Field(..., description="分类名称")
    slug: str = Field(..., description="分类标识")
    description: Optional[str] = Field(None, description="分类描述")
    cover_url: Optional[str] = Field(None, description="分类封面")
    novel_count: int = Field(..., description="小说数量")
    level: int = Field(..., description="分类层级")
    parent_id: Optional[uuid.UUID] = Field(None, description="父分类ID")

    class Config:
        orm_mode = True


# 标签相关
class TagResponse(BaseModel):
    """标签响应"""
    id: uuid.UUID = Field(..., description="标签ID")
    name: str = Field(..., description="标签名称")
    color: str = Field(..., description="标签颜色")
    description: Optional[str] = Field(None, description="标签描述")
    usage_count: int = Field(..., description="使用次数")

    class Config:
        orm_mode = True


# 作者相关
class AuthorResponse(BaseModel):
    """作者响应"""
    id: uuid.UUID = Field(..., description="作者ID")
    name: str = Field(..., description="作者姓名")
    pen_name: Optional[str] = Field(None, description="笔名")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    biography: Optional[str] = Field(None, description="作者简介")
    novel_count: int = Field(..., description="小说数量")
    total_words: int = Field(..., description="总字数")
    followers_count: int = Field(..., description="粉丝数")
    is_verified: bool = Field(..., description="是否认证")

    class Config:
        orm_mode = True


# 小说基础响应
class NovelBasicResponse(BaseModel):
    """小说基础响应"""
    id: uuid.UUID = Field(..., description="小说ID")
    title: str = Field(..., description="小说标题")
    cover_url: Optional[str] = Field(None, description="封面URL")
    author_name: str = Field(..., description="作者名")
    category_name: Optional[str] = Field(None, description="分类名称")
    status: str = Field(..., description="小说状态")
    word_count: int = Field(..., description="字数")
    chapter_count: int = Field(..., description="章节数")
    rating: Decimal = Field(..., description="评分")
    view_count: int = Field(..., description="浏览量")
    favorite_count: int = Field(..., description="收藏数")
    is_vip: bool = Field(..., description="是否VIP")
    is_free: bool = Field(..., description="是否免费")
    last_update_time: Optional[datetime] = Field(None, description="最后更新时间")

    class Config:
        orm_mode = True


# 小说详细响应
class NovelDetailResponse(BaseModel):
    """小说详细响应"""
    id: uuid.UUID = Field(..., description="小说ID")
    title: str = Field(..., description="小说标题")
    subtitle: Optional[str] = Field(None, description="副标题")
    description: Optional[str] = Field(None, description="小说描述")
    cover_url: Optional[str] = Field(None, description="封面URL")
    language: str = Field(..., description="语言")
    word_count: int = Field(..., description="字数")
    chapter_count: int = Field(..., description="章节数")
    status: str = Field(..., description="小说状态")
    publish_status: str = Field(..., description="发布状态")
    is_vip: bool = Field(..., description="是否VIP")
    is_free: bool = Field(..., description="是否免费")
    price_per_chapter: Decimal = Field(..., description="章节价格")

    # 统计信息
    view_count: int = Field(..., description="浏览量")
    favorite_count: int = Field(..., description="收藏数")
    comment_count: int = Field(..., description="评论数")
    rating: Decimal = Field(..., description="评分")
    rating_count: int = Field(..., description="评分人数")

    # 更新信息
    last_chapter_title: Optional[str] = Field(None, description="最新章节标题")
    last_update_time: Optional[datetime] = Field(None, description="最后更新时间")

    # 关联信息
    author: AuthorResponse = Field(..., description="作者信息")
    category: Optional[CategoryResponse] = Field(None, description="分类信息")
    tags: List[TagResponse] = Field(..., description="标签列表")

    # 用户相关(需要登录)
    is_favorited: Optional[bool] = Field(None, description="是否已收藏")
    user_rating: Optional[int] = Field(None, description="用户评分")
    reading_progress: Optional[Dict[str, Any]] = Field(None, description="阅读进度")

    # 时间信息
    created_at: datetime = Field(..., description="创建时间")
    published_at: Optional[datetime] = Field(None, description="发布时间")

    class Config:
        orm_mode = True


# 小说列表响应
class NovelListResponse(BaseModel):
    """小说列表响应"""
    items: List[NovelBasicResponse] = Field(..., description="小说列表")
    total: int = Field(..., description="总数")
    has_more: bool = Field(..., description="是否有更多")

    class Config:
        schema_extra = {
            "example": {
                "items": [],
                "total": 100,
                "has_more": True
            }
        }


# 小说搜索请求
class NovelSearchRequest(BaseModel):
    """小说搜索请求"""
    keyword: str = Field(..., min_length=1, max_length=100, description="搜索关键词")
    category_id: Optional[uuid.UUID] = Field(None, description="分类ID")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    status: Optional[str] = Field(None, description="小说状态")
    language: Optional[str] = Field(None, description="语言")
    is_free: Optional[bool] = Field(None, description="是否免费")
    word_count_min: Optional[int] = Field(None, ge=0, description="最小字数")
    word_count_max: Optional[int] = Field(None, ge=0, description="最大字数")
    rating_min: Optional[Decimal] = Field(None, ge=0, le=5, description="最小评分")
    sort_by: Optional[str] = Field(None, description="排序方式")
    sort_order: Optional[str] = Field(None, description="排序顺序")

    @validator('status')
    def validate_status(cls, v):
        if v and v not in ['ongoing', 'completed', 'paused', 'dropped']:
            raise ValueError('无效的小说状态')
        return v

    @validator('sort_by')
    def validate_sort_by(cls, v):
        if v and v not in ['created_at', 'updated_at', 'view_count', 'favorite_count', 'rating', 'word_count']:
            raise ValueError('无效的排序字段')
        return v

    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v and v not in ['asc', 'desc']:
            raise ValueError('排序顺序只能是asc或desc')
        return v

    class Config:
        schema_extra = {
            "example": {
                "keyword": "修仙",
                "category_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "ongoing",
                "is_free": True,
                "word_count_min": 100000,
                "rating_min": 4.0,
                "sort_by": "view_count",
                "sort_order": "desc"
            }
        }


# 章节基础响应
class ChapterBasicResponse(BaseModel):
    """章节基础响应"""
    id: uuid.UUID = Field(..., description="章节ID")
    title: str = Field(..., description="章节标题")
    chapter_number: int = Field(..., description="章节号")
    volume_number: int = Field(..., description="卷号")
    word_count: int = Field(..., description="字数")
    is_vip: bool = Field(..., description="是否VIP章节")
    is_free: bool = Field(..., description="是否免费")
    price: Decimal = Field(..., description="章节价格")
    status: str = Field(..., description="状态")
    created_at: datetime = Field(..., description="创建时间")
    published_at: Optional[datetime] = Field(None, description="发布时间")

    class Config:
        orm_mode = True


# 章节详细响应
class ChapterDetailResponse(BaseModel):
    """章节详细响应"""
    id: uuid.UUID = Field(..., description="章节ID")
    novel_id: uuid.UUID = Field(..., description="小说ID")
    title: str = Field(..., description="章节标题")
    chapter_number: int = Field(..., description="章节号")
    volume_number: int = Field(..., description="卷号")
    content: Optional[str] = Field(None, description="章节内容")
    summary: Optional[str] = Field(None, description="章节摘要")
    author_notes: Optional[str] = Field(None, description="作者话")
    word_count: int = Field(..., description="字数")
    view_count: int = Field(..., description="浏览量")
    comment_count: int = Field(..., description="评论数")
    is_vip: bool = Field(..., description="是否VIP章节")
    is_free: bool = Field(..., description="是否免费")
    price: Decimal = Field(..., description="章节价格")
    status: str = Field(..., description="状态")
    language: str = Field(..., description="语言")

    # 用户相关
    is_purchased: Optional[bool] = Field(None, description="是否已购买")
    can_read: Optional[bool] = Field(None, description="是否可以阅读")

    created_at: datetime = Field(..., description="创建时间")
    published_at: Optional[datetime] = Field(None, description="发布时间")

    class Config:
        orm_mode = True


# 章节列表响应
class ChapterListResponse(BaseModel):
    """章节列表响应"""
    items: List[ChapterBasicResponse] = Field(..., description="章节列表")
    total: int = Field(..., description="总数")
    has_more: bool = Field(..., description="是否有更多")

    class Config:
        schema_extra = {
            "example": {
                "items": [],
                "total": 100,
                "has_more": True
            }
        }


# 相邻章节响应
class AdjacentChaptersResponse(BaseModel):
    """相邻章节响应"""
    previous: Optional[ChapterBasicResponse] = Field(None, description="上一章")
    next: Optional[ChapterBasicResponse] = Field(None, description="下一章")

    class Config:
        schema_extra = {
            "example": {
                "previous": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "title": "第九章 突破",
                    "chapter_number": 9
                },
                "next": {
                    "id": "123e4567-e89b-12d3-a456-426614174001",
                    "title": "第十一章 新的开始",
                    "chapter_number": 11
                }
            }
        }


# 评论相关
class CommentCreateRequest(BaseModel):
    """创建评论请求"""
    target_id: uuid.UUID = Field(..., description="目标ID")
    target_type: str = Field(..., description="目标类型")
    content: str = Field(..., min_length=1, max_length=1000, description="评论内容")
    parent_id: Optional[uuid.UUID] = Field(None, description="父评论ID")

    @validator('target_type')
    def validate_target_type(cls, v):
        if v not in ['novel', 'chapter', 'comment']:
            raise ValueError('目标类型只能是novel、chapter或comment')
        return v

    class Config:
        schema_extra = {
            "example": {
                "target_id": "123e4567-e89b-12d3-a456-426614174000",
                "target_type": "novel",
                "content": "这本小说很不错！",
                "parent_id": None
            }
        }


class CommentResponse(BaseModel):
    """评论响应"""
    id: uuid.UUID = Field(..., description="评论ID")
    target_id: uuid.UUID = Field(..., description="目标ID")
    target_type: str = Field(..., description="目标类型")
    content: str = Field(..., description="评论内容")
    like_count: int = Field(..., description="点赞数")
    reply_count: int = Field(..., description="回复数")
    level: int = Field(..., description="评论层级")
    status: str = Field(..., description="状态")

    # 用户信息
    user_id: uuid.UUID = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    user_avatar: Optional[str] = Field(None, description="用户头像")
    user_level: int = Field(..., description="用户等级")

    # 用户相关
    is_liked: Optional[bool] = Field(None, description="是否已点赞")
    can_delete: Optional[bool] = Field(None, description="是否可以删除")

    # 回复列表(仅限父评论)
    replies: Optional[List['CommentResponse']] = Field(None, description="回复列表")

    created_at: datetime = Field(..., description="创建时间")

    class Config:
        orm_mode = True


# 评论列表响应
class CommentListResponse(BaseModel):
    """评论列表响应"""
    items: List[CommentResponse] = Field(..., description="评论列表")
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


# 评分相关
class NovelRatingRequest(BaseModel):
    """小说评分请求"""
    rating: int = Field(..., ge=1, le=5, description="评分")
    review: Optional[str] = Field(None, max_length=500, description="评价内容")

    class Config:
        schema_extra = {
            "example": {
                "rating": 5,
                "review": "非常精彩的小说，强烈推荐！"
            }
        }


# 收藏相关
class FavoriteResponse(BaseModel):
    """收藏响应"""
    novel_id: uuid.UUID = Field(..., description="小说ID")
    folder_name: str = Field(..., description="收藏夹名称")
    notes: Optional[str] = Field(None, description="收藏备注")
    is_public: bool = Field(..., description="是否公开")
    created_at: datetime = Field(..., description="收藏时间")

    # 小说信息
    novel: NovelBasicResponse = Field(..., description="小说信息")

    class Config:
        orm_mode = True


class FavoriteListResponse(BaseModel):
    """收藏列表响应"""
    items: List[FavoriteResponse] = Field(..., description="收藏列表")
    total: int = Field(..., description="总数")
    has_more: bool = Field(..., description="是否有更多")

    class Config:
        schema_extra = {
            "example": {
                "items": [],
                "total": 30,
                "has_more": True
            }
        }


# 分享相关
class ShareRequest(BaseModel):
    """分享请求"""
    platform: str = Field(..., description="分享平台")

    @validator('platform')
    def validate_platform(cls, v):
        if v not in ['wechat', 'weibo', 'qq', 'link']:
            raise ValueError('无效的分享平台')
        return v

    class Config:
        schema_extra = {
            "example": {
                "platform": "wechat"
            }
        }


# 举报相关
class ReportRequest(BaseModel):
    """举报请求"""
    target_id: uuid.UUID = Field(..., description="目标ID")
    target_type: str = Field(..., description="举报类型")
    reason: str = Field(..., description="举报原因")
    description: Optional[str] = Field(None, max_length=500, description="举报描述")

    @validator('target_type')
    def validate_target_type(cls, v):
        if v not in ['novel', 'chapter', 'comment']:
            raise ValueError('举报类型只能是novel、chapter或comment')
        return v

    class Config:
        schema_extra = {
            "example": {
                "target_id": "123e4567-e89b-12d3-a456-426614174000",
                "target_type": "novel",
                "reason": "内容违规",
                "description": "包含不当内容"
            }
        }


# 热门搜索
class HotKeywordsResponse(BaseModel):
    """热门搜索关键词响应"""
    keywords: List[str] = Field(..., description="热门关键词列表")

    class Config:
        schema_extra = {
            "example": {
                "keywords": ["修仙", "都市", "玄幻", "科幻", "言情"]
            }
        }


# 搜索建议响应
class SearchSuggestionsResponse(BaseModel):
    """搜索建议响应"""
    suggestions: List[str] = Field(..., description="搜索建议列表")

    class Config:
        schema_extra = {
            "example": {
                "suggestions": ["修仙小说", "修仙世界", "修仙传说"]
            }
        }


# 更新 CommentResponse 以避免循环引用
CommentResponse.update_forward_refs()