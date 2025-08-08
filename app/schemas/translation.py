"""
翻译相关数据模式
定义翻译项目、配置、任务等请求和响应的数据结构
"""

from pydantic import \1, ConfigDictng import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
import uuid


# AI模型相关
class AIModelResponse(BaseModel):
    """AI模型响应"""
    id: uuid.UUID = Field(..., description="模型ID")
    name: str = Field(..., description="模型名称")
    display_name: str = Field(..., description="显示名称")
    provider: str = Field(..., description="提供商")
    models_id: str = Field(..., description="模型ID")
    version: Optional[str] = Field(None, description="版本")
    capabilities: List[str] = Field(..., description="模型能力")
    supported_languages: List[str] = Field(..., description="支持的语言")
    max_tokens: int = Field(..., description="最大tokens")
    cost_per_1k_input_tokens: Decimal = Field(..., description="千输入tokens成本")
    cost_per_1k_output_tokens: Decimal = Field(..., description="千输出tokens成本")
    is_active: bool = Field(..., description="是否激活")
    is_default: bool = Field(..., description="是否默认")
    health_status: str = Field(..., description="健康状态")

    class Config:
        protected_namespaces = ()
        from_attributes = True


class AIModelTestRequest(BaseModel):
    """AI模型测试请求"""
    models_id: uuid.UUID = Field(..., description="模型ID")
    test_text: str = Field(..., min_length=1, max_length=1000, description="测试文本")

    class Config:
        protected_namespaces = ()
        json_schema_extra = {
            "example": {
                "models_id": "123e4567-e89b-12d3-a456-426614174000",
                "test_text": "Hello, world!"
            }
        }


class AIModelTestResponse(BaseModel):
    """AI模型测试响应"""
    success: bool = Field(..., description="是否成功")
    response_text: Optional[str] = Field(None, description="响应文本")
    response_time: float = Field(..., description="响应时间(秒)")
    tokens_used: int = Field(..., description="使用tokens")
    error_message: Optional[str] = Field(None, description="错误信息")

    class Config:
        protected_namespaces = ()
        json_schema_extra = {
            "example": {
                "success": True,
                "response_text": "你好，世界！",
                "response_time": 1.5,
                "tokens_used": 10,
                "error_message": None
            }
        }


# 翻译配置相关
class TranslationConfigCreateRequest(BaseModel):
    """翻译配置创建请求"""
    name: str = Field(..., min_length=1, max_length=100, description="配置名称")
    description: Optional[str] = Field(None, description="配置描述")
    source_language: str = Field(..., description="源语言")
    target_language: str = Field(..., description="目标语言")

    # AI模型配置
    outline_models_id: Optional[uuid.UUID] = Field(None, description="大纲模型ID")
    translation_models_id: Optional[uuid.UUID] = Field(None, description="翻译模型ID")
    review_models_id: Optional[uuid.UUID] = Field(None, description="审核模型ID")

    # 翻译策略
    translation_strategy: str = Field(default='direct', description="翻译策略")

    # 处理选项
    generate_outline: bool = Field(default=True, description="生成大纲")
    rewrite_based_on_outline: bool = Field(default=True, description="基于大纲重写")
    preserve_formatting: bool = Field(default=True, description="保持格式")
    translate_character_names: bool = Field(default=True, description="翻译角色名")
    use_character_mapping: bool = Field(default=True, description="使用角色映射")
    maintain_cultural_context: bool = Field(default=True, description="保持文化背景")

    # 质量控制
    enable_quality_check: bool = Field(default=True, description="启用质量检查")
    quality_threshold: Decimal = Field(default=3.5, ge=0, le=5, description="质量阈值")
    max_retry_count: int = Field(default=3, ge=0, le=10, description="最大重试次数")

    # 风格设置
    writing_style: str = Field(default='literary', description="写作风格")
    tone: str = Field(default='neutral', description="语调")
    target_audience: str = Field(default='general', description="目标受众")

    # 处理参数
    batch_size: int = Field(default=1, ge=1, le=10, description="批处理大小")
    delay_between_requests: int = Field(default=2, ge=0, description="请求间延迟")
    max_parallel_tasks: int = Field(default=3, ge=1, le=10, description="最大并行任务")

    # 自定义提示词
    custom_prompts: Optional[Dict[str, str]] = Field(None, description="自定义提示词")

    is_public: bool = Field(default=False, description="是否公开")

    @validator('translation_strategy')
    def validate_translation_strategy(cls, v):
        if v not in ['direct', 'outline_based', 'multi_pass']:
            raise ValueError('翻译策略只能是direct、outline_based或multi_pass')
        return v

    @validator('writing_style')
    def validate_writing_style(cls, v):
        if v not in ['formal', 'casual', 'literary', 'technical']:
            raise ValueError('写作风格只能是formal、casual、literary或technical')
        return v

    @validator('tone')
    def validate_tone(cls, v):
        if v not in ['neutral', 'serious', 'humorous', 'dramatic']:
            raise ValueError('语调只能是neutral、serious、humorous或dramatic')
        return v

    @validator('target_audience')
    def validate_target_audience(cls, v):
        if v not in ['children', 'young_adult', 'adult', 'general']:
            raise ValueError('目标受众只能是children、young_adult、adult或general')
        return v

    class Config:
        protected_namespaces = ()
        json_schema_extra = {
            "example": {
                "name": "标准中英翻译",
                "description": "适用于中文小说翻译成英文的标准配置",
                "source_language": "zh-CN",
                "target_language": "en-US",
                "translation_strategy": "outline_based",
                "writing_style": "literary",
                "tone": "neutral",
                "target_audience": "adult"
            }
        }


class TranslationConfigResponse(BaseModel):
    """翻译配置响应"""
    id: uuid.UUID = Field(..., description="配置ID")
    name: str = Field(..., description="配置名称")
    description: Optional[str] = Field(None, description="配置描述")
    source_language: str = Field(..., description="源语言")
    target_language: str = Field(..., description="目标语言")
    translation_strategy: str = Field(..., description="翻译策略")

    # 处理选项
    generate_outline: bool = Field(..., description="生成大纲")
    preserve_formatting: bool = Field(..., description="保持格式")
    translate_character_names: bool = Field(..., description="翻译角色名")

    # 质量控制
    enable_quality_check: bool = Field(..., description="启用质量检查")
    quality_threshold: Decimal = Field(..., description="质量阈值")

    # 风格设置
    writing_style: str = Field(..., description="写作风格")
    tone: str = Field(..., description="语调")
    target_audience: str = Field(..., description="目标受众")

    # 状态
    is_default: bool = Field(..., description="是否默认")
    is_active: bool = Field(..., description="是否激活")
    is_public: bool = Field(..., description="是否公开")

    # AI模型信息
    outline_model: Optional[AIModelResponse] = Field(None, description="大纲模型")
    translation_model: Optional[AIModelResponse] = Field(None, description="翻译模型")
    review_model: Optional[AIModelResponse] = Field(None, description="审核模型")

    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        protected_namespaces = ()
        from_attributes = True


# 翻译项目相关
class TranslationProjectCreateRequest(BaseModel):
    """翻译项目创建请求"""
    name: str = Field(..., min_length=1, max_length=200, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    source_novel_id: uuid.UUID = Field(..., description="源小说ID")
    source_language: str = Field(default='zh-CN', description="源语言")
    target_language: str = Field(default='en-US', description="目标语言")
    config_id: uuid.UUID = Field(..., description="配置ID")

    # 翻译范围
    start_chapter: int = Field(default=1, ge=1, description="开始章节")
    end_chapter: Optional[int] = Field(None, ge=1, description="结束章节")
    chapter_filter: Optional[Dict[str, Any]] = Field(None, description="章节过滤")

    # 输出配置
    output_format: str = Field(default='database', description="输出格式")
    output_path: Optional[str] = Field(None, description="输出路径")

    # 自定义配置覆盖
    custom_config: Optional[Dict[str, Any]] = Field(None, description="自定义配置")

    @validator('output_format')
    def validate_output_format(cls, v):
        if v not in ['database', 'file', 'both']:
            raise ValueError('输出格式只能是database、file或both')
        return v

    class Config:
        protected_namespaces = ()
        json_schema_extra = {
            "example": {
                "name": "《修真世界》英文翻译",
                "description": "将《修真世界》翻译成英文",
                "source_novel_id": "123e4567-e89b-12d3-a456-426614174000",
                "source_language": "zh-CN",
                "target_language": "en-US",
                "config_id": "123e4567-e89b-12d3-a456-426614174001",
                "start_chapter": 1,
                "end_chapter": 100
            }
        }


class TranslationProjectUpdateRequest(BaseModel):
    """翻译项目更新请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    start_chapter: Optional[int] = Field(None, ge=1, description="开始章节")
    end_chapter: Optional[int] = Field(None, ge=1, description="结束章节")
    output_format: Optional[str] = Field(None, description="输出格式")
    output_path: Optional[str] = Field(None, description="输出路径")
    custom_config: Optional[Dict[str, Any]] = Field(None, description="自定义配置")

    @validator('output_format')
    def validate_output_format(cls, v):
        if v and v not in ['database', 'file', 'both']:
            raise ValueError('输出格式只能是database、file或both')
        return v


class TranslationProjectResponse(BaseModel):
    """翻译项目响应"""
    id: uuid.UUID = Field(..., description="项目ID")
    name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    source_language: str = Field(..., description="源语言")
    target_language: str = Field(..., description="目标语言")
    status: str = Field(..., description="状态")
    progress: Decimal = Field(..., description="进度百分比")

    # 章节信息
    total_chapters: int = Field(..., description="总章节数")
    completed_chapters: int = Field(..., description="完成章节数")
    failed_chapters: int = Field(..., description="失败章节数")

    # 翻译范围
    start_chapter: int = Field(..., description="开始章节")
    end_chapter: Optional[int] = Field(None, description="结束章节")

    # 质量统计
    average_quality_score: Optional[Decimal] = Field(None, description="平均质量分")
    quality_issues_count: int = Field(..., description="质量问题数")

    # 成本统计
    estimated_cost: Decimal = Field(..., description="预估成本")
    actual_cost: Decimal = Field(..., description="实际成本")
    tokens_used: int = Field(..., description="使用tokens")

    # 时间统计
    estimated_completion_time: Optional[datetime] = Field(None, description="预计完成时间")
    actual_completion_time: Optional[datetime] = Field(None, description="实际完成时间")
    total_processing_time: int = Field(..., description="总处理时间(秒)")

    # 输出配置
    output_format: str = Field(..., description="输出格式")
    output_path: Optional[str] = Field(None, description="输出路径")

    # 状态时间戳
    started_at: Optional[datetime] = Field(None, description="开始时间")
    paused_at: Optional[datetime] = Field(None, description="暂停时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    failed_at: Optional[datetime] = Field(None, description="失败时间")

    # 关联信息
    source_novel_title: str = Field(..., description="源小说标题")
    config_name: str = Field(..., description="配置名称")
    creator_username: str = Field(..., description="创建者用户名")

    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        protected_namespaces = ()
        from_attributes = True


class TranslationProjectListResponse(BaseModel):
    """翻译项目列表响应"""
    items: List[TranslationProjectResponse] = Field(..., description="项目列表")
    total: int = Field(..., description="总数")
    has_more: bool = Field(..., description="是否有更多")

    class Config:
        protected_namespaces = ()
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 20,
                "has_more": True
            }
        }


# 翻译进度响应
class TranslationProgressResponse(BaseModel):
    """翻译进度响应"""
    project_id: uuid.UUID = Field(..., description="项目ID")
    status: str = Field(..., description="状态")
    progress: Decimal = Field(..., description="进度百分比")
    current_chapter: Optional[int] = Field(None, description="当前章节")

    # 章节统计
    total_chapters: int = Field(..., description="总章节数")
    completed_chapters: int = Field(..., description="完成章节数")
    failed_chapters: int = Field(..., description="失败章节数")

    # 队列统计
    pending_tasks: int = Field(..., description="待处理任务")
    running_tasks: int = Field(..., description="运行中任务")

    # 时间预估
    estimated_remaining_time: Optional[int] = Field(None, description="预计剩余时间(秒)")

    # 最近活动
    recent_activities: List[Dict[str, Any]] = Field(..., description="最近活动")

    class Config:
        protected_namespaces = ()
        json_schema_extra = {
            "example": {
                "project_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "translating",
                "progress": 65.5,
                "current_chapter": 66,
                "total_chapters": 100,
                "completed_chapters": 65,
                "failed_chapters": 1,
                "pending_tasks": 34,
                "running_tasks": 1,
                "estimated_remaining_time": 3600,
                "recent_activities": []
            }
        }


# 角色映射相关
class CharacterMappingCreateRequest(BaseModel):
    """角色映射创建请求"""
    original_name: str = Field(..., min_length=1, max_length=100, description="原名")
    translated_name: str = Field(..., min_length=1, max_length=100, description="译名")
    alternative_names: Optional[List[str]] = Field(None, description="别名列表")
    character_type: str = Field(default='character', description="角色类型")
    importance_level: int = Field(default=5, ge=1, le=10, description="重要程度")
    description: Optional[str] = Field(None, description="角色描述")
    personality_traits: Optional[List[str]] = Field(None, description="性格特征")
    relationships: Optional[Dict[str, str]] = Field(None, description="角色关系")

    @validator('character_type')
    def validate_character_type(cls, v):
        allowed_types = ['protagonist', 'antagonist', 'supporting', 'background', 'place', 'organization', 'item']
        if v not in allowed_types:
            raise ValueError(f'角色类型只能是{", ".join(allowed_types)}')
        return v

    class Config:
        protected_namespaces = ()
        json_schema_extra = {
            "example": {
                "original_name": "李逍遥",
                "translated_name": "Li Xiaoyao",
                "alternative_names": ["逍遥", "小李"],
                "character_type": "protagonist",
                "importance_level": 10,
                "description": "主角，天资聪颖的修仙者"
            }
        }


class CharacterMappingResponse(BaseModel):
    """角色映射响应"""
    id: uuid.UUID = Field(..., description="映射ID")
    original_name: str = Field(..., description="原名")
    translated_name: str = Field(..., description="译名")
    alternative_names: List[str] = Field(..., description="别名列表")
    character_type: str = Field(..., description="角色类型")
    importance_level: int = Field(..., description="重要程度")
    description: Optional[str] = Field(None, description="角色描述")
    personality_traits: List[str] = Field(..., description="性格特征")
    relationships: Dict[str, str] = Field(..., description="角色关系")

    # 出现信息
    first_appearance_chapter: Optional[int] = Field(None, description="首次出现章节")
    last_appearance_chapter: Optional[int] = Field(None, description="最后出现章节")
    appearance_frequency: int = Field(..., description="出现频率")

    # 映射质量
    mapping_confidence: Decimal = Field(..., description="映射置信度")
    is_verified: bool = Field(..., description="是否已验证")
    verification_notes: Optional[str] = Field(None, description="验证备注")

    # 自动检测信息
    auto_detected: bool = Field(..., description="是否自动检测")
    detection_method: Optional[str] = Field(None, description="检测方法")

    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        protected_namespaces = ()
        from_attributes = True


# 翻译任务相关
class TranslationTaskResponse(BaseModel):
    """翻译任务响应"""
    id: uuid.UUID = Field(..., description="任务ID")
    task_type: str = Field(..., description="任务类型")
    priority: int = Field(..., description="优先级")
    target_type: str = Field(..., description="目标类型")
    target_id: uuid.UUID = Field(..., description="目标ID")
    status: str = Field(..., description="状态")
    progress: Decimal = Field(..., description="进度")
    current_step: Optional[str] = Field(None, description="当前步骤")
    total_steps: int = Field(..., description="总步骤")
    completed_steps: int = Field(..., description="完成步骤")

    # 执行信息
    worker_id: Optional[str] = Field(None, description="工作者ID")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")

    # 结果信息
    result: Dict[str, Any] = Field(..., description="结果")
    error_message: Optional[str] = Field(None, description="错误信息")

    # 重试信息
    retry_count: int = Field(..., description="重试次数")
    max_retries: int = Field(..., description="最大重试次数")

    # 资源使用
    estimated_cost: Decimal = Field(..., description="预估成本")
    actual_cost: Decimal = Field(..., description="实际成本")
    tokens_used: int = Field(..., description="使用tokens")

    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        protected_namespaces = ()
        from_attributes = True


# 翻译统计响应
class TranslationStatsResponse(BaseModel):
    """翻译统计响应"""
    project_id: uuid.UUID = Field(..., description="项目ID")
    date: str = Field(..., description="日期")

    # 进度统计
    chapters_completed: int = Field(..., description="完成章节数")
    words_translated: int = Field(..., description="翻译字数")
    characters_mapped: int = Field(..., description="映射角色数")

    # 质量统计
    average_quality_score: Optional[Decimal] = Field(None, description="平均质量分")
    quality_issues_found: int = Field(..., description="发现质量问题数")
    quality_issues_fixed: int = Field(..., description="修复质量问题数")

    # 成本统计
    total_tokens_used: int = Field(..., description="总使用tokens")
    total_cost: Decimal = Field(..., description="总成本")
    api_requests_made: int = Field(..., description="API请求数")

    # 时间统计
    total_processing_time: int = Field(..., description="总处理时间(秒)")
    average_chapter_time: int = Field(..., description="平均章节时间(秒)")

    # 错误统计
    total_errors: int = Field(..., description="总错误数")
    retry_count: int = Field(..., description="重试次数")

    class Config:
        protected_namespaces = ()
        from_attributes = True


# 翻译章节相关
class TranslatedChapterResponse(BaseModel):
    """翻译章节响应"""
    id: uuid.UUID = Field(..., description="翻译章节ID")
    original_chapter_id: uuid.UUID = Field(..., description="原章节ID")
    title: str = Field(..., description="标题")
    chapter_number: int = Field(..., description="章节号")
    volume_number: int = Field(..., description="卷号")
    content: Optional[str] = Field(None, description="内容")
    outline: Optional[str] = Field(None, description="AI生成的大纲")
    summary: Optional[str] = Field(None, description="章节摘要")
    translator_notes: Optional[str] = Field(None, description="译者注")

    # 翻译过程信息
    translation_method: str = Field(..., description="翻译方法")
    ai_model_used: Optional[str] = Field(None, description="使用的AI模型")

    # 处理统计
    input_tokens: int = Field(..., description="输入tokens")
    output_tokens: int = Field(..., description="输出tokens")
    processing_time_seconds: int = Field(..., description="处理时间(秒)")
    word_count: int = Field(..., description="字数")

    # 质量控制
    quality_score: Optional[Decimal] = Field(None, description="质量分")
    quality_details: Dict[str, Any] = Field(..., description="质量详情")
    quality_issues: List[Dict[str, Any]] = Field(..., description="质量问题")

    # 审核状态
    review_status: str = Field(..., description="审核状态")
    reviewer_notes: Optional[str] = Field(None, description="审核备注")
    reviewed_at: Optional[datetime] = Field(None, description="审核时间")

    # 处理状态
    status: str = Field(..., description="状态")
    retry_count: int = Field(..., description="重试次数")
    error_message: Optional[str] = Field(None, description="错误信息")

    # 版本控制
    version_number: int = Field(..., description="版本号")
    is_latest_version: bool = Field(..., description="是否最新版本")

    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        protected_namespaces = ()
        from_attributes = True


# 章节审核请求
class ChapterReviewRequest(BaseModel):
    """章节审核请求"""
    review_status: str = Field(..., description="审核状态")
    reviewer_notes: Optional[str] = Field(None, max_length=1000, description="审核备注")

    @validator('review_status')
    def validate_review_status(cls, v):
        if v not in ['approved', 'rejected', 'needs_revision']:
            raise ValueError('审核状态只能是approved、rejected或needs_revision')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "review_status": "approved",
                "reviewer_notes": "翻译质量良好，通过审核"
            }
        }