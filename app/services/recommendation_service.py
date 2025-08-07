# app/services/recommendation_service.py
# -*- coding: utf-8 -*-
"""
推荐系统业务服务
处理推荐相关的业务逻辑，包括个性化推荐、协同过滤、内容推荐等
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func, desc, asc
from sqlalchemy.orm import selectinload, joinedload
import uuid
import random
import json

from ..models.novel import Novel
from ..models.user import User
from ..models.chapter import ReadingProgress, UserFavorite
from ..schemas.recommendation import (
    RecommendationResponse, RecommendationReasonResponse,
    UserPreferenceResponse, RecommendationStatsResponse,
    DiversifiedRecommendationResponse
)
from ..utils.cache import CacheManager
from .base import BaseService


class RecommendationService(BaseService):
    """推荐系统服务类"""

    def __init__(self, db: AsyncSession, cache: Optional[CacheManager] = None):
        super().__init__(db, cache)

    async def get_personalized_recommendations(
        self,
        user_id: uuid.UUID,
        limit: int = 20,
        exclude_read: bool = True
    ) -> List[RecommendationResponse]:
        """获取个性化推荐"""
        
        # 获取用户阅读历史和偏好
        user_preferences = await self._get_user_preferences(user_id)
        
        # 获取用户已读小说ID
        read_novel_ids = []
        if exclude_read:
            read_novel_ids = await self._get_user_read_novels(user_id)
        
        # 基于用户偏好推荐
        recommendations = []
        
        # 1. 基于分类偏好推荐
        if user_preferences.get("preferred_categories"):
            category_recs = await self._recommend_by_categories(
                user_preferences["preferred_categories"],
                exclude_ids=read_novel_ids,
                limit=limit // 2
            )
            recommendations.extend(category_recs)
        
        # 2. 基于标签偏好推荐
        if user_preferences.get("preferred_tags"):
            tag_recs = await self._recommend_by_tags(
                user_preferences["preferred_tags"],
                exclude_ids=read_novel_ids + [r.id for r in recommendations],
                limit=limit // 2
            )
            recommendations.extend(tag_recs)
        
        # 3. 如果推荐不足，补充热门推荐
        if len(recommendations) < limit:
            hot_recs = await self._get_hot_recommendations(
                exclude_ids=read_novel_ids + [r.id for r in recommendations],
                limit=limit - len(recommendations)
            )
            recommendations.extend(hot_recs)
        
        return recommendations[:limit]

    async def get_similar_novels(
        self,
        novel_id: uuid.UUID,
        limit: int = 10
    ) -> List[RecommendationResponse]:
        """获取相似小说推荐"""
        
        # 获取目标小说信息
        novel_query = select(Novel).where(Novel.id == novel_id)
        novel_result = await self.db.execute(novel_query)
        novel = novel_result.scalar_one_or_none()
        
        if not novel:
            return []
        
        # 基于分类和标签查找相似小说
        similar_query = select(Novel).where(
            and_(
                Novel.id != novel_id,
                Novel.is_deleted == False,
                or_(
                    Novel.category == novel.category,
                    Novel.tags.ilike(f"%{novel.tags}%") if novel.tags else False
                )
            )
        ).order_by(desc(Novel.rating), desc(Novel.view_count)).limit(limit)
        
        result = await self.db.execute(similar_query)
        similar_novels = result.scalars().all()
        
        recommendations = [
            RecommendationResponse(
                id=str(similar_novel.id),
                title=similar_novel.title,
                author=similar_novel.author,
                description=similar_novel.description,
                category=similar_novel.category,
                tags=similar_novel.tags.split(",") if similar_novel.tags else [],
                cover_url=similar_novel.cover_url,
                rating=similar_novel.rating,
                view_count=similar_novel.view_count,
                chapter_count=similar_novel.chapter_count,
                word_count=similar_novel.word_count,
                reason="与《{}》类型相似".format(novel.title),
                score=0.8 + random.random() * 0.2  # 模拟推荐分数
            )
            for similar_novel in similar_novels
        ]
        
        return recommendations

    async def get_hot_recommendations(
        self,
        category: Optional[str] = None,
        limit: int = 20
    ) -> List[RecommendationResponse]:
        """获取热门推荐"""
        
        return await self._get_hot_recommendations(
            category=category,
            limit=limit
        )

    async def get_trending_recommendations(
        self,
        period: str = "week",
        limit: int = 20
    ) -> List[RecommendationResponse]:
        """获取趋势推荐"""
        
        # 计算时间范围
        if period == "day":
            start_date = datetime.now() - timedelta(days=1)
        elif period == "week":
            start_date = datetime.now() - timedelta(weeks=1)
        elif period == "month":
            start_date = datetime.now() - timedelta(days=30)
        else:
            start_date = datetime.now() - timedelta(weeks=1)
        
        # 查询趋势小说（基于最近的阅读量增长）
        trending_query = select(Novel).where(
            and_(
                Novel.is_deleted == False,
                Novel.created_at >= start_date
            )
        ).order_by(desc(Novel.view_count), desc(Novel.rating)).limit(limit)
        
        result = await self.db.execute(trending_query)
        trending_novels = result.scalars().all()
        
        recommendations = [
            RecommendationResponse(
                id=str(novel.id),
                title=novel.title,
                author=novel.author,
                description=novel.description,
                category=novel.category,
                tags=novel.tags.split(",") if novel.tags else [],
                cover_url=novel.cover_url,
                rating=novel.rating,
                view_count=novel.view_count,
                chapter_count=novel.chapter_count,
                word_count=novel.word_count,
                reason="最近热门",
                score=0.9 + random.random() * 0.1
            )
            for novel in trending_novels
        ]
        
        return recommendations

    async def get_new_book_recommendations(
        self,
        days: int = 7,
        limit: int = 20
    ) -> List[RecommendationResponse]:
        """获取新书推荐"""
        
        start_date = datetime.now() - timedelta(days=days)
        
        new_books_query = select(Novel).where(
            and_(
                Novel.is_deleted == False,
                Novel.created_at >= start_date
            )
        ).order_by(desc(Novel.created_at), desc(Novel.rating)).limit(limit)
        
        result = await self.db.execute(new_books_query)
        new_books = result.scalars().all()
        
        recommendations = [
            RecommendationResponse(
                id=str(novel.id),
                title=novel.title,
                author=novel.author,
                description=novel.description,
                category=novel.category,
                tags=novel.tags.split(",") if novel.tags else [],
                cover_url=novel.cover_url,
                rating=novel.rating,
                view_count=novel.view_count,
                chapter_count=novel.chapter_count,
                word_count=novel.word_count,
                reason="新书推荐",
                score=0.7 + random.random() * 0.3
            )
            for novel in new_books
        ]
        
        return recommendations

    async def get_category_recommendations(
        self,
        category: str,
        user_id: Optional[uuid.UUID] = None,
        limit: int = 20
    ) -> List[RecommendationResponse]:
        """获取分类推荐"""
        
        # 获取用户已读小说（如果提供了用户ID）
        exclude_ids = []
        if user_id:
            exclude_ids = await self._get_user_read_novels(user_id)
        
        return await self._recommend_by_categories(
            [category],
            exclude_ids=exclude_ids,
            limit=limit
        )

    async def get_author_recommendations(
        self,
        author: str,
        exclude_novel_id: Optional[uuid.UUID] = None,
        limit: int = 10
    ) -> List[RecommendationResponse]:
        """获取作者推荐"""
        
        author_query = select(Novel).where(
            and_(
                Novel.author == author,
                Novel.is_deleted == False,
                Novel.id != exclude_novel_id if exclude_novel_id else True
            )
        ).order_by(desc(Novel.rating), desc(Novel.view_count)).limit(limit)
        
        result = await self.db.execute(author_query)
        author_novels = result.scalars().all()
        
        recommendations = [
            RecommendationResponse(
                id=str(novel.id),
                title=novel.title,
                author=novel.author,
                description=novel.description,
                category=novel.category,
                tags=novel.tags.split(",") if novel.tags else [],
                cover_url=novel.cover_url,
                rating=novel.rating,
                view_count=novel.view_count,
                chapter_count=novel.chapter_count,
                word_count=novel.word_count,
                reason=f"来自作者 {author}",
                score=0.8 + random.random() * 0.2
            )
            for novel in author_novels
        ]
        
        return recommendations

    async def get_collaborative_filtering_recommendations(
        self,
        user_id: uuid.UUID,
        limit: int = 20
    ) -> List[RecommendationResponse]:
        """获取协同过滤推荐"""
        
        # 简化的协同过滤实现
        # 1. 找到相似用户（有相同收藏的用户）
        user_favorites_query = select(UserFavorite.novel_id).where(
            UserFavorite.user_id == user_id
        )
        user_favorites_result = await self.db.execute(user_favorites_query)
        user_favorite_novels = [row[0] for row in user_favorites_result]
        
        if not user_favorite_novels:
            return await self.get_hot_recommendations(limit=limit)
        
        # 2. 找到也收藏了这些小说的其他用户
        similar_users_query = select(UserFavorite.user_id).where(
            and_(
                UserFavorite.novel_id.in_(user_favorite_novels),
                UserFavorite.user_id != user_id
            )
        ).group_by(UserFavorite.user_id).having(
            func.count(UserFavorite.novel_id) >= 2  # 至少有2本相同收藏
        )
        
        similar_users_result = await self.db.execute(similar_users_query)
        similar_user_ids = [row[0] for row in similar_users_result]
        
        if not similar_user_ids:
            return await self.get_hot_recommendations(limit=limit)
        
        # 3. 获取相似用户收藏的其他小说
        recommended_novels_query = select(Novel).join(
            UserFavorite, Novel.id == UserFavorite.novel_id
        ).where(
            and_(
                UserFavorite.user_id.in_(similar_user_ids),
                UserFavorite.novel_id.notin_(user_favorite_novels),
                Novel.is_deleted == False
            )
        ).group_by(Novel.id).order_by(
            desc(func.count(UserFavorite.user_id)),
            desc(Novel.rating)
        ).limit(limit)
        
        result = await self.db.execute(recommended_novels_query)
        recommended_novels = result.scalars().all()
        
        recommendations = [
            RecommendationResponse(
                id=str(novel.id),
                title=novel.title,
                author=novel.author,
                description=novel.description,
                category=novel.category,
                tags=novel.tags.split(",") if novel.tags else [],
                cover_url=novel.cover_url,
                rating=novel.rating,
                view_count=novel.view_count,
                chapter_count=novel.chapter_count,
                word_count=novel.word_count,
                reason="喜欢相似小说的用户也喜欢",
                score=0.85 + random.random() * 0.15
            )
            for novel in recommended_novels
        ]
        
        return recommendations

    async def get_content_based_recommendations(
        self,
        user_id: uuid.UUID,
        limit: int = 20
    ) -> List[RecommendationResponse]:
        """获取基于内容的推荐"""
        
        # 获取用户偏好
        user_preferences = await self._get_user_preferences(user_id)
        
        # 基于用户偏好推荐
        recommendations = []
        
        if user_preferences.get("preferred_categories"):
            category_recs = await self._recommend_by_categories(
                user_preferences["preferred_categories"],
                limit=limit // 2
            )
            recommendations.extend(category_recs)
        
        if user_preferences.get("preferred_tags"):
            tag_recs = await self._recommend_by_tags(
                user_preferences["preferred_tags"],
                exclude_ids=[r.id for r in recommendations],
                limit=limit - len(recommendations)
            )
            recommendations.extend(tag_recs)
        
        return recommendations[:limit]

    async def get_recommendation_reason(
        self,
        user_id: uuid.UUID,
        novel_id: uuid.UUID
    ) -> RecommendationReasonResponse:
        """获取推荐理由"""
        
        # 简化实现，返回基本推荐理由
        novel_query = select(Novel).where(Novel.id == novel_id)
        novel_result = await self.db.execute(novel_query)
        novel = novel_result.scalar_one_or_none()
        
        if not novel:
            return RecommendationReasonResponse(
                reasons=["小说不存在"],
                score=0.0
            )
        
        reasons = []
        score = 0.0
        
        # 检查用户是否收藏了相同分类的小说
        user_categories_query = select(func.distinct(Novel.category)).join(
            UserFavorite, Novel.id == UserFavorite.novel_id
        ).where(UserFavorite.user_id == user_id)
        
        user_categories_result = await self.db.execute(user_categories_query)
        user_categories = [row[0] for row in user_categories_result]
        
        if novel.category in user_categories:
            reasons.append(f"您喜欢{novel.category}类小说")
            score += 0.3
        
        # 检查评分
        if novel.rating >= 4.0:
            reasons.append("高评分作品")
            score += 0.2
        
        # 检查热门程度
        if novel.view_count >= 10000:
            reasons.append("热门作品")
            score += 0.2
        
        # 检查更新状态
        if novel.status == "serializing":
            reasons.append("正在连载")
            score += 0.1
        
        if not reasons:
            reasons = ["系统推荐"]
            score = 0.5
        
        return RecommendationReasonResponse(
            reasons=reasons,
            score=min(score, 1.0)
        )

    async def submit_recommendation_feedback(
        self,
        user_id: uuid.UUID,
        novel_id: uuid.UUID,
        feedback_type: str,
        rating: Optional[float] = None
    ) -> None:
        """提交推荐反馈"""
        
        # 这里简化实现，实际项目中应该保存反馈到数据库
        # 用于改进推荐算法
        pass

    async def get_user_preferences(
        self,
        user_id: uuid.UUID
    ) -> UserPreferenceResponse:
        """获取用户偏好"""
        
        preferences = await self._get_user_preferences(user_id)
        
        return UserPreferenceResponse(
            preferred_categories=preferences.get("preferred_categories", []),
            preferred_tags=preferences.get("preferred_tags", []),
            preferred_authors=preferences.get("preferred_authors", []),
            reading_time_preference=preferences.get("reading_time_preference", "any"),
            content_length_preference=preferences.get("content_length_preference", "any")
        )

    async def update_user_preferences(
        self,
        user_id: uuid.UUID,
        preferences: Dict[str, Any]
    ) -> None:
        """更新用户偏好"""
        
        # 这里简化实现，实际项目中应该保存到用户偏好表
        pass

    async def get_recommendation_stats(
        self,
        user_id: uuid.UUID
    ) -> RecommendationStatsResponse:
        """获取推荐统计"""
        
        # 简化实现，返回模拟数据
        return RecommendationStatsResponse(
            total_recommendations=100,
            clicked_recommendations=25,
            click_rate=0.25,
            favorite_recommendations=10,
            favorite_rate=0.10
        )

    async def get_diversified_recommendations(
        self,
        user_id: uuid.UUID,
        limit: int = 20
    ) -> List[DiversifiedRecommendationResponse]:
        """获取多样化推荐"""
        
        recommendations = []
        
        # 1. 个性化推荐
        personalized = await self.get_personalized_recommendations(user_id, limit=5)
        for rec in personalized:
            recommendations.append(DiversifiedRecommendationResponse(
                **rec.dict(),
                recommendation_type="personalized"
            ))
        
        # 2. 热门推荐
        hot = await self.get_hot_recommendations(limit=5)
        for rec in hot:
            recommendations.append(DiversifiedRecommendationResponse(
                **rec.dict(),
                recommendation_type="hot"
            ))
        
        # 3. 新书推荐
        new_books = await self.get_new_book_recommendations(limit=5)
        for rec in new_books:
            recommendations.append(DiversifiedRecommendationResponse(
                **rec.dict(),
                recommendation_type="new"
            ))
        
        # 4. 趋势推荐
        trending = await self.get_trending_recommendations(limit=5)
        for rec in trending:
            recommendations.append(DiversifiedRecommendationResponse(
                **rec.dict(),
                recommendation_type="trending"
            ))
        
        # 随机打乱以增加多样性
        random.shuffle(recommendations)
        
        return recommendations[:limit]

    async def get_cold_start_recommendations(
        self,
        user_id: uuid.UUID,
        limit: int = 20
    ) -> List[RecommendationResponse]:
        """获取冷启动推荐（新用户）"""
        
        # 为新用户推荐热门和高评分小说
        cold_start_query = select(Novel).where(
            Novel.is_deleted == False
        ).order_by(
            desc(Novel.rating),
            desc(Novel.view_count)
        ).limit(limit)
        
        result = await self.db.execute(cold_start_query)
        novels = result.scalars().all()
        
        recommendations = [
            RecommendationResponse(
                id=str(novel.id),
                title=novel.title,
                author=novel.author,
                description=novel.description,
                category=novel.category,
                tags=novel.tags.split(",") if novel.tags else [],
                cover_url=novel.cover_url,
                rating=novel.rating,
                view_count=novel.view_count,
                chapter_count=novel.chapter_count,
                word_count=novel.word_count,
                reason="热门推荐",
                score=0.8 + random.random() * 0.2
            )
            for novel in novels
        ]
        
        return recommendations

    async def refresh_recommendation_cache(self, user_id: uuid.UUID) -> None:
        """刷新推荐缓存"""
        
        if self.cache:
            # 清除用户相关的推荐缓存
            cache_keys = [
                f"recommendations:personalized:{user_id}",
                f"recommendations:collaborative:{user_id}",
                f"recommendations:content_based:{user_id}",
                f"user_preferences:{user_id}"
            ]
            
            for key in cache_keys:
                await self.cache.delete(key)

    # 私有方法
    async def _get_user_preferences(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """获取用户偏好（内部方法）"""
        
        # 基于用户收藏和阅读历史分析偏好
        favorites_query = select(Novel.category, Novel.tags).join(
            UserFavorite, Novel.id == UserFavorite.novel_id
        ).where(UserFavorite.user_id == user_id)
        
        favorites_result = await self.db.execute(favorites_query)
        favorites = favorites_result.all()
        
        # 统计偏好分类
        category_counts = {}
        tag_counts = {}
        
        for favorite in favorites:
            category = favorite.category
            if category:
                category_counts[category] = category_counts.get(category, 0) + 1
            
            tags = favorite.tags
            if tags:
                for tag in tags.split(","):
                    tag = tag.strip()
                    if tag:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # 获取前3个偏好分类和标签
        preferred_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        preferred_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "preferred_categories": [cat[0] for cat in preferred_categories],
            "preferred_tags": [tag[0] for tag in preferred_tags]
        }

    async def _get_user_read_novels(self, user_id: uuid.UUID) -> List[str]:
        """获取用户已读小说ID列表"""
        
        # 从阅读进度表获取
        read_query = select(ReadingProgress.novel_id).where(
            ReadingProgress.user_id == user_id
        )
        read_result = await self.db.execute(read_query)
        read_novels = [str(row[0]) for row in read_result]
        
        # 从收藏表获取
        favorite_query = select(UserFavorite.novel_id).where(
            UserFavorite.user_id == user_id
        )
        favorite_result = await self.db.execute(favorite_query)
        favorite_novels = [str(row[0]) for row in favorite_result]
        
        return list(set(read_novels + favorite_novels))

    async def _recommend_by_categories(
        self,
        categories: List[str],
        exclude_ids: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[RecommendationResponse]:
        """基于分类推荐"""
        
        exclude_ids = exclude_ids or []
        
        category_query = select(Novel).where(
            and_(
                Novel.category.in_(categories),
                Novel.is_deleted == False,
                Novel.id.notin_([uuid.UUID(id) for id in exclude_ids]) if exclude_ids else True
            )
        ).order_by(desc(Novel.rating), desc(Novel.view_count)).limit(limit)
        
        result = await self.db.execute(category_query)
        novels = result.scalars().all()
        
        recommendations = [
            RecommendationResponse(
                id=str(novel.id),
                title=novel.title,
                author=novel.author,
                description=novel.description,
                category=novel.category,
                tags=novel.tags.split(",") if novel.tags else [],
                cover_url=novel.cover_url,
                rating=novel.rating,
                view_count=novel.view_count,
                chapter_count=novel.chapter_count,
                word_count=novel.word_count,
                reason=f"您喜欢{novel.category}类小说",
                score=0.8 + random.random() * 0.2
            )
            for novel in novels
        ]
        
        return recommendations

    async def _recommend_by_tags(
        self,
        tags: List[str],
        exclude_ids: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[RecommendationResponse]:
        """基于标签推荐"""
        
        exclude_ids = exclude_ids or []
        
        # 构建标签查询条件
        tag_conditions = []
        for tag in tags:
            tag_conditions.append(Novel.tags.ilike(f"%{tag}%"))
        
        tag_query = select(Novel).where(
            and_(
                or_(*tag_conditions),
                Novel.is_deleted == False,
                Novel.id.notin_([uuid.UUID(id) for id in exclude_ids]) if exclude_ids else True
            )
        ).order_by(desc(Novel.rating), desc(Novel.view_count)).limit(limit)
        
        result = await self.db.execute(tag_query)
        novels = result.scalars().all()
        
        recommendations = [
            RecommendationResponse(
                id=str(novel.id),
                title=novel.title,
                author=novel.author,
                description=novel.description,
                category=novel.category,
                tags=novel.tags.split(",") if novel.tags else [],
                cover_url=novel.cover_url,
                rating=novel.rating,
                view_count=novel.view_count,
                chapter_count=novel.chapter_count,
                word_count=novel.word_count,
                reason="基于您的标签偏好",
                score=0.75 + random.random() * 0.25
            )
            for novel in novels
        ]
        
        return recommendations

    async def _get_hot_recommendations(
        self,
        category: Optional[str] = None,
        exclude_ids: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[RecommendationResponse]:
        """获取热门推荐（内部方法）"""
        
        exclude_ids = exclude_ids or []
        
        hot_query = select(Novel).where(
            and_(
                Novel.is_deleted == False,
                Novel.category == category if category else True,
                Novel.id.notin_([uuid.UUID(id) for id in exclude_ids]) if exclude_ids else True
            )
        ).order_by(desc(Novel.view_count), desc(Novel.rating)).limit(limit)
        
        result = await self.db.execute(hot_query)
        novels = result.scalars().all()
        
        recommendations = [
            RecommendationResponse(
                id=str(novel.id),
                title=novel.title,
                author=novel.author,
                description=novel.description,
                category=novel.category,
                tags=novel.tags.split(",") if novel.tags else [],
                cover_url=novel.cover_url,
                rating=novel.rating,
                view_count=novel.view_count,
                chapter_count=novel.chapter_count,
                word_count=novel.word_count,
                reason="热门推荐",
                score=0.9 + random.random() * 0.1
            )
            for novel in novels
        ]
        
        return recommendations