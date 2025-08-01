# app/services/base.py
# -*- coding: utf-8 -*-
"""
基础服务类
定义所有服务的基础功能和通用方法
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, asc
from sqlalchemy.orm import selectinload
from loguru import logger
import redis.asyncio as redis

from app.config import settings
from app.core.exceptions import NotFoundException, ValidationException
from app.models.base import BaseModel

T = TypeVar('T', bound=BaseModel)


class BaseService:
    """基础服务类"""

    def __init__(self, db: AsyncSession):
        """
        初始化服务

        Args:
            db: 数据库会话
        """
        self.db = db
        self._redis_client: Optional[redis.Redis] = None

    @property
    async def redis(self) -> redis.Redis:
        """获取Redis客户端"""
        if self._redis_client is None:
            self._redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )
        return self._redis_client

    async def get_by_id(
            self,
            model: Type[T],
            id: Union[str, int],
            relationships: Optional[List[str]] = None
    ) -> Optional[T]:
        """
        根据ID获取记录

        Args:
            model: 模型类
            id: 记录ID
            relationships: 需要加载的关联关系

        Returns:
            Optional[T]: 模型实例
        """

        try:
            query = select(model).where(model.id == id)

            # 加载关联关系
            if relationships:
                for rel in relationships:
                    query = query.options(selectinload(getattr(model, rel)))

            result = await self.db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"根据ID获取记录失败: {e}")
            raise

    async def get_by_id_or_404(
            self,
            model: Type[T],
            id: Union[str, int],
            relationships: Optional[List[str]] = None,
            error_message: str = "记录不存在"
    ) -> T:
        """
        根据ID获取记录，不存在则抛出404异常

        Args:
            model: 模型类
            id: 记录ID
            relationships: 需要加载的关联关系
            error_message: 错误消息

        Returns:
            T: 模型实例

        Raises:
            NotFoundException: 记录不存在
        """

        instance = await self.get_by_id(model, id, relationships)
        if not instance:
            raise NotFoundException(
                message=error_message,
                resource_type=model.__name__,
                resource_id=str(id)
            )
        return instance

    async def create(
            self,
            model: Type[T],
            data: Dict[str, Any],
            commit: bool = True
    ) -> T:
        """
        创建记录

        Args:
            model: 模型类
            data: 创建数据
            commit: 是否提交事务

        Returns:
            T: 创建的模型实例
        """

        try:
            instance = model(**data)
            self.db.add(instance)

            if commit:
                await self.db.commit()
                await self.db.refresh(instance)

            return instance

        except Exception as e:
            if commit:
                await self.db.rollback()
            logger.error(f"创建记录失败: {e}")
            raise

    async def update(
            self,
            instance: T,
            data: Dict[str, Any],
            commit: bool = True
    ) -> T:
        """
        更新记录

        Args:
            instance: 模型实例
            data: 更新数据
            commit: 是否提交事务

        Returns:
            T: 更新后的模型实例
        """

        try:
            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)

            if commit:
                await self.db.commit()
                await self.db.refresh(instance)

            return instance

        except Exception as e:
            if commit:
                await self.db.rollback()
            logger.error(f"更新记录失败: {e}")
            raise

    async def delete(
            self,
            instance: T,
            commit: bool = True
    ) -> bool:
        """
        删除记录

        Args:
            instance: 模型实例
            commit: 是否提交事务

        Returns:
            bool: 删除成功
        """

        try:
            await self.db.delete(instance)

            if commit:
                await self.db.commit()

            return True

        except Exception as e:
            if commit:
                await self.db.rollback()
            logger.error(f"删除记录失败: {e}")
            raise

    async def get_list(
            self,
            model: Type[T],
            filters: Optional[Dict[str, Any]] = None,
            sort_by: str = "created_at",
            sort_order: str = "desc",
            page: int = 1,
            page_size: int = 20,
            relationships: Optional[List[str]] = None
    ) -> tuple[List[T], int]:
        """
        获取记录列表

        Args:
            model: 模型类
            filters: 过滤条件
            sort_by: 排序字段
            sort_order: 排序方向
            page: 页码
            page_size: 每页数量
            relationships: 需要加载的关联关系

        Returns:
            tuple: (记录列表, 总数)
        """

        try:
            # 构建查询
            query = select(model)
            count_query = select(model.id)

            # 添加过滤条件
            if filters:
                conditions = []
                for key, value in filters.items():
                    if hasattr(model, key) and value is not None:
                        if isinstance(value, list):
                            conditions.append(getattr(model, key).in_(value))
                        else:
                            conditions.append(getattr(model, key) == value)

                if conditions:
                    query = query.where(and_(*conditions))
                    count_query = count_query.where(and_(*conditions))

            # 获取总数
            total_result = await self.db.execute(count_query)
            total = len(total_result.fetchall())

            # 添加排序
            if hasattr(model, sort_by):
                sort_column = getattr(model, sort_by)
                if sort_order.lower() == "desc":
                    query = query.order_by(desc(sort_column))
                else:
                    query = query.order_by(asc(sort_column))

            # 添加分页
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)

            # 加载关联关系
            if relationships:
                for rel in relationships:
                    query = query.options(selectinload(getattr(model, rel)))

            # 执行查询
            result = await self.db.execute(query)
            items = result.scalars().all()

            return list(items), total

        except Exception as e:
            logger.error(f"获取记录列表失败: {e}")
            raise

    async def exists(
            self,
            model: Type[T],
            filters: Dict[str, Any]
    ) -> bool:
        """
        检查记录是否存在

        Args:
            model: 模型类
            filters: 查询条件

        Returns:
            bool: 是否存在
        """

        try:
            conditions = []
            for key, value in filters.items():
                if hasattr(model, key):
                    conditions.append(getattr(model, key) == value)

            if not conditions:
                return False

            query = select(model.id).where(and_(*conditions)).limit(1)
            result = await self.db.execute(query)

            return result.scalar_one_or_none() is not None

        except Exception as e:
            logger.error(f"检查记录存在性失败: {e}")
            return False

    async def count(
            self,
            model: Type[T],
            filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        统计记录数量

        Args:
            model: 模型类
            filters: 过滤条件

        Returns:
            int: 记录数量
        """

        try:
            query = select(model.id)

            # 添加过滤条件
            if filters:
                conditions = []
                for key, value in filters.items():
                    if hasattr(model, key) and value is not None:
                        conditions.append(getattr(model, key) == value)

                if conditions:
                    query = query.where(and_(*conditions))

            result = await self.db.execute(query)
            return len(result.fetchall())

        except Exception as e:
            logger.error(f"统计记录数量失败: {e}")
            return 0

    async def cache_get(self, key: str) -> Optional[str]:
        """
        从缓存获取数据

        Args:
            key: 缓存键

        Returns:
            Optional[str]: 缓存值
        """

        try:
            redis_client = await self.redis
            cache_key = f"{settings.CACHE_KEY_PREFIX}{key}"
            return await redis_client.get(cache_key)

        except Exception as e:
            logger.warning(f"缓存获取失败: {e}")
            return None

    async def cache_set(
            self,
            key: str,
            value: str,
            ttl: Optional[int] = None
    ) -> bool:
        """
        设置缓存数据

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）

        Returns:
            bool: 设置成功
        """

        try:
            redis_client = await self.redis
            cache_key = f"{settings.CACHE_KEY_PREFIX}{key}"
            expire_time = ttl or settings.CACHE_TTL

            await redis_client.setex(cache_key, expire_time, value)
            return True

        except Exception as e:
            logger.warning(f"缓存设置失败: {e}")
            return False

    async def cache_delete(self, key: str) -> bool:
        """
        删除缓存数据

        Args:
            key: 缓存键

        Returns:
            bool: 删除成功
        """

        try:
            redis_client = await self.redis
            cache_key = f"{settings.CACHE_KEY_PREFIX}{key}"
            await redis_client.delete(cache_key)
            return True

        except Exception as e:
            logger.warning(f"缓存删除失败: {e}")
            return False




