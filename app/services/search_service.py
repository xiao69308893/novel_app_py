# app/services/search_service.py
# -*- coding: utf-8 -*-
"""
搜索业务服务
处理搜索相关的业务逻辑，包括全文搜索、搜索建议、搜索历史等
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func, desc, asc, text
from sqlalchemy.orm import selectinload, joinedload
import uuid
import json

from ..models.novel import Novel
from ..models.user import User
from ..models.chapter import Chapter
from ..schemas.search import (
    SearchNovelResponse, SearchAuthorResponse, SearchSuggestionResponse,
    SearchHistoryResponse, SearchStatsResponse, SearchTrendResponse,
    SearchFilterResponse, AutoCompleteResponse
)
from ..utils.cache import CacheManager
from .base import BaseService


class SearchService(BaseService):
    """搜索服务类"""

    def __init__(self, db: AsyncSession, cache: Optional[CacheManager] = None):
        super().__init__(db, cache)

    async def search_novels(
        self,
        query: str,
        category: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        author: Optional[str] = None,
        sort_by: str = "relevance",
        page: int = 1,
        page_size: int = 20,
        user_id: Optional[uuid.UUID] = None
    ) -> Tuple[List[SearchNovelResponse], int]:
        """搜索小说"""
        
        offset = (page - 1) * page_size
        
        # 构建基础查询
        base_query = select(Novel).where(Novel.is_deleted == False)
        
        # 添加搜索条件
        if query:
            # 简单的文本搜索，实际项目中可以使用全文搜索引擎
            search_condition = or_(
                Novel.title.ilike(f"%{query}%"),
                Novel.description.ilike(f"%{query}%"),
                Novel.author.ilike(f"%{query}%"),
                Novel.tags.ilike(f"%{query}%")
            )
            base_query = base_query.where(search_condition)
        
        # 添加过滤条件
        if category:
            base_query = base_query.where(Novel.category == category)
        
        if status:
            base_query = base_query.where(Novel.status == status)
        
        if author:
            base_query = base_query.where(Novel.author.ilike(f"%{author}%"))
        
        if tags:
            for tag in tags:
                base_query = base_query.where(Novel.tags.ilike(f"%{tag}%"))
        
        # 获取总数
        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # 添加排序
        if sort_by == "relevance":
            # 相关性排序（简化版）
            base_query = base_query.order_by(desc(Novel.view_count))
        elif sort_by == "popularity":
            base_query = base_query.order_by(desc(Novel.view_count))
        elif sort_by == "rating":
            base_query = base_query.order_by(desc(Novel.rating))
        elif sort_by == "latest":
            base_query = base_query.order_by(desc(Novel.created_at))
        elif sort_by == "updated":
            base_query = base_query.order_by(desc(Novel.updated_at))
        else:
            base_query = base_query.order_by(desc(Novel.view_count))
        
        # 分页查询
        query_with_pagination = base_query.offset(offset).limit(page_size)
        result = await self.db.execute(query_with_pagination)
        novels = result.scalars().all()
        
        # 转换为响应模型
        search_results = [
            SearchNovelResponse(
                id=str(novel.id),
                title=novel.title,
                author=novel.author,
                description=novel.description,
                category=novel.category,
                tags=novel.tags.split(",") if novel.tags else [],
                status=novel.status,
                cover_url=novel.cover_url,
                rating=novel.rating,
                view_count=novel.view_count,
                chapter_count=novel.chapter_count,
                word_count=novel.word_count,
                created_at=novel.created_at,
                updated_at=novel.updated_at
            )
            for novel in novels
        ]
        
        # 记录搜索历史
        if user_id and query:
            await self._save_search_history(user_id, query, "novel")
        
        return search_results, total

    async def search_authors(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
        user_id: Optional[uuid.UUID] = None
    ) -> Tuple[List[SearchAuthorResponse], int]:
        """搜索作者"""
        
        offset = (page - 1) * page_size
        
        # 搜索作者（基于小说表中的作者字段）
        author_query = select(
            Novel.author,
            func.count(Novel.id).label('novel_count'),
            func.sum(Novel.view_count).label('total_views'),
            func.avg(Novel.rating).label('avg_rating')
        ).where(
            and_(
                Novel.is_deleted == False,
                Novel.author.ilike(f"%{query}%")
            )
        ).group_by(
            Novel.author
        ).order_by(
            desc(func.count(Novel.id))
        )
        
        # 获取总数
        count_query = select(func.count(func.distinct(Novel.author))).where(
            and_(
                Novel.is_deleted == False,
                Novel.author.ilike(f"%{query}%")
            )
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # 分页查询
        author_query = author_query.offset(offset).limit(page_size)
        result = await self.db.execute(author_query)
        authors = result.all()
        
        # 转换为响应模型
        search_results = [
            SearchAuthorResponse(
                name=author.author,
                novel_count=author.novel_count,
                total_views=author.total_views or 0,
                avg_rating=float(author.avg_rating or 0)
            )
            for author in authors
        ]
        
        # 记录搜索历史
        if user_id:
            await self._save_search_history(user_id, query, "author")
        
        return search_results, total

    async def get_search_suggestions(
        self,
        query: str,
        limit: int = 10
    ) -> List[SearchSuggestionResponse]:
        """获取搜索建议"""
        
        if not query or len(query) < 2:
            return []
        
        # 从小说标题中获取建议
        title_query = select(Novel.title).where(
            and_(
                Novel.is_deleted == False,
                Novel.title.ilike(f"%{query}%")
            )
        ).order_by(desc(Novel.view_count)).limit(limit)
        
        title_result = await self.db.execute(title_query)
        titles = [row[0] for row in title_result]
        
        # 从作者中获取建议
        author_query = select(func.distinct(Novel.author)).where(
            and_(
                Novel.is_deleted == False,
                Novel.author.ilike(f"%{query}%")
            )
        ).limit(limit)
        
        author_result = await self.db.execute(author_query)
        authors = [row[0] for row in author_result]
        
        # 组合建议
        suggestions = []
        
        # 添加标题建议
        for title in titles[:5]:
            suggestions.append(SearchSuggestionResponse(
                text=title,
                type="title",
                highlight=self._highlight_text(title, query)
            ))
        
        # 添加作者建议
        for author in authors[:5]:
            suggestions.append(SearchSuggestionResponse(
                text=author,
                type="author",
                highlight=self._highlight_text(author, query)
            ))
        
        return suggestions[:limit]

    async def get_hot_searches(self, limit: int = 10) -> List[str]:
        """获取热门搜索"""
        
        # 这里简化实现，实际项目中应该基于搜索频率统计
        hot_query = select(Novel.title).where(
            Novel.is_deleted == False
        ).order_by(desc(Novel.view_count)).limit(limit)
        
        result = await self.db.execute(hot_query)
        hot_searches = [row[0] for row in result]
        
        return hot_searches

    async def get_search_history(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[SearchHistoryResponse], int]:
        """获取搜索历史"""
        
        # 这里简化实现，实际项目中应该有专门的搜索历史表
        # 暂时返回空列表
        return [], 0

    async def clear_search_history(self, user_id: uuid.UUID) -> None:
        """清空搜索历史"""
        
        # 这里简化实现，实际项目中应该删除用户的搜索历史记录
        pass

    async def delete_search_history_item(
        self,
        user_id: uuid.UUID,
        history_id: str
    ) -> None:
        """删除单条搜索历史"""
        
        # 这里简化实现
        pass

    async def get_search_stats(self) -> SearchStatsResponse:
        """获取搜索统计"""
        
        # 获取总搜索次数（简化实现）
        total_searches = 1000  # 模拟数据
        
        # 获取热门关键词
        popular_keywords = await self.get_hot_searches(10)
        
        return SearchStatsResponse(
            total_searches=total_searches,
            popular_keywords=popular_keywords
        )

    async def get_search_trends(
        self,
        period: str = "7d"
    ) -> List[SearchTrendResponse]:
        """获取搜索趋势"""
        
        # 这里简化实现，返回模拟数据
        trends = []
        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            trends.append(SearchTrendResponse(
                date=date.date(),
                search_count=100 + i * 10,
                popular_keywords=["玄幻", "都市", "历史"]
            ))
        
        return trends

    async def get_related_searches(self, query: str) -> List[str]:
        """获取相关搜索"""
        
        # 简化实现，基于相似标题
        related_query = select(Novel.title).where(
            and_(
                Novel.is_deleted == False,
                Novel.title.ilike(f"%{query}%")
            )
        ).order_by(desc(Novel.view_count)).limit(5)
        
        result = await self.db.execute(related_query)
        related = [row[0] for row in result]
        
        return related

    async def submit_search_feedback(
        self,
        user_id: uuid.UUID,
        query: str,
        feedback_type: str,
        content: Optional[str] = None
    ) -> None:
        """提交搜索反馈"""
        
        # 这里简化实现，实际项目中应该保存反馈到数据库
        pass

    async def get_autocomplete(
        self,
        query: str,
        limit: int = 10
    ) -> List[AutoCompleteResponse]:
        """获取自动补全"""
        
        if not query or len(query) < 1:
            return []
        
        # 从小说标题获取自动补全
        autocomplete_query = select(Novel.title).where(
            and_(
                Novel.is_deleted == False,
                Novel.title.ilike(f"{query}%")
            )
        ).order_by(desc(Novel.view_count)).limit(limit)
        
        result = await self.db.execute(autocomplete_query)
        completions = [
            AutoCompleteResponse(
                text=row[0],
                type="title"
            )
            for row in result
        ]
        
        return completions

    async def get_search_filters(self) -> SearchFilterResponse:
        """获取搜索过滤器选项"""
        
        # 获取所有分类
        category_query = select(func.distinct(Novel.category)).where(
            Novel.is_deleted == False
        )
        category_result = await self.db.execute(category_query)
        categories = [row[0] for row in category_result if row[0]]
        
        # 获取所有状态
        status_query = select(func.distinct(Novel.status)).where(
            Novel.is_deleted == False
        )
        status_result = await self.db.execute(status_query)
        statuses = [row[0] for row in status_result if row[0]]
        
        # 获取热门标签
        tag_query = select(Novel.tags).where(
            and_(
                Novel.is_deleted == False,
                Novel.tags.isnot(None)
            )
        ).limit(100)
        tag_result = await self.db.execute(tag_query)
        
        all_tags = []
        for row in tag_result:
            if row[0]:
                all_tags.extend(row[0].split(","))
        
        # 统计标签频率并取前20个
        tag_counts = {}
        for tag in all_tags:
            tag = tag.strip()
            if tag:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        popular_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        tags = [tag[0] for tag in popular_tags]
        
        return SearchFilterResponse(
            categories=categories,
            statuses=statuses,
            tags=tags,
            sort_options=[
                {"value": "relevance", "label": "相关性"},
                {"value": "popularity", "label": "热门度"},
                {"value": "rating", "label": "评分"},
                {"value": "latest", "label": "最新"},
                {"value": "updated", "label": "最近更新"}
            ]
        )

    async def _save_search_history(
        self,
        user_id: uuid.UUID,
        query: str,
        search_type: str
    ) -> None:
        """保存搜索历史"""
        
        # 这里简化实现，实际项目中应该保存到搜索历史表
        pass

    def _highlight_text(self, text: str, query: str) -> str:
        """高亮显示搜索关键词"""
        
        if not query or not text:
            return text
        
        # 简单的高亮实现
        import re
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        return pattern.sub(f"<mark>{query}</mark>", text)