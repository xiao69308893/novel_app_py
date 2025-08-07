# app/utils/recommendation.py
# -*- coding: utf-8 -*-
"""
推荐算法工具函数
"""

from typing import Dict, List, Any, Optional, Tuple
import math
import logging
from collections import defaultdict, Counter
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """推荐引擎"""
    
    def __init__(self):
        self.user_item_matrix = {}
        self.item_features = {}
        self.user_profiles = {}
        self.similarity_cache = {}
    
    def calculate_user_similarity(
        self,
        user1_id: int,
        user2_id: int,
        user_behaviors: Dict[int, List[Dict[str, Any]]]
    ) -> float:
        """计算用户相似度（协同过滤）"""
        try:
            user1_items = set()
            user2_items = set()
            
            # 获取用户行为数据
            if user1_id in user_behaviors:
                user1_items = {item["novel_id"] for item in user_behaviors[user1_id]}
            
            if user2_id in user_behaviors:
                user2_items = {item["novel_id"] for item in user_behaviors[user2_id]}
            
            # 计算Jaccard相似度
            intersection = len(user1_items & user2_items)
            union = len(user1_items | user2_items)
            
            if union == 0:
                return 0.0
            
            return intersection / union
            
        except Exception as e:
            logger.error(f"计算用户相似度失败: {e}")
            return 0.0
    
    def calculate_item_similarity(
        self,
        item1_features: Dict[str, Any],
        item2_features: Dict[str, Any]
    ) -> float:
        """计算物品相似度（基于内容）"""
        try:
            similarity_score = 0.0
            total_weight = 0.0
            
            # 类型相似度
            if item1_features.get("category") == item2_features.get("category"):
                similarity_score += 0.3
            total_weight += 0.3
            
            # 标签相似度
            tags1 = set(item1_features.get("tags", []))
            tags2 = set(item2_features.get("tags", []))
            
            if tags1 and tags2:
                tag_similarity = len(tags1 & tags2) / len(tags1 | tags2)
                similarity_score += tag_similarity * 0.2
            total_weight += 0.2
            
            # 作者相似度
            if item1_features.get("author_id") == item2_features.get("author_id"):
                similarity_score += 0.1
            total_weight += 0.1
            
            # 评分相似度
            rating1 = item1_features.get("rating", 0)
            rating2 = item2_features.get("rating", 0)
            
            if rating1 > 0 and rating2 > 0:
                rating_diff = abs(rating1 - rating2) / 5.0  # 假设评分范围是1-5
                rating_similarity = 1 - rating_diff
                similarity_score += rating_similarity * 0.2
            total_weight += 0.2
            
            # 字数相似度
            word_count1 = item1_features.get("word_count", 0)
            word_count2 = item2_features.get("word_count", 0)
            
            if word_count1 > 0 and word_count2 > 0:
                word_ratio = min(word_count1, word_count2) / max(word_count1, word_count2)
                similarity_score += word_ratio * 0.2
            total_weight += 0.2
            
            return similarity_score / total_weight if total_weight > 0 else 0.0
            
        except Exception as e:
            logger.error(f"计算物品相似度失败: {e}")
            return 0.0
    
    def collaborative_filtering_recommendation(
        self,
        target_user_id: int,
        user_behaviors: Dict[int, List[Dict[str, Any]]],
        k_neighbors: int = 10,
        n_recommendations: int = 10
    ) -> List[Dict[str, Any]]:
        """协同过滤推荐"""
        try:
            if target_user_id not in user_behaviors:
                return []
            
            # 计算用户相似度
            user_similarities = []
            target_user_items = {item["novel_id"] for item in user_behaviors[target_user_id]}
            
            for user_id, behaviors in user_behaviors.items():
                if user_id != target_user_id:
                    similarity = self.calculate_user_similarity(
                        target_user_id, user_id, user_behaviors
                    )
                    if similarity > 0:
                        user_similarities.append((user_id, similarity))
            
            # 选择最相似的K个用户
            user_similarities.sort(key=lambda x: x[1], reverse=True)
            top_k_users = user_similarities[:k_neighbors]
            
            # 生成推荐
            item_scores = defaultdict(float)
            
            for user_id, similarity in top_k_users:
                user_items = {item["novel_id"] for item in user_behaviors[user_id]}
                # 推荐目标用户没有交互过的物品
                new_items = user_items - target_user_items
                
                for item_id in new_items:
                    item_scores[item_id] += similarity
            
            # 排序并返回推荐结果
            recommendations = sorted(
                item_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:n_recommendations]
            
            return [
                {
                    "novel_id": item_id,
                    "score": score,
                    "reason": "基于相似用户偏好"
                }
                for item_id, score in recommendations
            ]
            
        except Exception as e:
            logger.error(f"协同过滤推荐失败: {e}")
            return []
    
    def content_based_recommendation(
        self,
        user_id: int,
        user_preferences: Dict[str, Any],
        candidate_items: List[Dict[str, Any]],
        n_recommendations: int = 10
    ) -> List[Dict[str, Any]]:
        """基于内容的推荐"""
        try:
            recommendations = []
            
            for item in candidate_items:
                score = self._calculate_content_score(user_preferences, item)
                
                if score > 0:
                    recommendations.append({
                        "novel_id": item["id"],
                        "score": score,
                        "reason": "基于内容偏好匹配",
                        "item_info": item
                    })
            
            # 按分数排序
            recommendations.sort(key=lambda x: x["score"], reverse=True)
            
            return recommendations[:n_recommendations]
            
        except Exception as e:
            logger.error(f"基于内容推荐失败: {e}")
            return []
    
    def hybrid_recommendation(
        self,
        user_id: int,
        user_behaviors: Dict[int, List[Dict[str, Any]]],
        user_preferences: Dict[str, Any],
        candidate_items: List[Dict[str, Any]],
        cf_weight: float = 0.6,
        cb_weight: float = 0.4,
        n_recommendations: int = 10
    ) -> List[Dict[str, Any]]:
        """混合推荐算法"""
        try:
            # 协同过滤推荐
            cf_recommendations = self.collaborative_filtering_recommendation(
                user_id, user_behaviors, n_recommendations=n_recommendations * 2
            )
            
            # 基于内容推荐
            cb_recommendations = self.content_based_recommendation(
                user_id, user_preferences, candidate_items, n_recommendations=n_recommendations * 2
            )
            
            # 合并推荐结果
            combined_scores = defaultdict(float)
            
            # 协同过滤结果
            for rec in cf_recommendations:
                novel_id = rec["novel_id"]
                combined_scores[novel_id] += rec["score"] * cf_weight
            
            # 基于内容结果
            for rec in cb_recommendations:
                novel_id = rec["novel_id"]
                combined_scores[novel_id] += rec["score"] * cb_weight
            
            # 排序并返回最终推荐
            final_recommendations = sorted(
                combined_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:n_recommendations]
            
            return [
                {
                    "novel_id": novel_id,
                    "score": score,
                    "reason": "混合推荐算法"
                }
                for novel_id, score in final_recommendations
            ]
            
        except Exception as e:
            logger.error(f"混合推荐失败: {e}")
            return []
    
    def trending_recommendation(
        self,
        time_window_days: int = 7,
        category: Optional[str] = None,
        n_recommendations: int = 10
    ) -> List[Dict[str, Any]]:
        """热门趋势推荐"""
        try:
            # 这里应该从数据库获取热门数据
            # 暂时返回模拟数据
            trending_items = [
                {
                    "novel_id": i,
                    "score": 0.9 - i * 0.1,
                    "reason": f"最近{time_window_days}天热门",
                    "trend_score": 0.9 - i * 0.1
                }
                for i in range(1, n_recommendations + 1)
            ]
            
            return trending_items
            
        except Exception as e:
            logger.error(f"热门推荐失败: {e}")
            return []
    
    def _calculate_content_score(
        self,
        user_preferences: Dict[str, Any],
        item: Dict[str, Any]
    ) -> float:
        """计算基于内容的推荐分数"""
        try:
            score = 0.0
            
            # 类型偏好
            preferred_categories = user_preferences.get("categories", [])
            if item.get("category") in preferred_categories:
                score += 0.3
            
            # 标签偏好
            preferred_tags = set(user_preferences.get("tags", []))
            item_tags = set(item.get("tags", []))
            
            if preferred_tags and item_tags:
                tag_match_ratio = len(preferred_tags & item_tags) / len(preferred_tags)
                score += tag_match_ratio * 0.2
            
            # 作者偏好
            preferred_authors = user_preferences.get("authors", [])
            if item.get("author_id") in preferred_authors:
                score += 0.2
            
            # 评分偏好
            min_rating = user_preferences.get("min_rating", 0)
            item_rating = item.get("rating", 0)
            
            if item_rating >= min_rating:
                score += 0.1
            
            # 字数偏好
            preferred_length = user_preferences.get("preferred_length", "medium")
            item_word_count = item.get("word_count", 0)
            
            if self._match_length_preference(preferred_length, item_word_count):
                score += 0.1
            
            # 状态偏好
            preferred_status = user_preferences.get("preferred_status", [])
            if not preferred_status or item.get("status") in preferred_status:
                score += 0.1
            
            return score
            
        except Exception as e:
            logger.error(f"计算内容分数失败: {e}")
            return 0.0
    
    def _match_length_preference(self, preferred_length: str, word_count: int) -> bool:
        """匹配长度偏好"""
        if preferred_length == "short" and word_count < 100000:
            return True
        elif preferred_length == "medium" and 100000 <= word_count < 500000:
            return True
        elif preferred_length == "long" and word_count >= 500000:
            return True
        return False


class PopularityCalculator:
    """热度计算器"""
    
    @staticmethod
    def calculate_novel_popularity(
        view_count: int,
        favorite_count: int,
        comment_count: int,
        rating: float,
        rating_count: int,
        update_frequency: float,
        days_since_last_update: int
    ) -> float:
        """计算小说热度分数"""
        try:
            # 基础分数
            base_score = 0.0
            
            # 阅读量权重 (30%)
            view_score = math.log10(max(view_count, 1)) / 6  # 假设最大阅读量为10^6
            base_score += view_score * 0.3
            
            # 收藏量权重 (25%)
            favorite_score = math.log10(max(favorite_count, 1)) / 5  # 假设最大收藏量为10^5
            base_score += favorite_score * 0.25
            
            # 评论量权重 (15%)
            comment_score = math.log10(max(comment_count, 1)) / 4  # 假设最大评论量为10^4
            base_score += comment_score * 0.15
            
            # 评分权重 (20%)
            if rating_count > 0:
                rating_score = (rating / 5.0) * math.log10(max(rating_count, 1)) / 3
                base_score += rating_score * 0.2
            
            # 更新频率权重 (10%)
            update_score = min(update_frequency / 7.0, 1.0)  # 每周更新为满分
            base_score += update_score * 0.1
            
            # 时间衰减
            time_decay = max(0.1, 1.0 - (days_since_last_update / 365.0))
            base_score *= time_decay
            
            return min(base_score, 1.0)
            
        except Exception as e:
            logger.error(f"计算热度分数失败: {e}")
            return 0.0
    
    @staticmethod
    def calculate_trending_score(
        recent_views: int,
        recent_favorites: int,
        recent_comments: int,
        growth_rate: float,
        time_window_hours: int = 24
    ) -> float:
        """计算趋势分数"""
        try:
            # 基于最近活动的趋势分数
            activity_score = (
                recent_views * 0.5 +
                recent_favorites * 3.0 +
                recent_comments * 2.0
            ) / time_window_hours
            
            # 增长率加成
            growth_bonus = min(growth_rate, 2.0)  # 最大2倍增长率
            
            trending_score = activity_score * (1 + growth_bonus)
            
            return min(trending_score / 100.0, 1.0)  # 归一化到0-1
            
        except Exception as e:
            logger.error(f"计算趋势分数失败: {e}")
            return 0.0


def get_user_reading_preferences(user_behaviors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """分析用户阅读偏好"""
    try:
        preferences = {
            "categories": [],
            "tags": [],
            "authors": [],
            "min_rating": 0.0,
            "preferred_length": "medium",
            "preferred_status": [],
            "reading_time_preference": "evening"
        }
        
        if not user_behaviors:
            return preferences
        
        # 统计类型偏好
        category_counter = Counter()
        tag_counter = Counter()
        author_counter = Counter()
        ratings = []
        word_counts = []
        statuses = []
        
        for behavior in user_behaviors:
            novel_info = behavior.get("novel_info", {})
            
            # 类型统计
            category = novel_info.get("category")
            if category:
                category_counter[category] += 1
            
            # 标签统计
            tags = novel_info.get("tags", [])
            for tag in tags:
                tag_counter[tag] += 1
            
            # 作者统计
            author_id = novel_info.get("author_id")
            if author_id:
                author_counter[author_id] += 1
            
            # 评分统计
            rating = novel_info.get("rating")
            if rating:
                ratings.append(rating)
            
            # 字数统计
            word_count = novel_info.get("word_count")
            if word_count:
                word_counts.append(word_count)
            
            # 状态统计
            status = novel_info.get("status")
            if status:
                statuses.append(status)
        
        # 生成偏好
        preferences["categories"] = [cat for cat, _ in category_counter.most_common(3)]
        preferences["tags"] = [tag for tag, _ in tag_counter.most_common(5)]
        preferences["authors"] = [author for author, _ in author_counter.most_common(3)]
        
        if ratings:
            preferences["min_rating"] = sum(ratings) / len(ratings) - 0.5
        
        if word_counts:
            avg_word_count = sum(word_counts) / len(word_counts)
            if avg_word_count < 100000:
                preferences["preferred_length"] = "short"
            elif avg_word_count > 500000:
                preferences["preferred_length"] = "long"
            else:
                preferences["preferred_length"] = "medium"
        
        if statuses:
            status_counter = Counter(statuses)
            preferences["preferred_status"] = [status for status, _ in status_counter.most_common(2)]
        
        return preferences
        
    except Exception as e:
        logger.error(f"分析用户偏好失败: {e}")
        return preferences