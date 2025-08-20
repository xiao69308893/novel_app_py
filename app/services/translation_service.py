# app/services/translation_service.py
"""
翻译业务服务
处理AI翻译相关的所有业务逻辑，包括翻译项目管理、任务调度、质量控制等
"""

from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, desc
from sqlalchemy.orm import selectinload, joinedload
from datetime import datetime, timedelta
import uuid
import asyncio
import json

from ..models.translation import (
    TranslationProject, TranslationConfig, TranslatedNovel, TranslatedChapter,
    CharacterMapping, TranslationTask, AIModel
)
from ..models.novel import Novel
from ..models.chapter import Chapter
from ..models.user import User
from ..core.exceptions import NotFoundException, BusinessException
from .base import BaseService


class TranslationService(BaseService):
    """翻译业务服务类"""

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_translation_projects(
            self,
            user_id: uuid.UUID,
            page: int = 1,
            limit: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取翻译项目列表"""
        offset = (page - 1) * limit

        # 查询翻译项目
        query = select(TranslationProject).options(
            joinedload(TranslationProject.source_novel),
            joinedload(TranslationProject.config)
        ).where(
            TranslationProject.created_by == user_id
        ).order_by(
            TranslationProject.created_at.desc()
        ).offset(offset).limit(limit)

        result = await self.db.execute(query)
        projects = result.scalars().all()

        # 查询总数
        count_query = select(func.count()).select_from(TranslationProject).where(
            TranslationProject.created_by == user_id
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # 构建响应数据
        project_list = []
        for project in projects:
            project_data = {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "progress": float(project.progress),
                "source_novel_title": project.source_novel.title if project.source_novel else None,
                "source_language": project.source_language,
                "target_language": project.target_language,
                "total_chapters": project.total_chapters,
                "completed_chapters": project.completed_chapters,
                "created_at": project.created_at,
                "updated_at": project.updated_at
            }
            project_list.append(project_data)

        return project_list, total

    async def get_translation_project(self, project_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """获取翻译项目详情"""
        query = select(TranslationProject).options(
            joinedload(TranslationProject.source_novel),
            joinedload(TranslationProject.config),
            joinedload(TranslationProject.translated_novel)
        ).where(TranslationProject.id == project_id)

        result = await self.db.execute(query)
        project = result.scalar_one_or_none()

        if not project:
            return None

        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "progress": float(project.progress),
            "source_novel": {
                "id": project.source_novel.id,
                "title": project.source_novel.title
            } if project.source_novel else None,
            "source_language": project.source_language,
            "target_language": project.target_language,
            "total_chapters": project.total_chapters,
            "completed_chapters": project.completed_chapters,
            "failed_chapters": project.failed_chapters,
            "estimated_cost": float(project.estimated_cost),
            "actual_cost": float(project.actual_cost),
            "created_at": project.created_at,
            "updated_at": project.updated_at
        }

    async def create_translation_project(
            self,
            user_id: uuid.UUID,
            project_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建翻译项目"""
        # 检查源小说是否存在
        novel_query = select(Novel).where(Novel.id == project_data["source_novel_id"])
        novel_result = await self.db.execute(novel_query)
        novel = novel_result.scalar_one_or_none()

        if not novel:
            raise NotFoundException("源小说不存在")

        # 创建翻译项目
        project = TranslationProject(
            name=project_data["name"],
            description=project_data.get("description"),
            created_by=user_id,
            source_novel_id=project_data["source_novel_id"],
            source_language=project_data["source_language"],
            target_language=project_data["target_language"],
            start_chapter=project_data.get("start_chapter", 1),
            end_chapter=project_data.get("end_chapter")
        )

        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)

        return await self.get_translation_project(project.id)

    async def update_translation_project(
            self,
            project_id: uuid.UUID,
            user_id: uuid.UUID,
            update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新翻译项目"""
        query = select(TranslationProject).where(
            and_(
                TranslationProject.id == project_id,
                TranslationProject.created_by == user_id
            )
        )
        result = await self.db.execute(query)
        project = result.scalar_one_or_none()

        if not project:
            raise NotFoundException("翻译项目不存在")

        # 更新字段
        for field, value in update_data.items():
            if hasattr(project, field):
                setattr(project, field, value)

        project.updated_at = datetime.utcnow()
        await self.db.commit()

        return await self.get_translation_project(project_id)

    async def delete_translation_project(
            self,
            project_id: uuid.UUID,
            user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """删除翻译项目"""
        query = select(TranslationProject).where(
            and_(
                TranslationProject.id == project_id,
                TranslationProject.created_by == user_id
            )
        )
        result = await self.db.execute(query)
        project = result.scalar_one_or_none()

        if not project:
            raise NotFoundException("翻译项目不存在")

        await self.db.delete(project)
        await self.db.commit()

        return {"message": "翻译项目删除成功"}