
# app/schemas/base.py
# -*- coding: utf-8 -*-
"""
基础Pydantic模式
定义通用的响应格式和基础字段
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import uuid

# 类型变量
T = TypeVar('T')


class BaseSchema(BaseModel):
    """基础模式类"""

    model_config = ConfigDict(
        # 允许从ORM模型创建
        from_attributes=True,
        # 使用枚举值
        use_enum_values=True,
        # 验证赋值
        validate_assignment=True,
        # 时间序列化格式
        json_encoders={
            datetime: lambda v: v.isoformat(),
            uuid.UUID: lambda v: str(v)
        }
    )


class PaginationInfo(BaseSchema):
    """分页信息"""

    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")
    total: int = Field(description="总记录数")
    total_pages: int = Field(description="总页数")
    has_more: bool = Field(description="是否有更多数据")
    has_next_page: bool = Field(description="是否有下一页")
    has_previous_page: bool = Field(description="是否有上一页")


class BaseResponse(BaseSchema, Generic[T]):
    """基础响应格式"""

    success: bool = Field(default=True, description="操作是否成功")
    code: int = Field(default=200, description="状态码")
    message: str = Field(default="操作成功", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间")


class ListResponse(BaseSchema, Generic[T]):
    """列表响应格式"""

    success: bool = Field(default=True, description="操作是否成功")
    code: int = Field(default=200, description="状态码")
    message: str = Field(default="获取成功", description="响应消息")
    data: List[T] = Field(default=[], description="数据列表")
    pagination: Optional[PaginationInfo] = Field(default=None, description="分页信息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间")


class ErrorResponse(BaseSchema):
    """错误响应格式"""

    success: bool = Field(default=False, description="操作是否成功")
    code: int = Field(description="错误状态码")
    error_code: str = Field(description="错误代码")
    message: str = Field(description="错误消息")
    details: Optional[Dict[str, Any]] = Field(default=None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间")
    path: Optional[str] = Field(default=None, description="请求路径")


class SuccessResponse(BaseSchema):
    """成功响应格式"""

    success: bool = Field(default=True, description="操作是否成功")
    code: int = Field(default=200, description="状态码")
    message: str = Field(description="成功消息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间")


class IdResponse(BaseSchema):
    """ID响应格式"""

    success: bool = Field(default=True, description="操作是否成功")
    code: int = Field(default=201, description="状态码")
    message: str = Field(default="创建成功", description="响应消息")
    data: Dict[str, str] = Field(description="包含ID的数据")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间")


class BatchOperationRequest(BaseSchema):
    """批量操作请求"""

    ids: List[str] = Field(description="ID列表")
    action: str = Field(description="操作类型")
    data: Optional[Dict[str, Any]] = Field(default=None, description="额外数据")


class BatchOperationResponse(BaseSchema):
    """批量操作响应"""

    success: bool = Field(default=True, description="操作是否成功")
    code: int = Field(default=200, description="状态码")
    message: str = Field(description="响应消息")
    data: Dict[str, Any] = Field(description="操作结果")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间")


class SearchRequest(BaseSchema):
    """搜索请求基类"""

    keyword: str = Field(description="搜索关键词")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")
    sort_by: Optional[str] = Field(default=None, description="排序字段")
    sort_order: Optional[str] = Field(default="desc", regex="^(asc|desc)$", description="排序方向")


class FilterRequest(BaseSchema):
    """过滤请求基类"""

    filters: Dict[str, Any] = Field(default={}, description="过滤条件")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")


class UploadResponse(BaseSchema):
    """文件上传响应"""

    success: bool = Field(default=True, description="上传是否成功")
    code: int = Field(default=200, description="状态码")
    message: str = Field(default="上传成功", description="响应消息")
    data: Dict[str, str] = Field(description="文件信息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间")


class StatusRequest(BaseSchema):
    """状态更新请求基类"""

    status: str = Field(description="新状态")
    reason: Optional[str] = Field(default=None, description="状态变更原因")

