"""
章节相关数据模型
包含章节、阅读进度、章节购买记录等模型
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DECIMAL, Text,
    TIMESTAMP, ForeignKey, JSON, CheckConstraint, BigInteger
)
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .base import BaseModel


class Chapter(BaseModel):
    """章节表"""
    __tablename__ = "chapters"

    novel_id = Column(UUID(as_uuid=True), ForeignKey('novels.id', ondelete='CASCADE'),
                      nullable=False, comment="小说ID")

    # 基础信息
    title = Column(String(200), nullable=False, comment="章节标题")
    chapter_number = Column(Integer, nullable=False, comment="章节号")
    volume_number = Column(Integer, default=1, comment="卷号")

    # 内容
    content = Column(Text, comment="章节内容")
    summary = Column(Text, comment="章节摘要")
    author_notes = Column(Text, comment="作者话")

    # 统计信息
    word_count = Column(Integer, default=0, comment="字数")
    view_count = Column(BigInteger, default=0, comment="浏览量")
    comment_count = Column(Integer, default=0, comment="评论数")

    # 付费设置
    is_vip = Column(Boolean, default=False, comment="是否VIP章节")
    price = Column(DECIMAL(8, 2), default=0, comment="章节价格")
    is_free = Column(Boolean, default=True, comment="是否免费")

    # 状态
    status = Column(String(20), default='published', comment="状态")

    # 语言
    language = Column(String(10), default='zh-CN', comment="语言")

    # 全文搜索向量
    search_vector = Column(TSVECTOR, comment="搜索向量")

    # 发布时间
    published_at = Column(TIMESTAMP(timezone=True), comment="发布时间")

    # 约束
    __table_args__ = (
        CheckConstraint('chapter_number > 0', name='chapter_number_positive'),
        CheckConstraint('word_count >= 0', name='word_count_non_negative'),
        CheckConstraint('price >= 0', name='price_non_negative'),
        CheckConstraint("status IN ('draft', 'published', 'locked')", name='chapter_status_check'),
    )

    # 关联关系
    novel = relationship("Novel", back_populates="chapters")
    purchases = relationship("ChapterPurchase", back_populates="chapter")
    reading_progress = relationship("ReadingProgress", back_populates="chapter")
    bookmarks = relationship("Bookmark", back_populates="chapter")
    comments = relationship("Comment", back_populates="chapter",
                            primaryjoin="and_(Chapter.id==Comment.target_id, Comment.target_type=='chapter')")


class ChapterPurchase(BaseModel):
    """章节购买记录表"""
    __tablename__ = "chapter_purchases"

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'),
                     nullable=False, comment="用户ID")
    chapter_id = Column(UUID(as_uuid=True), ForeignKey('chapters.id', ondelete='CASCADE'),
                        nullable=False, comment="章节ID")
    novel_id = Column(UUID(as_uuid=True), ForeignKey('novels.id', ondelete='CASCADE'),
                      nullable=False, comment="小说ID")

    # 购买信息
    price = Column(DECIMAL(8, 2), nullable=False, comment="购买价格")
    payment_method = Column(String(20), comment="支付方式")
    transaction_id = Column(String(100), comment="交易ID")

    # 状态
    status = Column(String(20), default='completed', comment="状态")

    # 约束
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'completed', 'failed', 'refunded')", name='purchase_status_check'),
    )

    # 关联关系
    user = relationship("User")
    chapter = relationship("Chapter", back_populates="purchases")
    novel = relationship("Novel")


class ReadingProgress(BaseModel):
    """阅读进度表"""
    __tablename__ = "reading_progress"

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'),
                     nullable=False, comment="用户ID")
    novel_id = Column(UUID(as_uuid=True), ForeignKey('novels.id', ondelete='CASCADE'),
                      nullable=False, comment="小说ID")
    chapter_id = Column(UUID(as_uuid=True), ForeignKey('chapters.id', ondelete='SET NULL'),
                        nullable=True, comment="当前章节ID")

    # 进度信息
    chapter_number = Column(Integer, default=1, comment="章节号")
    position = Column(Integer, default=0, comment="章节内位置")
    progress = Column(DECIMAL(5, 4), default=0, comment="整本书进度百分比")

    # 阅读时间
    reading_time = Column(Integer, default=0, comment="总阅读时间(分钟)")
    last_read_duration = Column(Integer, default=0, comment="最后一次阅读时长")

    # 设备信息
    device_type = Column(String(20), comment="设备类型")

    # 约束
    __table_args__ = ()

    # 关联关系
    user = relationship("User", back_populates="reading_progress")
    novel = relationship("Novel", back_populates="reading_progress")
    chapter = relationship("Chapter", back_populates="reading_progress")


class Bookmark(BaseModel):
    """书签表"""
    __tablename__ = "bookmarks"

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'),
                     nullable=False, comment="用户ID")
    novel_id = Column(UUID(as_uuid=True), ForeignKey('novels.id', ondelete='CASCADE'),
                      nullable=False, comment="小说ID")
    chapter_id = Column(UUID(as_uuid=True), ForeignKey('chapters.id', ondelete='CASCADE'),
                        nullable=False, comment="章节ID")

    # 书签信息
    title = Column(String(200), comment="书签标题")
    notes = Column(Text, comment="书签备注")
    position = Column(Integer, nullable=False, default=0, comment="位置")
    content_preview = Column(Text, comment="内容预览")

    # 分类
    folder_name = Column(String(100), default='默认书签', comment="文件夹名称")
    color = Column(String(7), default='#1890ff', comment="颜色")

    # 关联关系
    user = relationship("User", back_populates="bookmarks")
    novel = relationship("Novel")
    chapter = relationship("Chapter", back_populates="bookmarks")