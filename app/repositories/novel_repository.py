# app/repositories/novel_repository.py
# -*- coding: utf-8 -*-
"""
小说仓库
提供小说相关的数据访问方法
"""

from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc, text
from sqlalchemy.orm import selectinload, joinedload
from datetime import datetime, timedelta
import logging

from app.repositories.base import BaseRepository
from app.models.novel import Novel, Chapter, Category, Tag, NovelTag, Favorite, ReadingHistory

logger = logging.getLogger(__name__)


class NovelRepository(BaseRepository):
    """小说仓库"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Novel)

    async def get_with_details(self, novel_id: int) -> Optional[Novel]:
        """获取小说详情（包含关联数据）"""
        try:
            query = select(Novel).where(Novel.id == novel_id).options(
                selectinload(Novel.author),
                selectinload(Novel.category),
                selectinload(Novel.tags),
                selectinload(Novel.chapters)
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取小说详情失败: {e}")
            return None

    async def get_by_category(
        self, 
        category_id: int,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "updated_at"
    ) -> List[Novel]:
        """根据分类获取小说列表"""
        filters = {"category_id": category_id, "status": {"ne": "deleted"}}
        return await self.get_multi(
            filters=filters,
            sort_by=sort_by,
            sort_order="desc",
            offset=skip,
            limit=limit
        )

    async def get_by_status(
        self, 
        status: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Novel]:
        """根据状态获取小说列表"""
        filters = {"status": status}
        return await self.get_multi(
            filters=filters,
            sort_by="updated_at",
            sort_order="desc",
            offset=skip,
            limit=limit
        )

    async def get_hot_novels(
        self, 
        days: int = 7,
        skip: int = 0,
        limit: int = 20
    ) -> List[Novel]:
        """获取热门小说"""
        try:
            # 根据最近几天的阅读量、收藏量等排序
            since_date = datetime.utcnow() - timedelta(days=days)
            
            query = select(Novel).where(
                and_(
                    Novel.status.in_(["serializing", "completed"]),
                    Novel.updated_at >= since_date
                )
            ).order_by(
                desc(Novel.view_count),
                desc(Novel.favorite_count),
                desc(Novel.updated_at)
            ).offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"获取热门小说失败: {e}")
            return []

    async def get_latest_novels(
        self, 
        skip: int = 0,
        limit: int = 20
    ) -> List[Novel]:
        """获取最新小说"""
        filters = {"status": {"in": ["serializing", "completed"]}}
        return await self.get_multi(
            filters=filters,
            sort_by="created_at",
            sort_order="desc",
            offset=skip,
            limit=limit
        )

    async def get_recommended_novels(
        self, 
        skip: int = 0,
        limit: int = 20
    ) -> List[Novel]:
        """获取推荐小说"""
        filters = {
            "status": {"in": ["serializing", "completed"]},
            "is_recommended": True
        }
        return await self.get_multi(
            filters=filters,
            sort_by="recommendation_score",
            sort_order="desc",
            offset=skip,
            limit=limit
        )

    async def search_novels(
        self, 
        keyword: str,
        category_id: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Novel]:
        """搜索小说"""
        try:
            # 构建基础查询
            conditions = [
                or_(
                    Novel.title.ilike(f"%{keyword}%"),
                    Novel.description.ilike(f"%{keyword}%"),
                    Novel.author_name.ilike(f"%{keyword}%")
                )
            ]
            
            # 添加分类过滤
            if category_id:
                conditions.append(Novel.category_id == category_id)
            
            # 添加状态过滤
            if status:
                conditions.append(Novel.status == status)
            else:
                conditions.append(Novel.status != "deleted")
            
            query = select(Novel).where(and_(*conditions)).order_by(
                desc(Novel.view_count),
                desc(Novel.updated_at)
            ).offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"搜索小说失败: {e}")
            return []

    async def get_similar_novels(
        self, 
        novel_id: int,
        limit: int = 10
    ) -> List[Novel]:
        """获取相似小说"""
        try:
            # 获取当前小说信息
            novel = await self.get_by_id(novel_id)
            if not novel:
                return []
            
            # 基于分类和标签查找相似小说
            query = select(Novel).where(
                and_(
                    Novel.id != novel_id,
                    Novel.category_id == novel.category_id,
                    Novel.status.in_(["serializing", "completed"])
                )
            ).order_by(
                desc(Novel.view_count),
                desc(Novel.favorite_count)
            ).limit(limit)
            
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"获取相似小说失败: {e}")
            return []

    async def get_author_novels(
        self, 
        author_id: int,
        exclude_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Novel]:
        """获取作者的其他小说"""
        try:
            conditions = [
                Novel.author_id == author_id,
                Novel.status != "deleted"
            ]
            
            if exclude_id:
                conditions.append(Novel.id != exclude_id)
            
            query = select(Novel).where(and_(*conditions)).order_by(
                desc(Novel.updated_at)
            ).offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"获取作者小说失败: {e}")
            return []

    async def update_view_count(self, novel_id: int) -> bool:
        """更新阅读量"""
        try:
            novel = await self.get_by_id(novel_id)
            if not novel:
                return False
            
            await self.update(novel, {"view_count": novel.view_count + 1})
            return True
        except Exception as e:
            logger.error(f"更新阅读量失败: {e}")
            return False

    async def update_favorite_count(self, novel_id: int, increment: int = 1) -> bool:
        """更新收藏量"""
        try:
            novel = await self.get_by_id(novel_id)
            if not novel:
                return False
            
            new_count = max(0, novel.favorite_count + increment)
            await self.update(novel, {"favorite_count": new_count})
            return True
        except Exception as e:
            logger.error(f"更新收藏量失败: {e}")
            return False

    async def get_novel_statistics(self, novel_id: int) -> Dict[str, Any]:
        """获取小说统计信息"""
        try:
            novel = await self.get_by_id(novel_id)
            if not novel:
                return {}
            
            # 获取章节统计
            chapter_count = await self.db.execute(
                select(func.count(Chapter.id)).where(Chapter.novel_id == novel_id)
            )
            total_chapters = chapter_count.scalar() or 0
            
            # 获取总字数
            word_count = await self.db.execute(
                select(func.sum(Chapter.word_count)).where(Chapter.novel_id == novel_id)
            )
            total_words = word_count.scalar() or 0
            
            return {
                "novel_id": novel_id,
                "title": novel.title,
                "view_count": novel.view_count,
                "favorite_count": novel.favorite_count,
                "comment_count": novel.comment_count,
                "total_chapters": total_chapters,
                "total_words": total_words,
                "status": novel.status,
                "created_at": novel.created_at,
                "updated_at": novel.updated_at
            }
        except Exception as e:
            logger.error(f"获取小说统计失败: {e}")
            return {}


class ChapterRepository(BaseRepository):
    """章节仓库"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Chapter)

    async def get_novel_chapters(
        self, 
        novel_id: int,
        skip: int = 0,
        limit: int = 100,
        order: str = "asc"
    ) -> List[Chapter]:
        """获取小说章节列表"""
        filters = {"novel_id": novel_id}
        return await self.get_multi(
            filters=filters,
            sort_by="chapter_number",
            sort_order=order,
            offset=skip,
            limit=limit
        )

    async def get_by_number(self, novel_id: int, chapter_number: int) -> Optional[Chapter]:
        """根据章节号获取章节"""
        try:
            query = select(Chapter).where(
                and_(
                    Chapter.novel_id == novel_id,
                    Chapter.chapter_number == chapter_number
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"根据章节号获取章节失败: {e}")
            return None

    async def get_latest_chapter(self, novel_id: int) -> Optional[Chapter]:
        """获取最新章节"""
        try:
            query = select(Chapter).where(
                Chapter.novel_id == novel_id
            ).order_by(desc(Chapter.chapter_number)).limit(1)
            
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取最新章节失败: {e}")
            return None

    async def get_previous_chapter(self, novel_id: int, chapter_number: int) -> Optional[Chapter]:
        """获取上一章节"""
        try:
            query = select(Chapter).where(
                and_(
                    Chapter.novel_id == novel_id,
                    Chapter.chapter_number < chapter_number
                )
            ).order_by(desc(Chapter.chapter_number)).limit(1)
            
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取上一章节失败: {e}")
            return None

    async def get_next_chapter(self, novel_id: int, chapter_number: int) -> Optional[Chapter]:
        """获取下一章节"""
        try:
            query = select(Chapter).where(
                and_(
                    Chapter.novel_id == novel_id,
                    Chapter.chapter_number > chapter_number
                )
            ).order_by(asc(Chapter.chapter_number)).limit(1)
            
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取下一章节失败: {e}")
            return None

    async def update_view_count(self, chapter_id: int) -> bool:
        """更新章节阅读量"""
        try:
            chapter = await self.get_by_id(chapter_id)
            if not chapter:
                return False
            
            await self.update(chapter, {"view_count": chapter.view_count + 1})
            return True
        except Exception as e:
            logger.error(f"更新章节阅读量失败: {e}")
            return False


class CategoryRepository(BaseRepository):
    """分类仓库"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Category)

    async def get_all_categories(self) -> List[Category]:
        """获取所有分类"""
        return await self.get_multi(
            sort_by="sort_order",
            sort_order="asc",
            limit=1000
        )

    async def get_by_name(self, name: str) -> Optional[Category]:
        """根据名称获取分类"""
        return await self.get_by_field("name", name)

    async def get_category_with_novels_count(self, category_id: int) -> Dict[str, Any]:
        """获取分类及其小说数量"""
        try:
            category = await self.get_by_id(category_id)
            if not category:
                return {}
            
            # 统计小说数量
            novel_count = await self.db.execute(
                select(func.count(Novel.id)).where(
                    and_(
                        Novel.category_id == category_id,
                        Novel.status != "deleted"
                    )
                )
            )
            total_novels = novel_count.scalar() or 0
            
            return {
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "novel_count": total_novels
            }
        except Exception as e:
            logger.error(f"获取分类统计失败: {e}")
            return {}


class FavoriteRepository(BaseRepository):
    """收藏仓库"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Favorite)

    async def get_user_favorites(
        self, 
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[Favorite]:
        """获取用户收藏列表"""
        filters = {"user_id": user_id}
        return await self.get_multi(
            filters=filters,
            sort_by="created_at",
            sort_order="desc",
            offset=skip,
            limit=limit,
            relationships=["novel"]
        )

    async def check_favorite_exists(self, user_id: int, novel_id: int) -> bool:
        """检查是否已收藏"""
        return await self.exists({"user_id": user_id, "novel_id": novel_id})

    async def add_favorite(self, user_id: int, novel_id: int) -> Optional[Favorite]:
        """添加收藏"""
        try:
            # 检查是否已收藏
            if await self.check_favorite_exists(user_id, novel_id):
                return None
            
            favorite_data = {
                "user_id": user_id,
                "novel_id": novel_id
            }
            return await self.create(favorite_data)
        except Exception as e:
            logger.error(f"添加收藏失败: {e}")
            return None

    async def remove_favorite(self, user_id: int, novel_id: int) -> bool:
        """取消收藏"""
        try:
            from sqlalchemy import delete
            stmt = delete(Favorite).where(
                and_(
                    Favorite.user_id == user_id,
                    Favorite.novel_id == novel_id
                )
            )
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"取消收藏失败: {e}")
            return False


class ReadingHistoryRepository(BaseRepository):
    """阅读历史仓库"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, ReadingHistory)

    async def get_user_history(
        self, 
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[ReadingHistory]:
        """获取用户阅读历史"""
        filters = {"user_id": user_id}
        return await self.get_multi(
            filters=filters,
            sort_by="updated_at",
            sort_order="desc",
            offset=skip,
            limit=limit,
            relationships=["novel", "chapter"]
        )

    async def get_or_create_history(
        self, 
        user_id: int, 
        novel_id: int
    ) -> Optional[ReadingHistory]:
        """获取或创建阅读历史"""
        try:
            # 先尝试获取现有记录
            history = await self.get_by_field("user_id", user_id)
            if history and history.novel_id == novel_id:
                return history
            
            # 查找是否存在该小说的历史记录
            query = select(ReadingHistory).where(
                and_(
                    ReadingHistory.user_id == user_id,
                    ReadingHistory.novel_id == novel_id
                )
            )
            result = await self.db.execute(query)
            history = result.scalar_one_or_none()
            
            if history:
                return history
            
            # 创建新的历史记录
            history_data = {
                "user_id": user_id,
                "novel_id": novel_id,
                "chapter_id": None,
                "progress": 0
            }
            return await self.create(history_data)
        except Exception as e:
            logger.error(f"获取或创建阅读历史失败: {e}")
            return None

    async def update_reading_progress(
        self, 
        user_id: int, 
        novel_id: int,
        chapter_id: int,
        progress: int = 0
    ) -> bool:
        """更新阅读进度"""
        try:
            history = await self.get_or_create_history(user_id, novel_id)
            if not history:
                return False
            
            update_data = {
                "chapter_id": chapter_id,
                "progress": progress,
                "updated_at": datetime.utcnow()
            }
            
            await self.update(history, update_data)
            return True
        except Exception as e:
            logger.error(f"更新阅读进度失败: {e}")
            return False