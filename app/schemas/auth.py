"""
认证相关数据模式
定义登录、注册、token等请求和响应的数据结构
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import uuid


# 登录相关
class LoginRequest(BaseModel):
    """密码登录请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码")

    class Config:
        schema_extra = {
            "example": {
                "username": "testuser",
                "password": "password123"
            }
        }


class PhoneLoginRequest(BaseModel):
    """手机验证码登录请求"""
    phone: str = Field(..., pattern=r'^1[3-9]\d{9}$', description="手机号")
    verification_code: str = Field(..., min_length=4, max_length=6, description="验证码")

    class Config:
        schema_extra = {
            "example": {
                "phone": "13812345678",
                "verification_code": "1234"
            }
        }


class RegisterRequest(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, pattern=r'^1[3-9]\d{9}$', description="手机号")
    invite_code: Optional[str] = Field(None, max_length=20, description="邀请码")

    @validator('username')
    def validate_username(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('用户名只能包含字母、数字、下划线和短横线')
        return v

    class Config:
        schema_extra = {
            "example": {
                "username": "newuser",
                "password": "password123",
                "email": "user@example.com",
                "phone": "13812345678"
            }
        }


# Token相关
class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str = Field(..., description="访问token")
    refresh_token: str = Field(..., description="刷新token")
    token_type: str = Field(default="Bearer", description="token类型")
    expires_in: int = Field(..., description="过期时间(秒)")
    user: 'UserInfo' = Field(..., description="用户信息")

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "Bearer",
                "expires_in": 3600,
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "username": "testuser",
                    "email": "user@example.com",
                    "avatar": "https://example.com/avatar.jpg"
                }
            }
        }


class RefreshTokenRequest(BaseModel):
    """刷新token请求"""
    refresh_token: str = Field(..., description="刷新token")

    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
            }
        }


# 密码相关
class PasswordChangeRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., min_length=6, max_length=128, description="原密码")
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")

    @validator('new_password')
    def validate_new_password(cls, v, values):
        if 'old_password' in values and v == values['old_password']:
            raise ValueError('新密码不能与原密码相同')
        return v

    class Config:
        schema_extra = {
            "example": {
                "old_password": "oldpassword123",
                "new_password": "newpassword123"
            }
        }


class ForgotPasswordRequest(BaseModel):
    """忘记密码请求"""
    account: str = Field(..., description="账号(手机号或邮箱)")
    verification_code: str = Field(..., min_length=4, max_length=6, description="验证码")
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")

    class Config:
        schema_extra = {
            "example": {
                "account": "user@example.com",
                "verification_code": "1234",
                "new_password": "newpassword123"
            }
        }


# 验证码相关
class SMSCodeRequest(BaseModel):
    """发送短信验证码请求"""
    phone: str = Field(..., pattern=r'^1[3-9]\d{9}$', description="手机号")
    type: str = Field(..., description="验证码类型")

    @validator('type')
    def validate_type(cls, v):
        if v not in ['login', 'register', 'forgot_password', 'bind_phone']:
            raise ValueError('无效的验证码类型')
        return v

    class Config:
        schema_extra = {
            "example": {
                "phone": "13812345678",
                "type": "login"
            }
        }


class EmailCodeRequest(BaseModel):
    """发送邮箱验证码请求"""
    email: EmailStr = Field(..., description="邮箱")
    type: str = Field(..., description="验证码类型")

    @validator('type')
    def validate_type(cls, v):
        if v not in ['login', 'register', 'forgot_password', 'bind_email']:
            raise ValueError('无效的验证码类型')
        return v

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "type": "register"
            }
        }


class VerificationCodeResponse(BaseModel):
    """验证码发送响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    expires_in: int = Field(..., description="过期时间(秒)")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "验证码已发送",
                "expires_in": 300
            }
        }


# 绑定相关
class BindPhoneRequest(BaseModel):
    """绑定手机号请求"""
    phone: str = Field(..., pattern=r'^1[3-9]\d{9}$', description="手机号")
    verification_code: str = Field(..., min_length=4, max_length=6, description="验证码")

    class Config:
        schema_extra = {
            "example": {
                "phone": "13812345678",
                "verification_code": "1234"
            }
        }


class BindEmailRequest(BaseModel):
    """绑定邮箱请求"""
    email: EmailStr = Field(..., description="邮箱")
    verification_code: str = Field(..., min_length=4, max_length=6, description="验证码")

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "verification_code": "1234"
            }
        }


# 用户信息
class UserInfo(BaseModel):
    """用户基础信息"""
    id: uuid.UUID = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: Optional[str] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, description="手机号")
    avatar: Optional[str] = Field(None, description="头像URL")
    nickname: Optional[str] = Field(None, description="昵称")
    level: int = Field(..., description="用户等级")
    vip_level: int = Field(..., description="VIP等级")
    is_verified: bool = Field(..., description="是否已验证")
    email_verified: bool = Field(..., description="邮箱是否已验证")
    phone_verified: bool = Field(..., description="手机号是否已验证")
    created_at: datetime = Field(..., description="注册时间")

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "testuser",
                "email": "user@example.com",
                "phone": "13812345678",
                "avatar": "https://example.com/avatar.jpg",
                "nickname": "测试用户",
                "level": 1,
                "vip_level": 0,
                "is_verified": True,
                "email_verified": True,
                "phone_verified": True,
                "created_at": "2023-01-01T00:00:00Z"
            }
        }


# 登录日志
class LoginLogInfo(BaseModel):
    """登录日志信息"""
    id: uuid.UUID = Field(..., description="日志ID")
    login_type: str = Field(..., description="登录类型")
    ip_address: str = Field(..., description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    status: str = Field(..., description="登录状态")
    created_at: datetime = Field(..., description="登录时间")
    country: Optional[str] = Field(None, description="国家")
    city: Optional[str] = Field(None, description="城市")

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "login_type": "password",
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0...",
                "status": "success",
                "created_at": "2023-01-01T00:00:00Z",
                "country": "中国",
                "city": "北京"
            }
        }


# 通用响应
class AuthResponse(BaseModel):
    """认证通用响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "操作成功"
            }
        }


# 更新 TokenResponse 以避免循环引用
TokenResponse.update_forward_refs()