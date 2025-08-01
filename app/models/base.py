
# app/models/base.py
# -*- coding: utf-8 -*-
"""
基础模型类
定义所有模型的基础字段和方法
"""

from typing import Any, Dict, Optional, Type
from sqlalchemy import Column, String, DateTime, text
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid


class Base(DeclarativeBase):
    """SQLAlchemy基类"""
    pass


class UUIDMixin:
    """UUID主键混入类"""

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        comment="主键ID"
    )


class TimestampMixin:
    """时间戳混入类"""

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default=text("NOW()"),
        comment="创建时间"
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=text("NOW()"),
        comment="更新时间"
    )


class BaseModel(Base, UUIDMixin, TimestampMixin):
    """基础模型类"""

    __abstract__ = True

    @declared_attr
    def __tablename__(cls) -> str:
        """自动生成表名"""
        return cls.__name__.lower()

    def to_dict(self, exclude: Optional[list] = None) -> Dict[str, Any]:
        """
        转换为字典

        Args:
            exclude: 排除的字段列表

        Returns:
            Dict[str, Any]: 字典表示
        """

        exclude = exclude or []
        result = {}

        for column in self.__table__.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)

                # 处理特殊类型
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif isinstance(value, uuid.UUID):
                    value = str(value)

                result[column.name] = value

        return result

    @classmethod
    def from_dict(cls: Type["BaseModel"], data: Dict[str, Any]) -> "BaseModel":
        """
        从字典创建实例

        Args:
            data: 数据字典

        Returns:
            BaseModel: 模型实例
        """

        # 过滤不存在的字段
        valid_fields = {c.name for c in cls.__table__.columns}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}

        return cls(**filtered_data)

    def update_from_dict(self, data: Dict[str, Any], exclude: Optional[list] = None) -> None:
        """
        从字典更新实例

        Args:
            data: 数据字典
            exclude: 排除的字段列表
        """

        exclude = exclude or ['id', 'created_at']
        valid_fields = {c.name for c in self.__table__.columns}

        for key, value in data.items():
            if key in valid_fields and key not in exclude:
                setattr(self, key, value)

    def __repr__(self) -> str:
        """字符串表示"""
        return f"<{self.__class__.__name__}(id='{self.id}')>"




