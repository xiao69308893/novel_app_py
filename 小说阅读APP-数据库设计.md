-- =====================================================
-- 小说阅读APP PostgreSQL数据库表设计方案
-- 支持AI翻译功能的完整数据库架构
-- =====================================================

-- 启用UUID扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- 全文搜索支持
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- 复合索引优化

-- =====================================================
-- 1. 用户系统相关表
-- =====================================================

-- 用户基础表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(32) NOT NULL,
    
    -- 基础信息
    nickname VARCHAR(100),
    avatar_url VARCHAR(500),
    gender VARCHAR(10) CHECK (gender IN ('male', 'female', 'other')),
    birthday DATE,
    bio TEXT,
    
    -- 等级和积分
    level INTEGER DEFAULT 1 CHECK (level >= 1),
    vip_level INTEGER DEFAULT 0 CHECK (vip_level >= 0),
    points INTEGER DEFAULT 0 CHECK (points >= 0),
    coins INTEGER DEFAULT 0 CHECK (coins >= 0),
    experience INTEGER DEFAULT 0 CHECK (experience >= 0),
    
    -- 状态管理
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'banned', 'deleted')),
    is_verified BOOLEAN DEFAULT false,
    email_verified BOOLEAN DEFAULT false,
    phone_verified BOOLEAN DEFAULT false,
    
    -- 安全相关
    last_login_at TIMESTAMP WITH TIME ZONE,
    last_login_ip INET,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    
    -- 审计字段
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 索引
    CONSTRAINT users_username_length CHECK (char_length(username) >= 3),
    CONSTRAINT users_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- 用户详细资料表
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 个人信息
    real_name VARCHAR(100),
    id_card VARCHAR(50),
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100),
    timezone VARCHAR(50) DEFAULT 'Asia/Shanghai',
    language VARCHAR(10) DEFAULT 'zh-CN',
    
    -- 偏好设置
    reading_preferences JSONB DEFAULT '{}',
    notification_settings JSONB DEFAULT '{}',
    privacy_settings JSONB DEFAULT '{}',
    
    -- 社交信息
    website VARCHAR(500),
    social_links JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id)
);

-- 用户设置表
CREATE TABLE user_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 阅读设置
    reader_theme VARCHAR(20) DEFAULT 'light',
    font_size INTEGER DEFAULT 16 CHECK (font_size BETWEEN 12 AND 24),
    line_spacing DECIMAL(3,1) DEFAULT 1.5 CHECK (line_spacing BETWEEN 1.0 AND 3.0),
    page_margin INTEGER DEFAULT 20 CHECK (page_margin BETWEEN 10 AND 50),
    auto_scroll BOOLEAN DEFAULT false,
    
    -- 通知设置
    email_notifications BOOLEAN DEFAULT true,
    push_notifications BOOLEAN DEFAULT true,
    sms_notifications BOOLEAN DEFAULT false,
    
    -- 隐私设置
    profile_public BOOLEAN DEFAULT true,
    reading_history_public BOOLEAN DEFAULT false,
    allow_friend_requests BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id)
);

-- 用户统计表
CREATE TABLE user_statistics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 阅读统计
    total_reading_time INTEGER DEFAULT 0, -- 总阅读时间(分钟)
    books_read INTEGER DEFAULT 0,         -- 已读完书籍数
    chapters_read INTEGER DEFAULT 0,      -- 已读章节数
    words_read BIGINT DEFAULT 0,          -- 已读字数
    
    -- 收藏统计
    favorites_count INTEGER DEFAULT 0,
    bookmarks_count INTEGER DEFAULT 0,
    
    -- 社交统计
    comments_count INTEGER DEFAULT 0,
    likes_received INTEGER DEFAULT 0,
    
    -- 翻译统计
    translations_created INTEGER DEFAULT 0,
    translation_words INTEGER DEFAULT 0,
    
    -- 日期统计
    streak_days INTEGER DEFAULT 0,        -- 连续签到天数
    last_read_date DATE,
    last_checkin_date DATE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id)
);

-- 登录日志表
CREATE TABLE login_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- 登录信息
    login_type VARCHAR(20) NOT NULL CHECK (login_type IN ('password', 'phone', 'email', 'social')),
    ip_address INET NOT NULL,
    user_agent TEXT,
    device_info JSONB,
    
    -- 地理位置
    country VARCHAR(100),
    city VARCHAR(100),
    
    -- 状态
    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'failed', 'blocked')),
    failure_reason VARCHAR(100),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 2. 小说分类和标签系统
-- =====================================================

-- 小说分类表
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    cover_url VARCHAR(500),
    
    -- 层级结构
    parent_id UUID REFERENCES categories(id),
    level INTEGER DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    
    -- 统计信息
    novel_count INTEGER DEFAULT 0,
    
    -- 状态
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 小说标签表
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL UNIQUE,
    color VARCHAR(7) DEFAULT '#1890ff',
    description TEXT,
    
    -- 统计
    usage_count INTEGER DEFAULT 0,
    
    -- 状态
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 3. 作者系统
-- =====================================================

-- 作者表
CREATE TABLE authors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL, -- 关联用户(如果作者也是平台用户)
    
    -- 基础信息
    name VARCHAR(100) NOT NULL,
    pen_name VARCHAR(100),
    avatar_url VARCHAR(500),
    biography TEXT,
    
    -- 联系信息
    email VARCHAR(100),
    website VARCHAR(500),
    social_links JSONB DEFAULT '{}',
    
    -- 统计信息
    novel_count INTEGER DEFAULT 0,
    total_words BIGINT DEFAULT 0,
    followers_count INTEGER DEFAULT 0,
    
    -- 状态
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'banned')),
    is_verified BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 4. 小说主体系统
-- =====================================================

-- 小说表
CREATE TABLE novels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 基础信息
    title VARCHAR(200) NOT NULL,
    subtitle VARCHAR(200),
    description TEXT,
    cover_url VARCHAR(500),
    
    -- 作者信息
    author_id UUID NOT NULL REFERENCES authors(id),
    
    -- 分类标签
    category_id UUID REFERENCES categories(id),
    
    -- 内容信息
    language VARCHAR(10) DEFAULT 'zh-CN',
    word_count BIGINT DEFAULT 0,
    chapter_count INTEGER DEFAULT 0,
    
    -- 状态信息
    status VARCHAR(20) DEFAULT 'ongoing' CHECK (status IN ('ongoing', 'completed', 'paused', 'dropped')),
    publish_status VARCHAR(20) DEFAULT 'draft' CHECK (publish_status IN ('draft', 'published', 'reviewing', 'rejected')),
    
    -- VIP和付费设置
    is_vip BOOLEAN DEFAULT false,
    is_free BOOLEAN DEFAULT true,
    price_per_chapter DECIMAL(8,2) DEFAULT 0,
    
    -- 统计信息
    view_count BIGINT DEFAULT 0,
    favorite_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    rating DECIMAL(3,2) DEFAULT 0 CHECK (rating BETWEEN 0 AND 5),
    rating_count INTEGER DEFAULT 0,
    
    -- 更新信息
    last_chapter_id UUID,
    last_chapter_title VARCHAR(200),
    last_update_time TIMESTAMP WITH TIME ZONE,
    
    -- SEO相关
    seo_title VARCHAR(200),
    seo_description TEXT,
    seo_keywords VARCHAR(500),
    
    -- 翻译相关
    is_translated BOOLEAN DEFAULT false,
    original_language VARCHAR(10),
    translation_count INTEGER DEFAULT 0,
    
    -- 审计字段
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- 全文搜索向量
    search_vector tsvector
);

-- 小说标签关联表
CREATE TABLE novel_tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    novel_id UUID NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(novel_id, tag_id)
);

-- 小说评分表
CREATE TABLE novel_ratings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    novel_id UUID NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(novel_id, user_id)
);

-- =====================================================
-- 5. 章节系统
-- =====================================================

-- 章节表
CREATE TABLE chapters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    novel_id UUID NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
    
    -- 基础信息
    title VARCHAR(200) NOT NULL,
    chapter_number INTEGER NOT NULL,
    volume_number INTEGER DEFAULT 1,
    
    -- 内容
    content TEXT,
    summary TEXT,
    author_notes TEXT,
    
    -- 统计信息
    word_count INTEGER DEFAULT 0,
    view_count BIGINT DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    
    -- 付费设置
    is_vip BOOLEAN DEFAULT false,
    price DECIMAL(8,2) DEFAULT 0,
    is_free BOOLEAN DEFAULT true,
    
    -- 状态
    status VARCHAR(20) DEFAULT 'published' CHECK (status IN ('draft', 'published', 'reviewing', 'locked')),
    
    -- 语言
    language VARCHAR(10) DEFAULT 'zh-CN',
    
    -- 审计字段
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- 全文搜索向量
    search_vector tsvector,
    
    -- 约束
    UNIQUE(novel_id, chapter_number)
);

-- 章节购买记录表
CREATE TABLE chapter_purchases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    chapter_id UUID NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    novel_id UUID NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
    
    -- 购买信息
    price DECIMAL(8,2) NOT NULL,
    payment_method VARCHAR(20),
    transaction_id VARCHAR(100),
    
    -- 状态
    status VARCHAR(20) DEFAULT 'completed' CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, chapter_id)
);

-- =====================================================
-- 6. 用户收藏和阅读系统
-- =====================================================

-- 用户收藏表
CREATE TABLE user_favorites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    novel_id UUID NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
    
    -- 收藏信息
    folder_name VARCHAR(100) DEFAULT '默认收藏夹',
    notes TEXT,
    is_public BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, novel_id)
);

-- 阅读进度表
CREATE TABLE reading_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    novel_id UUID NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
    chapter_id UUID REFERENCES chapters(id) ON DELETE SET NULL,
    
    -- 进度信息
    chapter_number INTEGER DEFAULT 1,
    position INTEGER DEFAULT 0,      -- 章节内位置
    progress DECIMAL(5,4) DEFAULT 0, -- 整本书进度百分比
    
    -- 阅读时间
    reading_time INTEGER DEFAULT 0,  -- 总阅读时间(分钟)
    last_read_duration INTEGER DEFAULT 0, -- 最后一次阅读时长
    
    -- 设备信息
    device_type VARCHAR(20),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, novel_id)
);

-- 阅读历史表 (按日期分区)
CREATE TABLE reading_history (
    id UUID DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    novel_id UUID NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
    chapter_id UUID REFERENCES chapters(id) ON DELETE SET NULL,
    
    -- 阅读信息
    chapter_number INTEGER,
    reading_time INTEGER DEFAULT 0, -- 本次阅读时长(秒)
    start_position INTEGER DEFAULT 0,
    end_position INTEGER DEFAULT 0,
    
    -- 设备信息
    device_type VARCHAR(20),
    ip_address INET,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- 创建阅读历史分区表(按月分区)
CREATE TABLE reading_history_2024_01 PARTITION OF reading_history
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE reading_history_2024_02 PARTITION OF reading_history
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- 书签表
CREATE TABLE bookmarks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    novel_id UUID NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
    chapter_id UUID NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    
    -- 书签信息
    title VARCHAR(200),
    notes TEXT,
    position INTEGER NOT NULL DEFAULT 0,
    content_preview TEXT, -- 书签位置的内容预览
    
    -- 分类
    folder_name VARCHAR(100) DEFAULT '默认书签',
    color VARCHAR(7) DEFAULT '#1890ff',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 7. 评论系统
-- =====================================================

-- 评论表
CREATE TABLE comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 评论目标
    target_type VARCHAR(20) NOT NULL CHECK (target_type IN ('novel', 'chapter', 'comment')),
    target_id UUID NOT NULL,
    
    -- 评论内容
    content TEXT NOT NULL,
    content_type VARCHAR(20) DEFAULT 'text' CHECK (content_type IN ('text', 'html', 'markdown')),
    
    -- 层级结构
    parent_id UUID REFERENCES comments(id) ON DELETE CASCADE,
    root_id UUID REFERENCES comments(id) ON DELETE CASCADE,
    level INTEGER DEFAULT 0,
    
    -- 统计信息
    like_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,
    
    -- 状态
    status VARCHAR(20) DEFAULT 'published' CHECK (status IN ('published', 'hidden', 'deleted', 'reviewing')),
    
    -- IP信息
    ip_address INET,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 评论点赞表
CREATE TABLE comment_likes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    comment_id UUID NOT NULL REFERENCES comments(id) ON DELETE CASCADE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, comment_id)
);

-- =====================================================
-- 8. AI翻译系统核心表
-- =====================================================

-- AI模型配置表
CREATE TABLE ai_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 模型基础信息
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL CHECK (provider IN ('deepseek', 'zhipu', 'ollama')),
    models_id VARCHAR(100) NOT NULL,
    version VARCHAR(50),
    
    -- 模型能力
    capabilities JSONB DEFAULT '[]', -- ['translation', 'outline_generation', 'character_analysis', 'quality_check']
    supported_languages JSONB DEFAULT '[]', -- ['zh-CN', 'en-US', 'ja-JP']
    
    -- 性能参数
    max_tokens INTEGER DEFAULT 4000,
    max_requests_per_minute INTEGER DEFAULT 60,
    max_requests_per_day INTEGER DEFAULT 10000,
    max_concurrent_requests INTEGER DEFAULT 5,
    
    -- API配置
    api_endpoint VARCHAR(200),
    api_version VARCHAR(20),
    timeout_seconds INTEGER DEFAULT 30,
    
    -- 成本配置
    cost_per_1k_input_tokens DECIMAL(8,6) DEFAULT 0,
    cost_per_1k_output_tokens DECIMAL(8,6) DEFAULT 0,
    
    -- 质量配置
    default_temperature DECIMAL(3,2) DEFAULT 0.7,
    default_top_p DECIMAL(3,2) DEFAULT 0.9,
    
    -- 状态管理
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,
    health_status VARCHAR(20) DEFAULT 'unknown' CHECK (health_status IN ('healthy', 'degraded', 'unhealthy', 'unknown')),
    last_health_check TIMESTAMP WITH TIME ZONE,
    
    -- 使用统计
    total_requests BIGINT DEFAULT 0,
    total_tokens BIGINT DEFAULT 0,
    total_cost DECIMAL(12,4) DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 翻译配置模板表
CREATE TABLE translation_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 基础信息
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- 语言配置
    source_language VARCHAR(10) NOT NULL DEFAULT 'zh-CN',
    target_language VARCHAR(10) NOT NULL DEFAULT 'en-US',
    
    -- AI模型配置
    outline_models_id UUID REFERENCES ai_models(id),
    translation_models_id UUID REFERENCES ai_models(id),
    review_models_id UUID REFERENCES ai_models(id),
    
    -- 翻译策略
    translation_strategy VARCHAR(50) DEFAULT 'direct' CHECK (translation_strategy IN ('direct', 'outline_based', 'multi_pass')),
    
    -- 处理选项
    generate_outline BOOLEAN DEFAULT true,
    rewrite_based_on_outline BOOLEAN DEFAULT true,
    preserve_formatting BOOLEAN DEFAULT true,
    translate_character_names BOOLEAN DEFAULT true,
    use_character_mapping BOOLEAN DEFAULT true,
    maintain_cultural_context BOOLEAN DEFAULT true,
    
    -- 质量控制
    enable_quality_check BOOLEAN DEFAULT true,
    quality_threshold DECIMAL(3,2) DEFAULT 3.5,
    max_retry_count INTEGER DEFAULT 3,
    
    -- 风格设置
    writing_style VARCHAR(50) DEFAULT 'literary' CHECK (writing_style IN ('formal', 'casual', 'literary', 'technical')),
    tone VARCHAR(50) DEFAULT 'neutral' CHECK (tone IN ('neutral', 'serious', 'humorous', 'dramatic')),
    target_audience VARCHAR(50) DEFAULT 'general' CHECK (target_audience IN ('children', 'young_adult', 'adult', 'general')),
    
    -- 处理参数
    batch_size INTEGER DEFAULT 1 CHECK (batch_size BETWEEN 1 AND 10),
    delay_between_requests INTEGER DEFAULT 2,
    max_parallel_tasks INTEGER DEFAULT 3,
    
    -- 自定义提示词
    custom_prompts JSONB DEFAULT '{}',
    
    -- 状态
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    is_public BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 翻译项目表
CREATE TABLE translation_projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 项目基础信息
    name VARCHAR(200) NOT NULL,
    description TEXT,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 源小说信息
    source_novel_id UUID NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
    source_language VARCHAR(10) NOT NULL DEFAULT 'zh-CN',
    target_language VARCHAR(10) NOT NULL DEFAULT 'en-US',
    
    -- 翻译配置
    config_id UUID NOT NULL REFERENCES translation_configs(id),
    custom_config JSONB DEFAULT '{}', -- 项目特定的配置覆盖
    
    -- 进度信息
    status VARCHAR(20) DEFAULT 'created' CHECK (status IN ('created', 'analyzing', 'translating', 'reviewing', 'completed', 'paused', 'failed', 'cancelled')),
    progress DECIMAL(5,2) DEFAULT 0 CHECK (progress BETWEEN 0 AND 100), -- 进度百分比
    
    -- 章节信息
    total_chapters INTEGER DEFAULT 0,
    completed_chapters INTEGER DEFAULT 0,
    failed_chapters INTEGER DEFAULT 0,
    
    -- 翻译范围
    start_chapter INTEGER DEFAULT 1,
    end_chapter INTEGER,
    chapter_filter JSONB, -- 特定章节范围或过滤条件
    
    -- 质量统计
    average_quality_score DECIMAL(3,2),
    quality_issues_count INTEGER DEFAULT 0,
    
    -- 成本统计
    estimated_cost DECIMAL(10,4) DEFAULT 0,
    actual_cost DECIMAL(10,4) DEFAULT 0,
    tokens_used BIGINT DEFAULT 0,
    
    -- 时间统计
    estimated_completion_time TIMESTAMP WITH TIME ZONE,
    actual_completion_time TIMESTAMP WITH TIME ZONE,
    total_processing_time INTEGER DEFAULT 0, -- 总处理时间(秒)
    
    -- 输出配置
    output_format VARCHAR(20) DEFAULT 'database' CHECK (output_format IN ('database', 'file', 'both')),
    output_path VARCHAR(500),
    
    -- 状态时间戳
    started_at TIMESTAMP WITH TIME ZONE,
    paused_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    failed_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 翻译后小说表
CREATE TABLE translated_novels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 关联信息
    original_novel_id UUID NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
    translation_project_id UUID NOT NULL REFERENCES translation_projects(id) ON DELETE CASCADE,
    
    -- 翻译后的内容
    title VARCHAR(200) NOT NULL,
    subtitle VARCHAR(200),
    description TEXT,
    cover_url VARCHAR(500),
    
    -- 作者信息(翻译后)
    translated_author_name VARCHAR(100),
    translator_notes TEXT,
    
    -- 语言和分类
    language VARCHAR(10) NOT NULL,
    category_id UUID REFERENCES categories(id),
    
    -- 内容统计
    word_count BIGINT DEFAULT 0,
    chapter_count INTEGER DEFAULT 0,
    
    -- 翻译质量
    overall_quality_score DECIMAL(3,2),
    review_status VARCHAR(20) DEFAULT 'pending' CHECK (review_status IN ('pending', 'approved', 'rejected', 'needs_revision')),
    
    -- 发布状态
    is_published BOOLEAN DEFAULT false,
    publish_status VARCHAR(20) DEFAULT 'draft' CHECK (publish_status IN ('draft', 'reviewing', 'published', 'hidden')),
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- SEO信息
    seo_title VARCHAR(200),
    seo_description TEXT,
    seo_keywords VARCHAR(500),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(translation_project_id)
);

-- 角色映射表
CREATE TABLE character_mappings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    translation_project_id UUID NOT NULL REFERENCES translation_projects(id) ON DELETE CASCADE,
    
    -- 角色信息
    original_name VARCHAR(100) NOT NULL,
    translated_name VARCHAR(100) NOT NULL,
    alternative_names JSONB DEFAULT '[]', -- 别名列表
    
    -- 角色分类
    character_type VARCHAR(50) DEFAULT 'character' CHECK (character_type IN ('protagonist', 'antagonist', 'supporting', 'background', 'place', 'organization', 'item')),
    importance_level INTEGER DEFAULT 5 CHECK (importance_level BETWEEN 1 AND 10), -- 重要程度
    
    -- 角色描述
    description TEXT,
    personality_traits JSONB DEFAULT '[]',
    relationships JSONB DEFAULT '{}', -- 与其他角色的关系
    
    -- 出现信息
    first_appearance_chapter INTEGER,
    last_appearance_chapter INTEGER,
    appearance_frequency INTEGER DEFAULT 0,
    
    -- 映射质量
    mapping_confidence DECIMAL(3,2) DEFAULT 1.0 CHECK (mapping_confidence BETWEEN 0 AND 1),
    is_verified BOOLEAN DEFAULT false,
    verified_by UUID REFERENCES users(id),
    verification_notes TEXT,
    
    -- 自动检测信息
    auto_detected BOOLEAN DEFAULT false,
    detection_method VARCHAR(50), -- 'ai_analysis', 'frequency_analysis', 'manual'
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(translation_project_id, original_name)
);

-- 翻译后章节表
CREATE TABLE translated_chapters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 关联信息
    original_chapter_id UUID NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    translated_novel_id UUID NOT NULL REFERENCES translated_novels(id) ON DELETE CASCADE,
    translation_project_id UUID NOT NULL REFERENCES translation_projects(id) ON DELETE CASCADE,
    
    -- 章节基础信息
    title VARCHAR(200) NOT NULL,
    chapter_number INTEGER NOT NULL,
    volume_number INTEGER DEFAULT 1,
    
    -- 翻译内容
    content TEXT,
    outline TEXT, -- AI生成的大纲
    summary TEXT, -- 章节摘要
    translator_notes TEXT,
    
    -- 翻译过程信息
    translation_method VARCHAR(50) DEFAULT 'ai_direct' CHECK (translation_method IN ('ai_direct', 'ai_outline_based', 'hybrid', 'manual')),
    ai_model_used VARCHAR(100),
    prompt_used TEXT,
    
    -- 处理统计
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    processing_time_seconds INTEGER DEFAULT 0,
    word_count INTEGER DEFAULT 0,
    
    -- 质量控制
    quality_score DECIMAL(3,2),
    quality_details JSONB DEFAULT '{}', -- 详细质量分析
    quality_issues JSONB DEFAULT '[]', -- 质量问题列表
    
    -- 审核状态
    review_status VARCHAR(20) DEFAULT 'pending' CHECK (review_status IN ('pending', 'approved', 'rejected', 'needs_revision')),
    reviewed_by UUID REFERENCES users(id),
    reviewer_notes TEXT,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    
    -- 处理状态
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'outline_generating', 'translating', 'quality_checking', 'completed', 'failed', 'reviewing')),
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    
    -- 版本控制
    version_number INTEGER DEFAULT 1,
    is_latest_version BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(translation_project_id, original_chapter_id, version_number)
);

-- 翻译任务队列表
CREATE TABLE translation_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 任务基础信息
    translation_project_id UUID NOT NULL REFERENCES translation_projects(id) ON DELETE CASCADE,
    task_type VARCHAR(20) NOT NULL CHECK (task_type IN ('outline', 'translate', 'review', 'character_map', 'quality_check')),
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10), -- 优先级，1最高
    
    -- 任务目标
    target_type VARCHAR(20) NOT NULL CHECK (target_type IN ('novel', 'chapter', 'batch')),
    target_id UUID NOT NULL,
    
    -- 任务配置
    task_config JSONB DEFAULT '{}',
    
    -- 执行信息
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled', 'paused')),
    worker_id VARCHAR(100),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- 进度信息
    progress DECIMAL(5,2) DEFAULT 0,
    current_step VARCHAR(100),
    total_steps INTEGER DEFAULT 1,
    completed_steps INTEGER DEFAULT 0,
    
    -- 结果信息
    result JSONB DEFAULT '{}',
    error_message TEXT,
    error_code VARCHAR(50),
    stack_trace TEXT,
    
    -- 重试配置
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    retry_delay_seconds INTEGER DEFAULT 60,
    
    -- 依赖关系
    depends_on UUID REFERENCES translation_tasks(id),
    
    -- 资源使用
    estimated_cost DECIMAL(8,4) DEFAULT 0,
    actual_cost DECIMAL(8,4) DEFAULT 0,
    tokens_used INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 翻译统计表(按日期分区)
CREATE TABLE translation_statistics (
    id UUID DEFAULT uuid_generate_v4(),
    translation_project_id UUID NOT NULL REFERENCES translation_projects(id) ON DELETE CASCADE,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- 进度统计
    chapters_completed INTEGER DEFAULT 0,
    words_translated INTEGER DEFAULT 0,
    characters_mapped INTEGER DEFAULT 0,
    
    -- 质量统计
    average_quality_score DECIMAL(3,2),
    quality_issues_found INTEGER DEFAULT 0,
    quality_issues_fixed INTEGER DEFAULT 0,
    
    -- 成本统计
    total_tokens_used INTEGER DEFAULT 0,
    total_cost DECIMAL(8,4) DEFAULT 0,
    api_requests_made INTEGER DEFAULT 0,
    
    -- 时间统计
    total_processing_time INTEGER DEFAULT 0, -- 秒
    average_chapter_time INTEGER DEFAULT 0,  -- 秒
    
    -- 错误统计
    total_errors INTEGER DEFAULT 0,
    retry_count INTEGER DEFAULT 0,
    
    PRIMARY KEY (id, date)
) PARTITION BY RANGE (date);

-- 创建翻译统计分区表
CREATE TABLE translation_statistics_2024 PARTITION OF translation_statistics
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

-- =====================================================
-- 9. 系统管理表
-- =====================================================

-- 系统配置表
CREATE TABLE system_configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 配置信息
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT,
    config_type VARCHAR(20) DEFAULT 'string' CHECK (config_type IN ('string', 'integer', 'boolean', 'json', 'decimal')),
    
    -- 描述信息
    category VARCHAR(50) NOT NULL,
    description TEXT,
    default_value TEXT,
    
    -- 验证规则
    validation_rules JSONB DEFAULT '{}',
    
    -- 权限
    is_public BOOLEAN DEFAULT false,
    requires_restart BOOLEAN DEFAULT false,
    
    -- 版本控制
    version INTEGER DEFAULT 1,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 操作日志表(按日期分区)
CREATE TABLE operation_logs (
    id UUID DEFAULT uuid_generate_v4(),
    
    -- 操作信息
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    operation_type VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    
    -- 操作详情
    action VARCHAR(50) NOT NULL,
    description TEXT,
    old_values JSONB,
    new_values JSONB,
    
    -- 请求信息
    ip_address INET,
    user_agent TEXT,
    request_id UUID,
    
    -- 结果信息
    status VARCHAR(20) DEFAULT 'success' CHECK (status IN ('success', 'failed', 'warning')),
    error_message TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- 创建操作日志分区表
CREATE TABLE operation_logs_2024_01 PARTITION OF operation_logs
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- =====================================================
-- 10. 索引创建
-- =====================================================

-- 用户表索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_last_login ON users(last_login_at);

-- 小说表索引
CREATE INDEX idx_novels_author ON novels(author_id);
CREATE INDEX idx_novels_category ON novels(category_id);
CREATE INDEX idx_novels_status ON novels(status);
CREATE INDEX idx_novels_language ON novels(language);
CREATE INDEX idx_novels_publish_status ON novels(publish_status);
CREATE INDEX idx_novels_rating ON novels(rating DESC);
CREATE INDEX idx_novels_view_count ON novels(view_count DESC);
CREATE INDEX idx_novels_favorite_count ON novels(favorite_count DESC);
CREATE INDEX idx_novels_update_time ON novels(last_update_time DESC);
CREATE INDEX idx_novels_created_at ON novels(created_at DESC);
CREATE INDEX idx_novels_translated ON novels(is_translated);

-- 全文搜索索引
CREATE INDEX idx_novels_search ON novels USING GIN(search_vector);
CREATE INDEX idx_novels_title_gin ON novels USING GIN(title gin_trgm_ops);
CREATE INDEX idx_chapters_search ON chapters USING GIN(search_vector);

-- 章节表索引
CREATE INDEX idx_chapters_novel ON chapters(novel_id, chapter_number);
CREATE INDEX idx_chapters_status ON chapters(status);
CREATE INDEX idx_chapters_created_at ON chapters(created_at DESC);
CREATE INDEX idx_chapters_vip ON chapters(is_vip);

-- 阅读相关索引
CREATE INDEX idx_reading_progress_user ON reading_progress(user_id);
CREATE INDEX idx_reading_progress_novel ON reading_progress(novel_id);
CREATE INDEX idx_reading_progress_updated ON reading_progress(updated_at DESC);
CREATE INDEX idx_user_favorites_user ON user_favorites(user_id);
CREATE INDEX idx_bookmarks_user ON bookmarks(user_id);
CREATE INDEX idx_bookmarks_novel ON bookmarks(novel_id);

-- 评论系统索引
CREATE INDEX idx_comments_target ON comments(target_type, target_id);
CREATE INDEX idx_comments_user ON comments(user_id);
CREATE INDEX idx_comments_parent ON comments(parent_id);
CREATE INDEX idx_comments_created_at ON comments(created_at DESC);
CREATE INDEX idx_comments_status ON comments(status);

-- 翻译系统索引
CREATE INDEX idx_translation_projects_user ON translation_projects(created_by);
CREATE INDEX idx_translation_projects_novel ON translation_projects(source_novel_id);
CREATE INDEX idx_translation_projects_status ON translation_projects(status);
CREATE INDEX idx_translation_projects_language ON translation_projects(source_language, target_language);

CREATE INDEX idx_translated_chapters_project ON translated_chapters(translation_project_id);
CREATE INDEX idx_translated_chapters_original ON translated_chapters(original_chapter_id);
CREATE INDEX idx_translated_chapters_status ON translated_chapters(status);
CREATE INDEX idx_translated_chapters_quality ON translated_chapters(quality_score DESC);

CREATE INDEX idx_character_mappings_project ON character_mappings(translation_project_id);
CREATE INDEX idx_character_mappings_original ON character_mappings(original_name);
CREATE INDEX idx_character_mappings_type ON character_mappings(character_type);

CREATE INDEX idx_translation_tasks_project ON translation_tasks(translation_project_id);
CREATE INDEX idx_translation_tasks_status ON translation_tasks(status);
CREATE INDEX idx_translation_tasks_priority ON translation_tasks(priority DESC, created_at);
CREATE INDEX idx_translation_tasks_type ON translation_tasks(task_type);

-- AI模型索引
CREATE INDEX idx_ai_models_provider ON ai_models(provider);
CREATE INDEX idx_ai_models_active ON ai_models(is_active);
CREATE INDEX idx_ai_models_health ON ai_models(health_status);

-- 系统日志索引
CREATE INDEX idx_login_logs_user ON login_logs(user_id);
CREATE INDEX idx_login_logs_created_at ON login_logs(created_at DESC);
CREATE INDEX idx_login_logs_ip ON login_logs(ip_address);

-- =====================================================
-- 11. 触发器和函数
-- =====================================================

-- 更新updated_at字段的触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表创建updated_at触发器
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_novels_updated_at BEFORE UPDATE ON novels
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chapters_updated_at BEFORE UPDATE ON chapters
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_translation_projects_updated_at BEFORE UPDATE ON translation_projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 更新小说统计信息的触发器函数
CREATE OR REPLACE FUNCTION update_novel_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        -- 更新章节数和字数
        UPDATE novels SET 
            chapter_count = chapter_count + 1,
            word_count = word_count + COALESCE(NEW.word_count, 0),
            last_chapter_id = NEW.id,
            last_chapter_title = NEW.title,
            last_update_time = NEW.created_at
        WHERE id = NEW.novel_id;
        
    ELSIF TG_OP = 'UPDATE' THEN
        -- 更新字数
        UPDATE novels SET 
            word_count = word_count - COALESCE(OLD.word_count, 0) + COALESCE(NEW.word_count, 0),
            last_update_time = NEW.updated_at
        WHERE id = NEW.novel_id;
        
    ELSIF TG_OP = 'DELETE' THEN
        -- 减少章节数和字数
        UPDATE novels SET 
            chapter_count = chapter_count - 1,
            word_count = word_count - COALESCE(OLD.word_count, 0)
        WHERE id = OLD.novel_id;
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- 为章节表创建统计更新触发器
CREATE TRIGGER update_novel_stats_trigger
    AFTER INSERT OR UPDATE OR DELETE ON chapters
    FOR EACH ROW EXECUTE FUNCTION update_novel_stats();

-- 更新全文搜索向量的触发器函数
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('chinese', COALESCE(NEW.title, '') || ' ' || COALESCE(NEW.description, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为小说表创建搜索向量更新触发器
CREATE TRIGGER update_novels_search_vector
    BEFORE INSERT OR UPDATE ON novels
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();

-- =====================================================
-- 12. 基础数据插入
-- =====================================================

-- 插入默认分类
INSERT INTO categories (id, name, slug, description, level) VALUES
(uuid_generate_v4(), '玄幻小说', 'xuanhuan', '以修真、魔法为主题的小说', 0),
(uuid_generate_v4(), '都市小说', 'urban', '以现代都市生活为背景的小说', 0),
(uuid_generate_v4(), '历史小说', 'history', '以历史为背景的小说', 0),
(uuid_generate_v4(), '科幻小说', 'scifi', '以科学幻想为主题的小说', 0),
(uuid_generate_v4(), '言情小说', 'romance', '以爱情为主线的小说', 0);

-- 插入常用标签
INSERT INTO tags (name, color, description) VALUES
('热血', '#ff4d4f', '充满激情和斗志的故事'),
('爽文', '#52c41a', '让读者感到爽快的情节'),
('系统流', '#1890ff', '主角获得系统帮助的设定'),
('穿越', '#722ed1', '主角穿越到其他时空'),
('重生', '#eb2f96', '主角重新来过的设定'),
('修真', '#fa8c16', '修炼成仙的故事'),
('都市', '#13c2c2', '现代都市背景');

-- 插入默认AI模型配置
INSERT INTO ai_models (name, display_name, provider, models_id, capabilities, supported_languages, max_tokens, cost_per_1k_input_tokens, cost_per_1k_output_tokens, is_default) VALUES
('deepseek-chat', 'DeepSeek Chat', 'deepseek', 'deepseek-chat', '["translation", "outline_generation", "character_analysis"]', '["zh-CN", "en-US", "ja-JP"]', 4000, 0.0014, 0.0028, true),
('glm-4', '智谱 GLM-4', 'zhipu', 'glm-4', '["translation", "quality_check"]', '["zh-CN", "en-US"]', 8000, 0.0050, 0.0150, false),
('llama3.1-8b', 'Llama 3.1 8B', 'ollama', 'llama3.1:8b', '["translation", "outline_generation"]', '["zh-CN", "en-US"]', 4096, 0, 0, false);

-- 插入默认翻译配置
INSERT INTO translation_configs (name, description, source_language, target_language, translation_strategy, is_default, is_public) VALUES
('标准中英翻译', '适用于中文小说翻译成英文的标准配置', 'zh-CN', 'en-US', 'outline_based', true, true),
('快速翻译模式', '快速翻译模式，适合批量处理', 'zh-CN', 'en-US', 'direct', false, true),
('高质量翻译', '高质量翻译模式，包含多轮审核', 'zh-CN', 'en-US', 'multi_pass', false, true);

-- 插入系统配置
INSERT INTO system_configurations (config_key, config_value, config_type, category, description, is_public) VALUES
('site_name', '小说阅读平台', 'string', 'basic', '网站名称', true),
('site_description', '提供高质量小说阅读和AI翻译服务', 'string', 'basic', '网站描述', true),
('max_upload_size', '10485760', 'integer', 'upload', '最大上传文件大小(字节)', false),
('translation_daily_limit', '50', 'integer', 'translation', '每日翻译章节数限制', false),
('ai_request_timeout', '30', 'integer', 'ai', 'AI请求超时时间(秒)', false),
('enable_auto_translation', 'true', 'boolean', 'translation', '是否启用自动翻译', false);

-- =====================================================
-- 13. 性能优化和分区策略
-- =====================================================

-- 为大表创建分区索引
CREATE INDEX CONCURRENTLY idx_reading_history_2024_01_user_date 
ON reading_history_2024_01(user_id, created_at DESC);

CREATE INDEX CONCURRENTLY idx_translation_statistics_2024_project_date 
ON translation_statistics_2024(translation_project_id, date DESC);

-- 创建部分索引(仅对活跃数据)
CREATE INDEX CONCURRENTLY idx_active_novels 
ON novels(created_at DESC) WHERE status = 'ongoing' AND publish_status = 'published';

CREATE INDEX CONCURRENTLY idx_active_translation_projects 
ON translation_projects(created_at DESC) WHERE status IN ('translating', 'reviewing');

-- =====================================================
-- 14. 数据库维护
-- =====================================================

-- 自动清理过期数据的函数
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS void AS $$
BEGIN
    -- 清理90天前的登录日志
    DELETE FROM login_logs WHERE created_at < NOW() - INTERVAL '90 days';
    
    -- 清理180天前的操作日志
    DELETE FROM operation_logs WHERE created_at < NOW() - INTERVAL '180 days';
    
    -- 清理失败的翻译任务(30天前)
    DELETE FROM translation_tasks 
    WHERE status = 'failed' AND created_at < NOW() - INTERVAL '30 days';
    
    RAISE NOTICE '数据清理完成';
END;
$$ LANGUAGE plpgsql;

-- 创建定期清理任务(需要配合cron或pg_cron)
-- SELECT cron.schedule('cleanup-old-data', '0 2 * * *', 'SELECT cleanup_old_data();');

-- =====================================================
-- 15. 权限和安全
-- =====================================================

-- 创建应用用户角色
CREATE ROLE novel_app_user LOGIN PASSWORD 'secure_password_here';
CREATE ROLE novel_app_readonly LOGIN PASSWORD 'readonly_password_here';

-- 授予应用用户权限
GRANT CONNECT ON DATABASE novel_db TO novel_app_user;
GRANT USAGE ON SCHEMA public TO novel_app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO novel_app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO novel_app_user;

-- 授予只读用户权限
GRANT CONNECT ON DATABASE novel_db TO novel_app_readonly;
GRANT USAGE ON SCHEMA public TO novel_app_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO novel_app_readonly;

-- 设置默认权限
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO novel_app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO novel_app_readonly;

-- =====================================================
-- 完成数据库设计
-- =====================================================