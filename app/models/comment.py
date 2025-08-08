"""
评论相关数据模型
包含评论、点赞等模型
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, Text,
    TIMESTAMP, ForeignKey, JSON, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .base import BaseModel


class Comment(BaseModel):
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
    ip_address = Column(String(45), comment="IP地址")  # IPv6最长为45字符

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


class CommentLike(BaseModel):
    """评论点赞表"""
    __tablename__ = "comment_likes"

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'),
                     nullable=False, comment="用户ID")
    comment_id = Column(UUID(as_uuid=True), ForeignKey('comments.id', ondelete='CASCADE'),
                        nullable=False, comment="评论ID")

    # 约束
    __table_args__ = (
        CheckConstraint("action IN ('like', 'dislike')", name='comment_like_action_check'),
    )

    # 关联关系
    user = relationship("User")
    comment = relationship("Comment", back_populates="likes")


class CommentReport(BaseModel):
    """评论举报表"""
    __tablename__ = "comment_reports"

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'),
                     nullable=False, comment="举报用户ID")
    comment_id = Column(UUID(as_uuid=True), ForeignKey('comments.id', ondelete='CASCADE'),
                        nullable=False, comment="被举报评论ID")
    
    # 举报信息
    reason = Column(String(50), nullable=False, comment="举报原因")
    description = Column(Text, comment="举报描述")
    
    # 处理状态
    status = Column(String(20), default='pending', comment="处理状态")
    handled_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'),
                        comment="处理人ID")
    handled_at = Column(TIMESTAMP(timezone=True), comment="处理时间")
    handle_result = Column(Text, comment="处理结果")

    # 约束
    __table_args__ = (
        CheckConstraint("reason IN ('spam', 'abuse', 'inappropriate', 'copyright', 'other')", 
                       name='comment_report_reason_check'),
        CheckConstraint("status IN ('pending', 'processing', 'resolved', 'rejected')", 
                       name='comment_report_status_check'),
    )

    # 关联关系
    user = relationship("User", foreign_keys=[user_id])
    comment = relationship("Comment")
    handler = relationship("User", foreign_keys=[handled_by])