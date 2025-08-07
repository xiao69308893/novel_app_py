# app/repositories/user_repository.py
# -*- coding: utf-8 -*-
"""
用户仓库
提供用户相关的数据访问方法
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta

from app.repositories.base import BaseRepository
from app.models.user import User, UserProfile, UserSettings, LoginLog


class UserRepository(BaseRepository):
    """用户仓库"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, User)

    async def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return await self.get_by_field("username", username)

    async def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return await self.get_by_field("email", email)

    async def get_by_phone(self, phone: str) -> Optional[User]:
        """根据手机号获取用户"""
        return await self.get_by_field("phone", phone)

    async def get_with_profile(self, user_id: int) -> Optional[User]:
        """获取用户及其资料"""
        try:
            query = select(User).where(User.id == user_id).options(
                selectinload(User.profile),
                selectinload(User.settings)
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取用户资料失败: {e}")
            return None

    async def check_username_exists(self, username: str, exclude_id: Optional[int] = None) -> bool:
        """检查用户名是否存在"""
        try:
            query = select(func.count(User.id)).where(User.username == username)
            if exclude_id:
                query = query.where(User.id != exclude_id)
            
            result = await self.db.execute(query)
            count = result.scalar() or 0
            return count > 0
        except Exception as e:
            logger.error(f"检查用户名存在性失败: {e}")
            return False

    async def check_email_exists(self, email: str, exclude_id: Optional[int] = None) -> bool:
        """检查邮箱是否存在"""
        try:
            query = select(func.count(User.id)).where(User.email == email)
            if exclude_id:
                query = query.where(User.id != exclude_id)
            
            result = await self.db.execute(query)
            count = result.scalar() or 0
            return count > 0
        except Exception as e:
            logger.error(f"检查邮箱存在性失败: {e}")
            return False

    async def check_phone_exists(self, phone: str, exclude_id: Optional[int] = None) -> bool:
        """检查手机号是否存在"""
        try:
            query = select(func.count(User.id)).where(User.phone == phone)
            if exclude_id:
                query = query.where(User.id != exclude_id)
            
            result = await self.db.execute(query)
            count = result.scalar() or 0
            return count > 0
        except Exception as e:
            logger.error(f"检查手机号存在性失败: {e}")
            return False

    async def get_active_users(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[User]:
        """获取活跃用户列表"""
        filters = {"is_active": True}
        return await self.get_multi(
            filters=filters,
            sort_by="last_login_at",
            sort_order="desc",
            offset=skip,
            limit=limit
        )

    async def search_users(
        self, 
        keyword: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """搜索用户"""
        try:
            query = select(User).where(
                or_(
                    User.username.ilike(f"%{keyword}%"),
                    User.nickname.ilike(f"%{keyword}%"),
                    User.email.ilike(f"%{keyword}%")
                )
            ).offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"搜索用户失败: {e}")
            return []

    async def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """获取用户统计信息"""
        try:
            # 这里需要根据实际的关联模型来实现
            # 暂时返回基础统计
            user = await self.get_by_id(user_id)
            if not user:
                return {}

            return {
                "user_id": user_id,
                "username": user.username,
                "register_date": user.created_at,
                "last_login": user.last_login_at,
                "is_active": user.is_active,
                "is_vip": user.is_vip
            }
        except Exception as e:
            logger.error(f"获取用户统计失败: {e}")
            return {}

    async def update_last_login(self, user_id: int, ip_address: str = None) -> bool:
        """更新最后登录时间"""
        try:
            user = await self.get_by_id(user_id)
            if not user:
                return False

            update_data = {
                "last_login_at": datetime.utcnow(),
                "login_count": user.login_count + 1
            }
            
            if ip_address:
                update_data["last_login_ip"] = ip_address

            await self.update(user, update_data)
            return True
        except Exception as e:
            logger.error(f"更新最后登录时间失败: {e}")
            return False

    async def ban_user(self, user_id: int, reason: str = None) -> bool:
        """封禁用户"""
        try:
            user = await self.get_by_id(user_id)
            if not user:
                return False

            update_data = {
                "is_active": False,
                "ban_reason": reason,
                "banned_at": datetime.utcnow()
            }

            await self.update(user, update_data)
            return True
        except Exception as e:
            logger.error(f"封禁用户失败: {e}")
            return False

    async def unban_user(self, user_id: int) -> bool:
        """解封用户"""
        try:
            user = await self.get_by_id(user_id)
            if not user:
                return False

            update_data = {
                "is_active": True,
                "ban_reason": None,
                "banned_at": None
            }

            await self.update(user, update_data)
            return True
        except Exception as e:
            logger.error(f"解封用户失败: {e}")
            return False


class UserProfileRepository(BaseRepository):
    """用户资料仓库"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, UserProfile)

    async def get_by_user_id(self, user_id: int) -> Optional[UserProfile]:
        """根据用户ID获取用户资料"""
        return await self.get_by_field("user_id", user_id)

    async def create_default_profile(self, user_id: int) -> Optional[UserProfile]:
        """创建默认用户资料"""
        try:
            profile_data = {
                "user_id": user_id,
                "avatar": "/static/images/default_avatar.png",
                "bio": "",
                "gender": 0,  # 未知
                "birthday": None,
                "location": "",
                "website": ""
            }
            return await self.create(profile_data)
        except Exception as e:
            logger.error(f"创建默认用户资料失败: {e}")
            return None


class UserSettingsRepository(BaseRepository):
    """用户设置仓库"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, UserSettings)

    async def get_by_user_id(self, user_id: int) -> Optional[UserSettings]:
        """根据用户ID获取用户设置"""
        return await self.get_by_field("user_id", user_id)

    async def create_default_settings(self, user_id: int) -> Optional[UserSettings]:
        """创建默认用户设置"""
        try:
            settings_data = {
                "user_id": user_id,
                "theme": "light",
                "language": "zh-CN",
                "timezone": "Asia/Shanghai",
                "email_notifications": True,
                "push_notifications": True,
                "privacy_level": 1,  # 公开
                "auto_subscribe": False
            }
            return await self.create(settings_data)
        except Exception as e:
            logger.error(f"创建默认用户设置失败: {e}")
            return None


class LoginLogRepository(BaseRepository):
    """登录日志仓库"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, LoginLog)

    async def create_login_log(
        self, 
        user_id: int,
        ip_address: str,
        user_agent: str,
        login_type: str = "password",
        success: bool = True
    ) -> Optional[LoginLog]:
        """创建登录日志"""
        try:
            log_data = {
                "user_id": user_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "login_type": login_type,
                "success": success,
                "login_time": datetime.utcnow()
            }
            return await self.create(log_data)
        except Exception as e:
            logger.error(f"创建登录日志失败: {e}")
            return None

    async def get_user_login_logs(
        self, 
        user_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[LoginLog]:
        """获取用户登录日志"""
        filters = {"user_id": user_id}
        return await self.get_multi(
            filters=filters,
            sort_by="login_time",
            sort_order="desc",
            offset=skip,
            limit=limit
        )

    async def get_recent_failed_logins(
        self, 
        ip_address: str,
        minutes: int = 30
    ) -> int:
        """获取最近失败登录次数"""
        try:
            since_time = datetime.utcnow() - timedelta(minutes=minutes)
            
            query = select(func.count(LoginLog.id)).where(
                and_(
                    LoginLog.ip_address == ip_address,
                    LoginLog.success == False,
                    LoginLog.login_time >= since_time
                )
            )
            
            result = await self.db.execute(query)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"获取失败登录次数失败: {e}")
            return 0

    async def cleanup_old_logs(self, days: int = 90) -> int:
        """清理旧日志"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            from sqlalchemy import delete
            stmt = delete(LoginLog).where(LoginLog.login_time < cutoff_date)
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            return result.rowcount
        except Exception as e:
            logger.error(f"清理旧日志失败: {e}")
            return 0