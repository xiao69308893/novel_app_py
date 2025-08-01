
# app/tasks/celery_app.py
# -*- coding: utf-8 -*-
"""
Celery应用配置
"""

from celery import Celery
from kombu import Exchange, Queue
from datetime import timedelta

from app.config import settings

# 创建Celery应用
celery_app = Celery(
    "novel_app",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.file_tasks",
        "app.tasks.translation_tasks"
    ]
)

# Celery配置
celery_app.conf.update(
    # 时区设置
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=settings.CELERY_ENABLE_UTC,

    # 任务序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # 任务路由
    task_routes={
        "app.tasks.email_tasks.*": {"queue": "email"},
        "app.tasks.file_tasks.*": {"queue": "file"},
        "app.tasks.translation_tasks.*": {"queue": "translation"},
    },

    # 队列定义
    task_default_queue="default",
    task_queues=(
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("email", Exchange("email"), routing_key="email"),
        Queue("file", Exchange("file"), routing_key="file"),
        Queue("translation", Exchange("translation"), routing_key="translation"),
    ),

    # 工作进程配置
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,

    # 任务执行配置
    task_soft_time_limit=300,  # 5分钟软限制
    task_time_limit=600,  # 10分钟硬限制
    task_default_retry_delay=60,
    task_max_retries=3,

    # 结果配置
    result_expires=3600,  # 结果1小时后过期
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },

    # 定时任务
    beat_schedule={
        # 每天凌晨2点清理临时文件
        "cleanup-temp-files": {
            "task": "app.tasks.file_tasks.cleanup_temp_files_task",
            "schedule": 60.0 * 60.0 * 2,  # 2小时执行一次
        },

        # 每小时统计翻译任务
        "translation-stats": {
            "task": "app.tasks.translation_tasks.update_translation_stats_task",
            "schedule": 60.0 * 60.0,  # 1小时执行一次
        },
    },

    # 监控配置
    worker_send_task_events=True,
    task_send_sent_event=True,

    # 安全配置
    worker_hijack_root_logger=False,
    worker_log_color=False,
)


# 任务基础配置
class BaseTaskConfig:
    """任务基础配置"""

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3, "countdown": 60}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = False


# 设置任务基类
celery_app.Task = BaseTaskConfig