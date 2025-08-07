# app/utils/notification.py
# -*- coding: utf-8 -*-
"""
通知系统工具函数
"""

from typing import Dict, List, Any, Optional, Union
from enum import Enum
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """通知类型"""
    SYSTEM = "system"  # 系统通知
    NOVEL_UPDATE = "novel_update"  # 小说更新
    COMMENT_REPLY = "comment_reply"  # 评论回复
    LIKE = "like"  # 点赞
    FOLLOW = "follow"  # 关注
    FAVORITE = "favorite"  # 收藏
    RECOMMENDATION = "recommendation"  # 推荐
    ANNOUNCEMENT = "announcement"  # 公告
    REWARD = "reward"  # 打赏
    ACHIEVEMENT = "achievement"  # 成就
    SECURITY = "security"  # 安全提醒


class NotificationPriority(Enum):
    """通知优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationChannel(Enum):
    """通知渠道"""
    IN_APP = "in_app"  # 应用内
    EMAIL = "email"  # 邮件
    SMS = "sms"  # 短信
    PUSH = "push"  # 推送
    WEBSOCKET = "websocket"  # WebSocket实时


@dataclass
class NotificationData:
    """通知数据"""
    id: Optional[int] = None
    user_id: int = 0
    type: NotificationType = NotificationType.SYSTEM
    title: str = ""
    content: str = ""
    data: Dict[str, Any] = None
    priority: NotificationPriority = NotificationPriority.NORMAL
    channels: List[NotificationChannel] = None
    is_read: bool = False
    created_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}
        if self.channels is None:
            self.channels = [NotificationChannel.IN_APP]
        if self.created_at is None:
            self.created_at = datetime.now()


class NotificationManager:
    """通知管理器"""
    
    def __init__(self):
        self.templates = {}
        self.user_preferences = {}
        self.delivery_handlers = {}
        self._load_templates()
        self._setup_handlers()
    
    def _load_templates(self):
        """加载通知模板"""
        self.templates = {
            NotificationType.NOVEL_UPDATE: {
                "title": "《{novel_title}》更新了",
                "content": "您关注的小说《{novel_title}》更新了第{chapter_number}章：{chapter_title}",
                "action_url": "/novels/{novel_id}/chapters/{chapter_id}"
            },
            NotificationType.COMMENT_REPLY: {
                "title": "有人回复了您的评论",
                "content": "{replier_name} 回复了您在《{novel_title}》中的评论：{reply_content}",
                "action_url": "/novels/{novel_id}/comments/{comment_id}"
            },
            NotificationType.LIKE: {
                "title": "您的评论收到了点赞",
                "content": "{liker_name} 点赞了您在《{novel_title}》中的评论",
                "action_url": "/novels/{novel_id}/comments/{comment_id}"
            },
            NotificationType.FOLLOW: {
                "title": "新的关注者",
                "content": "{follower_name} 关注了您",
                "action_url": "/users/{follower_id}"
            },
            NotificationType.FAVORITE: {
                "title": "您的小说被收藏了",
                "content": "{user_name} 收藏了您的小说《{novel_title}》",
                "action_url": "/novels/{novel_id}"
            },
            NotificationType.RECOMMENDATION: {
                "title": "为您推荐",
                "content": "根据您的阅读偏好，为您推荐小说《{novel_title}》",
                "action_url": "/novels/{novel_id}"
            },
            NotificationType.ANNOUNCEMENT: {
                "title": "{announcement_title}",
                "content": "{announcement_content}",
                "action_url": "/announcements/{announcement_id}"
            },
            NotificationType.REWARD: {
                "title": "收到打赏",
                "content": "{rewarder_name} 打赏了您的小说《{novel_title}》{amount}元",
                "action_url": "/novels/{novel_id}"
            },
            NotificationType.ACHIEVEMENT: {
                "title": "获得成就",
                "content": "恭喜您获得成就：{achievement_name}",
                "action_url": "/achievements/{achievement_id}"
            },
            NotificationType.SECURITY: {
                "title": "安全提醒",
                "content": "{security_message}",
                "action_url": "/security"
            }
        }
    
    def _setup_handlers(self):
        """设置投递处理器"""
        self.delivery_handlers = {
            NotificationChannel.IN_APP: self._deliver_in_app,
            NotificationChannel.EMAIL: self._deliver_email,
            NotificationChannel.SMS: self._deliver_sms,
            NotificationChannel.PUSH: self._deliver_push,
            NotificationChannel.WEBSOCKET: self._deliver_websocket
        }
    
    def create_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        data: Dict[str, Any],
        priority: NotificationPriority = NotificationPriority.NORMAL,
        channels: Optional[List[NotificationChannel]] = None,
        expires_in_days: Optional[int] = None
    ) -> NotificationData:
        """创建通知"""
        try:
            # 获取模板
            template = self.templates.get(notification_type, {})
            
            # 生成标题和内容
            title = template.get("title", "").format(**data)
            content = template.get("content", "").format(**data)
            
            # 设置过期时间
            expires_at = None
            if expires_in_days:
                expires_at = datetime.now() + timedelta(days=expires_in_days)
            
            # 获取用户偏好的通知渠道
            if channels is None:
                channels = self._get_user_preferred_channels(user_id, notification_type)
            
            # 创建通知对象
            notification = NotificationData(
                user_id=user_id,
                type=notification_type,
                title=title,
                content=content,
                data=data,
                priority=priority,
                channels=channels,
                expires_at=expires_at
            )
            
            return notification
            
        except Exception as e:
            logger.error(f"创建通知失败: {e}")
            raise
    
    def send_notification(self, notification: NotificationData) -> bool:
        """发送通知"""
        try:
            success = True
            
            # 检查通知是否过期
            if notification.expires_at and datetime.now() > notification.expires_at:
                logger.warning(f"通知已过期，跳过发送: {notification.id}")
                return False
            
            # 通过各个渠道发送
            for channel in notification.channels:
                try:
                    handler = self.delivery_handlers.get(channel)
                    if handler:
                        handler(notification)
                    else:
                        logger.warning(f"未找到渠道处理器: {channel}")
                        success = False
                except Exception as e:
                    logger.error(f"通过渠道 {channel} 发送通知失败: {e}")
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"发送通知失败: {e}")
            return False
    
    def batch_send_notifications(
        self,
        notifications: List[NotificationData]
    ) -> Dict[str, int]:
        """批量发送通知"""
        try:
            results = {"success": 0, "failed": 0}
            
            for notification in notifications:
                if self.send_notification(notification):
                    results["success"] += 1
                else:
                    results["failed"] += 1
            
            return results
            
        except Exception as e:
            logger.error(f"批量发送通知失败: {e}")
            return {"success": 0, "failed": len(notifications)}
    
    def send_novel_update_notification(
        self,
        novel_id: int,
        novel_title: str,
        chapter_id: int,
        chapter_number: int,
        chapter_title: str,
        follower_ids: List[int]
    ) -> Dict[str, int]:
        """发送小说更新通知"""
        try:
            notifications = []
            
            for user_id in follower_ids:
                notification = self.create_notification(
                    user_id=user_id,
                    notification_type=NotificationType.NOVEL_UPDATE,
                    data={
                        "novel_id": novel_id,
                        "novel_title": novel_title,
                        "chapter_id": chapter_id,
                        "chapter_number": chapter_number,
                        "chapter_title": chapter_title
                    },
                    priority=NotificationPriority.NORMAL,
                    expires_in_days=7
                )
                notifications.append(notification)
            
            return self.batch_send_notifications(notifications)
            
        except Exception as e:
            logger.error(f"发送小说更新通知失败: {e}")
            return {"success": 0, "failed": len(follower_ids)}
    
    def send_comment_reply_notification(
        self,
        user_id: int,
        novel_id: int,
        novel_title: str,
        comment_id: int,
        replier_name: str,
        reply_content: str
    ) -> bool:
        """发送评论回复通知"""
        try:
            notification = self.create_notification(
                user_id=user_id,
                notification_type=NotificationType.COMMENT_REPLY,
                data={
                    "novel_id": novel_id,
                    "novel_title": novel_title,
                    "comment_id": comment_id,
                    "replier_name": replier_name,
                    "reply_content": reply_content[:50] + "..." if len(reply_content) > 50 else reply_content
                },
                priority=NotificationPriority.HIGH
            )
            
            return self.send_notification(notification)
            
        except Exception as e:
            logger.error(f"发送评论回复通知失败: {e}")
            return False
    
    def send_system_announcement(
        self,
        title: str,
        content: str,
        target_users: Optional[List[int]] = None,
        priority: NotificationPriority = NotificationPriority.HIGH
    ) -> Dict[str, int]:
        """发送系统公告"""
        try:
            # 如果没有指定用户，则发送给所有用户
            if target_users is None:
                # 这里应该从数据库获取所有活跃用户
                target_users = self._get_all_active_users()
            
            notifications = []
            
            for user_id in target_users:
                notification = self.create_notification(
                    user_id=user_id,
                    notification_type=NotificationType.ANNOUNCEMENT,
                    data={
                        "announcement_title": title,
                        "announcement_content": content,
                        "announcement_id": 1  # 这里应该是实际的公告ID
                    },
                    priority=priority,
                    expires_in_days=30
                )
                notifications.append(notification)
            
            return self.batch_send_notifications(notifications)
            
        except Exception as e:
            logger.error(f"发送系统公告失败: {e}")
            return {"success": 0, "failed": len(target_users) if target_users else 0}
    
    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """标记通知为已读"""
        try:
            # 这里应该更新数据库中的通知状态
            # 暂时返回True表示成功
            logger.info(f"标记通知 {notification_id} 为已读，用户: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"标记通知已读失败: {e}")
            return False
    
    def mark_all_as_read(self, user_id: int) -> bool:
        """标记用户所有通知为已读"""
        try:
            # 这里应该批量更新数据库中的通知状态
            logger.info(f"标记用户 {user_id} 所有通知为已读")
            return True
            
        except Exception as e:
            logger.error(f"标记所有通知已读失败: {e}")
            return False
    
    def get_user_notifications(
        self,
        user_id: int,
        page: int = 1,
        per_page: int = 20,
        unread_only: bool = False
    ) -> Dict[str, Any]:
        """获取用户通知列表"""
        try:
            # 这里应该从数据库查询通知
            # 暂时返回模拟数据
            notifications = [
                {
                    "id": i,
                    "type": "novel_update",
                    "title": f"《测试小说{i}》更新了",
                    "content": f"您关注的小说《测试小说{i}》更新了第{i}章",
                    "is_read": i % 2 == 0,
                    "created_at": datetime.now().isoformat(),
                    "data": {"novel_id": i, "chapter_id": i}
                }
                for i in range(1, per_page + 1)
            ]
            
            if unread_only:
                notifications = [n for n in notifications if not n["is_read"]]
            
            return {
                "notifications": notifications,
                "total": len(notifications),
                "page": page,
                "per_page": per_page,
                "unread_count": len([n for n in notifications if not n["is_read"]])
            }
            
        except Exception as e:
            logger.error(f"获取用户通知失败: {e}")
            return {"notifications": [], "total": 0, "page": page, "per_page": per_page, "unread_count": 0}
    
    def get_unread_count(self, user_id: int) -> int:
        """获取未读通知数量"""
        try:
            # 这里应该从数据库查询未读通知数量
            # 暂时返回模拟数据
            return 5
            
        except Exception as e:
            logger.error(f"获取未读通知数量失败: {e}")
            return 0
    
    def delete_notification(self, notification_id: int, user_id: int) -> bool:
        """删除通知"""
        try:
            # 这里应该从数据库删除通知
            logger.info(f"删除通知 {notification_id}，用户: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除通知失败: {e}")
            return False
    
    def set_user_preferences(
        self,
        user_id: int,
        preferences: Dict[str, Any]
    ) -> bool:
        """设置用户通知偏好"""
        try:
            self.user_preferences[user_id] = preferences
            logger.info(f"设置用户 {user_id} 通知偏好: {preferences}")
            return True
            
        except Exception as e:
            logger.error(f"设置用户通知偏好失败: {e}")
            return False
    
    def _get_user_preferred_channels(
        self,
        user_id: int,
        notification_type: NotificationType
    ) -> List[NotificationChannel]:
        """获取用户偏好的通知渠道"""
        try:
            user_prefs = self.user_preferences.get(user_id, {})
            type_prefs = user_prefs.get(notification_type.value, {})
            
            # 默认渠道
            default_channels = [NotificationChannel.IN_APP]
            
            # 根据通知类型和用户偏好确定渠道
            if type_prefs.get("email", False):
                default_channels.append(NotificationChannel.EMAIL)
            
            if type_prefs.get("push", False):
                default_channels.append(NotificationChannel.PUSH)
            
            if type_prefs.get("sms", False) and notification_type in [
                NotificationType.SECURITY, NotificationType.URGENT
            ]:
                default_channels.append(NotificationChannel.SMS)
            
            return default_channels
            
        except Exception as e:
            logger.error(f"获取用户偏好渠道失败: {e}")
            return [NotificationChannel.IN_APP]
    
    def _get_all_active_users(self) -> List[int]:
        """获取所有活跃用户ID"""
        try:
            # 这里应该从数据库查询活跃用户
            # 暂时返回模拟数据
            return list(range(1, 101))  # 假设有100个活跃用户
            
        except Exception as e:
            logger.error(f"获取活跃用户失败: {e}")
            return []
    
    def _deliver_in_app(self, notification: NotificationData) -> bool:
        """应用内通知投递"""
        try:
            # 这里应该将通知保存到数据库
            logger.info(f"应用内通知投递: {notification.title}")
            return True
            
        except Exception as e:
            logger.error(f"应用内通知投递失败: {e}")
            return False
    
    def _deliver_email(self, notification: NotificationData) -> bool:
        """邮件通知投递"""
        try:
            # 这里应该发送邮件
            logger.info(f"邮件通知投递: {notification.title}")
            return True
            
        except Exception as e:
            logger.error(f"邮件通知投递失败: {e}")
            return False
    
    def _deliver_sms(self, notification: NotificationData) -> bool:
        """短信通知投递"""
        try:
            # 这里应该发送短信
            logger.info(f"短信通知投递: {notification.title}")
            return True
            
        except Exception as e:
            logger.error(f"短信通知投递失败: {e}")
            return False
    
    def _deliver_push(self, notification: NotificationData) -> bool:
        """推送通知投递"""
        try:
            # 这里应该发送推送通知
            logger.info(f"推送通知投递: {notification.title}")
            return True
            
        except Exception as e:
            logger.error(f"推送通知投递失败: {e}")
            return False
    
    def _deliver_websocket(self, notification: NotificationData) -> bool:
        """WebSocket实时通知投递"""
        try:
            # 这里应该通过WebSocket发送实时通知
            logger.info(f"WebSocket通知投递: {notification.title}")
            return True
            
        except Exception as e:
            logger.error(f"WebSocket通知投递失败: {e}")
            return False


# 全局通知管理器实例
notification_manager = NotificationManager()


def send_notification(
    user_id: int,
    notification_type: NotificationType,
    data: Dict[str, Any],
    priority: NotificationPriority = NotificationPriority.NORMAL,
    channels: Optional[List[NotificationChannel]] = None
) -> bool:
    """发送通知的便捷函数"""
    try:
        notification = notification_manager.create_notification(
            user_id=user_id,
            notification_type=notification_type,
            data=data,
            priority=priority,
            channels=channels
        )
        
        return notification_manager.send_notification(notification)
        
    except Exception as e:
        logger.error(f"发送通知失败: {e}")
        return False


def send_bulk_notification(
    user_ids: List[int],
    notification_type: NotificationType,
    data: Dict[str, Any],
    priority: NotificationPriority = NotificationPriority.NORMAL
) -> Dict[str, int]:
    """批量发送通知的便捷函数"""
    try:
        notifications = []
        
        for user_id in user_ids:
            notification = notification_manager.create_notification(
                user_id=user_id,
                notification_type=notification_type,
                data=data,
                priority=priority
            )
            notifications.append(notification)
        
        return notification_manager.batch_send_notifications(notifications)
        
    except Exception as e:
        logger.error(f"批量发送通知失败: {e}")
        return {"success": 0, "failed": len(user_ids)}