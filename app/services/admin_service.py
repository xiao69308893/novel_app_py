# app/services/admin_service.py
# -*- coding: utf-8 -*-
"""
管理员业务服务
处理管理员相关的业务逻辑，包括系统统计、用户管理、内容审核等
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func, desc, asc
from sqlalchemy.orm import selectinload, joinedload
from decimal import Decimal
import uuid

from ..models.user import User, UserProfile, UserStatistics
from ..models.novel import Novel
from ..models.chapter import Chapter, ChapterPurchase
from ..models.comment import Comment
from ..schemas.admin import (
    SystemStatsResponse, UserStatsResponse, NovelStatsResponse,
    RevenueStatsResponse, AdminLogResponse, AdminUserResponse,
    AdminUserCreate, AdminUserUpdate
)
from ..utils.cache import CacheManager
from ..utils.statistics import StatisticsManager
from .base import BaseService


class AdminService(BaseService):
    """管理员服务类"""

    def __init__(self, db: AsyncSession, cache: Optional[CacheManager] = None):
        super().__init__(db, cache)
        self.stats_manager = StatisticsManager()

    async def get_system_stats(self) -> SystemStatsResponse:
        """获取系统统计信息"""
        
        # 获取用户统计
        user_count_query = select(func.count()).select_from(User)
        user_count = await self.db.execute(user_count_query)
        total_users = user_count.scalar()

        # 获取今日新增用户
        today = datetime.now().date()
        today_users_query = select(func.count()).select_from(User).where(
            func.date(User.created_at) == today
        )
        today_users = await self.db.execute(today_users_query)
        new_users_today = today_users.scalar()

        # 获取小说统计
        novel_count_query = select(func.count()).select_from(Novel)
        novel_count = await self.db.execute(novel_count_query)
        total_novels = novel_count.scalar()

        # 获取章节统计
        chapter_count_query = select(func.count()).select_from(Chapter)
        chapter_count = await self.db.execute(chapter_count_query)
        total_chapters = chapter_count.scalar()

        # 获取评论统计
        comment_count_query = select(func.count()).select_from(Comment)
        comment_count = await self.db.execute(comment_count_query)
        total_comments = comment_count.scalar()

        # 获取收入统计
        revenue_query = select(func.sum(ChapterPurchase.amount)).select_from(ChapterPurchase)
        revenue_result = await self.db.execute(revenue_query)
        total_revenue = revenue_result.scalar() or Decimal('0')

        return SystemStatsResponse(
            total_users=total_users,
            new_users_today=new_users_today,
            total_novels=total_novels,
            total_chapters=total_chapters,
            total_comments=total_comments,
            total_revenue=float(total_revenue)
        )

    async def get_user_stats(self, period: str = "7d") -> UserStatsResponse:
        """获取用户统计信息"""
        
        # 解析时间周期
        if period == "7d":
            start_date = datetime.now() - timedelta(days=7)
        elif period == "30d":
            start_date = datetime.now() - timedelta(days=30)
        elif period == "90d":
            start_date = datetime.now() - timedelta(days=90)
        else:
            start_date = datetime.now() - timedelta(days=7)

        # 获取新增用户趋势
        new_users_query = select(
            func.date(User.created_at).label('date'),
            func.count().label('count')
        ).where(
            User.created_at >= start_date
        ).group_by(
            func.date(User.created_at)
        ).order_by(
            func.date(User.created_at)
        )
        
        new_users_result = await self.db.execute(new_users_query)
        new_users_trend = [
            {"date": str(row.date), "count": row.count}
            for row in new_users_result
        ]

        # 获取活跃用户数
        active_users_query = select(func.count(func.distinct(User.id))).select_from(User).where(
            User.last_login_at >= start_date
        )
        active_users_result = await self.db.execute(active_users_query)
        active_users = active_users_result.scalar()

        return UserStatsResponse(
            new_users_trend=new_users_trend,
            active_users=active_users,
            period=period
        )

    async def get_novel_stats(self, period: str = "7d") -> NovelStatsResponse:
        """获取小说统计信息"""
        
        # 解析时间周期
        if period == "7d":
            start_date = datetime.now() - timedelta(days=7)
        elif period == "30d":
            start_date = datetime.now() - timedelta(days=30)
        elif period == "90d":
            start_date = datetime.now() - timedelta(days=90)
        else:
            start_date = datetime.now() - timedelta(days=7)

        # 获取新增小说趋势
        new_novels_query = select(
            func.date(Novel.created_at).label('date'),
            func.count().label('count')
        ).where(
            Novel.created_at >= start_date
        ).group_by(
            func.date(Novel.created_at)
        ).order_by(
            func.date(Novel.created_at)
        )
        
        new_novels_result = await self.db.execute(new_novels_query)
        new_novels_trend = [
            {"date": str(row.date), "count": row.count}
            for row in new_novels_result
        ]

        # 获取分类统计
        category_query = select(
            Novel.category,
            func.count().label('count')
        ).group_by(
            Novel.category
        ).order_by(
            desc(func.count())
        )
        
        category_result = await self.db.execute(category_query)
        category_stats = [
            {"category": row.category, "count": row.count}
            for row in category_result
        ]

        return NovelStatsResponse(
            new_novels_trend=new_novels_trend,
            category_stats=category_stats,
            period=period
        )

    async def get_revenue_stats(self, period: str = "7d") -> RevenueStatsResponse:
        """获取收入统计信息"""
        
        # 解析时间周期
        if period == "7d":
            start_date = datetime.now() - timedelta(days=7)
        elif period == "30d":
            start_date = datetime.now() - timedelta(days=30)
        elif period == "90d":
            start_date = datetime.now() - timedelta(days=90)
        else:
            start_date = datetime.now() - timedelta(days=7)

        # 获取收入趋势
        revenue_query = select(
            func.date(ChapterPurchase.created_at).label('date'),
            func.sum(ChapterPurchase.amount).label('amount')
        ).where(
            ChapterPurchase.created_at >= start_date
        ).group_by(
            func.date(ChapterPurchase.created_at)
        ).order_by(
            func.date(ChapterPurchase.created_at)
        )
        
        revenue_result = await self.db.execute(revenue_query)
        revenue_trend = [
            {"date": str(row.date), "amount": float(row.amount or 0)}
            for row in revenue_result
        ]

        # 获取总收入
        total_revenue_query = select(func.sum(ChapterPurchase.amount)).where(
            ChapterPurchase.created_at >= start_date
        )
        total_revenue_result = await self.db.execute(total_revenue_query)
        total_revenue = float(total_revenue_result.scalar() or 0)

        return RevenueStatsResponse(
            revenue_trend=revenue_trend,
            total_revenue=total_revenue,
            period=period
        )

    async def update_user_status(
        self,
        user_id: str,
        status: str,
        reason: Optional[str] = None,
        admin_id: Optional[uuid.UUID] = None
    ) -> None:
        """更新用户状态"""
        
        # 更新用户状态
        update_query = update(User).where(
            User.id == uuid.UUID(user_id)
        ).values(
            status=status,
            updated_at=datetime.utcnow()
        )
        
        await self.db.execute(update_query)
        await self.db.commit()

        # 记录操作日志
        # TODO: 实现操作日志记录

    async def delete_user(self, user_id: str, admin_id: uuid.UUID) -> None:
        """删除用户"""
        
        # 软删除用户
        update_query = update(User).where(
            User.id == uuid.UUID(user_id)
        ).values(
            is_deleted=True,
            deleted_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        await self.db.execute(update_query)
        await self.db.commit()

        # 记录操作日志
        # TODO: 实现操作日志记录

    async def get_admin_users(
        self,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[AdminUserResponse], int]:
        """获取管理员用户列表"""
        
        offset = (page - 1) * page_size
        
        # 查询管理员用户
        query = select(User).where(
            User.role.in_(["admin", "super_admin"])
        ).order_by(desc(User.created_at))
        
        # 获取总数
        count_query = select(func.count()).select_from(User).where(
            User.role.in_(["admin", "super_admin"])
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # 分页查询
        query = query.offset(offset).limit(page_size)
        result = await self.db.execute(query)
        users = result.scalars().all()

        # 转换为响应模型
        admin_users = [
            AdminUserResponse(
                id=str(user.id),
                username=user.username,
                email=user.email,
                role=user.role,
                status=user.status,
                created_at=user.created_at,
                last_login_at=user.last_login_at
            )
            for user in users
        ]

        return admin_users, total

    async def create_admin_user(
        self,
        admin_data: AdminUserCreate,
        creator_id: uuid.UUID
    ) -> AdminUserResponse:
        """创建管理员用户"""
        
        # 检查用户名和邮箱是否已存在
        existing_user_query = select(User).where(
            or_(
                User.username == admin_data.username,
                User.email == admin_data.email
            )
        )
        existing_user = await self.db.execute(existing_user_query)
        if existing_user.scalar():
            raise ValueError("用户名或邮箱已存在")

        # 创建新管理员用户
        from ..utils.security import hash_password
        
        new_user = User(
            username=admin_data.username,
            email=admin_data.email,
            password_hash=hash_password(admin_data.password),
            role=admin_data.role,
            status="active",
            created_at=datetime.utcnow()
        )
        
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)

        return AdminUserResponse(
            id=str(new_user.id),
            username=new_user.username,
            email=new_user.email,
            role=new_user.role,
            status=new_user.status,
            created_at=new_user.created_at,
            last_login_at=new_user.last_login_at
        )

    async def update_admin_user(
        self,
        user_id: str,
        admin_data: AdminUserUpdate,
        updater_id: uuid.UUID
    ) -> AdminUserResponse:
        """更新管理员用户"""
        
        # 获取用户
        user_query = select(User).where(User.id == uuid.UUID(user_id))
        user_result = await self.db.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise ValueError("用户不存在")

        # 更新用户信息
        update_data = admin_data.dict(exclude_unset=True)
        if "password" in update_data:
            from ..utils.security import hash_password
            update_data["password_hash"] = hash_password(update_data.pop("password"))
        
        update_data["updated_at"] = datetime.utcnow()
        
        update_query = update(User).where(
            User.id == uuid.UUID(user_id)
        ).values(**update_data)
        
        await self.db.execute(update_query)
        await self.db.commit()

        # 重新获取更新后的用户
        updated_user_result = await self.db.execute(user_query)
        updated_user = updated_user_result.scalar_one()

        return AdminUserResponse(
            id=str(updated_user.id),
            username=updated_user.username,
            email=updated_user.email,
            role=updated_user.role,
            status=updated_user.status,
            created_at=updated_user.created_at,
            last_login_at=updated_user.last_login_at
        )

    async def delete_admin_user(self, user_id: str, deleter_id: uuid.UUID) -> None:
        """删除管理员用户"""
        
        # 软删除用户
        update_query = update(User).where(
            User.id == uuid.UUID(user_id)
        ).values(
            is_deleted=True,
            deleted_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        await self.db.execute(update_query)
        await self.db.commit()