# app/services/comment_service.py
# -*- coding: utf-8 -*-
"""
评论业务服务
处理评论相关的业务逻辑，包括评论发布、回复、点赞、举报等
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func, desc, asc
from sqlalchemy.orm import selectinload, joinedload
import uuid

from ..models.comment import Comment, CommentLike, CommentReport
from ..models.novel import Novel
from ..models.chapter import Chapter
from ..models.user import User
from ..schemas.comment import (
    CommentResponse, CommentCreateRequest, CommentUpdateRequest,
    CommentListResponse, CommentReplyResponse
)
from ..core.exceptions import NotFoundException, BusinessException, PermissionException
from .base import BaseService


class CommentService(BaseService):
    """评论服务类"""

    def __init__(self, db: AsyncSession):
        super().__init__(db)


    async def create_comment(
            self,
            user_id: uuid.UUID,
            comment_data: CommentCreateRequest
    ) -> CommentResponse:
        """创建评论"""
        # 内容过滤
        filtered_content = await self.content_filter.filter_text(comment_data.content)
        if not filtered_content:
            raise BusinessException("评论内容包含敏感信息")

        # 验证目标对象存在
        await self._validate_target_object(comment_data.target_type, comment_data.target_id)

        # 检查用户是否被禁言
        await self._check_user_mute_status(user_id)

        # 检查评论频率限制
        await self._check_comment_rate_limit(user_id)

        # 创建评论
        comment = Comment(
            user_id=user_id,
            target_type=comment_data.target_type,
            target_id=comment_data.target_id,
            parent_id=comment_data.parent_id,
            content=filtered_content,
            is_spoiler=comment_data.is_spoiler or False
        )
        self.db.add(comment)

        # 如果是回复，更新父评论的回复数
        if comment_data.parent_id:
            parent_update = update(Comment).where(
                Comment.id == comment_data.parent_id
            ).values(
                reply_count=Comment.reply_count + 1,
                updated_at=datetime.utcnow()
            )
            await self.db.execute(parent_update)

        await self.db.commit()

        # 清除相关缓存
        await self._clear_comment_cache(comment_data.target_type, comment_data.target_id)

        # 返回评论详情
        return await self.get_comment_detail(comment.id, user_id)

    async def get_comment_list(
            self,
            target_type: str,
            target_id: uuid.UUID,
            user_id: Optional[uuid.UUID] = None,
            parent_id: Optional[uuid.UUID] = None,
            page: int = 1,
            limit: int = 20,
            sort_by: str = "created_at",
            sort_order: str = "desc"
    ) -> Tuple[List[CommentResponse], int]:
        """获取评论列表"""
        offset = (page - 1) * limit

        # 构建查询条件
        conditions = [
            Comment.target_type == target_type,
            Comment.target_id == target_id,
            Comment.status == "approved"
        ]

        if parent_id:
            conditions.append(Comment.parent_id == parent_id)
        else:
            conditions.append(Comment.parent_id.is_(None))

        # 构建排序
        sort_column = getattr(Comment, sort_by, Comment.created_at)
        if sort_order == "desc":
            sort_column = sort_column.desc()
        else:
            sort_column = sort_column.asc()

        # 查询评论
        query = select(Comment).options(
            joinedload(Comment.user),
            selectinload(Comment.replies).joinedload(Comment.user)
        ).where(
            and_(*conditions)
        ).order_by(sort_column).offset(offset).limit(limit)

        result = await self.db.execute(query)
        comments = result.scalars().all()

        # 查询总数
        count_query = select(func.count()).select_from(Comment).where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # 获取用户点赞状态
        liked_comment_ids = set()
        if user_id and comments:
            comment_ids = [comment.id for comment in comments]
            like_query = select(CommentLike.comment_id).where(
                and_(
                    CommentLike.user_id == user_id,
                    CommentLike.comment_id.in_(comment_ids)
                )
            )
            like_result = await self.db.execute(like_query)
            liked_comment_ids = {row[0] for row in like_result.fetchall()}

        # 构建响应数据
        comment_list = []
        for comment in comments:
            comment_data = await self._build_comment_response(
                comment, user_id, liked_comment_ids
            )
            comment_list.append(comment_data)

        return comment_list, total

    async def get_comment_detail(
            self,
            comment_id: uuid.UUID,
            user_id: Optional[uuid.UUID] = None
    ) -> CommentResponse:
        """获取评论详情"""
        # 查询评论
        query = select(Comment).options(
            joinedload(Comment.user)
        ).where(Comment.id == comment_id)

        result = await self.db.execute(query)
        comment = result.scalar_one_or_none()

        if not comment:
            raise NotFoundException("评论不存在")

        # 检查用户点赞状态
        liked_comment_ids = set()
        if user_id:
            like_query = select(CommentLike.comment_id).where(
                and_(
                    CommentLike.user_id == user_id,
                    CommentLike.comment_id == comment_id
                )
            )
            like_result = await self.db.execute(like_query)
            if like_result.scalar_one_or_none():
                liked_comment_ids.add(comment_id)

        return await self._build_comment_response(comment, user_id, liked_comment_ids)

    async def update_comment(
            self,
            comment_id: uuid.UUID,
            user_id: uuid.UUID,
            update_data: CommentUpdateRequest
    ) -> CommentResponse:
        """更新评论"""
        # 查询评论
        query = select(Comment).where(Comment.id == comment_id)
        result = await self.db.execute(query)
        comment = result.scalar_one_or_none()

        if not comment:
            raise NotFoundException("评论不存在")

        if comment.user_id != user_id:
            raise PermissionException("无权修改此评论")

        # 检查修改时间限制（发布后30分钟内可修改）
        if datetime.utcnow() - comment.created_at > timedelta(minutes=30):
            raise BusinessException("评论发布超过30分钟后不能修改")

        # 内容过滤
        if update_data.content:
            filtered_content = await self.content_filter.filter_text(update_data.content)
            if not filtered_content:
                raise BusinessException("评论内容包含敏感信息")
            comment.content = filtered_content

        if update_data.is_spoiler is not None:
            comment.is_spoiler = update_data.is_spoiler

        comment.updated_at = datetime.utcnow()
        await self.db.commit()

        # 清除相关缓存
        await self._clear_comment_cache(comment.target_type, comment.target_id)

        return await self.get_comment_detail(comment_id, user_id)

    async def delete_comment(
            self,
            comment_id: uuid.UUID,
            user_id: uuid.UUID,
            is_admin: bool = False
    ) -> Dict[str, Any]:
        """删除评论"""
        # 查询评论
        query = select(Comment).where(Comment.id == comment_id)
        result = await self.db.execute(query)
        comment = result.scalar_one_or_none()

        if not comment:
            raise NotFoundException("评论不存在")

        if not is_admin and comment.user_id != user_id:
            raise PermissionException("无权删除此评论")

        # 软删除评论
        comment.status = "deleted"
        comment.updated_at = datetime.utcnow()

        # 如果有父评论，减少回复数
        if comment.parent_id:
            parent_update = update(Comment).where(
                Comment.id == comment.parent_id
            ).values(
                reply_count=Comment.reply_count - 1,
                updated_at=datetime.utcnow()
            )
            await self.db.execute(parent_update)

        await self.db.commit()

        # 清除相关缓存
        await self._clear_comment_cache(comment.target_type, comment.target_id)

        return {"message": "评论删除成功"}

    async def like_comment(
            self,
            comment_id: uuid.UUID,
            user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """点赞评论"""
        # 检查评论是否存在
        comment_query = select(Comment).where(Comment.id == comment_id)
        comment_result = await self.db.execute(comment_query)
        comment = comment_result.scalar_one_or_none()

        if not comment:
            raise NotFoundException("评论不存在")

        # 检查是否已点赞
        like_query = select(CommentLike).where(
            and_(
                CommentLike.user_id == user_id,
                CommentLike.comment_id == comment_id
            )
        )
        like_result = await self.db.execute(like_query)
        existing_like = like_result.scalar_one_or_none()

        if existing_like:
            # 取消点赞
            await self.db.delete(existing_like)
            comment.like_count -= 1
            action = "unliked"
        else:
            # 添加点赞
            like = CommentLike(
                user_id=user_id,
                comment_id=comment_id
            )
            self.db.add(like)
            comment.like_count += 1
            action = "liked"

        comment.updated_at = datetime.utcnow()
        await self.db.commit()

        return {
            "action": action,
            "like_count": comment.like_count
        }

    async def report_comment(
            self,
            comment_id: uuid.UUID,
            user_id: uuid.UUID,
            reason: str,
            description: Optional[str] = None
    ) -> Dict[str, Any]:
        """举报评论"""
        # 检查评论是否存在
        comment_query = select(Comment).where(Comment.id == comment_id)
        comment_result = await self.db.execute(comment_query)
        comment = comment_result.scalar_one_or_none()

        if not comment:
            raise NotFoundException("评论不存在")

        # 检查是否已举报
        report_query = select(CommentReport).where(
            and_(
                CommentReport.user_id == user_id,
                CommentReport.comment_id == comment_id
            )
        )
        report_result = await self.db.execute(report_query)
        if report_result.scalar_one_or_none():
            raise BusinessException("您已举报过此评论")

        # 创建举报记录
        report = CommentReport(
            user_id=user_id,
            comment_id=comment_id,
            reason=reason,
            description=description
        )
        self.db.add(report)

        # 增加评论举报数
        comment.report_count += 1
        comment.updated_at = datetime.utcnow()

        # 如果举报数达到阈值，自动隐藏评论
        if comment.report_count >= 5:
            comment.status = "hidden"

        await self.db.commit()

        return {"message": "举报提交成功"}

    async def get_user_comments(
            self,
            user_id: uuid.UUID,
            page: int = 1,
            limit: int = 20
    ) -> Tuple[List[CommentResponse], int]:
        """获取用户评论列表"""
        offset = (page - 1) * limit

        # 查询用户评论
        query = select(Comment).options(
            joinedload(Comment.user)
        ).where(
            and_(
                Comment.user_id == user_id,
                Comment.status == "approved"
            )
        ).order_by(
            Comment.created_at.desc()
        ).offset(offset).limit(limit)

        result = await self.db.execute(query)
        comments = result.scalars().all()

        # 查询总数
        count_query = select(func.count()).select_from(Comment).where(
            and_(
                Comment.user_id == user_id,
                Comment.status == "approved"
            )
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # 构建响应数据
        comment_list = []
        for comment in comments:
            comment_data = await self._build_comment_response(comment, user_id, set())
            comment_list.append(comment_data)

        return comment_list, total

    async def _validate_target_object(self, target_type: str, target_id: uuid.UUID) -> None:
        """验证目标对象是否存在"""
        if target_type == "novel":
            query = select(Novel).where(Novel.id == target_id)
        elif target_type == "chapter":
            query = select(Chapter).where(Chapter.id == target_id)
        else:
            raise BusinessException("不支持的评论目标类型")

        result = await self.db.execute(query)
        if not result.scalar_one_or_none():
            raise NotFoundException(f"{target_type}不存在")

    async def _check_user_mute_status(self, user_id: uuid.UUID) -> None:
        """检查用户是否被禁言"""
        user_query = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            raise NotFoundException("用户不存在")

        if user.is_muted and user.mute_until and user.mute_until > datetime.utcnow():
            raise BusinessException(f"您已被禁言至 {user.mute_until.strftime('%Y-%m-%d %H:%M:%S')}")

    async def _check_comment_rate_limit(self, user_id: uuid.UUID) -> None:
        """检查评论频率限制"""
        # 检查最近1分钟内的评论数量
        one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
        recent_count_query = select(func.count()).select_from(Comment).where(
            and_(
                Comment.user_id == user_id,
                Comment.created_at >= one_minute_ago
            )
        )
        recent_count_result = await self.db.execute(recent_count_query)
        recent_count = recent_count_result.scalar()

        if recent_count >= 3:  # 1分钟内最多3条评论
            raise BusinessException("评论过于频繁，请稍后再试")

    async def _build_comment_response(
            self,
            comment: Comment,
            user_id: Optional[uuid.UUID],
            liked_comment_ids: set
    ) -> CommentResponse:
        """构建评论响应数据"""
        # 获取回复列表（只显示前几条）
        replies = []
        if comment.replies:
            for reply in comment.replies[:3]:  # 只显示前3条回复
                reply_data = CommentReplyResponse(
                    id=reply.id,
                    user_id=reply.user_id,
                    username=reply.user.username,
                    avatar=reply.user.avatar,
                    content=reply.content,
                    like_count=reply.like_count,
                    is_liked=reply.id in liked_comment_ids,
                    created_at=reply.created_at
                )
                replies.append(reply_data)

        return CommentResponse(
            id=comment.id,
            user_id=comment.user_id,
            username=comment.user.username,
            avatar=comment.user.avatar,
            target_type=comment.target_type,
            target_id=comment.target_id,
            parent_id=comment.parent_id,
            content=comment.content,
            is_spoiler=comment.is_spoiler,
            like_count=comment.like_count,
            reply_count=comment.reply_count,
            is_liked=comment.id in liked_comment_ids,
            can_edit=user_id == comment.user_id,
            can_delete=user_id == comment.user_id,
            replies=replies,
            created_at=comment.created_at,
            updated_at=comment.updated_at
        )

    async def _clear_comment_cache(self, target_type: str, target_id: uuid.UUID) -> None:
        """清除评论相关缓存"""
        cache_keys = [
            f"comments:{target_type}:{target_id}:*",
            f"comment_count:{target_type}:{target_id}"
        ]
        for pattern in cache_keys:
            await self.cache_delete_pattern(pattern)