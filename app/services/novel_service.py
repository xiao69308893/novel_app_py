"""
小说业务服务
处理小说相关的业务逻辑，包括小说查询、搜索、推荐、收藏等
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func, desc, asc, text
from sqlalchemy.orm import selectinload, joinedload
from decimal import Decimal
import uuid
import json

from ..models.novel import Novel, Category, Tag, Author, NovelTag, NovelRating
from ..models.chapter import Chapter, ReadingProgress
from ..models.user import UserFavorite
from ..models.comment import Comment
from ..schemas.novel import (
    NovelDetailResponse, NovelBasicResponse, NovelListResponse,
    NovelSearchRequest, CategoryResponse, TagResponse, AuthorResponse,
    NovelRatingRequest, CommentCreateRequest, CommentResponse,
    AdjacentChaptersResponse, ChapterDetailResponse, ChapterListResponse
)
from ..core.exceptions import NotFoundException, BusinessException, PermissionException
from .base import BaseService


class NovelService(BaseService):
    """小说服务类"""

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_novel_detail(
            self,
            novel_id: uuid.UUID,
            user_id: Optional[uuid.UUID] = None
    ) -> NovelDetailResponse:
        """获取小说详情"""
        cache_key = f"novel_detail:{novel_id}"
        if user_id:
            cache_key += f":{user_id}"

        cached_data = await self.cache_get(cache_key)
        if cached_data:
            return NovelDetailResponse.parse_obj(cached_data)

        # 查询小说详情，包含关联数据
        query = select(Novel).options(
            joinedload(Novel.author),
            joinedload(Novel.category),
            selectinload(Novel.novel_tags).joinedload(NovelTag.tag)
        ).where(Novel.id == novel_id)

        result = await self.db.execute(query)
        novel = result.scalar_one_or_none()

        if not novel:
            raise NotFoundException("小说不存在")

        # 构建响应数据
        response_data = {
            "id": novel.id,
            "title": novel.title,
            "subtitle": novel.subtitle,
            "description": novel.description,
            "cover_url": novel.cover_url,
            "language": novel.language,
            "word_count": novel.word_count,
            "chapter_count": novel.chapter_count,
            "status": novel.status,
            "publish_status": novel.publish_status,
            "is_vip": novel.is_vip,
            "is_free": novel.is_free,
            "price_per_chapter": novel.price_per_chapter,
            "view_count": novel.view_count,
            "favorite_count": novel.favorite_count,
            "comment_count": novel.comment_count,
            "rating": novel.rating,
            "rating_count": novel.rating_count,
            "last_chapter_title": novel.last_chapter_title,
            "last_update_time": novel.last_update_time,
            "created_at": novel.created_at,
            "published_at": novel.published_at,
            "author": AuthorResponse.from_orm(novel.author),
            "category": CategoryResponse.from_orm(novel.category) if novel.category else None,
            "tags": [TagResponse.from_orm(nt.tag) for nt in novel.novel_tags],
        }

        # 如果用户已登录，获取用户相关信息
        if user_id:
            # 检查是否已收藏
            favorite_query = select(UserFavorite).where(
                and_(
                    UserFavorite.user_id == user_id,
                    UserFavorite.novel_id == novel_id
                )
            )
            favorite_result = await self.db.execute(favorite_query)
            is_favorited = favorite_result.scalar_one_or_none() is not None
            response_data["is_favorited"] = is_favorited

            # 获取用户评分
            rating_query = select(NovelRating).where(
                and_(
                    NovelRating.user_id == user_id,
                    NovelRating.novel_id == novel_id
                )
            )
            rating_result = await self.db.execute(rating_query)
            user_rating = rating_result.scalar_one_or_none()
            response_data["user_rating"] = user_rating.rating if user_rating else None

            # 获取阅读进度
            progress_query = select(ReadingProgress).where(
                and_(
                    ReadingProgress.user_id == user_id,
                    ReadingProgress.novel_id == novel_id
                )
            )
            progress_result = await self.db.execute(progress_query)
            progress = progress_result.scalar_one_or_none()
            if progress:
                response_data["reading_progress"] = {
                    "chapter_number": progress.chapter_number,
                    "progress": float(progress.progress),
                    "reading_time": progress.reading_time
                }

        response = NovelDetailResponse(**response_data)

        # 缓存结果
        await self.cache_set(cache_key, response.dict(), expire=300)

        return response

    async def search_novels(
            self,
            search_params: NovelSearchRequest,
            page: int = 1,
            limit: int = 20
    ) -> NovelListResponse:
        """搜索小说"""
        offset = (page - 1) * limit

        # 构建查询条件
        conditions = [Novel.publish_status == 'published']

        # 关键词搜索
        if search_params.keyword:
            # 使用全文搜索或模糊匹配
            keyword_condition = or_(
                Novel.title.ilike(f"%{search_params.keyword}%"),
                Novel.description.ilike(f"%{search_params.keyword}%")
            )
            conditions.append(keyword_condition)

        # 分类过滤
        if search_params.category_id:
            conditions.append(Novel.category_id == search_params.category_id)

        # 状态过滤
        if search_params.status:
            conditions.append(Novel.status == search_params.status)

        # 语言过滤
        if search_params.language:
            conditions.append(Novel.language == search_params.language)

        # 免费/付费过滤
        if search_params.is_free is not None:
            conditions.append(Novel.is_free == search_params.is_free)

        # 字数范围过滤
        if search_params.word_count_min:
            conditions.append(Novel.word_count >= search_params.word_count_min)
        if search_params.word_count_max:
            conditions.append(Novel.word_count <= search_params.word_count_max)

        # 评分过滤
        if search_params.rating_min:
            conditions.append(Novel.rating >= search_params.rating_min)

        # 构建基础查询
        query = select(Novel).options(
            joinedload(Novel.author),
            joinedload(Novel.category)
        ).where(and_(*conditions))

        # 标签过滤（需要额外处理）
        if search_params.tags:
            tag_query = select(NovelTag.novel_id).join(Tag).where(
                Tag.name.in_(search_params.tags)
            )
            tag_novel_ids = await self.db.execute(tag_query)
            novel_ids = [row[0] for row in tag_novel_ids.fetchall()]
            if novel_ids:
                query = query.where(Novel.id.in_(novel_ids))
            else:
                # 如果没有匹配的标签，返回空结果
                return NovelListResponse(items=[], total=0, has_more=False)

        # 排序
        if search_params.sort_by:
            sort_field = getattr(Novel, search_params.sort_by, None)
            if sort_field:
                if search_params.sort_order == 'asc':
                    query = query.order_by(asc(sort_field))
                else:
                    query = query.order_by(desc(sort_field))
        else:
            # 默认按更新时间倒序
            query = query.order_by(desc(Novel.last_update_time))

        # 获取总数
        count_query = select(func.count(Novel.id)).where(and_(*conditions))
        if search_params.tags:
            count_query = count_query.where(Novel.id.in_(novel_ids))

        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # 分页查询
        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        novels = result.scalars().all()

        # 构建响应
        items = []
        for novel in novels:
            item_data = {
                "id": novel.id,
                "title": novel.title,
                "cover_url": novel.cover_url,
                "author_name": novel.author.name,
                "category_name": novel.category.name if novel.category else None,
                "status": novel.status,
                "word_count": novel.word_count,
                "chapter_count": novel.chapter_count,
                "rating": novel.rating,
                "view_count": novel.view_count,
                "favorite_count": novel.favorite_count,
                "is_vip": novel.is_vip,
                "is_free": novel.is_free,
                "last_update_time": novel.last_update_time
            }
            items.append(NovelBasicResponse(**item_data))

        return NovelListResponse(
            items=items,
            total=total,
            has_more=total > page * limit
        )

    async def get_hot_novels(self, page: int = 1, limit: int = 20) -> NovelListResponse:
        """获取热门小说"""
        cache_key = f"hot_novels:{page}:{limit}"
        cached_data = await self.cache_get(cache_key)
        if cached_data:
            return NovelListResponse.parse_obj(cached_data)

        offset = (page - 1) * limit

        # 按浏览量和收藏量综合排序
        query = select(Novel).options(
            joinedload(Novel.author),
            joinedload(Novel.category)
        ).where(
            Novel.publish_status == 'published'
        ).order_by(
            desc(Novel.view_count + Novel.favorite_count * 10)
        ).offset(offset).limit(limit)

        result = await self.db.execute(query)
        novels = result.scalars().all()

        # 获取总数
        count_query = select(func.count(Novel.id)).where(
            Novel.publish_status == 'published'
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # 构建响应
        items = [self._build_novel_basic_response(novel) for novel in novels]

        response = NovelListResponse(
            items=items,
            total=total,
            has_more=total > page * limit
        )

        # 缓存结果
        await self.cache_set(cache_key, response.dict(), expire=300)

        return response

    async def get_new_novels(self, page: int = 1, limit: int = 20) -> NovelListResponse:
        """获取最新小说"""
        cache_key = f"new_novels:{page}:{limit}"
        cached_data = await self.cache_get(cache_key)
        if cached_data:
            return NovelListResponse.parse_obj(cached_data)

        offset = (page - 1) * limit

        query = select(Novel).options(
            joinedload(Novel.author),
            joinedload(Novel.category)
        ).where(
            Novel.publish_status == 'published'
        ).order_by(
            desc(Novel.created_at)
        ).offset(offset).limit(limit)

        result = await self.db.execute(query)
        novels = result.scalars().all()

        # 获取总数
        count_query = select(func.count(Novel.id)).where(
            Novel.publish_status == 'published'
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # 构建响应
        items = [self._build_novel_basic_response(novel) for novel in novels]

        response = NovelListResponse(
            items=items,
            total=total,
            has_more=total > page * limit
        )

        # 缓存结果
        await self.cache_set(cache_key, response.dict(), expire=300)

        return response

    async def get_personalized_recommendations(
            self,
            user_id: uuid.UUID,
            page: int = 1,
            limit: int = 20
    ) -> NovelListResponse:
        """获取个性化推荐"""
        # 简化的推荐算法：基于用户收藏的分类和标签
        offset = (page - 1) * limit

        # 获取用户收藏的小说分类
        favorite_categories_query = select(Novel.category_id).join(UserFavorite).where(
            and_(
                UserFavorite.user_id == user_id,
                Novel.category_id.is_not(None)
            )
        ).distinct()

        category_result = await self.db.execute(favorite_categories_query)
        favorite_category_ids = [row[0] for row in category_result.fetchall()]

        # 基于分类推荐
        conditions = [Novel.publish_status == 'published']
        if favorite_category_ids:
            conditions.append(Novel.category_id.in_(favorite_category_ids))

        # 排除用户已收藏的小说
        favorited_query = select(UserFavorite.novel_id).where(
            UserFavorite.user_id == user_id
        )
        favorited_result = await self.db.execute(favorited_query)
        favorited_novel_ids = [row[0] for row in favorited_result.fetchall()]

        if favorited_novel_ids:
            conditions.append(~Novel.id.in_(favorited_novel_ids))

        query = select(Novel).options(
            joinedload(Novel.author),
            joinedload(Novel.category)
        ).where(
            and_(*conditions)
        ).order_by(
            desc(Novel.rating),
            desc(Novel.favorite_count)
        ).offset(offset).limit(limit)

        result = await self.db.execute(query)
        novels = result.scalars().all()

        # 获取总数
        count_query = select(func.count(Novel.id)).where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # 构建响应
        items = [self._build_novel_basic_response(novel) for novel in novels]

        return NovelListResponse(
            items=items,
            total=total,
            has_more=total > page * limit
        )

    async def get_similar_novels(
            self,
            novel_id: uuid.UUID,
            limit: int = 10
    ) -> List[NovelBasicResponse]:
        """获取相似小说"""
        cache_key = f"similar_novels:{novel_id}:{limit}"
        cached_data = await self.cache_get(cache_key)
        if cached_data:
            return [NovelBasicResponse.parse_obj(item) for item in cached_data]

        # 获取目标小说信息
        target_novel_query = select(Novel).where(Novel.id == novel_id)
        target_result = await self.db.execute(target_novel_query)
        target_novel = target_result.scalar_one_or_none()

        if not target_novel:
            return []

        # 基于分类和标签查找相似小说
        conditions = [
            Novel.publish_status == 'published',
            Novel.id != novel_id
        ]

        if target_novel.category_id:
            conditions.append(Novel.category_id == target_novel.category_id)

        query = select(Novel).options(
            joinedload(Novel.author),
            joinedload(Novel.category)
        ).where(
            and_(*conditions)
        ).order_by(
            desc(Novel.rating),
            desc(Novel.favorite_count)
        ).limit(limit)

        result = await self.db.execute(query)
        novels = result.scalars().all()

        # 构建响应
        items = [self._build_novel_basic_response(novel) for novel in novels]

        # 缓存结果
        await self.cache_set(cache_key, [item.dict() for item in items], expire=600)

        return items

    async def add_to_favorites(
            self,
            user_id: uuid.UUID,
            novel_id: uuid.UUID,
            folder_name: str = "默认收藏夹"
    ):
        """添加到收藏"""
        # 检查小说是否存在
        novel_query = select(Novel).where(Novel.id == novel_id)
        novel_result = await self.db.execute(novel_query)
        novel = novel_result.scalar_one_or_none()

        if not novel:
            raise NotFoundException("小说不存在")

        # 检查是否已收藏
        existing_query = select(UserFavorite).where(
            and_(
                UserFavorite.user_id == user_id,
                UserFavorite.novel_id == novel_id
            )
        )
        existing_result = await self.db.execute(existing_query)
        existing_favorite = existing_result.scalar_one_or_none()

        if existing_favorite:
            raise BusinessException("已经收藏过该小说")

        # 创建收藏记录
        favorite = UserFavorite(
            user_id=user_id,
            novel_id=novel_id,
            folder_name=folder_name
        )
        self.db.add(favorite)

        # 更新小说收藏数
        update_query = update(Novel).where(Novel.id == novel_id).values(
            favorite_count=Novel.favorite_count + 1
        )
        await self.db.execute(update_query)

        await self.db.commit()

        # 清除相关缓存
        await self.cache_delete(f"novel_detail:{novel_id}")
        await self.cache_delete(f"user_favorites:{user_id}")

    async def remove_from_favorites(
            self,
            user_id: uuid.UUID,
            novel_id: uuid.UUID
    ):
        """从收藏中移除"""
        # 删除收藏记录
        delete_query = delete(UserFavorite).where(
            and_(
                UserFavorite.user_id == user_id,
                UserFavorite.novel_id == novel_id
            )
        )
        result = await self.db.execute(delete_query)

        if result.rowcount == 0:
            raise NotFoundException("收藏记录不存在")

        # 更新小说收藏数
        update_query = update(Novel).where(Novel.id == novel_id).values(
            favorite_count=Novel.favorite_count - 1
        )
        await self.db.execute(update_query)

        await self.db.commit()

        # 清除相关缓存
        await self.cache_delete(f"novel_detail:{novel_id}")
        await self.cache_delete(f"user_favorites:{user_id}")

    async def rate_novel(
            self,
            user_id: uuid.UUID,
            novel_id: uuid.UUID,
            rating_data: NovelRatingRequest
    ):
        """评分小说"""
        # 检查小说是否存在
        novel_query = select(Novel).where(Novel.id == novel_id)
        novel_result = await self.db.execute(novel_query)
        novel = novel_result.scalar_one_or_none()

        if not novel:
            raise NotFoundException("小说不存在")

        # 检查是否已评分
        existing_query = select(NovelRating).where(
            and_(
                NovelRating.user_id == user_id,
                NovelRating.novel_id == novel_id
            )
        )
        existing_result = await self.db.execute(existing_query)
        existing_rating = existing_result.scalar_one_or_none()

        if existing_rating:
            # 更新评分
            old_rating = existing_rating.rating
            existing_rating.rating = rating_data.rating
            existing_rating.review = rating_data.review
            existing_rating.updated_at = datetime.utcnow()

            # 重新计算平均评分
            new_rating = (novel.rating * novel.rating_count - old_rating + rating_data.rating) / novel.rating_count
        else:
            # 创建新评分
            new_rating_record = NovelRating(
                user_id=user_id,
                novel_id=novel_id,
                rating=rating_data.rating,
                review=rating_data.review
            )
            self.db.add(new_rating_record)

            # 重新计算平均评分
            new_rating = (novel.rating * novel.rating_count + rating_data.rating) / (novel.rating_count + 1)

            # 更新评分人数
            novel.rating_count += 1

        # 更新小说评分
        novel.rating = round(new_rating, 2)

        await self.db.commit()

        # 清除相关缓存
        await self.cache_delete(f"novel_detail:{novel_id}")

    async def get_categories(self) -> List[CategoryResponse]:
        """获取小说分类"""
        cache_key = "novel_categories"
        cached_data = await self.cache_get(cache_key)
        if cached_data:
            return [CategoryResponse.parse_obj(item) for item in cached_data]

        query = select(Category).where(Category.is_active == True).order_by(
            Category.level, Category.sort_order, Category.name
        )
        result = await self.db.execute(query)
        categories = result.scalars().all()

        items = [CategoryResponse.from_orm(category) for category in categories]

        # 缓存结果
        await self.cache_set(cache_key, [item.dict() for item in items], expire=3600)

        return items

    async def get_tags(self) -> List[dict]:
        """获取小说标签"""
        cache_key = "novel_tags"
        cached_data = await self.cache_get(cache_key)
        if cached_data:
            return cached_data

        query = select(Tag).where(Tag.is_active == True).order_by(
            Tag.sort_order, Tag.name
        )
        result = await self.db.execute(query)
        tags = result.scalars().all()

        items = [{
            "id": str(tag.id),
            "name": tag.name,
            "description": tag.description,
            "color": tag.color
        } for tag in tags]

        # 缓存结果
        await self.cache_set(cache_key, items, expire=3600)

        return items

    async def get_rankings(
            self,
            ranking_type: str,
            page: int = 1,
            page_size: int = 20,
            offset: int = 0
    ) -> Tuple[List[NovelBasicResponse], int]:
        """获取小说排行榜"""
        cache_key = f"novel_rankings:{ranking_type}:{page}:{page_size}"
        cached_data = await self.cache_get(cache_key)
        if cached_data:
            novels_data = [NovelBasicResponse.parse_obj(item) for item in cached_data["novels"]]
            return novels_data, cached_data["total"]

        # 构建查询
        query = select(Novel).options(
            joinedload(Novel.author),
            joinedload(Novel.category)
        ).where(
            Novel.publish_status == 'published'
        )

        # 根据排行榜类型排序
        if ranking_type == "hot":
            query = query.order_by(desc(Novel.view_count))
        elif ranking_type == "new":
            query = query.order_by(desc(Novel.created_at))
        elif ranking_type == "rating":
            query = query.order_by(desc(Novel.rating))
        elif ranking_type == "favorite":
            query = query.order_by(desc(Novel.favorite_count))
        else:
            query = query.order_by(desc(Novel.view_count))

        # 获取总数
        count_query = select(func.count(Novel.id)).where(
            Novel.publish_status == 'published'
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # 分页查询
        query = query.offset(offset).limit(page_size)
        result = await self.db.execute(query)
        novels = result.scalars().all()

        # 构建响应
        novel_responses = [self._build_novel_basic_response(novel) for novel in novels]

        # 缓存结果
        cache_data = {
            "novels": [novel.dict() for novel in novel_responses],
            "total": total
        }
        await self.cache_set(cache_key, cache_data, expire=1800)

        return novel_responses, total

    async def get_recommendations(
            self,
            page: int = 1,
            page_size: int = 20,
            offset: int = 0
    ) -> Tuple[List[NovelBasicResponse], int]:
        """获取推荐小说"""
        cache_key = f"novel_recommendations:{page}:{page_size}"
        cached_data = await self.cache_get(cache_key)
        if cached_data:
            novels_data = [NovelBasicResponse.parse_obj(item) for item in cached_data["novels"]]
            return novels_data, cached_data["total"]

        # 简化实现：按评分和热度综合排序
        query = select(Novel).options(
            joinedload(Novel.author),
            joinedload(Novel.category)
        ).where(
            and_(
                Novel.publish_status == 'published',
                Novel.rating >= 4.0
            )
        ).order_by(
            desc(Novel.rating * 0.6 + Novel.view_count * 0.4)
        )

        # 获取总数
        count_query = select(func.count(Novel.id)).where(
            and_(
                Novel.publish_status == 'published',
                Novel.rating >= 4.0
            )
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # 分页查询
        query = query.offset(offset).limit(page_size)
        result = await self.db.execute(query)
        novels = result.scalars().all()

        # 构建响应
        novel_responses = [self._build_novel_basic_response(novel) for novel in novels]

        # 缓存结果
        cache_data = {
            "novels": [novel.dict() for novel in novel_responses],
            "total": total
        }
        await self.cache_set(cache_key, cache_data, expire=1800)

        return novel_responses, total

    async def get_completed_novels(
            self,
            page: int = 1,
            page_size: int = 20,
            offset: int = 0
    ) -> Tuple[List[NovelBasicResponse], int]:
        """获取完结小说"""
        cache_key = f"completed_novels:{page}:{page_size}"
        cached_data = await self.cache_get(cache_key)
        if cached_data:
            novels_data = [NovelBasicResponse.parse_obj(item) for item in cached_data["novels"]]
            return novels_data, cached_data["total"]

        # 查询完结小说
        query = select(Novel).options(
            joinedload(Novel.author),
            joinedload(Novel.category)
        ).where(
            and_(
                Novel.publish_status == 'published',
                Novel.status == 'completed'
            )
        ).order_by(desc(Novel.last_update_time))

        # 获取总数
        count_query = select(func.count(Novel.id)).where(
            and_(
                Novel.publish_status == 'published',
                Novel.status == 'completed'
            )
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # 分页查询
        query = query.offset(offset).limit(page_size)
        result = await self.db.execute(query)
        novels = result.scalars().all()

        # 构建响应
        novel_responses = [self._build_novel_basic_response(novel) for novel in novels]

        # 缓存结果
        cache_data = {
            "novels": [novel.dict() for novel in novel_responses],
            "total": total
        }
        await self.cache_set(cache_key, cache_data, expire=1800)

        return novel_responses, total

    async def get_hot_keywords(self) -> List[str]:
        """获取热门搜索关键词"""
        cache_key = "hot_keywords"
        cached_data = await self.cache_get(cache_key)
        if cached_data:
            return cached_data

        # 简化实现：返回固定的热门关键词
        # 实际应该从搜索日志或统计表中获取
        keywords = [
            "修仙", "都市", "玄幻", "科幻", "言情",
            "穿越", "重生", "系统", "霸道总裁", "校园"
        ]

        # 缓存结果
        await self.cache_set(cache_key, keywords, expire=3600)

        return keywords

    async def get_search_suggestions(self, keyword: str) -> List[str]:
        """获取搜索建议"""
        if not keyword or len(keyword.strip()) < 2:
            return []

        # 简化实现：基于小说标题进行模糊匹配
        query = select(Novel.title).where(
            and_(
                Novel.title.ilike(f"%{keyword}%"),
                Novel.publish_status == 'published'
            )
        ).limit(10)

        result = await self.db.execute(query)
        titles = [row[0] for row in result.fetchall()]

        return titles

    def _build_novel_basic_response(self, novel: Novel) -> NovelBasicResponse:
        """构建小说基础响应"""
        return NovelBasicResponse(
            id=novel.id,
            title=novel.title,
            cover_url=novel.cover_url,
            author_name=novel.author.name,
            category_name=novel.category.name if novel.category else None,
            status=novel.status,
            word_count=novel.word_count,
            chapter_count=novel.chapter_count,
            rating=novel.rating,
            view_count=novel.view_count,
            favorite_count=novel.favorite_count,
            is_vip=novel.is_vip,
            is_free=novel.is_free,
            last_update_time=novel.last_update_time
        )