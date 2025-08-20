# app/services/bookshelf_service.py
# -*- coding: utf-8 -*-
"""
书架业务服务
处理用户书架相关的业务逻辑，包括收藏、分组、推荐等
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func, desc, asc
from sqlalchemy.orm import selectinload, joinedload
import uuid

from ..models.user import User, UserFavorite, UserBookshelf, ReadingHistory
from ..models.novel import Novel, NovelRating
from ..models.chapter import Chapter, ReadingProgress
from ..schemas.bookshelf import (
    BookshelfResponse, BookshelfCreateRequest, BookshelfUpdateRequest,
    FavoriteResponse, FavoriteCreateRequest, BookshelfNovelResponse
)
from ..core.exceptions import NotFoundException, BusinessException, PermissionException
from .base import BaseService


class BookshelfService(BaseService):
    """书架服务类"""

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_user_bookshelves(
            self,
            user_id: uuid.UUID,
            include_default: bool = True
    ) -> List[BookshelfResponse]:
        """获取用户书架列表"""
        cache_key = f"user_bookshelves:{user_id}"
        cached_data = await self.cache_get(cache_key)
        
        if cached_data:
            return [BookshelfResponse(**item) for item in cached_data]

        # 查询用户书架
        conditions = [UserBookshelf.user_id == user_id]
        if not include_default:
            conditions.append(UserBookshelf.is_default == False)

        query = select(UserBookshelf).where(
            and_(*conditions)
        ).order_by(UserBookshelf.sort_order.asc(), UserBookshelf.created_at.asc())

        result = await self.db.execute(query)
        bookshelves = result.scalars().all()

        # 获取每个书架的小说数量
        bookshelf_list = []
        for bookshelf in bookshelves:
            novel_count = await self._get_bookshelf_novel_count(bookshelf.id)
            
            bookshelf_data = BookshelfResponse(
                id=bookshelf.id,
                name=bookshelf.name,
                description=bookshelf.description,
                is_default=bookshelf.is_default,
                is_public=bookshelf.is_public,
                sort_order=bookshelf.sort_order,
                novel_count=novel_count,
                created_at=bookshelf.created_at,
                updated_at=bookshelf.updated_at
            )
            bookshelf_list.append(bookshelf_data)

        # 缓存结果
        cache_data = [item.dict() for item in bookshelf_list]
        await self.cache_set(cache_key, cache_data, expire=1800)

        return bookshelf_list

    async def create_bookshelf(
            self,
            user_id: uuid.UUID,
            bookshelf_data: BookshelfCreateRequest
    ) -> BookshelfResponse:
        """创建书架"""
        # 检查书架名称是否重复
        existing_query = select(UserBookshelf).where(
            and_(
                UserBookshelf.user_id == user_id,
                UserBookshelf.name == bookshelf_data.name
            )
        )
        existing_result = await self.db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise BusinessException("书架名称已存在")

        # 获取排序顺序
        max_order_query = select(func.max(UserBookshelf.sort_order)).where(
            UserBookshelf.user_id == user_id
        )
        max_order_result = await self.db.execute(max_order_query)
        max_order = max_order_result.scalar() or 0

        # 创建书架
        bookshelf = UserBookshelf(
            user_id=user_id,
            name=bookshelf_data.name,
            description=bookshelf_data.description,
            is_public=bookshelf_data.is_public,
            sort_order=max_order + 1
        )
        self.db.add(bookshelf)
        await self.db.commit()

        # 清除缓存
        await self._clear_user_bookshelf_cache(user_id)

        return BookshelfResponse(
            id=bookshelf.id,
            name=bookshelf.name,
            description=bookshelf.description,
            is_default=bookshelf.is_default,
            is_public=bookshelf.is_public,
            sort_order=bookshelf.sort_order,
            novel_count=0,
            created_at=bookshelf.created_at,
            updated_at=bookshelf.updated_at
        )

    async def update_bookshelf(
            self,
            bookshelf_id: uuid.UUID,
            user_id: uuid.UUID,
            update_data: BookshelfUpdateRequest
    ) -> BookshelfResponse:
        """更新书架"""
        # 查询书架
        query = select(UserBookshelf).where(
            and_(
                UserBookshelf.id == bookshelf_id,
                UserBookshelf.user_id == user_id
            )
        )
        result = await self.db.execute(query)
        bookshelf = result.scalar_one_or_none()

        if not bookshelf:
            raise NotFoundException("书架不存在")

        if bookshelf.is_default:
            raise BusinessException("默认书架不能修改")

        # 检查名称重复
        if update_data.name and update_data.name != bookshelf.name:
            existing_query = select(UserBookshelf).where(
                and_(
                    UserBookshelf.user_id == user_id,
                    UserBookshelf.name == update_data.name,
                    UserBookshelf.id != bookshelf_id
                )
            )
            existing_result = await self.db.execute(existing_query)
            if existing_result.scalar_one_or_none():
                raise BusinessException("书架名称已存在")

        # 更新字段
        update_fields = update_data.dict(exclude_unset=True)
        for field, value in update_fields.items():
            setattr(bookshelf, field, value)
        
        bookshelf.updated_at = datetime.utcnow()
        await self.db.commit()

        # 清除缓存
        await self._clear_user_bookshelf_cache(user_id)

        # 获取小说数量
        novel_count = await self._get_bookshelf_novel_count(bookshelf.id)

        return BookshelfResponse(
            id=bookshelf.id,
            name=bookshelf.name,
            description=bookshelf.description,
            is_default=bookshelf.is_default,
            is_public=bookshelf.is_public,
            sort_order=bookshelf.sort_order,
            novel_count=novel_count,
            created_at=bookshelf.created_at,
            updated_at=bookshelf.updated_at
        )

    async def delete_bookshelf(
            self,
            bookshelf_id: uuid.UUID,
            user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """删除书架"""
        # 查询书架
        query = select(UserBookshelf).where(
            and_(
                UserBookshelf.id == bookshelf_id,
                UserBookshelf.user_id == user_id
            )
        )
        result = await self.db.execute(query)
        bookshelf = result.scalar_one_or_none()

        if not bookshelf:
            raise NotFoundException("书架不存在")

        if bookshelf.is_default:
            raise BusinessException("默认书架不能删除")

        # 将书架中的收藏移动到默认书架
        default_bookshelf = await self._get_default_bookshelf(user_id)
        
        update_favorites_query = update(UserFavorite).where(
            UserFavorite.bookshelf_id == bookshelf_id
        ).values(bookshelf_id=default_bookshelf.id)
        await self.db.execute(update_favorites_query)

        # 删除书架
        delete_query = delete(UserBookshelf).where(UserBookshelf.id == bookshelf_id)
        await self.db.execute(delete_query)

        await self.db.commit()

        # 清除缓存
        await self._clear_user_bookshelf_cache(user_id)

        return {"message": "书架删除成功"}

    async def get_bookshelf_novels(
            self,
            bookshelf_id: uuid.UUID,
            user_id: uuid.UUID,
            page: int = 1,
            limit: int = 20,
            sort_by: str = "created_at",
            sort_order: str = "desc"
    ) -> Tuple[List[BookshelfNovelResponse], int]:
        """获取书架中的小说"""
        # 验证书架权限
        await self._check_bookshelf_permission(bookshelf_id, user_id)

        offset = (page - 1) * limit

        # 构建排序
        sort_column = getattr(UserFavorite, sort_by, UserFavorite.created_at)
        if sort_order == "desc":
            sort_column = sort_column.desc()
        else:
            sort_column = sort_column.asc()

        # 查询收藏的小说
        query = select(UserFavorite).options(
            joinedload(UserFavorite.novel).selectinload(Novel.author),
            joinedload(UserFavorite.novel).selectinload(Novel.category)
        ).where(
            UserFavorite.bookshelf_id == bookshelf_id
        ).order_by(sort_column).offset(offset).limit(limit)

        result = await self.db.execute(query)
        favorites = result.scalars().all()

        # 查询总数
        count_query = select(func.count()).select_from(UserFavorite).where(
            UserFavorite.bookshelf_id == bookshelf_id
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # 获取阅读进度
        novel_ids = [fav.novel_id for fav in favorites]
        progress_dict = {}
        if novel_ids:
            progress_query = select(ReadingProgress).where(
                and_(
                    ReadingProgress.user_id == user_id,
                    ReadingProgress.novel_id.in_(novel_ids)
                )
            )
            progress_result = await self.db.execute(progress_query)
            progress_dict = {
                progress.novel_id: progress 
                for progress in progress_result.scalars().all()
            }

        # 构建响应数据
        novel_list = []
        for favorite in favorites:
            novel = favorite.novel
            progress = progress_dict.get(novel.id)
            
            novel_data = BookshelfNovelResponse(
                id=novel.id,
                title=novel.title,
                author_name=novel.author.name if novel.author else "未知作者",
                cover_image=novel.cover_image,
                category_name=novel.category.name if novel.category else None,
                status=novel.status,
                word_count=novel.word_count,
                chapter_count=novel.chapter_count,
                last_chapter_title=novel.last_chapter_title,
                updated_at=novel.updated_at,
                favorited_at=favorite.created_at,
                reading_progress=progress.progress if progress else 0.0,
                last_read_chapter=progress.chapter_number if progress else 0
            )
            novel_list.append(novel_data)

        return novel_list, total

    async def add_to_favorite(
            self,
            user_id: uuid.UUID,
            favorite_data: FavoriteCreateRequest
    ) -> FavoriteResponse:
        """添加收藏"""
        # 检查小说是否存在
        novel_query = select(Novel).where(Novel.id == favorite_data.novel_id)
        novel_result = await self.db.execute(novel_query)
        novel = novel_result.scalar_one_or_none()

        if not novel:
            raise NotFoundException("小说不存在")

        # 检查是否已收藏
        existing_query = select(UserFavorite).where(
            and_(
                UserFavorite.user_id == user_id,
                UserFavorite.novel_id == favorite_data.novel_id
            )
        )
        existing_result = await self.db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise BusinessException("小说已收藏")

        # 获取书架
        bookshelf_id = favorite_data.bookshelf_id
        if not bookshelf_id:
            # 使用默认书架
            default_bookshelf = await self._get_default_bookshelf(user_id)
            bookshelf_id = default_bookshelf.id
        else:
            # 验证书架权限
            await self._check_bookshelf_permission(bookshelf_id, user_id)

        # 创建收藏
        favorite = UserFavorite(
            user_id=user_id,
            novel_id=favorite_data.novel_id,
            bookshelf_id=bookshelf_id
        )
        self.db.add(favorite)

        # 更新小说收藏数
        novel.favorite_count += 1
        novel.updated_at = datetime.utcnow()

        await self.db.commit()

        # 清除相关缓存
        await self._clear_user_bookshelf_cache(user_id)

        return FavoriteResponse(
            id=favorite.id,
            novel_id=favorite.novel_id,
            bookshelf_id=favorite.bookshelf_id,
            created_at=favorite.created_at
        )

    async def remove_from_favorite(
            self,
            user_id: uuid.UUID,
            novel_id: uuid.UUID
    ) -> Dict[str, Any]:
        """取消收藏"""
        # 查询收藏记录
        query = select(UserFavorite).where(
            and_(
                UserFavorite.user_id == user_id,
                UserFavorite.novel_id == novel_id
            )
        )
        result = await self.db.execute(query)
        favorite = result.scalar_one_or_none()

        if not favorite:
            raise NotFoundException("收藏记录不存在")

        # 删除收藏
        await self.db.delete(favorite)

        # 更新小说收藏数
        novel_query = select(Novel).where(Novel.id == novel_id)
        novel_result = await self.db.execute(novel_query)
        novel = novel_result.scalar_one_or_none()
        
        if novel and novel.favorite_count > 0:
            novel.favorite_count -= 1
            novel.updated_at = datetime.utcnow()

        await self.db.commit()

        # 清除相关缓存
        await self._clear_user_bookshelf_cache(user_id)

        return {"message": "取消收藏成功"}

    async def move_to_bookshelf(
            self,
            user_id: uuid.UUID,
            novel_id: uuid.UUID,
            target_bookshelf_id: uuid.UUID
    ) -> Dict[str, Any]:
        """移动小说到指定书架"""
        # 查询收藏记录
        favorite_query = select(UserFavorite).where(
            and_(
                UserFavorite.user_id == user_id,
                UserFavorite.novel_id == novel_id
            )
        )
        favorite_result = await self.db.execute(favorite_query)
        favorite = favorite_result.scalar_one_or_none()

        if not favorite:
            raise NotFoundException("收藏记录不存在")

        # 验证目标书架权限
        await self._check_bookshelf_permission(target_bookshelf_id, user_id)

        # 更新书架
        favorite.bookshelf_id = target_bookshelf_id
        favorite.updated_at = datetime.utcnow()

        await self.db.commit()

        # 清除相关缓存
        await self._clear_user_bookshelf_cache(user_id)

        return {"message": "移动成功"}

    async def get_recommendations(
            self,
            user_id: uuid.UUID,
            limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取推荐小说"""
        cache_key = f"user_recommendations:{user_id}"
        cached_data = await self.cache_get(cache_key)
        
        if cached_data:
            return cached_data

        # 基于用户收藏的小说类型推荐
        category_query = select(
            Novel.category_id,
            func.count().label('count')
        ).select_from(
            UserFavorite
        ).join(
            Novel, UserFavorite.novel_id == Novel.id
        ).where(
            UserFavorite.user_id == user_id
        ).group_by(
            Novel.category_id
        ).order_by(
            func.count().desc()
        ).limit(3)

        category_result = await self.db.execute(category_query)
        preferred_categories = [row.category_id for row in category_result.fetchall()]

        if not preferred_categories:
            # 如果用户没有收藏，推荐热门小说
            recommendations = await self._get_popular_novels(limit)
        else:
            # 基于偏好类型推荐
            recommendations = await self._get_category_recommendations(
                user_id, preferred_categories, limit
            )

        # 缓存推荐结果
        await self.cache_set(cache_key, recommendations, expire=3600)

        return recommendations

    async def _get_bookshelf_novel_count(self, bookshelf_id: uuid.UUID) -> int:
        """获取书架中的小说数量"""
        count_query = select(func.count()).select_from(UserFavorite).where(
            UserFavorite.bookshelf_id == bookshelf_id
        )
        count_result = await self.db.execute(count_query)
        return count_result.scalar() or 0

    async def _get_default_bookshelf(self, user_id: uuid.UUID) -> UserBookshelf:
        """获取用户默认书架"""
        query = select(UserBookshelf).where(
            and_(
                UserBookshelf.user_id == user_id,
                UserBookshelf.is_default == True
            )
        )
        result = await self.db.execute(query)
        bookshelf = result.scalar_one_or_none()

        if not bookshelf:
            # 创建默认书架
            bookshelf = UserBookshelf(
                user_id=user_id,
                name="我的收藏",
                description="默认收藏书架",
                is_default=True,
                is_public=False,
                sort_order=0
            )
            self.db.add(bookshelf)
            await self.db.commit()

        return bookshelf

    async def _check_bookshelf_permission(
            self,
            bookshelf_id: uuid.UUID,
            user_id: uuid.UUID
    ) -> None:
        """检查书架权限"""
        query = select(UserBookshelf).where(
            and_(
                UserBookshelf.id == bookshelf_id,
                UserBookshelf.user_id == user_id
            )
        )
        result = await self.db.execute(query)
        if not result.scalar_one_or_none():
            raise PermissionException("无权访问该书架")

    async def _clear_user_bookshelf_cache(self, user_id: uuid.UUID) -> None:
        """清除用户书架相关缓存"""
        cache_keys = [
            f"user_bookshelves:{user_id}",
            f"user_recommendations:{user_id}"
        ]
        for key in cache_keys:
            await self.cache_delete(key)

    async def _get_popular_novels(self, limit: int) -> List[Dict[str, Any]]:
        """获取热门小说"""
        query = select(Novel).options(
            joinedload(Novel.author),
            joinedload(Novel.category)
        ).where(
            Novel.status.in_(["serializing", "completed"])
        ).order_by(
            Novel.favorite_count.desc(),
            Novel.view_count.desc()
        ).limit(limit)

        result = await self.db.execute(query)
        novels = result.scalars().all()

        return [
            {
                "id": str(novel.id),
                "title": novel.title,
                "author_name": novel.author.name if novel.author else "未知作者",
                "cover_image": novel.cover_image,
                "category_name": novel.category.name if novel.category else None,
                "description": novel.description,
                "favorite_count": novel.favorite_count,
                "view_count": novel.view_count,
                "reason": "热门推荐"
            }
            for novel in novels
        ]

    async def get_user_favorites(
            self,
            user_id: uuid.UUID,
            sort_by: str = "created_at",
            sort_order: str = "desc",
            page: int = 1,
            page_size: int = 20,
            offset: int = 0
    ) -> Tuple[List[dict], int]:
        """获取用户收藏列表"""
        from ..models.novel import Novel
        
        # 查询收藏列表
        order_column = getattr(UserFavorite, sort_by, UserFavorite.created_at)
        order_func = desc if sort_order == "desc" else asc
        
        query = select(UserFavorite, Novel).join(
            Novel, UserFavorite.novel_id == Novel.id
        ).where(
            UserFavorite.user_id == user_id
        ).order_by(order_func(order_column)).offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        favorites_data = result.all()
        
        # 获取总数
        count_query = select(func.count(UserFavorite.id)).where(
            UserFavorite.user_id == user_id
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # 构建响应
        favorites = []
        for favorite, novel in favorites_data:
            favorites.append({
                "id": str(favorite.id),
                "novel_id": str(novel.id),
                "title": novel.title,
                "cover_url": novel.cover_url,
                "author_name": novel.author.name if novel.author else "",
                "category_name": novel.category.name if novel.category else "",
                "status": novel.status,
                "word_count": novel.word_count,
                "chapter_count": novel.chapter_count,
                "rating": novel.rating,
                "created_at": favorite.created_at,
                "folder_name": favorite.folder_name
            })
        
        return favorites, total

    async def get_reading_history(
            self,
            user_id: uuid.UUID,
            page: int = 1,
            page_size: int = 20,
            offset: int = 0
    ) -> Tuple[List[dict], int]:
        """获取阅读历史"""
        from ..models.novel import Novel
        from ..models.chapter import Chapter
        
        # 查询阅读历史
        query = select(ReadingHistory, Novel, Chapter).join(
            Novel, ReadingHistory.novel_id == Novel.id
        ).join(
            Chapter, ReadingHistory.chapter_id == Chapter.id
        ).where(
            ReadingHistory.user_id == user_id
        ).order_by(ReadingHistory.updated_at.desc()).offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        history_data = result.all()
        
        # 获取总数
        count_query = select(func.count(ReadingHistory.id)).where(
            ReadingHistory.user_id == user_id
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # 构建响应
        history = []
        for reading_history, novel, chapter in history_data:
            history.append({
                "id": str(reading_history.id),
                "novel_id": str(novel.id),
                "novel_title": novel.title,
                "novel_cover_url": novel.cover_url,
                "chapter_id": str(chapter.id),
                "chapter_title": chapter.title,
                "chapter_number": chapter.chapter_number,
                "reading_progress": reading_history.reading_progress,
                "reading_time": reading_history.reading_time,
                "last_read_at": reading_history.updated_at
            })
        
        return history, total

    async def get_recently_read(
            self,
            user_id: uuid.UUID,
            limit: int = 10
    ) -> List[dict]:
        """获取最近阅读的小说"""
        from ..models.novel import Novel
        from ..models.chapter import Chapter
        
        # 查询最近阅读
        query = select(ReadingHistory, Novel, Chapter).join(
            Novel, ReadingHistory.novel_id == Novel.id
        ).join(
            Chapter, ReadingHistory.chapter_id == Chapter.id
        ).where(
            ReadingHistory.user_id == user_id
        ).order_by(ReadingHistory.updated_at.desc()).limit(limit)
        
        result = await self.db.execute(query)
        recent_data = result.all()
        
        # 构建响应
        recent_novels = []
        for reading_history, novel, chapter in recent_data:
            recent_novels.append({
                "novel_id": str(novel.id),
                "novel_title": novel.title,
                "novel_cover_url": novel.cover_url,
                "chapter_id": str(chapter.id),
                "chapter_title": chapter.title,
                "chapter_number": chapter.chapter_number,
                "reading_progress": reading_history.reading_progress,
                "last_read_at": reading_history.updated_at
            })
        
        return recent_novels

    async def clear_reading_history(
            self,
            user_id: uuid.UUID,
            novel_ids: Optional[List[str]] = None
    ) -> dict:
        """清理阅读历史"""
        if novel_ids:
            # 删除指定小说的阅读历史
            novel_uuids = [uuid.UUID(novel_id) for novel_id in novel_ids]
            await self.db.execute(
                delete(ReadingHistory).where(
                    and_(
                        ReadingHistory.user_id == user_id,
                        ReadingHistory.novel_id.in_(novel_uuids)
                    )
                )
            )
        else:
            # 删除所有阅读历史
            await self.db.execute(
                delete(ReadingHistory).where(ReadingHistory.user_id == user_id)
            )
        
        await self.db.commit()
        
        return {
            "user_id": str(user_id),
            "message": "阅读历史清理成功"
        }

    async def add_to_favorites(
            self,
            user_id: uuid.UUID,
            novel_id: str,
            folder_name: str = "默认收藏夹"
    ) -> dict:
        """添加到收藏"""
        novel_uuid = uuid.UUID(novel_id)
        
        # 检查是否已收藏
        existing_query = select(UserFavorite).where(
            and_(
                UserFavorite.user_id == user_id,
                UserFavorite.novel_id == novel_uuid
            )
        )
        result = await self.db.execute(existing_query)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise BusinessException("已经收藏过该小说")
        
        # 创建收藏记录
        favorite = UserFavorite(
            user_id=user_id,
            novel_id=novel_uuid,
            folder_name=folder_name
        )
        self.db.add(favorite)
        await self.db.commit()
        
        return {
            "id": str(favorite.id),
            "novel_id": novel_id,
            "folder_name": folder_name,
            "message": "添加到收藏成功"
        }

    async def remove_from_favorites(
            self,
            user_id: uuid.UUID,
            novel_id: str
    ) -> dict:
        """从收藏中移除"""
        novel_uuid = uuid.UUID(novel_id)
        
        # 查找收藏记录
        query = select(UserFavorite).where(
            and_(
                UserFavorite.user_id == user_id,
                UserFavorite.novel_id == novel_uuid
            )
        )
        result = await self.db.execute(query)
        favorite = result.scalar_one_or_none()
        
        if not favorite:
            raise NotFoundException("收藏记录不存在")
        
        # 删除收藏记录
        await self.db.delete(favorite)
        await self.db.commit()
        
        return {
            "novel_id": novel_id,
            "message": "从收藏中移除成功"
        }

    async def sync_bookshelf(
            self,
            user_id: uuid.UUID,
            sync_data: dict
    ) -> dict:
        """同步书架数据"""
        # 这里可以实现书架数据同步逻辑
        # 比如从客户端同步收藏、阅读进度等数据
        
        # 清除缓存
        await self._clear_user_bookshelf_cache(user_id)
        
        return {
            "user_id": str(user_id),
            "message": "书架同步成功"
        }

    async def sort_bookshelf(
            self,
            user_id: uuid.UUID,
            sort_data: dict
    ) -> dict:
        """书架排序"""
        # 这里可以实现书架排序逻辑
        # 比如更新收藏的排序顺序
        
        # 清除缓存
        await self._clear_user_bookshelf_cache(user_id)
        
        return {
            "user_id": str(user_id),
            "message": "书架排序成功"
        }

    async def get_bookshelf(
            self,
            user_id: uuid.UUID,
            folder_name: Optional[str] = None,
            sort_by: str = "created_at",
            sort_order: str = "desc",
            page: int = 1,
            page_size: int = 20,
            offset: int = 0
    ) -> Tuple[List[dict], int]:
        """获取书架内容"""
        from ..models.novel import Novel
        
        # 构建查询条件
        conditions = [UserFavorite.user_id == user_id]
        if folder_name:
            conditions.append(UserFavorite.folder_name == folder_name)
        
        # 排序
        order_column = getattr(UserFavorite, sort_by, UserFavorite.created_at)
        order_func = desc if sort_order == "desc" else asc
        
        # 查询书架内容
        query = select(UserFavorite, Novel).join(
            Novel, UserFavorite.novel_id == Novel.id
        ).where(
            and_(*conditions)
        ).order_by(order_func(order_column)).offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        bookshelf_data = result.all()
        
        # 获取总数
        count_query = select(func.count(UserFavorite.id)).where(
            and_(*conditions)
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # 构建响应
        novels = []
        for favorite, novel in bookshelf_data:
            novels.append({
                "id": str(favorite.id),
                "novel_id": str(novel.id),
                "title": novel.title,
                "cover_url": novel.cover_url,
                "author_name": novel.author.name if novel.author else "",
                "category_name": novel.category.name if novel.category else "",
                "status": novel.status,
                "word_count": novel.word_count,
                "chapter_count": novel.chapter_count,
                "rating": novel.rating,
                "folder_name": favorite.folder_name,
                "created_at": favorite.created_at
            })
        
        return novels, total

    async def _get_category_recommendations(
            self,
            user_id: uuid.UUID,
            category_ids: List[uuid.UUID],
            limit: int
    ) -> List[Dict[str, Any]]:
        """基于类型推荐小说"""
        # 获取用户已收藏的小说ID
        favorited_query = select(UserFavorite.novel_id).where(
            UserFavorite.user_id == user_id
        )
        favorited_result = await self.db.execute(favorited_query)
        favorited_ids = [row[0] for row in favorited_result.fetchall()]

        # 推荐同类型的热门小说
        conditions = [
            Novel.category_id.in_(category_ids),
            Novel.status.in_(["serializing", "completed"])
        ]
        if favorited_ids:
            conditions.append(Novel.id.notin_(favorited_ids))

        query = select(Novel).options(
            joinedload(Novel.author),
            joinedload(Novel.category)
        ).where(
            and_(*conditions)
        ).order_by(
            Novel.favorite_count.desc(),
            Novel.view_count.desc()
        ).limit(limit)

        result = await self.db.execute(query)
        novels = result.scalars().all()

        return [
            {
                "id": str(novel.id),
                "title": novel.title,
                "author_name": novel.author.name if novel.author else "未知作者",
                "cover_image": novel.cover_image,
                "category_name": novel.category.name if novel.category else None,
                "description": novel.description,
                "favorite_count": novel.favorite_count,
                "view_count": novel.view_count,
                "reason": f"因为你喜欢{novel.category.name}类小说" if novel.category else "个性化推荐"
            }
            for novel in novels
        ]