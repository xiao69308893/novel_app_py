# app/services/chapter_service.py
# -*- coding: utf-8 -*-
"""
章节业务服务
处理章节相关的业务逻辑，包括章节查询、内容获取、购买、评论等
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func, desc, asc
from sqlalchemy.orm import selectinload, joinedload
from decimal import Decimal
import uuid

from ..models.chapter import Chapter, ChapterPurchase, ReadingProgress, Bookmark
from ..models.novel import Novel
from ..models.comment import Comment, CommentLike
from ..models.user import User
from ..schemas.chapter import (
    ChapterDetailResponse, ChapterListResponse, ChapterBasicResponse,
    BookmarkCreateRequest, BookmarkResponse, ReadingProgressRequest,
    ReadingProgressResponse
)
from ..schemas.novel import CommentCreateRequest, CommentResponse
from ..core.exceptions import NotFoundException, BusinessException, PermissionException
from .base import BaseService


class ChapterService(BaseService):
    """章节服务类"""

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_chapter_list(
            self,
            novel_id: uuid.UUID,
            user_id: Optional[uuid.UUID] = None,
            page: int = 1,
            limit: int = 50
    ) -> Tuple[List[ChapterBasicResponse], int]:
        """获取章节列表"""
        offset = (page - 1) * limit

        # 查询章节列表
        query = select(Chapter).where(
            Chapter.novel_id == novel_id
        ).order_by(Chapter.chapter_number.asc()).offset(offset).limit(limit)

        result = await self.db.execute(query)
        chapters = result.scalars().all()

        # 查询总数
        count_query = select(func.count()).select_from(Chapter).where(
            Chapter.novel_id == novel_id
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # 如果用户已登录，获取购买状态
        purchased_chapters = set()
        if user_id:
            purchase_query = select(ChapterPurchase.chapter_id).where(
                and_(
                    ChapterPurchase.user_id == user_id,
                    ChapterPurchase.novel_id == novel_id
                )
            )
            purchase_result = await self.db.execute(purchase_query)
            purchased_chapters = {row[0] for row in purchase_result.fetchall()}

        # 构建响应数据
        chapter_list = []
        for chapter in chapters:
            is_purchased = chapter.id in purchased_chapters if user_id else False
            is_free = chapter.is_free or chapter.chapter_number <= 3  # 前3章免费

            chapter_data = ChapterBasicResponse(
                id=chapter.id,
                title=chapter.title,
                chapter_number=chapter.chapter_number,
                volume_number=chapter.volume_number,
                word_count=chapter.word_count,
                is_vip=chapter.is_vip,
                is_free=is_free,
                price=chapter.price,
                published_at=chapter.published_at,
                is_purchased=is_purchased,
                can_read=is_free or is_purchased
            )
            chapter_list.append(chapter_data)

        return chapter_list, total

    async def get_chapter_detail(
            self,
            chapter_id: uuid.UUID,
            user_id: Optional[uuid.UUID] = None
    ) -> ChapterDetailResponse:
        """获取章节详情"""
        cache_key = f"chapter_detail:{chapter_id}"
        if user_id:
            cache_key += f":{user_id}"

        # 查询章节详情
        query = select(Chapter).options(
            joinedload(Chapter.novel)
        ).where(Chapter.id == chapter_id)

        result = await self.db.execute(query)
        chapter = result.scalar_one_or_none()

        if not chapter:
            raise NotFoundException("章节不存在")

        # 检查阅读权限
        can_read = await self._check_reading_permission(chapter, user_id)

        # 构建响应数据
        response_data = {
            "id": chapter.id,
            "title": chapter.title,
            "chapter_number": chapter.chapter_number,
            "volume_number": chapter.volume_number,
            "word_count": chapter.word_count,
            "is_vip": chapter.is_vip,
            "is_free": chapter.is_free,
            "price": chapter.price,
            "published_at": chapter.published_at,
            "can_read": can_read,
            "novel": {
                "id": chapter.novel.id,
                "title": chapter.novel.title,
                "author_name": chapter.novel.author.name if chapter.novel.author else None
            }
        }

        # 如果有阅读权限，返回内容
        if can_read:
            response_data["content"] = chapter.content
            response_data["summary"] = chapter.summary

            # 更新阅读统计
            if user_id:
                await self._update_reading_stats(chapter, user_id)

        # 获取相邻章节
        adjacent_chapters = await self._get_adjacent_chapters(chapter)
        response_data.update(adjacent_chapters)

        return ChapterDetailResponse(**response_data)

    async def purchase_chapter(
            self,
            chapter_id: uuid.UUID,
            user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """购买章节"""
        # 查询章节信息
        query = select(Chapter).options(
            joinedload(Chapter.novel)
        ).where(Chapter.id == chapter_id)

        result = await self.db.execute(query)
        chapter = result.scalar_one_or_none()

        if not chapter:
            raise NotFoundException("章节不存在")

        if chapter.is_free:
            raise BusinessException("免费章节无需购买")

        # 检查是否已购买
        purchase_query = select(ChapterPurchase).where(
            and_(
                ChapterPurchase.user_id == user_id,
                ChapterPurchase.chapter_id == chapter_id
            )
        )
        purchase_result = await self.db.execute(purchase_query)
        existing_purchase = purchase_result.scalar_one_or_none()

        if existing_purchase:
            raise BusinessException("章节已购买")

        # 查询用户余额
        user_query = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            raise NotFoundException("用户不存在")

        if user.coins < chapter.price:
            raise BusinessException("余额不足")

        # 扣除用户余额
        user.coins -= chapter.price
        user.updated_at = datetime.utcnow()

        # 创建购买记录
        purchase = ChapterPurchase(
            user_id=user_id,
            novel_id=chapter.novel_id,
            chapter_id=chapter_id,
            price=chapter.price,
            payment_method="coins"
        )
        self.db.add(purchase)

        await self.db.commit()

        return {
            "chapter_id": str(chapter_id),
            "price": float(chapter.price),
            "remaining_coins": float(user.coins)
        }

    async def create_bookmark(
            self,
            bookmark_data: BookmarkCreateRequest,
            user_id: uuid.UUID
    ) -> BookmarkResponse:
        """创建书签"""
        # 检查章节是否存在
        chapter_query = select(Chapter).where(Chapter.id == bookmark_data.chapter_id)
        chapter_result = await self.db.execute(chapter_query)
        chapter = chapter_result.scalar_one_or_none()

        if not chapter:
            raise NotFoundException("章节不存在")

        # 创建书签
        bookmark = Bookmark(
            user_id=user_id,
            novel_id=chapter.novel_id,
            chapter_id=bookmark_data.chapter_id,
            position=bookmark_data.position,
            note=bookmark_data.note
        )
        self.db.add(bookmark)
        await self.db.commit()

        return BookmarkResponse(
            id=bookmark.id,
            chapter_id=bookmark.chapter_id,
            position=bookmark.position,
            note=bookmark.note,
            created_at=bookmark.created_at
        )

    async def get_user_bookmarks(
            self,
            user_id: uuid.UUID,
            novel_id: Optional[uuid.UUID] = None,
            page: int = 1,
            limit: int = 20
    ) -> Tuple[List[BookmarkResponse], int]:
        """获取用户书签列表"""
        offset = (page - 1) * limit

        conditions = [Bookmark.user_id == user_id]
        if novel_id:
            conditions.append(Bookmark.novel_id == novel_id)

        query = select(Bookmark).options(
            joinedload(Bookmark.chapter)
        ).where(and_(*conditions)).order_by(
            Bookmark.created_at.desc()
        ).offset(offset).limit(limit)

        result = await self.db.execute(query)
        bookmarks = result.scalars().all()

        # 查询总数
        count_query = select(func.count()).select_from(Bookmark).where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        bookmark_list = [
            BookmarkResponse(
                id=bookmark.id,
                chapter_id=bookmark.chapter_id,
                chapter_title=bookmark.chapter.title,
                position=bookmark.position,
                note=bookmark.note,
                created_at=bookmark.created_at
            )
            for bookmark in bookmarks
        ]

        return bookmark_list, total

    async def update_reading_progress(
            self,
            progress_data: ReadingProgressRequest,
            user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """更新阅读进度"""
        # 查询或创建阅读进度记录
        progress_query = select(ReadingProgress).where(
            and_(
                ReadingProgress.user_id == user_id,
                ReadingProgress.novel_id == progress_data.novel_id
            )
        )
        progress_result = await self.db.execute(progress_query)
        progress = progress_result.scalar_one_or_none()

        if progress:
            # 更新现有记录
            progress.chapter_id = progress_data.chapter_id
            progress.chapter_number = progress_data.chapter_number
            progress.progress = progress_data.progress
            progress.reading_time += progress_data.reading_time
            progress.updated_at = datetime.utcnow()
        else:
            # 创建新记录
            progress = ReadingProgress(
                user_id=user_id,
                novel_id=progress_data.novel_id,
                chapter_id=progress_data.chapter_id,
                chapter_number=progress_data.chapter_number,
                progress=progress_data.progress,
                reading_time=progress_data.reading_time
            )
            self.db.add(progress)

        await self.db.commit()

        return {
            "novel_id": str(progress_data.novel_id),
            "chapter_id": str(progress_data.chapter_id),
            "progress": float(progress_data.progress),
            "reading_time": progress.reading_time
        }

    async def _check_reading_permission(
            self,
            chapter: Chapter,
            user_id: Optional[uuid.UUID]
    ) -> bool:
        """检查阅读权限"""
        # 免费章节或前几章免费
        if chapter.is_free or chapter.chapter_number <= 3:
            return True

        # 未登录用户无法阅读付费章节
        if not user_id:
            return False

        # 检查是否已购买
        purchase_query = select(ChapterPurchase).where(
            and_(
                ChapterPurchase.user_id == user_id,
                ChapterPurchase.chapter_id == chapter.id
            )
        )
        purchase_result = await self.db.execute(purchase_query)
        return purchase_result.scalar_one_or_none() is not None

    async def _update_reading_stats(
            self,
            chapter: Chapter,
            user_id: uuid.UUID
    ) -> None:
        """更新阅读统计"""
        # 更新章节阅读量
        chapter.view_count += 1

        # 更新小说阅读量
        novel_query = update(Novel).where(
            Novel.id == chapter.novel_id
        ).values(
            view_count=Novel.view_count + 1,
            updated_at=datetime.utcnow()
        )
        await self.db.execute(novel_query)

    async def _get_adjacent_chapters(
            self,
            chapter: Chapter
    ) -> Dict[str, Any]:
        """获取相邻章节"""
        # 上一章
        prev_query = select(Chapter).where(
            and_(
                Chapter.novel_id == chapter.novel_id,
                Chapter.chapter_number < chapter.chapter_number
            )
        ).order_by(Chapter.chapter_number.desc()).limit(1)

        prev_result = await self.db.execute(prev_query)
        prev_chapter = prev_result.scalar_one_or_none()

        # 下一章
        next_query = select(Chapter).where(
            and_(
                Chapter.novel_id == chapter.novel_id,
                Chapter.chapter_number > chapter.chapter_number
            )
        ).order_by(Chapter.chapter_number.asc()).limit(1)

        next_result = await self.db.execute(next_query)
        next_chapter = next_result.scalar_one_or_none()

        return {
            "prev_chapter": {
                "id": str(prev_chapter.id),
                "title": prev_chapter.title,
                "chapter_number": prev_chapter.chapter_number
            } if prev_chapter else None,
            "next_chapter": {
                "id": str(next_chapter.id),
                "title": next_chapter.title,
                "chapter_number": next_chapter.chapter_number
            } if next_chapter else None
        }

    async def get_novel_chapters(
            self,
            novel_id: str,
            page: int = 1,
            page_size: int = 50,
            offset: int = 0
    ) -> Tuple[List[ChapterBasicResponse], int]:
        """获取小说章节列表"""
        novel_uuid = uuid.UUID(novel_id)
        
        # 查询章节列表
        query = select(Chapter).where(
            Chapter.novel_id == novel_uuid
        ).order_by(Chapter.chapter_number.asc()).offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        chapters = result.scalars().all()
        
        # 获取总数
        count_query = select(func.count(Chapter.id)).where(
            Chapter.novel_id == novel_uuid
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # 构建响应
        chapter_responses = [
            ChapterBasicResponse(
                id=chapter.id,
                title=chapter.title,
                chapter_number=chapter.chapter_number,
                volume_number=chapter.volume_number,
                word_count=chapter.word_count,
                is_vip=chapter.is_vip,
                is_free=chapter.is_free,
                price=chapter.price,
                published_at=chapter.published_at,
                is_purchased=False,
                can_read=chapter.is_free or chapter.chapter_number <= 3
            ) for chapter in chapters
        ]
        
        return chapter_responses, total

    async def get_chapter_content(
            self,
            chapter_id: str,
            user_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """获取章节内容"""
        chapter_uuid = uuid.UUID(chapter_id)
        
        # 查询章节
        query = select(Chapter).options(
            joinedload(Chapter.novel)
        ).where(Chapter.id == chapter_uuid)
        
        result = await self.db.execute(query)
        chapter = result.scalar_one_or_none()
        
        if not chapter:
            raise NotFoundException("章节不存在")
        
        # 检查阅读权限
        has_permission = await self._check_reading_permission(chapter, user_id)
        if not has_permission:
            raise PermissionException("没有阅读权限，请先购买章节")
        
        # 更新阅读统计
        if user_id:
            await self._update_reading_stats(chapter, user_id)
        
        return {
            "id": str(chapter.id),
            "title": chapter.title,
            "content": chapter.content,
            "word_count": chapter.word_count,
            "chapter_number": chapter.chapter_number,
            "published_at": chapter.published_at,
            "is_vip": chapter.is_vip,
            "price": chapter.price
        }

    async def get_next_chapter(self, chapter_id: str) -> Optional[ChapterBasicResponse]:
        """获取下一章"""
        chapter_uuid = uuid.UUID(chapter_id)
        
        # 查询当前章节
        current_query = select(Chapter).where(Chapter.id == chapter_uuid)
        current_result = await self.db.execute(current_query)
        current_chapter = current_result.scalar_one_or_none()
        
        if not current_chapter:
            raise NotFoundException("章节不存在")
        
        # 查询下一章
        next_query = select(Chapter).where(
            and_(
                Chapter.novel_id == current_chapter.novel_id,
                Chapter.chapter_number > current_chapter.chapter_number
            )
        ).order_by(Chapter.chapter_number.asc()).limit(1)
        
        next_result = await self.db.execute(next_query)
        next_chapter = next_result.scalar_one_or_none()
        
        if not next_chapter:
            return None
        
        return ChapterBasicResponse(
            id=next_chapter.id,
            title=next_chapter.title,
            chapter_number=next_chapter.chapter_number,
            volume_number=next_chapter.volume_number,
            word_count=next_chapter.word_count,
            is_vip=next_chapter.is_vip,
            is_free=next_chapter.is_free,
            price=next_chapter.price,
            published_at=next_chapter.published_at,
            is_purchased=False,
            can_read=next_chapter.is_free or next_chapter.chapter_number <= 3
        )

    async def get_previous_chapter(self, chapter_id: str) -> Optional[ChapterBasicResponse]:
        """获取上一章"""
        chapter_uuid = uuid.UUID(chapter_id)
        
        # 查询当前章节
        current_query = select(Chapter).where(Chapter.id == chapter_uuid)
        current_result = await self.db.execute(current_query)
        current_chapter = current_result.scalar_one_or_none()
        
        if not current_chapter:
            raise NotFoundException("章节不存在")
        
        # 查询上一章
        previous_query = select(Chapter).where(
            and_(
                Chapter.novel_id == current_chapter.novel_id,
                Chapter.chapter_number < current_chapter.chapter_number
            )
        ).order_by(Chapter.chapter_number.desc()).limit(1)
        
        previous_result = await self.db.execute(previous_query)
        previous_chapter = previous_result.scalar_one_or_none()
        
        if not previous_chapter:
            return None
        
        return ChapterBasicResponse(
            id=previous_chapter.id,
            title=previous_chapter.title,
            chapter_number=previous_chapter.chapter_number,
            volume_number=previous_chapter.volume_number,
            word_count=previous_chapter.word_count,
            is_vip=previous_chapter.is_vip,
            is_free=previous_chapter.is_free,
            price=previous_chapter.price,
            published_at=previous_chapter.published_at,
            is_purchased=False,
            can_read=previous_chapter.is_free or previous_chapter.chapter_number <= 3
        )