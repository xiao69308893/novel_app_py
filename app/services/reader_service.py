# app/services/reader_service.py
# -*- coding: utf-8 -*-
"""
阅读器业务服务
处理阅读器相关的业务逻辑，包括阅读设置、阅读历史、阅读统计等
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func, desc, asc
from sqlalchemy.orm import selectinload, joinedload
import uuid
import json

from ..models.user import User, UserSettings, ReadingHistory
from ..models.chapter import Chapter, ReadingProgress
from ..models.novel import Novel
from ..schemas.reader import (
    ReaderSettingsResponse, ReaderSettingsUpdate,
    ReadingHistoryResponse, ReadingStatsResponse
)
from ..core.exceptions import NotFoundException, BusinessException
from ..utils.cache import CacheManager
from .base import BaseService


class ReaderService(BaseService):
    """阅读器服务类"""

    def __init__(self, db: AsyncSession, cache: CacheManager):
        super().__init__(db, cache)

    async def get_reader_settings(self, user_id: uuid.UUID) -> ReaderSettingsResponse:
        """获取阅读器设置"""
        cache_key = f"reader_settings:{user_id}"
        cached_settings = await self.cache.get(cache_key)
        
        if cached_settings:
            return ReaderSettingsResponse(**cached_settings)

        # 查询用户设置
        query = select(UserSettings).where(UserSettings.user_id == user_id)
        result = await self.db.execute(query)
        settings = result.scalar_one_or_none()

        if not settings:
            # 创建默认设置
            settings = await self._create_default_settings(user_id)

        # 解析阅读器设置
        reader_settings = settings.reader_settings or {}
        
        response = ReaderSettingsResponse(
            font_family=reader_settings.get("font_family", "system"),
            font_size=reader_settings.get("font_size", 16),
            line_height=reader_settings.get("line_height", 1.6),
            background_color=reader_settings.get("background_color", "#ffffff"),
            text_color=reader_settings.get("text_color", "#333333"),
            theme=reader_settings.get("theme", "light"),
            page_width=reader_settings.get("page_width", 800),
            auto_scroll=reader_settings.get("auto_scroll", False),
            scroll_speed=reader_settings.get("scroll_speed", 50),
            night_mode=reader_settings.get("night_mode", False),
            eye_protection=reader_settings.get("eye_protection", False),
            full_screen=reader_settings.get("full_screen", False)
        )

        # 缓存设置
        await self.cache.set(cache_key, response.dict(), expire=3600)
        
        return response

    async def update_reader_settings(
            self,
            user_id: uuid.UUID,
            settings_data: ReaderSettingsUpdate
    ) -> ReaderSettingsResponse:
        """更新阅读器设置"""
        # 查询用户设置
        query = select(UserSettings).where(UserSettings.user_id == user_id)
        result = await self.db.execute(query)
        settings = result.scalar_one_or_none()

        if not settings:
            settings = await self._create_default_settings(user_id)

        # 更新阅读器设置
        current_reader_settings = settings.reader_settings or {}
        
        # 只更新提供的字段
        update_data = settings_data.dict(exclude_unset=True)
        current_reader_settings.update(update_data)
        
        settings.reader_settings = current_reader_settings
        settings.updated_at = datetime.utcnow()

        await self.db.commit()

        # 清除缓存
        cache_key = f"reader_settings:{user_id}"
        await self.cache.delete(cache_key)

        # 返回更新后的设置
        return await self.get_reader_settings(user_id)

    async def get_reading_history(
            self,
            user_id: uuid.UUID,
            page: int = 1,
            limit: int = 20
    ) -> Tuple[List[ReadingHistoryResponse], int]:
        """获取阅读历史"""
        offset = (page - 1) * limit

        # 查询阅读历史
        query = select(ReadingHistory).options(
            joinedload(ReadingHistory.novel),
            joinedload(ReadingHistory.chapter)
        ).where(
            ReadingHistory.user_id == user_id
        ).order_by(
            ReadingHistory.last_read_at.desc()
        ).offset(offset).limit(limit)

        result = await self.db.execute(query)
        histories = result.scalars().all()

        # 查询总数
        count_query = select(func.count()).select_from(ReadingHistory).where(
            ReadingHistory.user_id == user_id
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # 构建响应数据
        history_list = []
        for history in histories:
            history_data = ReadingHistoryResponse(
                id=history.id,
                novel_id=history.novel_id,
                novel_title=history.novel.title,
                novel_cover=history.novel.cover_image,
                chapter_id=history.chapter_id,
                chapter_title=history.chapter.title if history.chapter else None,
                chapter_number=history.chapter_number,
                progress=history.progress,
                last_read_at=history.last_read_at,
                reading_time=history.reading_time
            )
            history_list.append(history_data)

        return history_list, total

    async def add_reading_history(
            self,
            user_id: uuid.UUID,
            novel_id: uuid.UUID,
            chapter_id: uuid.UUID,
            chapter_number: int,
            progress: float = 0.0,
            reading_time: int = 0
    ) -> None:
        """添加阅读历史"""
        # 查询是否已存在该小说的阅读历史
        query = select(ReadingHistory).where(
            and_(
                ReadingHistory.user_id == user_id,
                ReadingHistory.novel_id == novel_id
            )
        )
        result = await self.db.execute(query)
        history = result.scalar_one_or_none()

        if history:
            # 更新现有记录
            history.chapter_id = chapter_id
            history.chapter_number = chapter_number
            history.progress = progress
            history.reading_time += reading_time
            history.last_read_at = datetime.utcnow()
        else:
            # 创建新记录
            history = ReadingHistory(
                user_id=user_id,
                novel_id=novel_id,
                chapter_id=chapter_id,
                chapter_number=chapter_number,
                progress=progress,
                reading_time=reading_time,
                last_read_at=datetime.utcnow()
            )
            self.db.add(history)

        await self.db.commit()

    async def clear_reading_history(
            self,
            user_id: uuid.UUID,
            novel_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """清除阅读历史"""
        conditions = [ReadingHistory.user_id == user_id]
        if novel_id:
            conditions.append(ReadingHistory.novel_id == novel_id)

        # 删除阅读历史
        delete_query = delete(ReadingHistory).where(and_(*conditions))
        result = await self.db.execute(delete_query)
        deleted_count = result.rowcount

        await self.db.commit()

        return {
            "deleted_count": deleted_count,
            "message": f"已清除 {deleted_count} 条阅读历史"
        }

    async def get_reading_stats(self, user_id: uuid.UUID) -> ReadingStatsResponse:
        """获取阅读统计"""
        cache_key = f"reading_stats:{user_id}"
        cached_stats = await self.cache.get(cache_key)
        
        if cached_stats:
            return ReadingStatsResponse(**cached_stats)

        # 查询阅读统计数据
        now = datetime.utcnow()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        # 总阅读时间
        total_time_query = select(func.sum(ReadingHistory.reading_time)).where(
            ReadingHistory.user_id == user_id
        )
        total_time_result = await self.db.execute(total_time_query)
        total_reading_time = total_time_result.scalar() or 0

        # 今日阅读时间
        today_time_query = select(func.sum(ReadingHistory.reading_time)).where(
            and_(
                ReadingHistory.user_id == user_id,
                ReadingHistory.last_read_at >= today
            )
        )
        today_time_result = await self.db.execute(today_time_query)
        today_reading_time = today_time_result.scalar() or 0

        # 本周阅读时间
        week_time_query = select(func.sum(ReadingHistory.reading_time)).where(
            and_(
                ReadingHistory.user_id == user_id,
                ReadingHistory.last_read_at >= week_ago
            )
        )
        week_time_result = await self.db.execute(week_time_query)
        week_reading_time = week_time_result.scalar() or 0

        # 本月阅读时间
        month_time_query = select(func.sum(ReadingHistory.reading_time)).where(
            and_(
                ReadingHistory.user_id == user_id,
                ReadingHistory.last_read_at >= month_ago
            )
        )
        month_time_result = await self.db.execute(month_time_query)
        month_reading_time = month_time_result.scalar() or 0

        # 阅读小说数量
        novels_count_query = select(func.count(func.distinct(ReadingHistory.novel_id))).where(
            ReadingHistory.user_id == user_id
        )
        novels_count_result = await self.db.execute(novels_count_query)
        novels_count = novels_count_result.scalar() or 0

        # 阅读章节数量
        chapters_count_query = select(func.count(func.distinct(ReadingHistory.chapter_id))).where(
            ReadingHistory.user_id == user_id
        )
        chapters_count_result = await self.db.execute(chapters_count_query)
        chapters_count = chapters_count_result.scalar() or 0

        # 连续阅读天数
        consecutive_days = await self._calculate_consecutive_reading_days(user_id)

        # 平均每日阅读时间（基于有阅读记录的天数）
        reading_days_query = select(
            func.count(func.distinct(func.date(ReadingHistory.last_read_at)))
        ).where(ReadingHistory.user_id == user_id)
        reading_days_result = await self.db.execute(reading_days_query)
        reading_days = reading_days_result.scalar() or 1

        avg_daily_time = total_reading_time // reading_days if reading_days > 0 else 0

        response = ReadingStatsResponse(
            total_reading_time=total_reading_time,
            today_reading_time=today_reading_time,
            week_reading_time=week_reading_time,
            month_reading_time=month_reading_time,
            novels_count=novels_count,
            chapters_count=chapters_count,
            consecutive_days=consecutive_days,
            avg_daily_time=avg_daily_time,
            reading_days=reading_days
        )

        # 缓存统计数据（缓存时间较短，因为数据变化频繁）
        await self.cache.set(cache_key, response.dict(), expire=300)
        
        return response

    async def _create_default_settings(self, user_id: uuid.UUID) -> UserSettings:
        """创建默认用户设置"""
        default_reader_settings = {
            "font_family": "system",
            "font_size": 16,
            "line_height": 1.6,
            "background_color": "#ffffff",
            "text_color": "#333333",
            "theme": "light",
            "page_width": 800,
            "auto_scroll": False,
            "scroll_speed": 50,
            "night_mode": False,
            "eye_protection": False,
            "full_screen": False
        }

        settings = UserSettings(
            user_id=user_id,
            reader_settings=default_reader_settings,
            notification_settings={},
            privacy_settings={}
        )
        self.db.add(settings)
        await self.db.commit()
        
        return settings

    async def _calculate_consecutive_reading_days(self, user_id: uuid.UUID) -> int:
        """计算连续阅读天数"""
        # 获取最近的阅读记录，按日期分组
        query = select(
            func.date(ReadingHistory.last_read_at).label('reading_date')
        ).where(
            ReadingHistory.user_id == user_id
        ).group_by(
            func.date(ReadingHistory.last_read_at)
        ).order_by(
            func.date(ReadingHistory.last_read_at).desc()
        ).limit(365)  # 最多查询一年的数据

        result = await self.db.execute(query)
        reading_dates = [row.reading_date for row in result.fetchall()]

        if not reading_dates:
            return 0

        # 计算连续天数
        consecutive_days = 0
        today = datetime.utcnow().date()
        
        for i, reading_date in enumerate(reading_dates):
            expected_date = today - timedelta(days=i)
            if reading_date == expected_date:
                consecutive_days += 1
            else:
                break

        return consecutive_days