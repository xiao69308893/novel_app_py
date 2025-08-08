"""
用户业务服务
处理用户相关的业务逻辑，包括用户信息管理、设置、统计等
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from decimal import Decimal
import uuid

from ..models.user import User, UserProfile, UserSettings, UserStatistics
from ..models.chapter import ReadingProgress, Bookmark
from ..models.user import UserFavorite
from ..schemas.user import (
    UserProfileUpdate, UserProfileResponse, UserSettingsUpdate,
    UserSettingsResponse, UserStatisticsResponse, CheckinResponse,
    CheckinStatusResponse, ReadingHistoryItem, AddReadingHistoryRequest
)
from ..core.exceptions import NotFoundException, BusinessException
from ..utils.cache import CacheManager
from .base import BaseService


class UserService(BaseService):
    """用户服务类"""

    def __init__(self, db: AsyncSession, cache: CacheManager):
        super().__init__(db, cache)

    async def get_user_profile(self, user_id: uuid.UUID) -> UserProfileResponse:
        """获取用户资料"""
        cache_key = f"user_profile:{user_id}"
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return UserProfileResponse.parse_obj(cached_data)

        # 查询用户及其关联资料
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException("用户不存在")

        # 查询用户详细资料
        profile_query = select(UserProfile).where(UserProfile.user_id == user_id)
        profile_result = await self.db.execute(profile_query)
        profile = profile_result.scalar_one_or_none()

        # 构建响应数据
        profile_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "nickname": user.nickname,
            "avatar_url": user.avatar_url,
            "gender": user.gender,
            "birthday": user.birthday,
            "bio": user.bio,
            "level": user.level,
            "vip_level": user.vip_level,
            "points": user.points,
            "coins": user.coins,
            "experience": user.experience,
            "is_verified": user.is_verified,
            "email_verified": user.email_verified,
            "phone_verified": user.phone_verified,
            "created_at": user.created_at,
        }

        if profile:
            profile_data.update({
                "real_name": profile.real_name,
                "city": profile.city,
                "country": profile.country,
                "timezone": profile.timezone,
                "language": profile.language,
                "website": profile.website,
            })

        response = UserProfileResponse(**profile_data)

        # 缓存结果
        await self.cache.set(cache_key, response.dict(), expire=300)

        return response

    async def update_user_profile(
            self,
            user_id: uuid.UUID,
            profile_data: UserProfileUpdate
    ) -> UserProfileResponse:
        """更新用户资料"""
        # 更新用户基础信息
        user_updates = {}
        if profile_data.nickname is not None:
            user_updates['nickname'] = profile_data.nickname
        if profile_data.avatar_url is not None:
            user_updates['avatar_url'] = profile_data.avatar_url
        if profile_data.gender is not None:
            user_updates['gender'] = profile_data.gender
        if profile_data.birthday is not None:
            user_updates['birthday'] = profile_data.birthday
        if profile_data.bio is not None:
            user_updates['bio'] = profile_data.bio

        if user_updates:
            user_updates['updated_at'] = datetime.utcnow()
            user_query = update(User).where(User.id == user_id).values(**user_updates)
            await self.db.execute(user_query)

        # 更新用户详细资料
        profile_updates = {}
        if profile_data.real_name is not None:
            profile_updates['real_name'] = profile_data.real_name
        if profile_data.city is not None:
            profile_updates['city'] = profile_data.city
        if profile_data.country is not None:
            profile_updates['country'] = profile_data.country
        if profile_data.website is not None:
            profile_updates['website'] = profile_data.website

        if profile_updates:
            profile_updates['updated_at'] = datetime.utcnow()

            # 检查是否存在用户资料记录
            profile_query = select(UserProfile).where(UserProfile.user_id == user_id)
            result = await self.db.execute(profile_query)
            existing_profile = result.scalar_one_or_none()

            if existing_profile:
                # 更新现有记录
                update_query = update(UserProfile).where(
                    UserProfile.user_id == user_id
                ).values(**profile_updates)
                await self.db.execute(update_query)
            else:
                # 创建新记录
                new_profile = UserProfile(
                    user_id=user_id,
                    **profile_updates
                )
                self.db.add(new_profile)

        await self.db.commit()

        # 清除缓存
        cache_key = f"user_profile:{user_id}"
        await self.cache.delete(cache_key)

        return await self.get_user_profile(user_id)

    async def get_user_settings(self, user_id: uuid.UUID) -> UserSettingsResponse:
        """获取用户设置"""
        cache_key = f"user_settings:{user_id}"
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return UserSettingsResponse.parse_obj(cached_data)

        query = select(UserSettings).where(UserSettings.user_id == user_id)
        result = await self.db.execute(query)
        settings = result.scalar_one_or_none()

        if not settings:
            # 创建默认设置
            settings = UserSettings(user_id=user_id)
            self.db.add(settings)
            await self.db.commit()

        response = UserSettingsResponse.from_orm(settings)

        # 缓存结果
        await self.cache.set(cache_key, response.dict(), expire=300)

        return response

    async def update_user_settings(
            self,
            user_id: uuid.UUID,
            settings_data: UserSettingsUpdate
    ) -> UserSettingsResponse:
        """更新用户设置"""
        # 准备更新数据
        updates = {}
        for field, value in settings_data.dict(exclude_unset=True).items():
            if value is not None:
                updates[field] = value

        if updates:
            updates['updated_at'] = datetime.utcnow()

            # 检查是否存在设置记录
            query = select(UserSettings).where(UserSettings.user_id == user_id)
            result = await self.db.execute(query)
            existing_settings = result.scalar_one_or_none()

            if existing_settings:
                # 更新现有记录
                update_query = update(UserSettings).where(
                    UserSettings.user_id == user_id
                ).values(**updates)
                await self.db.execute(update_query)
            else:
                # 创建新记录
                new_settings = UserSettings(
                    user_id=user_id,
                    **updates
                )
                self.db.add(new_settings)

            await self.db.commit()

            # 清除缓存
            cache_key = f"user_settings:{user_id}"
            await self.cache.delete(cache_key)

        return await self.get_user_settings(user_id)

    async def get_user_statistics(self, user_id: uuid.UUID) -> UserStatisticsResponse:
        """获取用户统计信息"""
        cache_key = f"user_stats:{user_id}"
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return UserStatisticsResponse.parse_obj(cached_data)

        query = select(UserStatistics).where(UserStatistics.user_id == user_id)
        result = await self.db.execute(query)
        stats = result.scalar_one_or_none()

        if not stats:
            # 创建默认统计记录
            stats = UserStatistics(user_id=user_id)
            self.db.add(stats)
            await self.db.commit()

        response = UserStatisticsResponse.from_orm(stats)

        # 缓存结果
        await self.cache.set(cache_key, response.dict(), expire=60)

        return response

    async def user_checkin(self, user_id: uuid.UUID) -> CheckinResponse:
        """用户签到"""
        today = date.today()
        cache_key = f"user_checkin:{user_id}:{today}"

        # 检查今日是否已签到
        if await self.cache.exists(cache_key):
            raise BusinessException("今日已签到")

        # 获取用户统计信息
        stats_query = select(UserStatistics).where(UserStatistics.user_id == user_id)
        result = await self.db.execute(stats_query)
        stats = result.scalar_one_or_none()

        if not stats:
            stats = UserStatistics(user_id=user_id)
            self.db.add(stats)

        # 计算连续签到天数
        yesterday = today - timedelta(days=1)
        if stats.last_checkin_date == yesterday:
            # 连续签到
            streak_days = stats.streak_days + 1
        elif stats.last_checkin_date == today:
            # 今日已签到
            raise BusinessException("今日已签到")
        else:
            # 签到中断，重新开始
            streak_days = 1

        # 计算签到奖励
        base_points = 5
        bonus_points = min(streak_days // 7, 5) * 2  # 每连续7天额外奖励2积分，最多10积分
        points_earned = base_points + bonus_points

        # 更新统计信息
        stats.last_checkin_date = today
        stats.streak_days = streak_days

        # 更新用户积分
        user_query = update(User).where(User.id == user_id).values(
            points=User.points + points_earned,
            updated_at=datetime.utcnow()
        )
        await self.db.execute(user_query)

        await self.db.commit()

        # 设置签到缓存（24小时）
        await self.cache.set(cache_key, True, expire=86400)

        # 清除相关缓存
        await self.cache.delete(f"user_stats:{user_id}")
        await self.cache.delete(f"user_profile:{user_id}")

        # 计算下次签到时间
        next_checkin_time = datetime.combine(today + timedelta(days=1), datetime.min.time())

        return CheckinResponse(
            success=True,
            message=f"签到成功！连续签到{streak_days}天",
            points_earned=points_earned,
            streak_days=streak_days,
            next_checkin_time=next_checkin_time
        )

    async def get_checkin_status(self, user_id: uuid.UUID) -> CheckinStatusResponse:
        """获取签到状态"""
        today = date.today()
        cache_key = f"user_checkin:{user_id}:{today}"
        can_checkin = not await self.cache.exists(cache_key)

        # 获取用户统计信息
        stats_query = select(UserStatistics).where(UserStatistics.user_id == user_id)
        result = await self.db.execute(stats_query)
        stats = result.scalar_one_or_none()

        streak_days = stats.streak_days if stats else 0
        last_checkin_date = stats.last_checkin_date if stats else None

        # 计算下次签到时间
        next_checkin_time = None
        if not can_checkin:
            next_checkin_time = datetime.combine(today + timedelta(days=1), datetime.min.time())

        # 签到奖励配置
        checkin_rewards = [
            {"day": 1, "points": 5, "coins": 0},
            {"day": 2, "points": 5, "coins": 0},
            {"day": 3, "points": 5, "coins": 0},
            {"day": 4, "points": 5, "coins": 0},
            {"day": 5, "points": 5, "coins": 0},
            {"day": 6, "points": 5, "coins": 0},
            {"day": 7, "points": 7, "coins": 2},  # 第7天额外奖励
            {"day": 14, "points": 9, "coins": 3},  # 第14天额外奖励
            {"day": 21, "points": 11, "coins": 4},  # 第21天额外奖励
            {"day": 30, "points": 15, "coins": 5},  # 第30天额外奖励
        ]

        return CheckinStatusResponse(
            can_checkin=can_checkin,
            streak_days=streak_days,
            last_checkin_date=last_checkin_date,
            next_checkin_time=next_checkin_time,
            checkin_rewards=checkin_rewards
        )

    async def add_reading_history(
            self,
            user_id: uuid.UUID,
            history_data: AddReadingHistoryRequest
    ):
        """添加阅读历史"""
        # 这里简化实现，实际应该插入到reading_history表
        # 同时更新用户统计信息

        # 更新阅读进度
        progress_query = select(ReadingProgress).where(
            and_(
                ReadingProgress.user_id == user_id,
                ReadingProgress.novel_id == history_data.novel_id
            )
        )
        result = await self.db.execute(progress_query)
        progress = result.scalar_one_or_none()

        if progress:
            # 更新现有进度
            progress.reading_time += history_data.reading_time // 60  # 转换为分钟
            progress.last_read_duration = history_data.reading_time
            progress.updated_at = datetime.utcnow()

            if history_data.chapter_id:
                progress.chapter_id = history_data.chapter_id
        else:
            # 创建新的阅读进度
            progress = ReadingProgress(
                user_id=user_id,
                novel_id=history_data.novel_id,
                chapter_id=history_data.chapter_id,
                reading_time=history_data.reading_time // 60,
                last_read_duration=history_data.reading_time
            )
            self.db.add(progress)

        # 更新用户统计
        stats_query = select(UserStatistics).where(UserStatistics.user_id == user_id)
        result = await self.db.execute(stats_query)
        stats = result.scalar_one_or_none()

        if stats:
            stats.total_reading_time += history_data.reading_time // 60
            stats.last_read_date = date.today()
            stats.updated_at = datetime.utcnow()

        await self.db.commit()

        # 清除相关缓存
        await self.cache.delete(f"user_stats:{user_id}")

    async def get_reading_history(
            self,
            user_id: uuid.UUID,
            page: int = 1,
            limit: int = 20
    ) -> Dict[str, Any]:
        """获取阅读历史"""
        offset = (page - 1) * limit

        # 这里简化实现，从reading_progress表获取数据
        # 实际应该从reading_history表获取更详细的历史记录
        query = select(ReadingProgress).where(
            ReadingProgress.user_id == user_id
        ).order_by(ReadingProgress.updated_at.desc()).offset(offset).limit(limit)

        result = await self.db.execute(query)
        progress_list = result.scalars().all()

        # 获取总数
        count_query = select(func.count(ReadingProgress.id)).where(
            ReadingProgress.user_id == user_id
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # 构建响应数据（这里需要关联小说和章节信息）
        items = []
        for progress in progress_list:
            # 实际实现中需要关联查询小说和章节信息
            item = ReadingHistoryItem(
                novel_id=progress.novel_id,
                novel_title="",  # 需要关联查询
                novel_cover=None,
                chapter_id=progress.chapter_id,
                chapter_title="",  # 需要关联查询
                chapter_number=progress.chapter_number,
                reading_time=progress.reading_time,
                last_read_at=progress.updated_at
            )
            items.append(item)

        return {
            "items": items,
            "total": total,
            "has_more": total > page * limit
        }

    async def clear_reading_history(
            self,
            user_id: uuid.UUID,
            novel_ids: Optional[List[uuid.UUID]] = None
    ):
        """清理阅读历史"""
        if novel_ids:
            # 清理指定小说的历史
            query = delete(ReadingProgress).where(
                and_(
                    ReadingProgress.user_id == user_id,
                    ReadingProgress.novel_id.in_(novel_ids)
                )
            )
        else:
            # 清理所有历史
            query = delete(ReadingProgress).where(ReadingProgress.user_id == user_id)

        await self.db.execute(query)
        await self.db.commit()

    async def update_user_coins(
            self,
            user_id: uuid.UUID,
            amount: int,
            operation: str = "add"
    ):
        """更新用户金币"""
        if operation == "add":
            query = update(User).where(User.id == user_id).values(
                coins=User.coins + amount,
                updated_at=datetime.utcnow()
            )
        elif operation == "subtract":
            query = update(User).where(User.id == user_id).values(
                coins=User.coins - amount,
                updated_at=datetime.utcnow()
            )
        else:
            raise ValueError("无效的操作类型")

        await self.db.execute(query)
        await self.db.commit()

        # 清除缓存
        await self.cache.delete(f"user_profile:{user_id}")

    async def update_user_points(
            self,
            user_id: uuid.UUID,
            amount: int,
            operation: str = "add"
    ):
        """更新用户积分"""
        if operation == "add":
            query = update(User).where(User.id == user_id).values(
                points=User.points + amount,
                updated_at=datetime.utcnow()
            )
        elif operation == "subtract":
            query = update(User).where(User.id == user_id).values(
                points=User.points - amount,
                updated_at=datetime.utcnow()
            )
        else:
            raise ValueError("无效的操作类型")

        await self.db.execute(query)
        await self.db.commit()

        # 清除缓存
        await self.cache.delete(f"user_profile:{user_id}")