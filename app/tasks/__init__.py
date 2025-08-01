
# app/tasks/__init__.py
# -*- coding: utf-8 -*-
"""
异步任务模块
"""

from .celery_app import celery_app
from .email_tasks import send_email_task, send_verification_email_task
from .file_tasks import cleanup_temp_files_task, process_image_task
from .translation_tasks import start_translation_task, process_chapter_translation_task

__all__ = [
    "celery_app",
    "send_email_task",
    "send_verification_email_task",
    "cleanup_temp_files_task",
    "process_image_task",
    "start_translation_task",
    "process_chapter_translation_task"
]

