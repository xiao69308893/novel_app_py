# # app/services/translation_service.py
# """
# 翻译业务服务
# 处理AI翻译相关的所有业务逻辑，包括翻译项目管理、任务调度、质量控制等
# """
#
# from typing import Optional, List, Dict, Any, Tuple
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select, update, delete, func, and_, or_, desc
# from sqlalchemy.orm import selectinload, joinedload
# from datetime import datetime, timedelta
# import uuid
# import asyncio
# import json
#
# from ..models import (
#     TranslationProject, TranslationConfig, TranslatedNovel, TranslatedChapter,
#     CharacterMapping, TranslationTask, AIModel, Novel, Chapter, User,
#     ProjectStatusEnum, TaskStatusEnum, TaskTypeEnum, ReviewStatusEnum,
#     TranslationMethodEnum, CharacterTypeEnum
# )
# from ..schemas.translation import (
#     TranslationProjectCreate, TranslationProjectUpdate, TranslationProjectResponse,
#     TranslationConfigCreate, TranslationConfigResponse,
#     CharacterMappingCreate, CharacterMappingResponse,
#     TranslationTaskResponse, TranslationProgressResponse
# )
# from ..core.exceptions import (
#     TranslationProjectNotFoundError, TranslationConfigNotFoundError,
#     NovelNotFoundError, InsufficientPermissionError
# )
# from ..utils.cache import CacheManager
# from .base import BaseService
# from .ai_service import AIService
#
#
# class TranslationService(BaseService[TranslationProject, TranslationProjectCreate, TranslationProjectUpdate]):
#     """翻译业务服务类"""
#
#     def __init__(self, db: AsyncSession, cache: CacheManager, ai_service: AIService):
#         super().__init__(TranslationProject, db)
#         self.cache = cache
#         self.ai_service = ai_service
#
#     async def create_translation_project(
#             self,
#             user_id: uuid.UUID,
#             project_data: TranslationProjectCreate
#     ) -> TranslationProjectResponse:
#         """
#         创建翻译项目
#
#         Args:
#             user_id: 用户ID
#             project_data: 项目创建数据
#
#         Returns:
#             翻译项目响应
#         """
#         # 检查源小说是否存在
#         novel_stmt = select(Novel).where(Novel.id == project_data.source_novel_id)
#         novel_result = await self.db.execute(novel_stmt)
#         novel = novel_result.scalar_one_or_none()
#
#         if not novel:
#             raise NovelNotFoundError("源小说不存在")
#
#         # 检查翻译配置是否存在
#         config_stmt = select(TranslationConfig).where(TranslationConfig.id == project_data.config_id)
#         config_result = await self.db.execute(config_stmt)
#         config = config_result.scalar_one_or_none()
#
#         if not config:
#             raise TranslationConfigNotFoundError("翻译配置不存在")
#
#         # 创建翻译项目
#         project = TranslationProject(
#             name=project_data.name,
#             description=project_data.description,
#             created_by=user_id,
#             source_novel_id=project_data.source_novel_id,
#             source_language=project_data.source_language or config.source_language,
#             target_language=project_data.target_language or config.target_language,
#             config_id=project_data.config_id,
#             custom_config=project_data.custom_config or {},
#             start_chapter=project_data.start_chapter or 1,
#             end_chapter=project_data.end_chapter,
#             chapter_filter=project_data.chapter_filter
#         )
#
#         self.db.add(project)
#         await self.db.commit()
#         await self.db.refresh(project)
#
#         # 分析源小说并初始化项目
#         await self._initialize_project(project.id)
#
#         return await self.get_project_detail(project.id)
#
#     async def get_project_detail(self, project_id: uuid.UUID) -> TranslationProjectResponse:
#         """获取翻译项目详情"""
#         cache_key = f"translation_project:{project_id}"
#         cached_project = await self.cache.get(cache_key)
#
#         if cached_project:
#             return cached_project
#
#         stmt = (
#             select(TranslationProject)
#             .options(
#                 selectinload(TranslationProject.source_novel),
#                 selectinload(TranslationProject.config),
#                 selectinload(TranslationProject.created_by),
#                 selectinload(TranslationProject.translated_novel)
#             )
#             .where(TranslationProject.id == project_id)
#         )
#         result = await self.db.execute(stmt)
#         project = result.scalar_one_or_none()
#
#         if not project:
#             raise TranslationProjectNotFoundError("翻译项目不存在")
#
#         # 获取项目统计
#         stats = await self._get_project_statistics(project_id)
#
#         response = TranslationProjectResponse(
#             id=project.id,
#             name=project.name,
#             description=project.description,
#             status=project.status,
#             progress=float(project.progress),
#             source_novel={"id": project.source_novel.id, "title": project.source_novel.title},
#             source_language=project.source_language,
#             target_language=project.target_language,
#             config_name=project.config.name,
#             total_chapters=project.total_chapters,
#             completed_chapters=project.completed_chapters,
#             failed_chapters=project.failed_chapters,
#             average_quality_score=float(project.average_quality_score) if project.average_quality_score else None,
#             estimated_cost=float(project.estimated_cost),
#             actual_cost=float(project.actual_cost),
#             tokens_used=project.tokens_used,
#             created_at=project.created_at,
#             started_at=project.started_at,
#             completed_at=project.completed_at,
#             estimated_completion_time=project.estimated_completion_time,
#             **stats
#         )
#
#         # 缓存结果
#         await self.cache.set(cache_key, response, expire=300)  # 缓存5分钟
#
#         return response
#
#     async def start_translation(self, project_id: uuid.UUID, user_id: uuid.UUID) -> bool:
#         """启动翻译任务"""
#         project = await self.get(project_id)
#         if not project:
#             raise TranslationProjectNotFoundError("翻译项目不存在")
#
#         if project.created_by != user_id:
#             raise InsufficientPermissionError("无权限操作此项目")
#
#         if project.status not in [ProjectStatusEnum.CREATED, ProjectStatusEnum.PAUSED]:
#             raise ValueError(f"项目状态 {project.status} 无法启动翻译")
#
#         # 更新项目状态
#         project.status = ProjectStatusEnum.TRANSLATING
#         project.started_at = datetime.utcnow()
#
#         # 创建翻译任务
#         await self._create_translation_tasks(project_id)
#
#         await self.db.commit()
#
#         # 清除缓存
#         await self._invalidate_project_cache(project_id)
#
#         # 异步执行翻译任务
#         asyncio.create_task(self._execute_translation_tasks(project_id))
#
#         return True
#
#     async def pause_translation(self, project_id: uuid.UUID, user_id: uuid.UUID) -> bool:
#         """暂停翻译任务"""
#         project = await self.get(project_id)
#         if not project:
#             raise TranslationProjectNotFoundError("翻译项目不存在")
#
#         if project.created_by != user_id:
#             raise InsufficientPermissionError("无权限操作此项目")
#
#         if project.status != ProjectStatusEnum.TRANSLATING:
#             raise ValueError(f"项目状态 {project.status} 无法暂停")
#
#         # 更新项目状态
#         project.status = ProjectStatusEnum.PAUSED
#         project.paused_at = datetime.utcnow()
#
#         # 暂停未开始的任务
#         await self._pause_pending_tasks(project_id)
#
#         await self.db.commit()
#
#         # 清除缓存
#         await self._invalidate_project_cache(project_id)
#
#         return True
#
#     async def get_character_mappings(self, project_id: uuid.UUID) -> List[CharacterMappingResponse]:
#         """获取角色映射列表"""
#         cache_key = f"character_mappings:{project_id}"
#         cached_mappings = await self.cache.get(cache_key)
#
#         if cached_mappings:
#             return cached_mappings
#
#         stmt = (
#             select(CharacterMapping)
#             .where(CharacterMapping.translation_project_id == project_id)
#             .order_by(CharacterMapping.importance_level.desc(), CharacterMapping.appearance_frequency.desc())
#         )
#         result = await self.db.execute(stmt)
#         mappings = result.scalars().all()
#
#         mapping_list = []
#         for mapping in mappings:
#             mapping_response = CharacterMappingResponse(
#                 id=mapping.id,
#                 original_name=mapping.original_name,
#                 translated_name=mapping.translated_name,
#                 alternative_names=mapping.alternative_names,
#                 character_type=mapping.character_type,
#                 importance_level=mapping.importance_level,
#                 description=mapping.description,
#                 appearance_frequency=mapping.appearance_frequency,
#                 mapping_confidence=float(mapping.mapping_confidence),
#                 is_verified=mapping.is_verified,
#                 auto_detected=mapping.auto_detected
#             )
#             mapping_list.append(mapping_response)
#
#         # 缓存结果
#         await self.cache.set(cache_key, mapping_list, expire=1800)  # 缓存30分钟
#
#         return mapping_list
#
#     async def create_character_mapping(
#             self,
#             project_id: uuid.UUID,
#             mapping_data: CharacterMappingCreate
#     ) -> CharacterMappingResponse:
#         """创建角色映射"""
#         # 检查项目是否存在
#         project = await self.get(project_id)
#         if not project:
#             raise TranslationProjectNotFoundError("翻译项目不存在")
#
#         # 检查是否已存在相同的原始名称
#         existing_stmt = select(CharacterMapping).where(
#             and_(
#                 CharacterMapping.translation_project_id == project_id,
#                 CharacterMapping.original_name == mapping_data.original_name
#             )
#         )
#         existing_result = await self.db.execute(existing_stmt)
#         if existing_result.scalar_one_or_none():
#             raise ValueError(f"角色 {mapping_data.original_name} 已存在映射")
#
#         # 创建角色映射
#         mapping = CharacterMapping(
#             translation_project_id=project_id,
#             original_name=mapping_data.original_name,
#             translated_name=mapping_data.translated_name,
#             alternative_names=mapping_data.alternative_names or [],
#             character_type=mapping_data.character_type or CharacterTypeEnum.CHARACTER,
#             importance_level=mapping_data.importance_level or 5,
#             description=mapping_data.description,
#             mapping_confidence=mapping_data.mapping_confidence or 1.0,
#             auto_detected=False
#         )
#
#         self.db.add(mapping)
#         await self.db.commit()
#         await self.db.refresh(mapping)
#
#         # 清除缓存
#         await self.cache.delete(f"character_mappings:{project_id}")
#
#         return CharacterMappingResponse.from_orm(mapping)
#
#     async def get_translation_progress(self, project_id: uuid.UUID) -> TranslationProgressResponse:
#         """获取翻译进度"""
#         cache_key = f"translation_progress:{project_id}"
#         cached_progress = await self.cache.get(cache_key)
#
#         if cached_progress:
#             return cached_progress
#
#         project = await self.get(project_id)
#         if not project:
#             raise TranslationProjectNotFoundError("翻译项目不存在")
#
#         # 获取详细进度统计
#         chapter_stats = await self._get_chapter_progress_stats(project_id)
#         task_stats = await self._get_task_progress_stats(project_id)
#         quality_stats = await self._get_quality_stats(project_id)
#
#         progress = TranslationProgressResponse(
#             project_id=project_id,
#             status=project.status,
#             overall_progress=float(project.progress),
#             total_chapters=project.total_chapters,
#             completed_chapters=project.completed_chapters,
#             failed_chapters=project.failed_chapters,
#             in_progress_chapters=chapter_stats.get("in_progress", 0),
#             pending_chapters=chapter_stats.get("pending", 0),
#             total_tasks=task_stats.get("total", 0),
#             completed_tasks=task_stats.get("completed", 0),
#             failed_tasks=task_stats.get("failed", 0),
#             running_tasks=task_stats.get("running", 0),
#             average_quality_score=float(project.average_quality_score) if project.average_quality_score else None,
#             quality_issues_count=project.quality_issues_count,
#             estimated_completion_time=project.estimated_completion_time,
#             tokens_used=project.tokens_used,
#             actual_cost=float(project.actual_cost)
#         )
#
#         # 缓存结果
#         await self.cache.set(cache_key, progress, expire=60)  # 缓存1分钟
#
#         return progress
#
#     async def get_translated_chapters(
#             self,
#             project_id: uuid.UUID,
#             page: int = 1,
#             page_size: int = 20
#     ) -> Dict[str, Any]:
#         """获取翻译后的章节列表"""
#         stmt = (
#             select(TranslatedChapter)
#             .options(selectinload(TranslatedChapter.original_chapter))
#             .where(TranslatedChapter.translation_project_id == project_id)
#             .order_by(TranslatedChapter.chapter_number)
#             .offset((page - 1) * page_size)
#             .limit(page_size)
#         )
#
#         result = await self.db.execute(stmt)
#         chapters = result.scalars().all()
#
#         # 获取总数
#         count_stmt = select(func.count()).select_from(
#             select(TranslatedChapter).where(
#                 TranslatedChapter.translation_project_id == project_id
#             ).subquery()
#         )
#         count_result = await self.db.execute(count_stmt)
#         total = count_result.scalar()
#
#         chapter_list = []
#         for chapter in chapters:
#             chapter_data = {
#                 "id": chapter.id,
#                 "title": chapter.title,
#                 "chapter_number": chapter.chapter_number,
#                 "volume_number": chapter.volume_number,
#                 "word_count": chapter.word_count,
#                 "quality_score": float(chapter.quality_score) if chapter.quality_score else None,
#                 "review_status": chapter.review_status,
#                 "status": chapter.status,
#                 "translation_method": chapter.translation_method,
#                 "processing_time_seconds": chapter.processing_time_seconds,
#                 "created_at": chapter.created_at,
#                 "original_chapter_id": chapter.original_chapter_id
#             }
#             chapter_list.append(chapter_data)
#
#         return {
#             "chapters": chapter_list,
#             "total": total,
#             "page": page,
#             "page_size": page_size,
#             "has_more": total > page * page_size
#         }
#
#     # 私有方法
#
#     async def _initialize_project(self, project_id: uuid.UUID):
#         """初始化翻译项目"""
#         project = await self.get(project_id)
#         if not project:
#             return
#
#         # 获取源小说的章节信息
#         chapter_stmt = (
#             select(func.count(), func.max(Chapter.chapter_number))
#             .where(
#                 and_(
#                     Chapter.novel_id == project.source_novel_id,
#                     Chapter.status == "published"
#                 )
#             )
#         )
#         chapter_result = await self.db.execute(chapter_stmt)
#         total_chapters, max_chapter = chapter_result.first()
#
#         # 更新项目信息
#         project.total_chapters = total_chapters
#         if not project.end_chapter:
#             project.end_chapter = max_chapter
#
#         # 估算成本和时间
#         await self._estimate_project_cost(project_id)
#
#         # 分析角色名称
#         await self._analyze_characters(project_id)
#
#         await self.db.commit()
#
#     async def _create_translation_tasks(self, project_id: uuid.UUID):
#         """创建翻译任务"""
#         project = await self.get(project_id)
#         if not project:
#             return
#
#         # 获取需要翻译的章节
#         chapters_stmt = (
#             select(Chapter)
#             .where(
#                 and_(
#                     Chapter.novel_id == project.source_novel_id,
#                     Chapter.chapter_number >= project.start_chapter,
#                     Chapter.chapter_number <= (project.end_chapter or 999999),
#                     Chapter.status == "published"
#                 )
#             )
#             .order_by(Chapter.chapter_number)
#         )
#         chapters_result = await self.db.execute(chapters_stmt)
#         chapters = chapters_result.scalars().all()
#
#         # 为每个章节创建翻译任务
#         for i, chapter in enumerate(chapters):
#             # 1. 大纲生成任务（如果启用）
#             if project.config.generate_outline:
#                 outline_task = TranslationTask(
#                     translation_project_id=project_id,
#                     task_type=TaskTypeEnum.OUTLINE,
#                     target_type="chapter",
#                     target_id=chapter.id,
#                     priority=5,
#                     task_config={"chapter_id": str(chapter.id)}
#                 )
#                 self.db.add(outline_task)
#
#             # 2. 翻译任务
#             translate_task = TranslationTask(
#                 translation_project_id=project_id,
#                 task_type=TaskTypeEnum.TRANSLATE,
#                 target_type="chapter",
#                 target_id=chapter.id,
#                 priority=5,
#                 task_config={
#                     "chapter_id": str(chapter.id),
#                     "use_outline": project.config.generate_outline
#                 }
#             )
#             self.db.add(translate_task)
#
#             # 3. 质量检查任务（如果启用）
#             if project.config.enable_quality_check:
#                 quality_task = TranslationTask(
#                     translation_project_id=project_id,
#                     task_type=TaskTypeEnum.QUALITY_CHECK,
#                     target_type="chapter",
#                     target_id=chapter.id,
#                     priority=3,
#                     task_config={"chapter_id": str(chapter.id)}
#                 )
#                 self.db.add(quality_task)
#
#         await self.db.commit()
#
#     async def _execute_translation_tasks(self, project_id: uuid.UUID):
#         """执行翻译任务"""
#         try:
#             while True:
#                 # 获取待执行的任务
#                 task_stmt = (
#                     select(TranslationTask)
#                     .where(
#                         and_(
#                             TranslationTask.translation_project_id == project_id,
#                             TranslationTask.status == TaskStatusEnum.PENDING
#                         )
#                     )
#                     .order_by(TranslationTask.priority.desc(), TranslationTask.created_at)
#                     .limit(1)
#                 )
#                 task_result = await self.db.execute(task_stmt)
#                 task = task_result.scalar_one_or_none()
#
#                 if not task:
#                     break  # 没有更多任务
#
#                 # 执行任务
#                 await self._execute_single_task(task)
#
#                 # 检查项目状态
#                 project = await self.get(project_id)
#                 if project.status != ProjectStatusEnum.TRANSLATING:
#                     break  # 项目已暂停或停止
#
#                 # 短暂延迟，避免过度占用资源
#                 await asyncio.sleep(1)
#
#             # 检查是否完成
#             await self._check_project_completion(project_id)
#
#         except Exception as e:
#             # 记录错误并更新项目状态
#             print(f"翻译任务执行失败: {e}")
#             project = await self.get(project_id)
#             if project:
#                 project.status = ProjectStatusEnum.FAILED
#                 project.failed_at = datetime.utcnow()
#                 await self.db.commit()
#
#     async def _execute_single_task(self, task: TranslationTask):
#         """执行单个翻译任务"""
#         # 更新任务状态
#         task.status = TaskStatusEnum.RUNNING
#         task.started_at = datetime.utcnow()
#         await self.db.commit()
#
#         try:
#             if task.task_type == TaskTypeEnum.OUTLINE:
#                 await self._execute_outline_task(task)
#             elif task.task_type == TaskTypeEnum.TRANSLATE:
#                 await self._execute_translate_task(task)
#             elif task.task_type == TaskTypeEnum.QUALITY_CHECK:
#                 await self._execute_quality_check_task(task)
#
#             # 任务完成
#             task.status = TaskStatusEnum.COMPLETED
#             task.completed_at = datetime.utcnow()
#
#         except Exception as e:
#             # 任务失败
#             task.status = TaskStatusEnum.FAILED
#             task.error_message = str(e)
#             task.retry_count += 1
#
#             # 如果还有重试次数，重新设置为待执行
#             if task.retry_count < task.max_retries:
#                 task.status = TaskStatusEnum.PENDING
#
#         await self.db.commit()
#
#     async def _execute_outline_task(self, task: TranslationTask):
#         """执行大纲生成任务"""
#         chapter_id = uuid.UUID(task.task_config["chapter_id"])
#
#         # 获取章节内容
#         chapter_stmt = select(Chapter).where(Chapter.id == chapter_id)
#         chapter_result = await self.db.execute(chapter_stmt)
#         chapter = chapter_result.scalar_one_or_none()
#
#         if not chapter:
#             raise ValueError("章节不存在")
#
#         # 使用AI服务生成大纲
#         outline = await self.ai_service.generate_chapter_outline(
#             title=chapter.title,
#             content=chapter.content,
#             language=chapter.language
#         )
#
#         # 保存大纲到任务结果
#         task.result = {"outline": outline}
#         task.tokens_used = len(chapter.content) // 4  # 简化的token计算
#
#     async def _execute_translate_task(self, task: TranslationTask):
#         """执行翻译任务"""
#         chapter_id = uuid.UUID(task.task_config["chapter_id"])
#         use_outline = task.task_config.get("use_outline", False)
#
#         # 获取章节和项目信息
#         chapter_stmt = select(Chapter).where(Chapter.id == chapter_id)
#         chapter_result = await self.db.execute(chapter_stmt)
#         chapter = chapter_result.scalar_one_or_none()
#
#         if not chapter:
#             raise ValueError("章节不存在")
#
#         project_stmt = (
#             select(TranslationProject)
#             .options(selectinload(TranslationProject.config))
#             .where(TranslationProject.id == task.translation_project_id)
#         )
#         project_result = await self.db.execute(project_stmt)
#         project = project_result.scalar_one_or_none()
#
#         if not project:
#             raise ValueError("翻译项目不存在")
#
#         # 获取大纲（如果需要）
#         outline = None
#         if use_outline:
#             outline_task_stmt = (
#                 select(TranslationTask)
#                 .where(
#                     and_(
#                         TranslationTask.translation_project_id == task.translation_project_id,
#                         TranslationTask.task_type == TaskTypeEnum.OUTLINE,
#                         TranslationTask.target_id == chapter_id,
#                         TranslationTask.status == TaskStatusEnum.COMPLETED
#                     )
#                 )
#             )
#             outline_task_result = await self.db.execute(outline_task_stmt)
#             outline_task = outline_task_result.scalar_one_or_none()
#
#             if outline_task and outline_task.result:
#                 outline = outline_task.result.get("outline")
#
#         # 获取角色映射
#         character_mappings = await self._get_character_mappings_dict(task.translation_project_id)
#
#         # 执行翻译
#         translated_content = await self.ai_service.translate_chapter(
#             content=chapter.content,
#             title=chapter.title,
#             source_language=project.source_language,
#             target_language=project.target_language,
#             outline=outline,
#             character_mappings=character_mappings,
#             config=project.config
#         )
#
#         # 创建或更新翻译章节
#         await self._save_translated_chapter(
#             project=project,
#             original_chapter=chapter,
#             translated_content=translated_content,
#             outline=outline,
#             translation_method=TranslationMethodEnum.AI_OUTLINE_BASED if outline else TranslationMethodEnum.AI_DIRECT
#         )
#
#         # 更新任务结果
#         task.result = {"success": True}
#         task.tokens_used = len(chapter.content) // 4 + len(translated_content) // 4
#
#     async def _execute_quality_check_task(self, task: TranslationTask):
#         """执行质量检查任务"""
#         chapter_id = uuid.UUID(task.task_config["chapter_id"])
#
#         # 获取翻译后的章节
#         translated_chapter_stmt = (
#             select(TranslatedChapter)
#             .where(
#                 and_(
#                     TranslatedChapter.translation_project_id == task.translation_project_id,
#                     TranslatedChapter.original_chapter_id == chapter_id
#                 )
#             )
#         )
#         translated_chapter_result = await self.db.execute(translated_chapter_stmt)
#         translated_chapter = translated_chapter_result.scalar_one_or_none()
#
#         if not translated_chapter:
#             raise ValueError("找不到翻译后的章节")
#
#         # 执行质量检查
#         quality_result = await self.ai_service.check_translation_quality(
#             original_content=translated_chapter.original_chapter.content,
#             translated_content=translated_chapter.content,
#             title=translated_chapter.title
#         )
#
#         # 更新章节质量信息
#         translated_chapter.quality_score = quality_result.get("score", 0)
#         translated_chapter.quality_details = quality_result.get("details", {})
#         translated_chapter.quality_issues = quality_result.get("issues", [])
#
#         # 更新任务结果
#         task.result = quality_result
#         task.tokens_used = len(translated_chapter.content) // 4
#
#         await self.db.commit()
#
#     async def _save_translated_chapter(
#             self,
#             project: TranslationProject,
#             original_chapter: Chapter,
#             translated_content: str,
#             outline: Optional[str],
#             translation_method: TranslationMethodEnum
#     ):
#         """保存翻译后的章节"""
#         # 检查是否已存在
#         existing_stmt = (
#             select(TranslatedChapter)
#             .where(
#                 and_(
#                     TranslatedChapter.translation_project_id == project.id,
#                     TranslatedChapter.original_chapter_id == original_chapter.id
#                 )
#             )
#         )
#         existing_result = await self.db.execute(existing_stmt)
#         existing_chapter = existing_result.scalar_one_or_none()
#
#         if existing_chapter:
#             # 更新现有章节
#             existing_chapter.content = translated_content
#             existing_chapter.outline = outline
#             existing_chapter.translation_method = translation_method
#             existing_chapter.word_count = len(translated_content)
#             existing_chapter.updated_at = datetime.utcnow()
#             translated_chapter = existing_chapter
#         else:
#             # 创建新章节
#             translated_chapter = TranslatedChapter(
#                 translation_project_id=project.id,
#                 original_chapter_id=original_chapter.id,
#                 translated_novel_id=None,  # 稍后设置
#                 title=original_chapter.title,  # 可能需要翻译
#                 chapter_number=original_chapter.chapter_number,
#                 volume_number=original_chapter.volume_number,
#                 content=translated_content,
#                 outline=outline,
#                 translation_method=translation_method,
#                 word_count=len(translated_content)
#             )
#             self.db.add(translated_chapter)
#
#         await self.db.commit()
#
#         # 更新项目进度
#         await self._update_project_progress(project.id)
#
#     async def _get_character_mappings_dict(self, project_id: uuid.UUID) -> Dict[str, str]:
#         """获取角色映射字典"""
#         stmt = select(CharacterMapping).where(CharacterMapping.translation_project_id == project_id)
#         result = await self.db.execute(stmt)
#         mappings = result.scalars().all()
#
#         mapping_dict = {}
#         for mapping in mappings:
#             mapping_dict[mapping.original_name] = mapping.translated_name
#             # 添加别名映射
#             for alt_name in mapping.alternative_names:
#                 mapping_dict[alt_name] = mapping.translated_name
#
#         return mapping_dict
#
#     async def _update_project_progress(self, project_id: uuid.UUID):
#         """更新项目进度"""
#         # 获取完成的章节数
#         completed_stmt = (
#             select(func.count())
#             .select_from(TranslatedChapter)
#             .where(
#                 and_(
#                     TranslatedChapter.translation_project_id == project_id,
#                     TranslatedChapter.status == TaskStatusEnum.COMPLETED
#                 )
#             )
#         )
#         completed_result = await self.db.execute(completed_stmt)
#         completed_count = completed_result.scalar()
#
#         # 更新项目进度
#         project = await self.get(project_id)
#         if project:
#             project.completed_chapters = completed_count
#             if project.total_chapters > 0:
#                 project.progress = (completed_count / project.total_chapters) * 100
#
#             await self.db.commit()
#
#     async def _check_project_completion(self, project_id: uuid.UUID):
#         """检查项目是否完成"""
#         project = await self.get(project_id)
#         if not project:
#             return
#
#         # 检查是否还有未完成的任务
#         pending_tasks_stmt = (
#             select(func.count())
#             .select_from(TranslationTask)
#             .where(
#                 and_(
#                     TranslationTask.translation_project_id == project_id,
#                     TranslationTask.status.in_([TaskStatusEnum.PENDING, TaskStatusEnum.RUNNING])
#                 )
#             )
#         )
#         pending_result = await self.db.execute(pending_tasks_stmt)
#         pending_count = pending_result.scalar()
#
#         if pending_count == 0:
#             # 所有任务完成，更新项目状态
#             project.status = ProjectStatusEnum.COMPLETED
#             project.completed_at = datetime.utcnow()
#             project.progress = 100
#
#             await self.db.commit()
#
#             # 清除缓存
#             await self._invalidate_project_cache(project_id)
#
#     async def _estimate_project_cost(self, project_id: uuid.UUID):
#         """估算项目成本"""
#         # 简化的成本估算逻辑
#         project = await self.get(project_id)
#         if not project:
#             return
#
#         # 根据章节数和平均字数估算
#         estimated_cost = project.total_chapters * 0.5  # 每章0.5美元的估算
#         project.estimated_cost = estimated_cost
#
#         # 估算完成时间（假设每章需要5分钟）
#         estimated_minutes = project.total_chapters * 5
#         project.estimated_completion_time = datetime.utcnow() + timedelta(minutes=estimated_minutes)
#
#         await self.db.commit()
#
#     async def _analyze_characters(self, project_id: uuid.UUID):
#         """分析角色名称"""
#         # 这里可以实现基于AI的角色名称识别
#         # 简化实现：从章节内容中提取常见的人名模式
#         pass
#
#     async def _get_project_statistics(self, project_id: uuid.UUID) -> Dict[str, Any]:
#         """获取项目统计信息"""
#         # 获取任务统计
#         task_stats_stmt = (
#             select(
#                 TranslationTask.status,
#                 func.count().label('count')
#             )
#             .where(TranslationTask.translation_project_id == project_id)
#             .group_by(TranslationTask.status)
#         )
#         task_stats_result = await self.db.execute(task_stats_stmt)
#         task_stats = {row.status: row.count for row in task_stats_result}
#
#         return {
#             "task_stats": task_stats,
#             "total_tasks": sum(task_stats.values())
#         }
#
#     async def _get_chapter_progress_stats(self, project_id: uuid.UUID) -> Dict[str, int]:
#         """获取章节进度统计"""
#         stmt = (
#             select(
#                 TranslatedChapter.status,
#                 func.count().label('count')
#             )
#             .where(TranslatedChapter.translation_project_id == project_id)
#             .group_by(TranslatedChapter.status)
#         )
#         result = await self.db.execute(stmt)
#         stats = {row.status: row.count for row in result}
#
#         return stats
#
#     async def _get_task_progress_stats(self, project_id: uuid.UUID) -> Dict[str, int]:
#         """获取任务进度统计"""
#         stmt = (
#             select(
#                 TranslationTask.status,
#                 func.count().label('count')
#             )
#             .where(TranslationTask.translation_project_id == project_id)
#             .group_by(TranslationTask.status)
#         )
#         result = await self.db.execute(stmt)
#         stats = {row.status: row.count for row in result}
#
#         return stats
#
#     async def _get_quality_stats(self, project_id: uuid.UUID) -> Dict[str, Any]:
#         """获取质量统计"""
#         stmt = (
#             select(
#                 func.avg(TranslatedChapter.quality_score),
#                 func.count(TranslatedChapter.id).filter(TranslatedChapter.quality_score >= 4.0),
#                 func.count(TranslatedChapter.id).filter(TranslatedChapter.quality_score < 3.0)
#             )
#             .where(TranslatedChapter.translation_project_id == project_id)
#         )
#         result = await self.db.execute(stmt)
#         avg_score, high_quality, low_quality = result.first()
#
#         return {
#             "average_quality": float(avg_score) if avg_score else None,
#             "high_quality_count": high_quality or 0,
#             "low_quality_count": low_quality or 0
#         }
#
#     async def _pause_pending_tasks(self, project_id: uuid.UUID):
#         """暂停待执行的任务"""
#         stmt = (
#             update(TranslationTask)
#             .where(
#                 and_(
#                     TranslationTask.translation_project_id == project_id,
#                     TranslationTask.status == TaskStatusEnum.PENDING
#                 )
#             )
#             .values(status=TaskStatusEnum.PAUSED)
#         )
#         await self.db.execute(stmt)
#         await self.db.commit()
#
#     async def _invalidate_project_cache(self, project_id: uuid.UUID):
#         """清除项目相关缓存"""
#         cache_keys = [
#             f"translation_project:{project_id}",
#             f"translation_progress:{project_id}",
#             f"character_mappings:{project_id}"
#         ]
#
#         for key in cache_keys:
#             await self.cache.delete(key)
#
#
# # app/services/ai_service.py
# """
# AI服务
# 处理与AI模型交互的所有业务逻辑，包括模型调用、请求管理、错误处理等
# """
#
# from typing import Optional, Dict, Any, List
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select, update
# from datetime import datetime
# import uuid
# import json
# import asyncio
# import aiohttp
#
# from ..models import AIModel, TranslationConfig, AIProviderEnum, HealthStatusEnum
# from ..core.exceptions import AIModelNotFoundError, AIServiceError
# from ..utils.cache import CacheManager
# from .base import BaseService
#
#
# class AIService(BaseService[AIModel, None, None]):
#     """AI服务类"""
#
#     def __init__(self, db: AsyncSession, cache: CacheManager):
#         super().__init__(AIModel, db)
#         self.cache = cache
#         self._clients = {}  # 缓存AI客户端
#
#     async def get_available_models(self, capability: Optional[str] = None) -> List[Dict[str, Any]]:
#         """
#         获取可用的AI模型列表
#
#         Args:
#             capability: 能力筛选（如'translation', 'outline_generation'）
#
#         Returns:
#             可用模型列表
#         """
#         cache_key = f"available_models:{capability or 'all'}"
#         cached_models = await self.cache.get(cache_key)
#
#         if cached_models:
#             return cached_models
#
#         stmt = select(AIModel).where(AIModel.is_active == True)
#
#         if capability:
#             stmt = stmt.where(AIModel.capabilities.contains([capability]))
#
#         result = await self.db.execute(stmt)
#         models = result.scalars().all()
#
#         model_list = []
#         for model in models:
#             model_data = {
#                 "id": model.id,
#                 "name": model.name,
#                 "display_name": model.display_name,
#                 "provider": model.provider,
#                 "capabilities": model.capabilities,
#                 "supported_languages": model.supported_languages,
#                 "max_tokens": model.max_tokens,
#                 "health_status": model.health_status,
#                 "is_default": model.is_default
#             }
#             model_list.append(model_data)
#
#         # 缓存结果
#         await self.cache.set(cache_key, model_list, expire=3600)  # 缓存1小时
#
#         return model_list
#
#     async def translate_chapter(
#             self,
#             content: str,
#             title: str,
#             source_language: str,
#             target_language: str,
#             outline: Optional[str] = None,
#             character_mappings: Optional[Dict[str, str]] = None,
#             config: Optional[TranslationConfig] = None
#     ) -> str:
#         """
#         翻译章节内容
#
#         Args:
#             content: 原文内容
#             title: 章节标题
#             source_language: 源语言
#             target_language: 目标语言
#             outline: 章节大纲（可选）
#             character_mappings: 角色映射（可选）
#             config: 翻译配置（可选）
#
#         Returns:
#             翻译后的内容
#         """
#         # 选择合适的翻译模型
#         model = await self._get_best_model_for_task("translation", source_language, target_language)
#
#         if not model:
#             raise AIModelNotFoundError("没有可用的翻译模型")
#
#         # 构建翻译提示词
#         prompt = self._build_translation_prompt(
#             content=content,
#             title=title,
#             source_language=source_language,
#             target_language=target_language,
#             outline=outline,
#             character_mappings=character_mappings,
#             config=config
#         )
#
#         # 调用AI模型
#         try:
#             response = await self._call_ai_model(model, prompt)
#
#             # 记录使用统计
#             await self._record_model_usage(model.id, len(prompt), len(response), 0.01)
#
#             return response
#
#         except Exception as e:
#             raise AIServiceError(f"翻译失败: {str(e)}")
#
#     async def generate_chapter_outline(
#             self,
#             title: str,
#             content: str,
#             language: str = "zh-CN"
#     ) -> str:
#         """
#         生成章节大纲
#
#         Args:
#             title: 章节标题
#             content: 章节内容
#             language: 语言
#
#         Returns:
#             章节大纲
#         """
#         # 选择合适的大纲生成模型
#         model = await self._get_best_model_for_task("outline_generation", language)
#
#         if not model:
#             raise AIModelNotFoundError("没有可用的大纲生成模型")
#
#         # 构建大纲生成提示词
#         prompt = f"""请为以下章节生成简洁的大纲：
#
# 标题：{title}
#
# 内容：
# {content[:2000]}{"..." if len(content) > 2000 else ""}
#
# 请用{language}生成大纲，包含：
# 1. 主要情节要点
# 2. 重要角色出场
# 3. 关键事件发展
# 4. 章节主题总结
#
# 大纲格式：
# - 情节要点1
# - 情节要点2
# - ...
# """
#
#         try:
#             response = await self._call_ai_model(model, prompt)
#
#             # 记录使用统计
#             await self._record_model_usage(model.id, len(prompt), len(response), 0.005)
#
#             return response
#
#         except Exception as e:
#             raise AIServiceError(f"大纲生成失败: {str(e)}")
#
#     async def analyze_characters(
#             self,
#             content: str,
#             language: str = "zh-CN"
#     ) -> List[Dict[str, Any]]:
#         """
#         分析角色名称
#
#         Args:
#             content: 文本内容
#             language: 语言
#
#         Returns:
#             角色分析结果
#         """
#         # 选择合适的角色分析模型
#         model = await self._get_best_model_for_task("character_analysis", language)
#
#         if not model:
#             raise AIModelNotFoundError("没有可用的角色分析模型")
#
#         # 构建角色分析提示词
#         prompt = f"""请分析以下文本中的角色名称：
#
# {content[:3000]}{"..." if len(content) > 3000 else ""}
#
# 请以JSON格式返回角色信息，包含：
# - name: 角色名称
# - type: 角色类型 (protagonist/antagonist/supporting/background)
# - importance: 重要程度 (1-10)
# - description: 简短描述
#
# 示例格式：
# [
#   {{
#     "name": "张三",
#     "type": "protagonist",
#     "importance": 9,
#     "description": "主角，年轻的武者"
#   }}
# ]
# """
#
#         try:
#             response = await self._call_ai_model(model, prompt)
#
#             # 尝试解析JSON响应
#             try:
#                 characters = json.loads(response)
#                 if isinstance(characters, list):
#                     return characters
#             except json.JSONDecodeError:
#                 pass
#
#             # 如果JSON解析失败，返回空列表
#             return []
#
#         except Exception as e:
#             raise AIServiceError(f"角色分析失败: {str(e)}")
#
#     async def check_translation_quality(
#             self,
#             original_content: str,
#             translated_content: str,
#             title: str
#     ) -> Dict[str, Any]:
#         """
#         检查翻译质量
#
#         Args:
#             original_content: 原文内容
#             translated_content: 翻译内容
#             title: 标题
#
#         Returns:
#             质量检查结果
#         """
#         # 选择合适的质量检查模型
#         model = await self._get_best_model_for_task("quality_check")
#
#         if not model:
#             raise AIModelNotFoundError("没有可用的质量检查模型")
#
#         # 构建质量检查提示词
#         prompt = f"""请评估以下翻译的质量：
#
# 标题：{title}
#
# 原文：
# {original_content[:1000]}{"..." if len(original_content) > 1000 else ""}
#
# 译文：
# {translated_content[:1000]}{"..." if len(translated_content) > 1000 else ""}
#
# 请从以下维度评分（1-5分）并以JSON格式返回：
# - accuracy: 准确性
# - fluency: 流畅性
# - consistency: 一致性
# - cultural_adaptation: 文化适应性
# - overall: 整体评分
#
# 同时列出发现的问题：
# - issues: 问题列表
#
# 示例格式：
# {{
#   "score": 4.2,
#   "details": {{
#     "accuracy": 4,
#     "fluency": 4,
#     "consistency": 5,
#     "cultural_adaptation": 4
#   }},
#   "issues": ["角色名称不一致", "个别句子表达不够自然"]
# }}
# """
#
#         try:
#             response = await self._call_ai_model(model, prompt)
#
#             # 尝试解析JSON响应
#             try:
#                 result = json.loads(response)
#                 return result
#             except json.JSONDecodeError:
#                 # 如果JSON解析失败，返回默认结果
#                 return {
#                     "score": 3.0,
#                     "details": {},
#                     "issues": ["质量检查响应格式错误"]
#                 }
#
#         except Exception as e:
#             raise AIServiceError(f"质量检查失败: {str(e)}")
#
#     async def test_model_connection(self, model_id: uuid.UUID) -> Dict[str, Any]:
#         """
#         测试AI模型连接
#
#         Args:
#             model_id: 模型ID
#
#         Returns:
#             测试结果
#         """
#         model = await self.get(model_id)
#         if not model:
#             raise AIModelNotFoundError("AI模型不存在")
#
#         try:
#             # 发送简单的测试请求
#             test_prompt = "请回复'连接测试成功'"
#             start_time = datetime.utcnow()
#
#             response = await self._call_ai_model(model, test_prompt)
#
#             end_time = datetime.utcnow()
#             response_time = (end_time - start_time).total_seconds()
#
#             # 更新模型健康状态
#             model.health_status = HealthStatusEnum.HEALTHY
#             model.last_health_check = datetime.utcnow()
#             await self.db.commit()
#
#             return {
#                 "success": True,
#                 "response_time": response_time,
#                 "response": response[:100],
#                 "health_status": "healthy"
#             }
#
#         except Exception as e:
#             # 更新模型健康状态
#             model.health_status = HealthStatusEnum.UNHEALTHY
#             model.last_health_check = datetime.utcnow()
#             await self.db.commit()
#
#             return {
#                 "success": False,
#                 "error": str(e),
#                 "health_status": "unhealthy"
#             }
#
#     # 私有方法
#
#     async def _get_best_model_for_task(
#             self,
#             capability: str,
#             source_language: str = None,
#             target_language: str = None
#     ) -> Optional[AIModel]:
#         """获取最适合任务的模型"""
#         stmt = (
#             select(AIModel)
#             .where(
#                 and_(
#                     AIModel.is_active == True,
#                     AIModel.capabilities.contains([capability]),
#                     AIModel.health_status == HealthStatusEnum.HEALTHY
#                 )
#             )
#             .order_by(AIModel.is_default.desc(), AIModel.total_requests.asc())
#         )
#
#         # 语言筛选
#         if source_language or target_language:
#             languages_to_check = []
#             if source_language:
#                 languages_to_check.append(source_language)
#             if target_language:
#                 languages_to_check.append(target_language)
#
#             if languages_to_check:
#                 stmt = stmt.where(
#                     or_(*[AIModel.supported_languages.contains([lang]) for lang in languages_to_check])
#                 )
#
#         result = await self.db.execute(stmt)
#         return result.scalars().first()
#
#     def _build_translation_prompt(
#             self,
#             content: str,
#             title: str,
#             source_language: str,
#             target_language: str,
#             outline: Optional[str] = None,
#             character_mappings: Optional[Dict[str, str]] = None,
#             config: Optional[TranslationConfig] = None
#     ) -> str:
#         """构建翻译提示词"""
#         # 语言映射
#         language_names = {
#             "zh-CN": "中文",
#             "en-US": "英文",
#             "ja-JP": "日文",
#             "ko-KR": "韩文"
#         }
#
#         source_lang_name = language_names.get(source_language, source_language)
#         target_lang_name = language_names.get(target_language, target_language)
#
#         prompt = f"""请将以下{source_lang_name}小说章节翻译成{target_lang_name}：
#
# 章节标题：{title}
#
# """
#
#         # 添加大纲（如果有）
#         if outline:
#             prompt += f"""章节大纲：
# {outline}
#
# """
#
#         # 添加角色映射（如果有）
#         if character_mappings:
#             prompt += "角色名称对照：\n"
#             for original, translated in character_mappings.items():
#                 prompt += f"- {original} → {translated}\n"
#             prompt += "\n"
#
#         # 添加翻译要求
#         prompt += f"""翻译要求：
# 1. 保持原文的文学风格和语调
# 2. 确保角色名称翻译一致
# 3. 适当本地化文化背景
# 4. 保持段落结构不变
# 5. 翻译要自然流畅
#
# 章节内容：
# {content}
#
# 请直接输出翻译结果，不要添加额外说明："""
#
#         return prompt
#
#     async def _call_ai_model(self, model: AIModel, prompt: str) -> str:
#         """调用AI模型"""
#         if model.provider == AIProviderEnum.DEEPSEEK:
#             return await self._call_deepseek_api(model, prompt)
#         elif model.provider == AIProviderEnum.ZHIPU:
#             return await self._call_zhipu_api(model, prompt)
#         elif model.provider == AIProviderEnum.OLLAMA:
#             return await self._call_ollama_api(model, prompt)
#         else:
#             raise AIServiceError(f"不支持的AI提供商: {model.provider}")
#
#     async def _call_deepseek_api(self, model: AIModel, prompt: str) -> str:
#         """调用DeepSeek API"""
#         # 这里应该实现实际的DeepSeek API调用
#         # 为了演示，返回模拟响应
#         await asyncio.sleep(0.1)  # 模拟网络延迟
#         return f"[DeepSeek模拟响应] {prompt[:50]}... 的翻译结果"
#
#     async def _call_zhipu_api(self, model: AIModel, prompt: str) -> str:
#         """调用智谱AI API"""
#         # 这里应该实现实际的智谱AI API调用
#         await asyncio.sleep(0.1)  # 模拟网络延迟
#         return f"[智谱AI模拟响应] {prompt[:50]}... 的处理结果"
#
#     async def _call_ollama_api(self, model: AIModel, prompt: str) -> str:
#         """调用Ollama API"""
#         # 这里应该实现实际的Ollama API调用
#         await asyncio.sleep(0.1)  # 模拟网络延迟
#         return f"[Ollama模拟响应] {prompt[:50]}... 的本地处理结果"
#
#     async def _record_model_usage(
#             self,
#             model_id: uuid.UUID,
#             input_tokens: int,
#             output_tokens: int,
#             cost: float
#     ):
#         """记录模型使用统计"""
#         stmt = (
#             update(AIModel)
#             .where(AIModel.id == model_id)
#             .values(
#                 total_requests=AIModel.total_requests + 1,
#                 total_tokens=AIModel.total_tokens + input_tokens + output_tokens,
#                 total_cost=AIModel.total_cost + cost
#             )
#         )
#         await self.db.execute(stmt)
#         await self.db.commit()