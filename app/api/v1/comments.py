# app/api/v1/comments.py
# -*- coding: utf-8 -*-
"""
评论相关API接口
处理小说评论、章节评论等功能
"""

from typing import Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_db
from app.core.deps import get_current_active_user, get_pagination_params, get_current_user_optional
from app.schemas.base import BaseResponse, ListResponse, SuccessResponse
from app.schemas.comment import (
    CommentResponse, CommentCreate, CommentUpdate,
    CommentReplyResponse, CommentReplyCreate
)
from app.services.comment_service import CommentService
from app.models.user import User

# 创建路由器
router = APIRouter()


# 依赖注入
def get_comment_service(db: AsyncSession = Depends(get_db)) -> CommentService:
    """获取评论服务"""
    return CommentService(db)


@router.get("/novels/{novel_id}", response_model=ListResponse[CommentResponse], summary="获取小说评论")
async def get_novel_comments(
        novel_id: str,
        sort_by: str = Query("created_at", description="排序字段"),
        sort_order: str = Query("desc", description="排序方向"),
        pagination: dict = Depends(get_pagination_params),
        current_user: Optional[User] = Depends(get_current_user_optional),
        comment_service: CommentService = Depends(get_comment_service)
) -> Any:
    """获取小说评论列表"""
    
    comments, total = await comment_service.get_novel_comments(
        novel_id=novel_id,
        sort_by=sort_by,
        sort_order=sort_order,
        user_id=current_user.id if current_user else None,
        **pagination
    )
    
    return ListResponse(
        data=comments,
        pagination={
            "page": pagination["page"],
            "page_size": pagination["page_size"],
            "total": total,
            "total_pages": (total + pagination["page_size"] - 1) // pagination["page_size"],
            "has_more": total > pagination["offset"] + len(comments),
            "has_next_page": pagination["page"] * pagination["page_size"] < total,
            "has_previous_page": pagination["page"] > 1
        },
        message="获取小说评论成功"
    )


@router.post("/novels/{novel_id}", response_model=BaseResponse[CommentResponse], summary="发表小说评论")
async def create_novel_comment(
        novel_id: str,
        comment_data: CommentCreate,
        current_user: User = Depends(get_current_active_user),
        comment_service: CommentService = Depends(get_comment_service)
) -> Any:
    """发表小说评论"""
    
    comment = await comment_service.create_novel_comment(
        novel_id=novel_id,
        user_id=current_user.id,
        content=comment_data.content,
        rating=comment_data.rating,
        spoiler=comment_data.spoiler
    )
    
    return BaseResponse(
        data=comment,
        message="评论发表成功"
    )


@router.get("/chapters/{chapter_id}", response_model=ListResponse[CommentResponse], summary="获取章节评论")
async def get_chapter_comments(
        chapter_id: str,
        sort_by: str = Query("created_at", description="排序字段"),
        sort_order: str = Query("desc", description="排序方向"),
        pagination: dict = Depends(get_pagination_params),
        current_user: Optional[User] = Depends(get_current_user_optional),
        comment_service: CommentService = Depends(get_comment_service)
) -> Any:
    """获取章节评论列表"""
    
    comments, total = await comment_service.get_chapter_comments(
        chapter_id=chapter_id,
        sort_by=sort_by,
        sort_order=sort_order,
        user_id=current_user.id if current_user else None,
        **pagination
    )
    
    return ListResponse(
        data=comments,
        pagination={
            "page": pagination["page"],
            "page_size": pagination["page_size"],
            "total": total,
            "total_pages": (total + pagination["page_size"] - 1) // pagination["page_size"],
            "has_more": total > pagination["offset"] + len(comments),
            "has_next_page": pagination["page"] * pagination["page_size"] < total,
            "has_previous_page": pagination["page"] > 1
        },
        message="获取章节评论成功"
    )


@router.post("/chapters/{chapter_id}", response_model=BaseResponse[CommentResponse], summary="发表章节评论")
async def create_chapter_comment(
        chapter_id: str,
        comment_data: CommentCreate,
        current_user: User = Depends(get_current_active_user),
        comment_service: CommentService = Depends(get_comment_service)
) -> Any:
    """发表章节评论"""
    
    comment = await comment_service.create_chapter_comment(
        chapter_id=chapter_id,
        user_id=current_user.id,
        content=comment_data.content,
        spoiler=comment_data.spoiler
    )
    
    return BaseResponse(
        data=comment,
        message="评论发表成功"
    )


@router.get("/{comment_id}", response_model=BaseResponse[CommentResponse], summary="获取评论详情")
async def get_comment_detail(
        comment_id: str,
        current_user: Optional[User] = Depends(get_current_user_optional),
        comment_service: CommentService = Depends(get_comment_service)
) -> Any:
    """获取评论详情"""
    
    comment = await comment_service.get_comment_by_id(
        comment_id=comment_id,
        user_id=current_user.id if current_user else None
    )
    
    return BaseResponse(
        data=comment,
        message="获取评论详情成功"
    )


@router.put("/{comment_id}", response_model=BaseResponse[CommentResponse], summary="更新评论")
async def update_comment(
        comment_id: str,
        comment_data: CommentUpdate,
        current_user: User = Depends(get_current_active_user),
        comment_service: CommentService = Depends(get_comment_service)
) -> Any:
    """更新评论"""
    
    comment = await comment_service.update_comment(
        comment_id=comment_id,
        user_id=current_user.id,
        content=comment_data.content,
        rating=comment_data.rating,
        spoiler=comment_data.spoiler
    )
    
    return BaseResponse(
        data=comment,
        message="评论更新成功"
    )


@router.delete("/{comment_id}", response_model=SuccessResponse, summary="删除评论")
async def delete_comment(
        comment_id: str,
        current_user: User = Depends(get_current_active_user),
        comment_service: CommentService = Depends(get_comment_service)
) -> Any:
    """删除评论"""
    
    await comment_service.delete_comment(comment_id, current_user.id)
    
    return SuccessResponse(message="评论删除成功")


@router.post("/{comment_id}/like", response_model=BaseResponse[dict], summary="点赞评论")
async def like_comment(
        comment_id: str,
        current_user: User = Depends(get_current_active_user),
        comment_service: CommentService = Depends(get_comment_service)
) -> Any:
    """点赞评论"""
    
    result = await comment_service.like_comment(comment_id, current_user.id)
    
    return BaseResponse(
        data=result,
        message="点赞成功"
    )


@router.delete("/{comment_id}/like", response_model=BaseResponse[dict], summary="取消点赞评论")
async def unlike_comment(
        comment_id: str,
        current_user: User = Depends(get_current_active_user),
        comment_service: CommentService = Depends(get_comment_service)
) -> Any:
    """取消点赞评论"""
    
    result = await comment_service.unlike_comment(comment_id, current_user.id)
    
    return BaseResponse(
        data=result,
        message="取消点赞成功"
    )


@router.post("/{comment_id}/dislike", response_model=BaseResponse[dict], summary="踩评论")
async def dislike_comment(
        comment_id: str,
        current_user: User = Depends(get_current_active_user),
        comment_service: CommentService = Depends(get_comment_service)
) -> Any:
    """踩评论"""
    
    result = await comment_service.dislike_comment(comment_id, current_user.id)
    
    return BaseResponse(
        data=result,
        message="踩成功"
    )


@router.delete("/{comment_id}/dislike", response_model=BaseResponse[dict], summary="取消踩评论")
async def undislike_comment(
        comment_id: str,
        current_user: User = Depends(get_current_active_user),
        comment_service: CommentService = Depends(get_comment_service)
) -> Any:
    """取消踩评论"""
    
    result = await comment_service.undislike_comment(comment_id, current_user.id)
    
    return BaseResponse(
        data=result,
        message="取消踩成功"
    )


@router.get("/{comment_id}/replies", response_model=ListResponse[CommentReplyResponse], summary="获取评论回复")
async def get_comment_replies(
        comment_id: str,
        sort_by: str = Query("created_at", description="排序字段"),
        sort_order: str = Query("asc", description="排序方向"),
        pagination: dict = Depends(get_pagination_params),
        current_user: Optional[User] = Depends(get_current_user_optional),
        comment_service: CommentService = Depends(get_comment_service)
) -> Any:
    """获取评论回复列表"""
    
    replies, total = await comment_service.get_comment_replies(
        comment_id=comment_id,
        sort_by=sort_by,
        sort_order=sort_order,
        user_id=current_user.id if current_user else None,
        **pagination
    )
    
    return ListResponse(
        data=replies,
        pagination={
            "page": pagination["page"],
            "page_size": pagination["page_size"],
            "total": total,
            "total_pages": (total + pagination["page_size"] - 1) // pagination["page_size"],
            "has_more": total > pagination["offset"] + len(replies),
            "has_next_page": pagination["page"] * pagination["page_size"] < total,
            "has_previous_page": pagination["page"] > 1
        },
        message="获取评论回复成功"
    )


@router.post("/{comment_id}/replies", response_model=BaseResponse[CommentReplyResponse], summary="回复评论")
async def create_comment_reply(
        comment_id: str,
        reply_data: CommentReplyCreate,
        current_user: User = Depends(get_current_active_user),
        comment_service: CommentService = Depends(get_comment_service)
) -> Any:
    """回复评论"""
    
    reply = await comment_service.create_comment_reply(
        comment_id=comment_id,
        user_id=current_user.id,
        content=reply_data.content,
        reply_to_user_id=reply_data.reply_to_user_id
    )
    
    return BaseResponse(
        data=reply,
        message="回复成功"
    )


@router.put("/replies/{reply_id}", response_model=BaseResponse[CommentReplyResponse], summary="更新回复")
async def update_comment_reply(
        reply_id: str,
        content: str,
        current_user: User = Depends(get_current_active_user),
        comment_service: CommentService = Depends(get_comment_service)
) -> Any:
    """更新回复"""
    
    reply = await comment_service.update_comment_reply(
        reply_id=reply_id,
        user_id=current_user.id,
        content=content
    )
    
    return BaseResponse(
        data=reply,
        message="回复更新成功"
    )


@router.delete("/replies/{reply_id}", response_model=SuccessResponse, summary="删除回复")
async def delete_comment_reply(
        reply_id: str,
        current_user: User = Depends(get_current_active_user),
        comment_service: CommentService = Depends(get_comment_service)
) -> Any:
    """删除回复"""
    
    await comment_service.delete_comment_reply(reply_id, current_user.id)
    
    return SuccessResponse(message="回复删除成功")


@router.post("/replies/{reply_id}/like", response_model=BaseResponse[dict], summary="点赞回复")
async def like_comment_reply(
        reply_id: str,
        current_user: User = Depends(get_current_active_user),
        comment_service: CommentService = Depends(get_comment_service)
) -> Any:
    """点赞回复"""
    
    result = await comment_service.like_comment_reply(reply_id, current_user.id)
    
    return BaseResponse(
        data=result,
        message="点赞成功"
    )


@router.delete("/replies/{reply_id}/like", response_model=BaseResponse[dict], summary="取消点赞回复")
async def unlike_comment_reply(
        reply_id: str,
        current_user: User = Depends(get_current_active_user),
        comment_service: CommentService = Depends(get_comment_service)
) -> Any:
    """取消点赞回复"""
    
    result = await comment_service.unlike_comment_reply(reply_id, current_user.id)
    
    return BaseResponse(
        data=result,
        message="取消点赞成功"
    )


@router.post("/{comment_id}/report", response_model=SuccessResponse, summary="举报评论")
async def report_comment(
        comment_id: str,
        reason: str,
        description: Optional[str] = None,
        current_user: User = Depends(get_current_active_user),
        comment_service: CommentService = Depends(get_comment_service)
) -> Any:
    """举报评论"""
    
    await comment_service.report_comment(
        comment_id=comment_id,
        user_id=current_user.id,
        reason=reason,
        description=description
    )
    
    return SuccessResponse(message="举报成功")


@router.post("/replies/{reply_id}/report", response_model=SuccessResponse, summary="举报回复")
async def report_comment_reply(
        reply_id: str,
        reason: str,
        description: Optional[str] = None,
        current_user: User = Depends(get_current_active_user),
        comment_service: CommentService = Depends(get_comment_service)
) -> Any:
    """举报回复"""
    
    await comment_service.report_comment_reply(
        reply_id=reply_id,
        user_id=current_user.id,
        reason=reason,
        description=description
    )
    
    return SuccessResponse(message="举报成功")


@router.get("/user/{user_id}", response_model=ListResponse[CommentResponse], summary="获取用户评论")
async def get_user_comments(
        user_id: str,
        comment_type: Optional[str] = Query(None, description="评论类型"),
        sort_by: str = Query("created_at", description="排序字段"),
        sort_order: str = Query("desc", description="排序方向"),
        pagination: dict = Depends(get_pagination_params),
        current_user: Optional[User] = Depends(get_current_user_optional),
        comment_service: CommentService = Depends(get_comment_service)
) -> Any:
    """获取用户评论列表"""
    
    comments, total = await comment_service.get_user_comments(
        user_id=user_id,
        comment_type=comment_type,
        sort_by=sort_by,
        sort_order=sort_order,
        viewer_id=current_user.id if current_user else None,
        **pagination
    )
    
    return ListResponse(
        data=comments,
        pagination={
            "page": pagination["page"],
            "page_size": pagination["page_size"],
            "total": total,
            "total_pages": (total + pagination["page_size"] - 1) // pagination["page_size"],
            "has_more": total > pagination["offset"] + len(comments),
            "has_next_page": pagination["page"] * pagination["page_size"] < total,
            "has_previous_page": pagination["page"] > 1
        },
        message="获取用户评论成功"
    )


@router.get("/hot", response_model=ListResponse[CommentResponse], summary="获取热门评论")
async def get_hot_comments(
        time_range: str = Query("7d", description="时间范围"),
        limit: int = Query(20, ge=1, le=100, description="返回数量"),
        current_user: Optional[User] = Depends(get_current_user_optional),
        comment_service: CommentService = Depends(get_comment_service)
) -> Any:
    """获取热门评论"""
    
    comments = await comment_service.get_hot_comments(
        time_range=time_range,
        limit=limit,
        user_id=current_user.id if current_user else None
    )
    
    return ListResponse(
        data=comments,
        message="获取热门评论成功"
    )