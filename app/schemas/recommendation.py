# app/schemas/recommendation.py
# -*- coding: utf-8 -*-
"""
推荐系统相关的Pydantic模型
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.schemas.base import BaseSchema
from app.schemas.novel import NovelBasicResponse


class RecommendationResponse(BaseSchema):
    """推荐响应模型"""
    novel_id: str = Field(..., description="小说ID")
    novel: NovelBasicResponse = Field(..., description="小说信息")
    score: float = Field(..., description="推荐分数", ge=0.0, le=1.0)
    reason: Optional[str] = Field(None, description="推荐理由")
    algorithm: str = Field(..., description="推荐算法")
    rank: int = Field(..., description="推荐排名", ge=1)
    created_at: datetime = Field(..., description="推荐时间")


class RecommendationReasonResponse(BaseSchema):
    """推荐理由响应模型"""
    novel_id: str = Field(..., description="小说ID")
    reasons: List[str] = Field(..., description="推荐理由列表")
    similarity_score: Optional[float] = Field(None, description="相似度分数", ge=0.0, le=1.0)
    preference_match: Optional[Dict[str, float]] = Field(None, description="偏好匹配度")
    popularity_score: Optional[float] = Field(None, description="热度分数", ge=0.0, le=1.0)
    quality_score: Optional[float] = Field(None, description="质量分数", ge=0.0, le=1.0)


class UserPreferenceResponse(BaseSchema):
    """用户偏好响应模型"""
    user_id: str = Field(..., description="用户ID")
    favorite_categories: List[Dict[str, Any]] = Field(default_factory=list, description="喜欢的分类")
    favorite_tags: List[Dict[str, Any]] = Field(default_factory=list, description="喜欢的标签")
    favorite_authors: List[Dict[str, Any]] = Field(default_factory=list, description="喜欢的作者")
    reading_patterns: Dict[str, Any] = Field(default_factory=dict, description="阅读模式")
    exclude_categories: List[str] = Field(default_factory=list, description="排除的分类")
    exclude_tags: List[str] = Field(default_factory=list, description="排除的标签")
    min_rating: Optional[float] = Field(None, description="最低评分要求", ge=0.0, le=5.0)
    max_word_count: Optional[int] = Field(None, description="最大字数", ge=0)
    min_word_count: Optional[int] = Field(None, description="最小字数", ge=0)
    updated_at: datetime = Field(..., description="更新时间")


class RecommendationStatsResponse(BaseSchema):
    """推荐统计响应模型"""
    total_recommendations: int = Field(..., description="总推荐数", ge=0)
    clicked_recommendations: int = Field(..., description="点击推荐数", ge=0)
    added_to_bookshelf: int = Field(..., description="加入书架数", ge=0)
    started_reading: int = Field(..., description="开始阅读数", ge=0)
    click_through_rate: float = Field(..., description="点击率", ge=0.0, le=1.0)
    conversion_rate: float = Field(..., description="转化率", ge=0.0, le=1.0)
    avg_reading_time: Optional[float] = Field(None, description="平均阅读时长（分钟）", ge=0.0)
    popular_categories: List[Dict[str, Any]] = Field(default_factory=list, description="热门分类")
    popular_algorithms: List[Dict[str, Any]] = Field(default_factory=list, description="热门算法")
    time_range: str = Field(..., description="统计时间范围")


class RecommendationFeedbackRequest(BaseSchema):
    """推荐反馈请求模型"""
    novel_id: str = Field(..., description="小说ID")
    feedback_type: str = Field(..., description="反馈类型", pattern="^(like|dislike|not_interested|inappropriate)$")
    reason: Optional[str] = Field(None, description="反馈原因", max_length=500)


class UserPreferenceUpdateRequest(BaseSchema):
    """用户偏好更新请求模型"""
    categories: Optional[List[str]] = Field(None, description="喜欢的分类ID列表")
    tags: Optional[List[str]] = Field(None, description="喜欢的标签ID列表")
    authors: Optional[List[str]] = Field(None, description="喜欢的作者ID列表")
    exclude_categories: Optional[List[str]] = Field(None, description="排除的分类ID列表")
    exclude_tags: Optional[List[str]] = Field(None, description="排除的标签ID列表")
    min_rating: Optional[float] = Field(None, description="最低评分要求", ge=0.0, le=5.0)
    max_word_count: Optional[int] = Field(None, description="最大字数", ge=0)
    min_word_count: Optional[int] = Field(None, description="最小字数", ge=0)


class RecommendationAlgorithmResponse(BaseSchema):
    """推荐算法响应模型"""
    algorithm_name: str = Field(..., description="算法名称")
    algorithm_type: str = Field(..., description="算法类型")
    description: str = Field(..., description="算法描述")
    accuracy: Optional[float] = Field(None, description="准确率", ge=0.0, le=1.0)
    coverage: Optional[float] = Field(None, description="覆盖率", ge=0.0, le=1.0)
    diversity: Optional[float] = Field(None, description="多样性", ge=0.0, le=1.0)
    novelty: Optional[float] = Field(None, description="新颖性", ge=0.0, le=1.0)
    is_active: bool = Field(..., description="是否启用")


class RecommendationConfigResponse(BaseSchema):
    """推荐配置响应模型"""
    max_recommendations: int = Field(..., description="最大推荐数量", ge=1)
    refresh_interval: int = Field(..., description="刷新间隔（小时）", ge=1)
    diversity_factor: float = Field(..., description="多样性因子", ge=0.0, le=1.0)
    novelty_factor: float = Field(..., description="新颖性因子", ge=0.0, le=1.0)
    popularity_weight: float = Field(..., description="热度权重", ge=0.0, le=1.0)
    quality_weight: float = Field(..., description="质量权重", ge=0.0, le=1.0)
    personalization_weight: float = Field(..., description="个性化权重", ge=0.0, le=1.0)
    cold_start_threshold: int = Field(..., description="冷启动阈值", ge=0)
    min_similarity_threshold: float = Field(..., description="最小相似度阈值", ge=0.0, le=1.0)


class RecommendationMetricsResponse(BaseSchema):
    """推荐指标响应模型"""
    precision: float = Field(..., description="精确率", ge=0.0, le=1.0)
    recall: float = Field(..., description="召回率", ge=0.0, le=1.0)
    f1_score: float = Field(..., description="F1分数", ge=0.0, le=1.0)
    ndcg: float = Field(..., description="NDCG", ge=0.0, le=1.0)
    map_score: float = Field(..., description="MAP分数", ge=0.0, le=1.0)
    coverage: float = Field(..., description="覆盖率", ge=0.0, le=1.0)
    diversity: float = Field(..., description="多样性", ge=0.0, le=1.0)
    novelty: float = Field(..., description="新颖性", ge=0.0, le=1.0)
    serendipity: float = Field(..., description="意外性", ge=0.0, le=1.0)
    evaluation_date: datetime = Field(..., description="评估日期")


class RecommendationExplanationResponse(BaseSchema):
    """推荐解释响应模型"""
    novel_id: str = Field(..., description="小说ID")
    explanation_type: str = Field(..., description="解释类型")
    explanation_text: str = Field(..., description="解释文本")
    confidence: float = Field(..., description="置信度", ge=0.0, le=1.0)
    supporting_evidence: List[Dict[str, Any]] = Field(default_factory=list, description="支持证据")
    similar_novels: List[str] = Field(default_factory=list, description="相似小说ID列表")
    user_history_match: Optional[Dict[str, Any]] = Field(None, description="用户历史匹配")


class DiversifiedRecommendationResponse(BaseSchema):
    """多样化推荐响应模型"""
    id: str = Field(..., description="小说ID")
    title: str = Field(..., description="小说标题")
    author: str = Field(..., description="作者")
    description: Optional[str] = Field(None, description="小说描述")
    category: str = Field(..., description="分类")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    cover_url: Optional[str] = Field(None, description="封面URL")
    rating: float = Field(..., description="评分", ge=0.0, le=5.0)
    view_count: int = Field(..., description="浏览量", ge=0)
    chapter_count: int = Field(..., description="章节数", ge=0)
    word_count: int = Field(..., description="字数", ge=0)
    reason: str = Field(..., description="推荐理由")
    score: float = Field(..., description="推荐分数", ge=0.0, le=1.0)
    diversity_factor: float = Field(..., description="多样性因子", ge=0.0, le=1.0)