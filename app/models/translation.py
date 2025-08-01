"""
翻译相关数据模型
包含AI模型配置、翻译项目、翻译配置、角色映射等模型
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DECIMAL, Text,
    TIMESTAMP, ForeignKey, JSON, CheckConstraint, BigInteger
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .base import Base


class AIModel(Base):
    """AI模型配置表"""
    __tablename__ = "ai_models"

    # 模型基础信息
    name = Column(String(100), nullable=False, unique=True, comment="模型名称")
    display_name = Column(String(100), nullable=False, comment="显示名称")
    provider = Column(String(50), nullable=False, comment="提供商")
    model_id = Column(String(100), nullable=False, comment="模型ID")
    version = Column(String(50), comment="版本")

    # 模型能力
    capabilities = Column(JSON, default=[], comment="模型能力")
    supported_languages = Column(JSON, default=[], comment="支持的语言")

    # 性能参数
    max_tokens = Column(Integer, default=4000, comment="最大tokens")
    max_requests_per_minute = Column(Integer, default=60, comment="每分钟最大请求数")
    max_requests_per_day = Column(Integer, default=10000, comment="每天最大请求数")
    max_concurrent_requests = Column(Integer, default=5, comment="最大并发请求数")

    # API配置
    api_endpoint = Column(String(200), comment="API端点")
    api_version = Column(String(20), comment="API版本")
    timeout_seconds = Column(Integer, default=30, comment="超时时间")

    # 成本配置
    cost_per_1k_input_tokens = Column(DECIMAL(8, 6), default=0, comment="千输入tokens成本")
    cost_per_1k_output_tokens = Column(DECIMAL(8, 6), default=0, comment="千输出tokens成本")

    # 质量配置
    default_temperature = Column(DECIMAL(3, 2), default=0.7, comment="默认温度")
    default_top_p = Column(DECIMAL(3, 2), default=0.9, comment="默认top_p")

    # 状态管理
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_default = Column(Boolean, default=False, comment="是否默认")
    health_status = Column(String(20), default='unknown', comment="健康状态")
    last_health_check = Column(TIMESTAMP(timezone=True), comment="最后健康检查时间")

    # 使用统计
    total_requests = Column(BigInteger, default=0, comment="总请求数")
    total_tokens = Column(BigInteger, default=0, comment="总tokens")
    total_cost = Column(DECIMAL(12, 4), default=0, comment="总成本")

    # 约束
    __table_args__ = (
        CheckConstraint("provider IN ('deepseek', 'zhipu', 'ollama')", name='ai_model_provider_check'),
        CheckConstraint("health_status IN ('healthy', 'degraded', 'unhealthy', 'unknown')",
                        name='ai_model_health_check'),
    )


class TranslationConfig(Base):
    """翻译配置模板表"""
    __tablename__ = "translation_configs"

    # 基础信息
    name = Column(String(100), nullable=False, comment="配置名称")
    description = Column(Text, comment="配置描述")
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), comment="创建者")

    # 语言配置
    source_language = Column(String(10), nullable=False, default='zh-CN', comment="源语言")
    target_language = Column(String(10), nullable=False, default='en-US', comment="目标语言")

    # AI模型配置
    outline_model_id = Column(UUID(as_uuid=True), ForeignKey('ai_models.id'), comment="大纲模型ID")
    translation_model_id = Column(UUID(as_uuid=True), ForeignKey('ai_models.id'), comment="翻译模型ID")
    review_model_id = Column(UUID(as_uuid=True), ForeignKey('ai_models.id'), comment="审核模型ID")

    # 翻译策略
    translation_strategy = Column(String(50), default='direct', comment="翻译策略")

    # 处理选项
    generate_outline = Column(Boolean, default=True, comment="生成大纲")
    rewrite_based_on_outline = Column(Boolean, default=True, comment="基于大纲重写")
    preserve_formatting = Column(Boolean, default=True, comment="保持格式")
    translate_character_names = Column(Boolean, default=True, comment="翻译角色名")
    use_character_mapping = Column(Boolean, default=True, comment="使用角色映射")
    maintain_cultural_context = Column(Boolean, default=True, comment="保持文化背景")

    # 质量控制
    enable_quality_check = Column(Boolean, default=True, comment="启用质量检查")
    quality_threshold = Column(DECIMAL(3, 2), default=3.5, comment="质量阈值")
    max_retry_count = Column(Integer, default=3, comment="最大重试次数")

    # 风格设置
    writing_style = Column(String(50), default='literary', comment="写作风格")
    tone = Column(String(50), default='neutral', comment="语调")
    target_audience = Column(String(50), default='general', comment="目标受众")

    # 处理参数
    batch_size = Column(Integer, default=1, comment="批处理大小")
    delay_between_requests = Column(Integer, default=2, comment="请求间延迟")
    max_parallel_tasks = Column(Integer, default=3, comment="最大并行任务")

    # 自定义提示词
    custom_prompts = Column(JSON, default={}, comment="自定义提示词")

    # 状态
    is_default = Column(Boolean, default=False, comment="是否默认")
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_public = Column(Boolean, default=False, comment="是否公开")

    # 约束
    __table_args__ = (
        CheckConstraint("translation_strategy IN ('direct', 'outline_based', 'multi_pass')",
                        name='translation_strategy_check'),
        CheckConstraint("writing_style IN ('formal', 'casual', 'literary', 'technical')", name='writing_style_check'),
        CheckConstraint("tone IN ('neutral', 'serious', 'humorous', 'dramatic')", name='tone_check'),
        CheckConstraint("target_audience IN ('children', 'young_adult', 'adult', 'general')",
                        name='target_audience_check'),
        CheckConstraint('batch_size BETWEEN 1 AND 10', name='batch_size_check'),
    )

    # 关联关系
    creator = relationship("User")
    outline_model = relationship("AIModel", foreign_keys=[outline_model_id])
    translation_model = relationship("AIModel", foreign_keys=[translation_model_id])
    review_model = relationship("AIModel", foreign_keys=[review_model_id])


class TranslationProject(Base):
    """翻译项目表"""
    __tablename__ = "translation_projects"

    # 项目基础信息
    name = Column(String(200), nullable=False, comment="项目名称")
    description = Column(Text, comment="项目描述")
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'),
                        nullable=False, comment="创建者")

    # 源小说信息
    source_novel_id = Column(UUID(as_uuid=True), ForeignKey('novels.id', ondelete='CASCADE'),
                             nullable=False, comment="源小说ID")
    source_language = Column(String(10), nullable=False, default='zh-CN', comment="源语言")
    target_language = Column(String(10), nullable=False, default='en-US', comment="目标语言")

    # 翻译配置
    config_id = Column(UUID(as_uuid=True), ForeignKey('translation_configs.id'),
                       nullable=False, comment="配置ID")
    custom_config = Column(JSON, default={}, comment="自定义配置")

    # 进度信息
    status = Column(String(20), default='created', comment="状态")
    progress = Column(DECIMAL(5, 2), default=0, comment="进度百分比")

    # 章节信息
    total_chapters = Column(Integer, default=0, comment="总章节数")
    completed_chapters = Column(Integer, default=0, comment="完成章节数")
    failed_chapters = Column(Integer, default=0, comment="失败章节数")

    # 翻译范围
    start_chapter = Column(Integer, default=1, comment="开始章节")
    end_chapter = Column(Integer, comment="结束章节")
    chapter_filter = Column(JSON, comment="章节过滤")

    # 质量统计
    average_quality_score = Column(DECIMAL(3, 2), comment="平均质量分")
    quality_issues_count = Column(Integer, default=0, comment="质量问题数")

    # 成本统计
    estimated_cost = Column(DECIMAL(10, 4), default=0, comment="预估成本")
    actual_cost = Column(DECIMAL(10, 4), default=0, comment="实际成本")
    tokens_used = Column(BigInteger, default=0, comment="使用tokens")

    # 时间统计
    estimated_completion_time = Column(TIMESTAMP(timezone=True), comment="预计完成时间")
    actual_completion_time = Column(TIMESTAMP(timezone=True), comment="实际完成时间")
    total_processing_time = Column(Integer, default=0, comment="总处理时间(秒)")

    # 输出配置
    output_format = Column(String(20), default='database', comment="输出格式")
    output_path = Column(String(500), comment="输出路径")

    # 状态时间戳
    started_at = Column(TIMESTAMP(timezone=True), comment="开始时间")
    paused_at = Column(TIMESTAMP(timezone=True), comment="暂停时间")
    completed_at = Column(TIMESTAMP(timezone=True), comment="完成时间")
    failed_at = Column(TIMESTAMP(timezone=True), comment="失败时间")

    # 约束
    __table_args__ = (
        CheckConstraint(
            "status IN ('created', 'analyzing', 'translating', 'reviewing', 'completed', 'paused', 'failed', 'cancelled')",
            name='translation_project_status_check'),
        CheckConstraint('progress BETWEEN 0 AND 100', name='translation_progress_check'),
        CheckConstraint("output_format IN ('database', 'file', 'both')", name='output_format_check'),
    )

    # 关联关系
    creator = relationship("User")
    source_novel = relationship("Novel")
    config = relationship("TranslationConfig")
    translated_novels = relationship("TranslatedNovel", back_populates="project")
    character_mappings = relationship("CharacterMapping", back_populates="project")
    translated_chapters = relationship("TranslatedChapter", back_populates="project")
    tasks = relationship("TranslationTask", back_populates="project")


class TranslatedNovel(Base):
    """翻译后小说表"""
    __tablename__ = "translated_novels"

    # 关联信息
    original_novel_id = Column(UUID(as_uuid=True), ForeignKey('novels.id', ondelete='CASCADE'),
                               nullable=False, comment="原小说ID")
    translation_project_id = Column(UUID(as_uuid=True), ForeignKey('translation_projects.id', ondelete='CASCADE'),
                                    nullable=False, unique=True, comment="翻译项目ID")

    # 翻译后的内容
    title = Column(String(200), nullable=False, comment="标题")
    subtitle = Column(String(200), comment="副标题")
    description = Column(Text, comment="描述")
    cover_url = Column(String(500), comment="封面URL")

    # 作者信息(翻译后)
    translated_author_name = Column(String(100), comment="翻译后作者名")
    translator_notes = Column(Text, comment="译者注")

    # 语言和分类
    language = Column(String(10), nullable=False, comment="语言")
    category_id = Column(UUID(as_uuid=True), ForeignKey('categories.id'), comment="分类ID")

    # 内容统计
    word_count = Column(BigInteger, default=0, comment="字数")
    chapter_count = Column(Integer, default=0, comment="章节数")

    # 翻译质量
    overall_quality_score = Column(DECIMAL(3, 2), comment="整体质量分")
    review_status = Column(String(20), default='pending', comment="审核状态")

    # 发布状态
    is_published = Column(Boolean, default=False, comment="是否发布")
    publish_status = Column(String(20), default='draft', comment="发布状态")
    published_at = Column(TIMESTAMP(timezone=True), comment="发布时间")

    # SEO信息
    seo_title = Column(String(200), comment="SEO标题")
    seo_description = Column(Text, comment="SEO描述")
    seo_keywords = Column(String(500), comment="SEO关键词")

    # 约束
    __table_args__ = (
        CheckConstraint("review_status IN ('pending', 'approved', 'rejected', 'needs_revision')",
                        name='translated_novel_review_status_check'),
        CheckConstraint("publish_status IN ('draft', 'reviewing', 'published', 'hidden')",
                        name='translated_novel_publish_status_check'),
    )

    # 关联关系
    original_novel = relationship("Novel")
    project = relationship("TranslationProject", back_populates="translated_novels")
    category = relationship("Category")
    chapters = relationship("TranslatedChapter", back_populates="novel")


class CharacterMapping(Base):
    """角色映射表"""
    __tablename__ = "character_mappings"

    translation_project_id = Column(UUID(as_uuid=True), ForeignKey('translation_projects.id', ondelete='CASCADE'),
                                    nullable=False, comment="翻译项目ID")

    # 角色信息
    original_name = Column(String(100), nullable=False, comment="原名")
    translated_name = Column(String(100), nullable=False, comment="译名")
    alternative_names = Column(JSON, default=[], comment="别名列表")

    # 角色分类
    character_type = Column(String(50), default='character', comment="角色类型")
    importance_level = Column(Integer, default=5, comment="重要程度")

    # 角色描述
    description = Column(Text, comment="角色描述")
    personality_traits = Column(JSON, default=[], comment="性格特征")
    relationships = Column(JSON, default={}, comment="角色关系")

    # 出现信息
    first_appearance_chapter = Column(Integer, comment="首次出现章节")
    last_appearance_chapter = Column(Integer, comment="最后出现章节")
    appearance_frequency = Column(Integer, default=0, comment="出现频率")

    # 映射质量
    mapping_confidence = Column(DECIMAL(3, 2), default=1.0, comment="映射置信度")
    is_verified = Column(Boolean, default=False, comment="是否已验证")
    verified_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), comment="验证者")
    verification_notes = Column(Text, comment="验证备注")

    # 自动检测信息
    auto_detected = Column(Boolean, default=False, comment="是否自动检测")
    detection_method = Column(String(50), comment="检测方法")

    # 约束
    __table_args__ = (
        CheckConstraint(
            "character_type IN ('protagonist', 'antagonist', 'supporting', 'background', 'place', 'organization', 'item')",
            name='character_type_check'),
        CheckConstraint('importance_level BETWEEN 1 AND 10', name='importance_level_check'),
        CheckConstraint('mapping_confidence BETWEEN 0 AND 1', name='mapping_confidence_check'),
        {"postgresql_index": [("translation_project_id", "original_name")]},
    )

    # 关联关系
    project = relationship("TranslationProject", back_populates="character_mappings")
    verifier = relationship("User")


class TranslatedChapter(Base):
    """翻译后章节表"""
    __tablename__ = "translated_chapters"

    # 关联信息
    original_chapter_id = Column(UUID(as_uuid=True), ForeignKey('chapters.id', ondelete='CASCADE'),
                                 nullable=False, comment="原章节ID")
    translated_novel_id = Column(UUID(as_uuid=True), ForeignKey('translated_novels.id', ondelete='CASCADE'),
                                 nullable=False, comment="翻译小说ID")
    translation_project_id = Column(UUID(as_uuid=True), ForeignKey('translation_projects.id', ondelete='CASCADE'),
                                    nullable=False, comment="翻译项目ID")

    # 章节基础信息
    title = Column(String(200), nullable=False, comment="标题")
    chapter_number = Column(Integer, nullable=False, comment="章节号")
    volume_number = Column(Integer, default=1, comment="卷号")

    # 翻译内容
    content = Column(Text, comment="内容")
    outline = Column(Text, comment="AI生成的大纲")
    summary = Column(Text, comment="章节摘要")
    translator_notes = Column(Text, comment="译者注")

    # 翻译过程信息
    translation_method = Column(String(50), default='ai_direct', comment="翻译方法")
    ai_model_used = Column(String(100), comment="使用的AI模型")
    prompt_used = Column(Text, comment="使用的提示词")

    # 处理统计
    input_tokens = Column(Integer, default=0, comment="输入tokens")
    output_tokens = Column(Integer, default=0, comment="输出tokens")
    processing_time_seconds = Column(Integer, default=0, comment="处理时间(秒)")
    word_count = Column(Integer, default=0, comment="字数")

    # 质量控制
    quality_score = Column(DECIMAL(3, 2), comment="质量分")
    quality_details = Column(JSON, default={}, comment="质量详情")
    quality_issues = Column(JSON, default=[], comment="质量问题")

    # 审核状态
    review_status = Column(String(20), default='pending', comment="审核状态")
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), comment="审核者")
    reviewer_notes = Column(Text, comment="审核备注")
    reviewed_at = Column(TIMESTAMP(timezone=True), comment="审核时间")

    # 处理状态
    status = Column(String(20), default='pending', comment="状态")
    retry_count = Column(Integer, default=0, comment="重试次数")
    error_message = Column(Text, comment="错误信息")

    # 版本控制
    version_number = Column(Integer, default=1, comment="版本号")
    is_latest_version = Column(Boolean, default=True, comment="是否最新版本")

    # 约束
    __table_args__ = (
        CheckConstraint("translation_method IN ('ai_direct', 'ai_outline_based', 'hybrid', 'manual')",
                        name='translation_method_check'),
        CheckConstraint("review_status IN ('pending', 'approved', 'rejected', 'needs_revision')",
                        name='translated_chapter_review_status_check'),
        CheckConstraint(
            "status IN ('pending', 'outline_generating', 'translating', 'quality_checking', 'completed', 'failed', 'reviewing')",
            name='translated_chapter_status_check'),
        {"postgresql_index": [("translation_project_id", "original_chapter_id", "version_number")]},
    )

    # 关联关系
    original_chapter = relationship("Chapter")
    novel = relationship("TranslatedNovel", back_populates="chapters")
    project = relationship("TranslationProject", back_populates="translated_chapters")
    reviewer = relationship("User")


class TranslationTask(Base):
    """翻译任务队列表"""
    __tablename__ = "translation_tasks"

    # 任务基础信息
    translation_project_id = Column(UUID(as_uuid=True), ForeignKey('translation_projects.id', ondelete='CASCADE'),
                                    nullable=False, comment="翻译项目ID")
    task_type = Column(String(20), nullable=False, comment="任务类型")
    priority = Column(Integer, default=5, comment="优先级")

    # 任务目标
    target_type = Column(String(20), nullable=False, comment="目标类型")
    target_id = Column(UUID(as_uuid=True), nullable=False, comment="目标ID")

    # 任务配置
    task_config = Column(JSON, default={}, comment="任务配置")

    # 执行信息
    status = Column(String(20), default='pending', comment="状态")
    worker_id = Column(String(100), comment="工作者ID")
    started_at = Column(TIMESTAMP(timezone=True), comment="开始时间")
    completed_at = Column(TIMESTAMP(timezone=True), comment="完成时间")

    # 进度信息
    progress = Column(DECIMAL(5, 2), default=0, comment="进度")
    current_step = Column(String(100), comment="当前步骤")
    total_steps = Column(Integer, default=1, comment="总步骤")
    completed_steps = Column(Integer, default=0, comment="完成步骤")

    # 结果信息
    result = Column(JSON, default={}, comment="结果")
    error_message = Column(Text, comment="错误信息")
    error_code = Column(String(50), comment="错误代码")
    stack_trace = Column(Text, comment="堆栈跟踪")

    # 重试配置
    retry_count = Column(Integer, default=0, comment="重试次数")
    max_retries = Column(Integer, default=3, comment="最大重试次数")
    retry_delay_seconds = Column(Integer, default=60, comment="重试延迟(秒)")

    # 依赖关系
    depends_on = Column(UUID(as_uuid=True), ForeignKey('translation_tasks.id'), comment="依赖任务")

    # 资源使用
    estimated_cost = Column(DECIMAL(8, 4), default=0, comment="预估成本")
    actual_cost = Column(DECIMAL(8, 4), default=0, comment="实际成本")
    tokens_used = Column(Integer, default=0, comment="使用tokens")

    # 约束
    __table_args__ = (
        CheckConstraint("task_type IN ('outline', 'translate', 'review', 'character_map', 'quality_check')",
                        name='task_type_check'),
        CheckConstraint('priority BETWEEN 1 AND 10', name='task_priority_check'),
        CheckConstraint("target_type IN ('novel', 'chapter', 'batch')", name='task_target_type_check'),
        CheckConstraint("status IN ('pending', 'running', 'completed', 'failed', 'cancelled', 'paused')",
                        name='task_status_check'),
    )

    # 关联关系
    project = relationship("TranslationProject", back_populates="tasks")
    dependency = relationship("TranslationTask", remote_side="TranslationTask.id")