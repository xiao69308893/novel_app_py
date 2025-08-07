"""
用户相关数据模型
包含用户基础信息、详细资料、设置、统计等模型
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, Date, DECIMAL,
    Text, TIMESTAMP, ForeignKey, JSON, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .base import BaseModel


class User(BaseModel):
    """用户基础表"""
    __tablename__ = "users"

    # 基础信息
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    email = Column(String(100), unique=True, nullable=True, index=True, comment="邮箱")
    phone = Column(String(20), unique=True, nullable=True, index=True, comment="手机号")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    salt = Column(String(32), nullable=False, comment="密码盐值")

    # 个人信息
    nickname = Column(String(100), comment="昵称")
    avatar_url = Column(String(500), comment="头像URL")
    gender = Column(String(10), comment="性别")
    birthday = Column(Date, comment="生日")
    bio = Column(Text, comment="个人简介")

    # 等级和积分
    level = Column(Integer, default=1, nullable=False, comment="用户等级")
    vip_level = Column(Integer, default=0, nullable=False, comment="VIP等级")
    points = Column(Integer, default=0, nullable=False, comment="积分")
    coins = Column(Integer, default=0, nullable=False, comment="金币")
    experience = Column(Integer, default=0, nullable=False, comment="经验值")

    # 状态管理
    status = Column(String(20), default='active', nullable=False, comment="状态")
    is_verified = Column(Boolean, default=False, comment="是否已验证")
    email_verified = Column(Boolean, default=False, comment="邮箱是否已验证")
    phone_verified = Column(Boolean, default=False, comment="手机号是否已验证")

    # 安全相关
    last_login_at = Column(TIMESTAMP(timezone=True), comment="最后登录时间")
    last_login_ip = Column(String(45), comment="最后登录IP")  # IPv6最长45字符
    failed_login_attempts = Column(Integer, default=0, comment="失败登录尝试次数")
    locked_until = Column(TIMESTAMP(timezone=True), comment="锁定到期时间")

    # 约束
    __table_args__ = (
        CheckConstraint('char_length(username) >= 3', name='users_username_length'),
        CheckConstraint("email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'", name='users_email_format'),
        CheckConstraint("status IN ('active', 'inactive', 'banned', 'deleted')", name='users_status_check'),
        CheckConstraint("gender IN ('male', 'female', 'other')", name='users_gender_check'),
        CheckConstraint('level >= 1', name='users_level_check'),
        CheckConstraint('vip_level >= 0', name='users_vip_level_check'),
        CheckConstraint('points >= 0', name='users_points_check'),
        CheckConstraint('coins >= 0', name='users_coins_check'),
        CheckConstraint('experience >= 0', name='users_experience_check'),
    )

    # 关联关系
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    settings = relationship("UserSettings", back_populates="user", uselist=False)
    statistics = relationship("UserStatistics", back_populates="user", uselist=False)
    login_logs = relationship("LoginLog", back_populates="user")
    favorites = relationship("UserFavorite", back_populates="user")
    reading_progress = relationship("ReadingProgress", back_populates="user")
    bookmarks = relationship("Bookmark", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    ratings = relationship("NovelRating", back_populates="user")


class UserProfile(BaseModel):
    """用户详细资料表"""
    __tablename__ = "user_profiles"

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'),
                     nullable=False, unique=True, comment="用户ID")

    # 个人信息
    real_name = Column(String(100), comment="真实姓名")
    id_card = Column(String(50), comment="身份证号")
    address = Column(Text, comment="地址")
    city = Column(String(100), comment="城市")
    country = Column(String(100), comment="国家")
    timezone = Column(String(50), default='Asia/Shanghai', comment="时区")
    language = Column(String(10), default='zh-CN', comment="语言")

    # 偏好设置
    reading_preferences = Column(JSON, default={}, comment="阅读偏好")
    notification_settings = Column(JSON, default={}, comment="通知设置")
    privacy_settings = Column(JSON, default={}, comment="隐私设置")

    # 社交信息
    website = Column(String(500), comment="个人网站")
    social_links = Column(JSON, default={}, comment="社交链接")

    # 关联关系
    user = relationship("User", back_populates="profile")


class UserSettings(BaseModel):
    """用户设置表"""
    __tablename__ = "user_settings"

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'),
                     nullable=False, unique=True, comment="用户ID")

    # 阅读设置
    reader_theme = Column(String(20), default='light', comment="阅读主题")
    font_size = Column(Integer, default=16, comment="字体大小")
    line_spacing = Column(DECIMAL(3, 1), default=1.5, comment="行间距")
    page_margin = Column(Integer, default=20, comment="页边距")
    auto_scroll = Column(Boolean, default=False, comment="自动滚动")

    # 通知设置
    email_notifications = Column(Boolean, default=True, comment="邮件通知")
    push_notifications = Column(Boolean, default=True, comment="推送通知")
    sms_notifications = Column(Boolean, default=False, comment="短信通知")

    # 隐私设置
    profile_public = Column(Boolean, default=True, comment="资料公开")
    reading_history_public = Column(Boolean, default=False, comment="阅读历史公开")
    allow_friend_requests = Column(Boolean, default=True, comment="允许好友请求")

    # 约束
    __table_args__ = (
        CheckConstraint('font_size BETWEEN 12 AND 24', name='font_size_check'),
        CheckConstraint('line_spacing BETWEEN 1.0 AND 3.0', name='line_spacing_check'),
        CheckConstraint('page_margin BETWEEN 10 AND 50', name='page_margin_check'),
    )

    # 关联关系
    user = relationship("User", back_populates="settings")


class UserStatistics(BaseModel):
    """用户统计表"""
    __tablename__ = "user_statistics"

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'),
                     nullable=False, unique=True, comment="用户ID")

    # 阅读统计
    total_reading_time = Column(Integer, default=0, comment="总阅读时间(分钟)")
    books_read = Column(Integer, default=0, comment="已读完书籍数")
    chapters_read = Column(Integer, default=0, comment="已读章节数")
    words_read = Column(Integer, default=0, comment="已读字数")

    # 收藏统计
    favorites_count = Column(Integer, default=0, comment="收藏数")
    bookmarks_count = Column(Integer, default=0, comment="书签数")

    # 社交统计
    comments_count = Column(Integer, default=0, comment="评论数")
    likes_received = Column(Integer, default=0, comment="获得点赞数")

    # 翻译统计
    translations_created = Column(Integer, default=0, comment="创建翻译数")
    translation_words = Column(Integer, default=0, comment="翻译字数")

    # 日期统计
    streak_days = Column(Integer, default=0, comment="连续签到天数")
    last_read_date = Column(Date, comment="最后阅读日期")
    last_checkin_date = Column(Date, comment="最后签到日期")

    # 关联关系
    user = relationship("User", back_populates="statistics")


class LoginLog(BaseModel):
    """登录日志表"""
    __tablename__ = "login_logs"

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'),
                     nullable=True, comment="用户ID")

    # 登录信息
    login_type = Column(String(20), nullable=False, comment="登录类型")
    ip_address = Column(String(45), nullable=False, comment="IP地址")  # IPv6最长45字符
    user_agent = Column(Text, comment="用户代理")
    device_info = Column(JSON, comment="设备信息")

    # 地理位置
    country = Column(String(100), comment="国家")
    city = Column(String(100), comment="城市")

    # 状态
    status = Column(String(20), nullable=False, comment="状态")
    failure_reason = Column(String(100), comment="失败原因")

    # 约束
    __table_args__ = (
        CheckConstraint("login_type IN ('password', 'phone', 'email', 'social')", name='login_type_check'),
        CheckConstraint("status IN ('success', 'failed', 'blocked')", name='login_status_check'),
    )

    # 关联关系
    user = relationship("User", back_populates="login_logs")