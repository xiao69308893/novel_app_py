"""
小说相关数据模型
包含小说、分类、标签、作者等模型
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, Date, DECIMAL, Text,
    TIMESTAMP, ForeignKey, JSON, CheckConstraint, BigInteger
)
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .base import BaseModel


class Category(BaseModel):
    """小说分类表"""
    __tablename__ = "categories"

    name = Column(String(100), nullable=False, comment="分类名称")
    slug = Column(String(100), unique=True, nullable=False, comment="分类标识")
    description = Column(Text, comment="分类描述")
    cover_url = Column(String(500), comment="分类封面")

    # 层级结构
    parent_id = Column(UUID(as_uuid=True), ForeignKey('categories.id'), comment="父分类ID")
    level = Column(Integer, default=0, comment="分类层级")
    sort_order = Column(Integer, default=0, comment="排序")

    # 统计信息
    novel_count = Column(Integer, default=0, comment="小说数量")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")

    # 关联关系
    parent = relationship("Category", remote_side="Category.id", back_populates="children")
    children = relationship("Category", back_populates="parent")
    novels = relationship("Novel", back_populates="category")


class Tag(BaseModel):
    """小说标签表"""
    __tablename__ = "tags"

    name = Column(String(50), nullable=False, unique=True, comment="标签名称")
    color = Column(String(7), default='#1890ff', comment="标签颜色")
    description = Column(Text, comment="标签描述")

    # 统计
    usage_count = Column(Integer, default=0, comment="使用次数")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")

    # 关联关系
    novel_tags = relationship("NovelTag", back_populates="tag")


class Author(BaseModel):
    """作者表"""
    __tablename__ = "authors"

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'),
                     nullable=True, comment="关联用户ID")

    # 基础信息
    name = Column(String(100), nullable=False, comment="作者姓名")
    pen_name = Column(String(100), comment="笔名")
    avatar_url = Column(String(500), comment="头像URL")
    biography = Column(Text, comment="作者简介")

    # 联系信息
    email = Column(String(100), comment="邮箱")
    website = Column(String(500), comment="个人网站")
    social_links = Column(JSON, default={}, comment="社交链接")

    # 统计信息
    novel_count = Column(Integer, default=0, comment="小说数量")
    total_words = Column(BigInteger, default=0, comment="总字数")
    followers_count = Column(Integer, default=0, comment="粉丝数")

    # 状态
    status = Column(String(20), default='active', comment="状态")
    is_verified = Column(Boolean, default=False, comment="是否认证")

    # 约束
    __table_args__ = (
        CheckConstraint("status IN ('active', 'inactive', 'banned')", name='author_status_check'),
    )

    # 关联关系
    user = relationship("User")
    novels = relationship("Novel", back_populates="author")


class Novel(BaseModel):
    """小说表"""
    __tablename__ = "novels"

    # 基础信息
    title = Column(String(200), nullable=False, comment="小说标题")
    subtitle = Column(String(200), comment="副标题")
    description = Column(Text, comment="小说描述")
    cover_url = Column(String(500), comment="封面URL")

    # 作者信息
    author_id = Column(UUID(as_uuid=True), ForeignKey('authors.id'), nullable=False, comment="作者ID")

    # 分类标签
    category_id = Column(UUID(as_uuid=True), ForeignKey('categories.id'), comment="分类ID")

    # 内容信息
    language = Column(String(10), default='zh-CN', comment="语言")
    word_count = Column(BigInteger, default=0, comment="字数")
    chapter_count = Column(Integer, default=0, comment="章节数")

    # 状态信息
    status = Column(String(20), default='ongoing', comment="小说状态")
    publish_status = Column(String(20), default='draft', comment="发布状态")

    # VIP和付费设置
    is_vip = Column(Boolean, default=False, comment="是否VIP")
    is_free = Column(Boolean, default=True, comment="是否免费")
    price_per_chapter = Column(DECIMAL(8, 2), default=0, comment="章节价格")

    # 统计信息
    view_count = Column(BigInteger, default=0, comment="浏览量")
    favorite_count = Column(Integer, default=0, comment="收藏数")
    comment_count = Column(Integer, default=0, comment="评论数")
    rating = Column(DECIMAL(3, 2), default=0, comment="评分")
    rating_count = Column(Integer, default=0, comment="评分人数")

    # 更新信息
    last_chapter_id = Column(UUID(as_uuid=True), comment="最新章节ID")
    last_chapter_title = Column(String(200), comment="最新章节标题")
    last_update_time = Column(TIMESTAMP(timezone=True), comment="最后更新时间")

    # SEO相关
    seo_title = Column(String(200), comment="SEO标题")
    seo_description = Column(Text, comment="SEO描述")
    seo_keywords = Column(String(500), comment="SEO关键词")

    # 翻译相关
    is_translated = Column(Boolean, default=False, comment="是否翻译")
    original_language = Column(String(10), comment="原始语言")
    translation_count = Column(Integer, default=0, comment="翻译数量")

    # 全文搜索向量
    search_vector = Column(TSVECTOR, comment="搜索向量")

    # 发布时间
    published_at = Column(TIMESTAMP(timezone=True), comment="发布时间")

    # 约束
    __table_args__ = (
        CheckConstraint("status IN ('ongoing', 'completed', 'paused', 'dropped')", name='novel_status_check'),
        CheckConstraint("publish_status IN ('draft', 'published', 'reviewing', 'rejected')",
                        name='novel_publish_status_check'),
        CheckConstraint('rating BETWEEN 0 AND 5', name='novel_rating_check'),
    )

    # 关联关系
    author = relationship("Author", back_populates="novels")
    category = relationship("Category", back_populates="novels")
    chapters = relationship("Chapter", back_populates="novel")
    novel_tags = relationship("NovelTag", back_populates="novel")
    ratings = relationship("NovelRating", back_populates="novel")
    favorites = relationship("UserFavorite", back_populates="novel")
    reading_progress = relationship("ReadingProgress", back_populates="novel")
    comments = relationship("Comment", back_populates="novel",
                            primaryjoin="and_(Novel.id==Comment.target_id, Comment.target_type=='novel')")


class NovelTag(BaseModel):
    """小说标签关联表"""
    __tablename__ = "novel_tags"

    novel_id = Column(UUID(as_uuid=True), ForeignKey('novels.id', ondelete='CASCADE'),
                      nullable=False, comment="小说ID")
    tag_id = Column(UUID(as_uuid=True), ForeignKey('tags.id', ondelete='CASCADE'),
                    nullable=False, comment="标签ID")

    # 约束
    __table_args__ = ()

    # 关联关系
    novel = relationship("Novel", back_populates="novel_tags")
    tag = relationship("Tag", back_populates="novel_tags")


class NovelRating(BaseModel):
    """小说评分表"""
    __tablename__ = "novel_ratings"

    novel_id = Column(UUID(as_uuid=True), ForeignKey('novels.id', ondelete='CASCADE'),
                      nullable=False, comment="小说ID")
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'),
                     nullable=False, comment="用户ID")

    rating = Column(Integer, nullable=False, comment="评分")
    review = Column(Text, comment="评价内容")

    # 约束
    __table_args__ = (
        CheckConstraint('rating BETWEEN 1 AND 5', name='rating_value_check'),
    )

    # 关联关系
    novel = relationship("Novel", back_populates="ratings")
    user = relationship("User", back_populates="ratings")