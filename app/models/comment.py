"""
评论相关数据模型
包含评论、点赞等模型
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, Text,
    TIMESTAMP, ForeignKey, JSON, CheckConstraint, INET
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .base import Base


class Comment(Base):
    """评论表"""
    __tablename__ = "comments"

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'),
                     nullable=False, comment="用户ID")

    # 评论目标
    target_type = Column(String(20), nullable=False, comment="目标类型")
    target_id = Column(UUID(as_uuid=True), nullable=False, comment="目标ID")

    # 评论内容
    content = Column(Text, nullable=False, comment="评论内容")
    content_type = Column(String(20), default='text', comment="内容类型")

    # 层级结构
    parent_id = Column(UUID(as_uuid=True), ForeignKey('comments.id', ondelete='CASCADE'),
                       comment="父评论ID")
    root_id = Column(UUID(as_uuid=True), ForeignKey('comments.id', ondelete='CASCADE'),
                     comment="根评论ID")
    level = Column(Integer, default=0, comment="评论层级")

    # 统计信息
    like_count = Column(Integer, default=0, comment="点赞数")
    reply_count = Column(Integer, default=0, comment="回复数")

    # 状态
    status = Column(String(20), default='published', comment="状态")

    # IP信息
    ip_address = Column(INET, comment="IP地址")

    # 约束
    __table_args__ = (
        CheckConstraint("target_type IN ('novel', 'chapter', 'comment')", name='comment_target_type_check'),
        CheckConstraint("content_type IN ('text', 'html', 'markdown')", name='comment_content_type_check'),
        CheckConstraint("status IN ('published', 'hidden', 'deleted', 'reviewing')", name='comment_status_check'),
    )

    # 关联关系
    user = relationship("User", back_populates="comments")
    parent = relationship("Comment", remote_side="Comment.id", back_populates="replies")
    replies = relationship("Comment", back_populates="parent")
    root = relationship("Comment", remote_side="Comment.id")
    likes = relationship("CommentLike", back_populates="comment")

    # 目标关联（通过外键关联到具体的目标表）
    novel = relationship("Novel", back_populates="comments",
                         primaryjoin="and_(Comment.target_id==Novel.id, Comment.target_type=='novel')",
                         foreign_keys=[target_id])
    chapter = relationship("Chapter", back_populates="comments",
                           primaryjoin="and_(Comment.target_id==Chapter.id, Comment.target_type=='chapter')",
                           foreign_keys=[target_id])


class CommentLike(Base):
    """评论点赞表"""
    __tablename__ = "comment_likes"

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'),
                     nullable=False, comment="用户ID")
    comment_id = Column(UUID(as_uuid=True), ForeignKey('comments.id', ondelete='CASCADE'),
                        nullable=False, comment="评论ID")

    # 约束
    __table_args__ = (
        {"postgresql_index": [("user_id", "comment_id")]},
    )

    # 关联关系
    user = relationship("User")
    comment = relationship("Comment", back_populates="likes")