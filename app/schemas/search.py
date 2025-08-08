# app/schemas/search.py
# -*- coding: utf-8 -*-
"""
搜索相关的Pydantic模型
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from .novel import NovelBasicResponse
from .user import UserResponse


class SearchNovelResponse(BaseModel):
    """搜索小说响应模型"""
    id: str = Field(..., description="小说ID")
    title: str = Field(..., description="小说标题")
    author: str = Field(..., description="作者")
    description: Optional[str] = Field(None, description="小说描述")
    category: Optional[str] = Field(None, description="分类")
    tags: List[str] = Field(default_factory=list, description="标签")
    status: str = Field(..., description="状态")
    cover_url: Optional[str] = Field(None, description="封面URL")
    rating: float = Field(0.0, description="评分")
    view_count: int = Field(0, description="阅读量")
    chapter_count: int = Field(0, description="章节数")
    word_count: int = Field(0, description="字数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class SearchAuthorResponse(BaseModel):
    """搜索作者响应模型"""
    name: str = Field(..., description="作者名")
    novel_count: int = Field(0, description="小说数量")
    total_views: int = Field(0, description="总阅读量")
    avg_rating: float = Field(0.0, description="平均评分")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    description: Optional[str] = Field(None, description="作者简介")

    class Config:
        from_attributes = True


class SearchTrendResponse(BaseModel):
    """搜索趋势响应模型"""
    keyword: str = Field(..., description="关键词")
    trend_data: List[Dict[str, Any]] = Field(default_factory=list, description="趋势数据")
    period: str = Field(..., description="时间周期")


class SearchFilterResponse(BaseModel):
    """搜索过滤响应模型"""
    categories: List[Dict[str, Any]] = Field(default_factory=list, description="分类选项")
    tags: List[str] = Field(default_factory=list, description="标签选项")
    authors: List[str] = Field(default_factory=list, description="作者选项")
    status_options: List[str] = Field(default_factory=list, description="状态选项")


class AutoCompleteResponse(BaseModel):
    """自动完成响应模型"""
    suggestions: List[str] = Field(default_factory=list, description="建议列表")
    type: str = Field(..., description="建议类型")
    source: str = Field(..., description="数据源")


class SearchSuggestionResponse(BaseModel):
    """搜索建议响应模型"""
    keyword: str = Field(..., description="建议关键词")
    type: str = Field(..., description="建议类型")
    count: int = Field(0, description="相关数量")


class SearchHistoryResponse(BaseModel):
    """搜索历史响应模型"""
    id: str = Field(..., description="历史记录ID")
    keyword: str = Field(..., description="搜索关键词")
    search_type: str = Field(..., description="搜索类型")
    result_count: int = Field(0, description="搜索结果数量")
    created_at: datetime = Field(..., description="搜索时间")

    class Config:
        from_attributes = True


class HotSearchResponse(BaseModel):
    """热门搜索响应模型"""
    keyword: str = Field(..., description="搜索关键词")
    search_count: int = Field(..., description="搜索次数")
    trend: str = Field("stable", description="趋势")
    rank: int = Field(..., description="排名")


class SearchStatsResponse(BaseModel):
    """搜索统计响应模型"""
    total_searches: int = Field(0, description="总搜索次数")
    unique_keywords: int = Field(0, description="唯一关键词数")
    top_keywords: List[str] = Field(default_factory=list, description="热门关键词")
    search_trends: Dict[str, int] = Field(default_factory=dict, description="搜索趋势")


class SearchResponse(BaseModel):
    """综合搜索响应模型"""
    novels: List[NovelBasicResponse] = Field(default_factory=list, description="小说结果")
    authors: List[UserResponse] = Field(default_factory=list, description="作者结果")
    tags: List[str] = Field(default_factory=list, description="标签结果")
    total_novels: int = Field(0, description="小说总数")
    total_authors: int = Field(0, description="作者总数")
    total_tags: int = Field(0, description="标签总数")
    search_time: float = Field(0.0, description="搜索耗时（秒）")


class SearchFilterRequest(BaseModel):
    """搜索过滤请求模型"""
    keyword: str = Field(..., description="搜索关键词")
    category_id: Optional[str] = Field(None, description="分类ID")
    status: Optional[str] = Field(None, description="状态")
    author: Optional[str] = Field(None, description="作者")
    tags: Optional[List[str]] = Field(None, description="标签")
    word_count_min: Optional[int] = Field(None, description="最小字数")
    word_count_max: Optional[int] = Field(None, description="最大字数")
    rating_min: Optional[float] = Field(None, description="最低评分")
    sort_by: str = Field("relevance", description="排序字段")
    sort_order: str = Field("desc", description="排序方向")


class SearchAnalyticsResponse(BaseModel):
    """搜索分析响应模型"""
    keyword: str = Field(..., description="关键词")
    search_volume: int = Field(0, description="搜索量")
    click_through_rate: float = Field(0.0, description="点击率")
    conversion_rate: float = Field(0.0, description="转化率")
    related_keywords: List[str] = Field(default_factory=list, description="相关关键词")
    search_trends: Dict[str, Any] = Field(default_factory=dict, description="搜索趋势数据")


class SearchIndexRequest(BaseModel):
    """搜索索引请求模型"""
    content_type: str = Field(..., description="内容类型")
    content_id: str = Field(..., description="内容ID")
    title: str = Field(..., description="标题")
    content: str = Field(..., description="内容")
    tags: Optional[List[str]] = Field(None, description="标签")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class SearchIndexResponse(BaseModel):
    """搜索索引响应模型"""
    index_id: str = Field(..., description="索引ID")
    status: str = Field(..., description="索引状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True