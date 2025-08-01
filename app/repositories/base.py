
# app/repositories/base.py
# -*- coding: utf-8 -*-
"""
基础仓库类
定义所有仓库的基础CRUD操作
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Union, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, desc, asc, func
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.sql import Select
from loguru import logger

from app.models.base import BaseModel

T = TypeVar('T', bound=BaseModel)


class BaseRepository:
    """基础仓库类"""

    def __init__(self, db: AsyncSession, model: Type[T]):
        """
        初始化仓库

        Args:
            db: 数据库会话
            model: 模型类
        """
        self.db = db
        self.model = model

    async def get_by_id(
            self,
            id: Union[str, int],
            relationships: Optional[List[str]] = None
    ) -> Optional[T]:
        """
        根据ID获取记录

        Args:
            id: 记录ID
            relationships: 需要加载的关联关系

        Returns:
            Optional[T]: 模型实例
        """

        try:
            query = select(self.model).where(self.model.id == id)

            # 加载关联关系
            if relationships:
                for rel in relationships:
                    if hasattr(self.model, rel):
                        query = query.options(selectinload(getattr(self.model, rel)))

            result = await self.db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"根据ID获取记录失败: {e}")
            raise

    async def get_by_field(
            self,
            field: str,
            value: Any,
            relationships: Optional[List[str]] = None
    ) -> Optional[T]:
        """
        根据字段获取记录

        Args:
            field: 字段名
            value: 字段值
            relationships: 需要加载的关联关系

        Returns:
            Optional[T]: 模型实例
        """

        try:
            if not hasattr(self.model, field):
                raise ValueError(f"模型 {self.model.__name__} 没有字段 {field}")

            query = select(self.model).where(getattr(self.model, field) == value)

            # 加载关联关系
            if relationships:
                for rel in relationships:
                    if hasattr(self.model, rel):
                        query = query.options(selectinload(getattr(self.model, rel)))

            result = await self.db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"根据字段获取记录失败: {e}")
            raise

    async def get_multi(
            self,
            filters: Optional[Dict[str, Any]] = None,
            sort_by: Optional[str] = None,
            sort_order: str = "desc",
            offset: int = 0,
            limit: int = 100,
            relationships: Optional[List[str]] = None
    ) -> List[T]:
        """
        获取多条记录

        Args:
            filters: 过滤条件
            sort_by: 排序字段
            sort_order: 排序方向
            offset: 偏移量
            limit: 限制数量
            relationships: 需要加载的关联关系

        Returns:
            List[T]: 模型实例列表
        """

        try:
            query = select(self.model)

            # 添加过滤条件
            if filters:
                conditions = self._build_conditions(filters)
                if conditions:
                    query = query.where(and_(*conditions))

            # 添加排序
            if sort_by and hasattr(self.model, sort_by):
                sort_column = getattr(self.model, sort_by)
                if sort_order.lower() == "desc":
                    query = query.order_by(desc(sort_column))
                else:
                    query = query.order_by(asc(sort_column))

            # 添加分页
            query = query.offset(offset).limit(limit)

            # 加载关联关系
            if relationships:
                for rel in relationships:
                    if hasattr(self.model, rel):
                        query = query.options(selectinload(getattr(self.model, rel)))

            result = await self.db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"获取多条记录失败: {e}")
            raise

    async def count(
            self,
            filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        统计记录数量

        Args:
            filters: 过滤条件

        Returns:
            int: 记录数量
        """

        try:
            query = select(func.count(self.model.id))

            # 添加过滤条件
            if filters:
                conditions = self._build_conditions(filters)
                if conditions:
                    query = query.where(and_(*conditions))

            result = await self.db.execute(query)
            return result.scalar_one()

        except Exception as e:
            logger.error(f"统计记录数量失败: {e}")
            return 0

    async def create(
            self,
            obj_in: Dict[str, Any]
    ) -> T:
        """
        创建记录

        Args:
            obj_in: 创建数据

        Returns:
            T: 创建的模型实例
        """

        try:
            db_obj = self.model(**obj_in)
            self.db.add(db_obj)
            await self.db.commit()
            await self.db.refresh(db_obj)
            return db_obj

        except Exception as e:
            await self.db.rollback()
            logger.error(f"创建记录失败: {e}")
            raise

    async def update(
            self,
            db_obj: T,
            obj_in: Dict[str, Any]
    ) -> T:
        """
        更新记录

        Args:
            db_obj: 数据库对象
            obj_in: 更新数据

        Returns:
            T: 更新后的模型实例
        """

        try:
            for field, value in obj_in.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)

            await self.db.commit()
            await self.db.refresh(db_obj)
            return db_obj

        except Exception as e:
            await self.db.rollback()
            logger.error(f"更新记录失败: {e}")
            raise

    async def delete(self, id: Union[str, int]) -> bool:
        """
        删除记录

        Args:
            id: 记录ID

        Returns:
            bool: 删除成功
        """

        try:
            stmt = delete(self.model).where(self.model.id == id)
            result = await self.db.execute(stmt)
            await self.db.commit()

            return result.rowcount > 0

        except Exception as e:
            await self.db.rollback()
            logger.error(f"删除记录失败: {e}")
            raise

    async def bulk_create(self, objs_in: List[Dict[str, Any]]) -> List[T]:
        """
        批量创建记录

        Args:
            objs_in: 创建数据列表

        Returns:
            List[T]: 创建的模型实例列表
        """

        try:
            db_objs = [self.model(**obj_data) for obj_data in objs_in]
            self.db.add_all(db_objs)
            await self.db.commit()

            # 刷新所有对象
            for db_obj in db_objs:
                await self.db.refresh(db_obj)

            return db_objs

        except Exception as e:
            await self.db.rollback()
            logger.error(f"批量创建记录失败: {e}")
            raise

    async def bulk_update(
            self,
            filters: Dict[str, Any],
            obj_in: Dict[str, Any]
    ) -> int:
        """
        批量更新记录

        Args:
            filters: 过滤条件
            obj_in: 更新数据

        Returns:
            int: 更新的记录数
        """

        try:
            conditions = self._build_conditions(filters)

            stmt = update(self.model).values(**obj_in)

            if conditions:
                stmt = stmt.where(and_(*conditions))

            result = await self.db.execute(stmt)
            await self.db.commit()

            return result.rowcount

        except Exception as e:
            await self.db.rollback()
            logger.error(f"批量更新记录失败: {e}")
            raise

    async def exists(self, filters: Dict[str, Any]) -> bool:
        """
        检查记录是否存在

        Args:
            filters: 查询条件

        Returns:
            bool: 是否存在
        """

        try:
            conditions = self._build_conditions(filters)

            if not conditions:
                return False

            query = select(self.model.id).where(and_(*conditions)).limit(1)
            result = await self.db.execute(query)

            return result.scalar_one_or_none() is not None

        except Exception as e:
            logger.error(f"检查记录存在性失败: {e}")
            return False

    def _build_conditions(self, filters: Dict[str, Any]) -> List:
        """
        构建查询条件

        Args:
            filters: 过滤条件

        Returns:
            List: 条件列表
        """

        conditions = []

        for key, value in filters.items():
            if not hasattr(self.model, key) or value is None:
                continue

            column = getattr(self.model, key)

            # 处理不同类型的条件
            if isinstance(value, dict):
                # 处理复杂条件，如 {"gte": 10, "lte": 20}
                for op, val in value.items():
                    if op == "gte":
                        conditions.append(column >= val)
                    elif op == "gt":
                        conditions.append(column > val)
                    elif op == "lte":
                        conditions.append(column <= val)
                    elif op == "lt":
                        conditions.append(column < val)
                    elif op == "ne":
                        conditions.append(column != val)
                    elif op == "in":
                        conditions.append(column.in_(val))
                    elif op == "not_in":
                        conditions.append(~column.in_(val))
                    elif op == "like":
                        conditions.append(column.like(f"%{val}%"))
                    elif op == "ilike":
                        conditions.append(column.ilike(f"%{val}%"))
            elif isinstance(value, list):
                # 列表条件，使用 IN
                conditions.append(column.in_(value))
            else:
                # 等值条件
                conditions.append(column == value)

        return conditions