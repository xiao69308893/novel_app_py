# 小说阅读APP后端 - 详细文件结构和功能说明

## 1. 技术栈选择

### 核心框架

- **Web框架**: FastAPI (异步、高性能、自动API文档)
- **数据库**: PostgreSQL (主数据库) + Redis (缓存/会话)
- **ORM**: SQLAlchemy 2.0 (异步支持)
- **认证**: JWT + Passlib (密码加密)
- **任务队列**: Celery + Redis (异步任务处理)
- **搜索引擎**: Elasticsearch (可选，用于全文搜索)
- **文件存储**: MinIO (对象存储) 或 云存储服务

### 辅助工具

- **API文档**: FastAPI 自动生成 + ReDoc
- **日志**: Loguru (结构化日志)
- **配置管理**: Pydantic Settings
- **数据验证**: Pydantic Models
- **测试**: Pytest + Pytest-asyncio
- **代码格式**: Black + isort + flake8
- **容器化**: Docker + Docker Compose

## 2. 系统架构图

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │     CDN         │    │   File Storage  │
│    (Nginx)      │    │                 │    │    (MinIO)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway                              │
│                       (FastAPI)                                 │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Business Layer                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │Auth Service │ │User Service │ │Novel Service│ │Reader Service││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │Translation  │ │ AI Service  │ │Config Mgmt  │ │Task Manager ││
│  │   Service   │ │  Gateway    │ │   Service   │ │   Service   ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │ PostgreSQL  │ │    Redis    │ │Elasticsearch│ │   Celery    ││
│  │  (Primary)  │ │  (Cache)    │ │  (Search)   │ │  (Tasks)    ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │  AI Models  │ │ Vector DB   │ │ Translation │ │ Message     ││
│  │(OpenAI/etc) │ │(Chroma/etc) │ │   Storage   │ │   Queue     ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## 3. 项目目录结构

```
novel_backend/
├── app/                           # 应用主目录
│   ├── __init__.py
│   ├── main.py                    # FastAPI 应用入口
│   ├── config/                    # 配置管理
│   │   ├── __init__.py
│   │   ├── settings.py           # 应用配置
│   │   ├── database.py           # 数据库配置
│   │   └── ai_config.py          # AI模型配置
│   ├── core/                      # 核心功能
│   │   ├── __init__.py
│   │   ├── deps.py               # 依赖注入
│   │   ├── security.py           # 安全相关
│   │   ├── exceptions.py         # 异常处理
│   │   └── middleware.py         # 中间件
│   ├── api/                       # API路由
│   │   ├── __init__.py
│   │   ├── v1/                   # API版本1
│   │   │   ├── __init__.py
│   │   │   ├── auth.py           # 认证接口
│   │   │   ├── users.py          # 用户接口
│   │   │   ├── novels.py         # 小说接口
│   │   │   ├── chapters.py       # 章节接口
│   │   │   ├── bookshelf.py      # 书架接口
│   │   │   ├── reader.py         # 阅读器接口
│   │   │   ├── translation.py    # 翻译接口
│   │   │   └── ai_models.py      # AI模型管理接口
│   │   └── deps.py               # API依赖
│   ├── models/                    # 数据模型
│   │   ├── __init__.py
│   │   ├── base.py               # 基础模型
│   │   ├── user.py               # 用户模型
│   │   ├── novel.py              # 小说模型
│   │   ├── chapter.py            # 章节模型
│   │   ├── bookmark.py           # 书签模型
│   │   ├── comment.py            # 评论模型
│   │   ├── translation.py        # 翻译相关模型
│   │   └── ai_model.py           # AI模型配置模型
│   ├── schemas/                   # Pydantic模式
│   │   ├── __init__.py
│   │   ├── base.py               # 基础模式
│   │   ├── auth.py               # 认证模式
│   │   ├── user.py               # 用户模式
│   │   ├── novel.py              # 小说模式
│   │   ├── translation.py        # 翻译模式
│   │   └── response.py           # 响应模式
│   ├── services/                  # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── base.py               # 基础服务
│   │   ├── auth_service.py       # 认证服务
│   │   ├── user_service.py       # 用户服务
│   │   ├── novel_service.py      # 小说服务
│   │   ├── chapter_service.py    # 章节服务
│   │   ├── reader_service.py     # 阅读服务
│   │   ├── translation_service.py # 翻译服务
│   │   └── ai_service.py         # AI服务
│   ├── ai/                        # AI相关模块
│   │   ├── __init__.py
│   │   ├── base_client.py        # AI客户端基类
│   │   ├── openai_client.py      # OpenAI客户端
│   │   ├── claude_client.py      # Claude客户端
│   │   ├── translation_engine.py # 翻译引擎
│   │   ├── outline_generator.py  # 大纲生成器
│   │   ├── character_mapper.py   # 角色名称映射器
│   │   └── quality_checker.py    # 翻译质量检查
│   ├── repositories/              # 数据访问层
│   │   ├── __init__.py
│   │   ├── base.py               # 基础仓库
│   │   ├── user_repo.py          # 用户仓库
│   │   ├── novel_repo.py         # 小说仓库
│   │   ├── chapter_repo.py       # 章节仓库
│   │   └── translation_repo.py   # 翻译仓库
│   ├── utils/                     # 工具函数
│   │   ├── __init__.py
│   │   ├── cache.py              # 缓存工具
│   │   ├── email.py              # 邮件工具
│   │   ├── file_storage.py       # 文件存储
│   │   ├── pagination.py         # 分页工具
│   │   └── text_processing.py    # 文本处理工具
│   └── tasks/                     # 异步任务
│       ├── __init__.py
│       ├── celery_app.py         # Celery配置
│       ├── email_tasks.py        # 邮件任务
│       ├── file_tasks.py         # 文件处理任务
│       └── translation_tasks.py  # 翻译任务
├── migrations/                    # 数据库迁移
│   └── versions/
├── tests/                         # 测试代码
│   ├── __init__.py
│   ├── conftest.py               # pytest配置
│   ├── test_auth.py              # 认证测试
│   ├── test_users.py             # 用户测试
│   ├── test_novels.py            # 小说测试
│   └── test_translation.py       # 翻译测试
├── scripts/                       # 脚本文件
│   ├── init_db.py                # 初始化数据库
│   ├── create_admin.py           # 创建管理员
│   └── init_ai_models.py         # 初始化AI模型配置
├── docker/                        # Docker配置
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── nginx.conf
├── requirements/                  # 依赖文件
│   ├── base.txt                  # 基础依赖
│   ├── dev.txt                   # 开发依赖
│   └── prod.txt                  # 生产依赖
├── .env.example                   # 环境变量示例
├── .gitignore
├── README.md
└── pyproject.toml                 # 项目配置
```

## 

## 📁 项目根目录结构

```
novel_backend/
├── app/                           # 📦 应用主目录
├── migrations/                    # 📦 数据库迁移文件
├── tests/                         # 📦 测试代码
├── scripts/                       # 📦 脚本文件
├── docker/                        # 📦 Docker配置
├── requirements/                  # 📦 依赖管理
├── .env.example                   # 🔧 环境变量示例
├── .gitignore                     # 🔧 Git忽略文件
├── README.md                      # 📄 项目说明
└── pyproject.toml                 # 🔧 项目配置文件
```

------

## 📦 app/ 应用主目录详解

### 📁 app/config/ - 配置管理模块

#### 📄 app/config/**init**.py

- **功能**: Python包标识文件
- **内容**: 空文件或导出主要配置类

#### 📄 app/config/settings.py

- **功能**: 应用核心配置管理

- 实现功能

  :

  - 环境变量读取和验证（使用Pydantic Settings）
  - 数据库连接配置（PostgreSQL URL、连接池参数）
  - Redis缓存配置（URL、数据库索引、连接参数）
  - JWT认证配置（密钥、过期时间、算法）
  - 文件存储配置（上传路径、文件大小限制）
  - 日志配置（级别、格式、输出目标）
  - AI模型基础配置（API密钥、基础URL）
  - 邮件服务配置（SMTP设置）
  - 限流配置（请求频率限制）

#### 📄 app/config/database.py

- **功能**: 数据库连接和会话管理

- 实现功能

  :

  - SQLAlchemy异步引擎创建和配置
  - 数据库连接池管理（连接数、超时、回收）
  - 异步会话工厂创建
  - 数据库初始化和健康检查
  - 事务管理辅助函数
  - 数据库连接状态监控

#### 📄 app/config/ai_config.py

- **功能**: AI模型配置和管理

- 实现功能

  :

  - DeepSeek API配置（API密钥、请求参数、模型列表）
  - 智谱AI配置（API密钥、模型版本、参数设置）
  - Ollama本地模型配置（服务地址、可用模型、参数）
  - 模型能力定义（翻译、大纲生成、角色分析、质量检查）
  - 模型选择策略配置
  - 速率限制和成本控制参数
  - 故障转移和负载均衡配置

------

### 📁 app/core/ - 核心功能模块

#### 📄 app/core/**init**.py

- **功能**: 核心模块初始化
- **内容**: 导出核心类和函数

#### 📄 app/core/deps.py

- **功能**: 依赖注入管理

- 实现功能

  :

  - 数据库会话依赖（异步会话获取和释放）
  - 用户认证依赖（JWT token验证和用户提取）
  - 权限检查依赖（基于角色的访问控制）
  - 分页参数依赖（页码、每页数量验证）
  - 缓存依赖（Redis连接获取）
  - AI服务依赖（模型客户端注入）
  - 文件上传依赖（文件类型和大小验证）

#### 📄 app/core/security.py

- **功能**: 安全相关功能

- 实现功能

  :

  - 密码加密和验证（bcrypt）
  - JWT token生成和验证
  - 访问token和刷新token管理
  - API密钥生成和验证
  - 请求签名验证
  - 输入数据净化（防XSS、SQL注入）
  - 敏感数据脱敏
  - 权限装饰器

#### 📄 app/core/exceptions.py

- **功能**: 异常处理定义

- 实现功能

  :

  - 自定义异常类定义（业务异常、认证异常、权限异常）
  - HTTP状态码映射
  - 异常消息国际化
  - 异常日志记录
  - 异常响应格式统一
  - 异常处理器注册
  - 开发和生产环境异常处理差异

#### 📄 app/core/middleware.py

- **功能**: 中间件集合

- 实现功能

  :

  - 请求日志中间件（记录请求响应详情）
  - 限流中间件（基于IP和用户的请求限制）
  - CORS中间件配置
  - 安全头中间件（添加安全相关HTTP头）
  - 请求ID生成中间件（用于追踪）
  - 性能监控中间件（响应时间统计）
  - 异常捕获中间件
  - 数据压缩中间件

------

### 📁 app/api/ - API路由模块

#### 📄 app/api/**init**.py

- **功能**: API模块初始化
- **内容**: 导出主要路由

#### 📄 app/api/deps.py

- **功能**: API专用依赖

- 实现功能

  :

  - API版本依赖
  - 请求验证依赖
  - 响应格式化依赖
  - API文档生成依赖

#### 📁 app/api/v1/ - API版本1

##### 📄 app/api/v1/**init**.py

- **功能**: V1 API路由集合
- **内容**: 导入并组织所有v1路由

##### 📄 app/api/v1/auth.py

- **功能**: 认证相关API接口

- 实现接口

  :

  - `POST /auth/login` - 密码登录
  - `POST /auth/login/phone` - 手机验证码登录
  - `POST /auth/register` - 用户注册
  - `POST /auth/logout` - 用户登出
  - `POST /auth/refresh` - 刷新token
  - `POST /auth/forgot-password` - 忘记密码
  - `PUT /auth/change-password` - 修改密码
  - `POST /auth/sms/send` - 发送短信验证码
  - `POST /auth/email/send` - 发送邮箱验证码
  - `POST /auth/phone/bind` - 绑定手机号
  - `POST /auth/email/bind` - 绑定邮箱
  - `GET /auth/user` - 获取当前用户信息
  - `DELETE /auth/account` - 删除账户

##### 📄 app/api/v1/users.py

- **功能**: 用户管理API接口

- 实现接口

  :

  - `GET /user/profile` - 获取用户资料
  - `PUT /user/profile` - 更新用户资料
  - `POST /user/avatar` - 上传用户头像
  - `GET /user/preferences` - 获取用户偏好设置
  - `PUT /user/preferences` - 更新用户偏好设置
  - `GET /user/stats` - 获取用户统计信息
  - `GET /user/settings` - 获取用户设置
  - `PUT /user/settings` - 更新用户设置
  - `POST /user/checkin` - 用户签到
  - `GET /user/checkin/status` - 获取签到状态

##### 📄 app/api/v1/novels.py

- **功能**: 小说相关API接口

- 实现接口

  :

  - `GET /novels` - 获取小说列表
  - `GET /novels/{id}` - 获取小说详情
  - `GET /novels/hot` - 获取热门小说
  - `GET /novels/new` - 获取最新小说
  - `GET /novels/search` - 搜索小说
  - `GET /novels/categories` - 获取小说分类
  - `GET /novels/rankings` - 获取排行榜
  - `GET /novels/recommendations` - 获取推荐小说
  - `GET /novels/personalized` - 获取个性化推荐
  - `GET /novels/{id}/similar` - 获取相似小说
  - `POST /novels/{id}/favorite` - 收藏小说
  - `DELETE /novels/{id}/favorite` - 取消收藏
  - `POST /novels/{id}/rate` - 评分小说
  - `GET /novels/{id}/comments` - 获取小说评论
  - `POST /novels/{id}/share` - 分享小说

##### 📄 app/api/v1/chapters.py

- **功能**: 章节相关API接口

- 实现接口

  :

  - `GET /novels/{novel_id}/chapters` - 获取章节列表
  - `GET /chapters/{id}` - 获取章节详情
  - `GET /chapters/{id}/content` - 获取章节内容
  - `GET /chapters/{id}/adjacent` - 获取相邻章节
  - `GET /chapters/{id}/comments` - 获取章节评论
  - `POST /chapters/{id}/comments` - 发表章节评论
  - `POST /chapters/{id}/download` - 下载章节
  - `GET /novels/{novel_id}/chapters/search` - 搜索章节
  - `POST /purchases/chapters` - 购买章节
  - `GET /purchases/chapters/status` - 检查购买状态

##### 📄 app/api/v1/bookshelf.py

- **功能**: 书架相关API接口

- 实现接口

  :

  - `GET /user/favorites` - 获取收藏列表
  - `POST /user/favorites` - 添加收藏
  - `DELETE /user/favorites/{novel_id}` - 移除收藏
  - `GET /user/favorites/{novel_id}/status` - 检查收藏状态
  - `POST /user/favorites/batch` - 批量操作收藏
  - `GET /user/favorites/search` - 搜索收藏
  - `GET /user/reading-history` - 获取阅读历史
  - `POST /user/reading-history` - 添加阅读记录
  - `DELETE /user/reading-history` - 清理阅读历史
  - `GET /user/recently-read` - 获取最近阅读
  - `GET /user/data/export` - 导出用户数据
  - `POST /user/data/import` - 导入用户数据
  - `POST /user/data/sync` - 同步数据

##### 📄 app/api/v1/reader.py

- **功能**: 阅读器相关API接口

- 实现接口

  :

  - `GET /reading/progress/{novel_id}` - 获取阅读进度
  - `POST /reading/progress` - 保存阅读进度
  - `PUT /reading/progress` - 更新阅读进度
  - `POST /reading/progress/sync` - 同步阅读进度
  - `GET /bookmarks` - 获取书签列表
  - `POST /bookmarks` - 添加书签
  - `DELETE /bookmarks/{id}` - 删除书签
  - `PUT /bookmarks/{id}` - 更新书签
  - `GET /reading/settings` - 获取阅读设置
  - `PUT /reading/settings` - 更新阅读设置
  - `POST /reading/time` - 更新阅读时长
  - `GET /reading/stats` - 获取阅读统计

##### 📄 app/api/v1/translation.py

- **功能**: 翻译相关API接口

- 实现接口

  :

  - `GET /translation/projects` - 获取翻译项目列表
  - `POST /translation/projects` - 创建翻译项目
  - `GET /translation/projects/{id}` - 获取翻译项目详情
  - `PUT /translation/projects/{id}` - 更新翻译项目
  - `DELETE /translation/projects/{id}` - 删除翻译项目
  - `POST /translation/projects/{id}/start` - 启动翻译任务
  - `POST /translation/projects/{id}/pause` - 暂停翻译任务
  - `POST /translation/projects/{id}/resume` - 恢复翻译任务
  - `GET /translation/projects/{id}/progress` - 获取翻译进度
  - `GET /translation/projects/{id}/characters` - 获取角色映射
  - `POST /translation/projects/{id}/characters` - 创建角色映射
  - `PUT /translation/projects/{id}/characters/{char_id}` - 更新角色映射
  - `GET /translation/configs` - 获取翻译配置列表
  - `POST /translation/configs` - 创建翻译配置
  - `GET /translation/projects/{id}/chapters` - 获取翻译章节列表
  - `GET /translation/chapters/{id}` - 获取翻译章节详情
  - `POST /translation/chapters/{id}/review` - 审核翻译章节
  - `GET /translation/projects/{id}/stats` - 获取翻译统计

##### 📄 app/api/v1/ai_models.py

- **功能**: AI模型管理API接口

- 实现接口

  :

  - `GET /ai/models` - 获取可用AI模型列表
  - `GET /ai/models/{id}` - 获取AI模型详情
  - `PUT /ai/models/{id}` - 更新AI模型配置
  - `POST /ai/models/test` - 测试AI模型连接
  - `GET /ai/models/{id}/stats` - 获取模型使用统计
  - `GET /ai/models/{id}/health` - 检查模型健康状态

------

### 📁 app/models/ - 数据模型模块

#### 📄 app/models/**init**.py

- **功能**: 模型模块初始化
- **内容**: 导出所有模型类

#### 📄 app/models/base.py

- **功能**: 基础模型类

- 实现功能

  :

  - 基础字段定义（id、created_at、updated_at）
  - 公共方法（to_dict、from_dict）
  - 软删除支持
  - 审计字段（创建者、修改者）
  - 时间戳自动更新
  - 模型序列化方法

#### 📄 app/models/user.py

- **功能**: 用户相关模型

- 包含模型

  :

  - `User` - 用户基础信息
  - `UserProfile` - 用户详细资料
  - `UserSettings` - 用户设置
  - `UserStats` - 用户统计
  - `LoginLog` - 登录日志
  - `UserDevice` - 用户设备信息

#### 📄 app/models/novel.py

- **功能**: 小说相关模型

- 包含模型

  :

  - `Novel` - 小说基础信息
  - `Category` - 小说分类
  - `Tag` - 小说标签
  - `NovelTag` - 小说标签关联
  - `Author` - 作者信息
  - `NovelStats` - 小说统计
  - `NovelRating` - 小说评分

#### 📄 app/models/chapter.py

- **功能**: 章节相关模型

- 包含模型

  :

  - `Chapter` - 章节基础信息
  - `ChapterContent` - 章节内容（可分离存储）
  - `ReadingProgress` - 阅读进度
  - `ChapterPurchase` - 章节购买记录

#### 📄 app/models/bookmark.py

- **功能**: 书签相关模型

- 包含模型

  :

  - `Bookmark` - 书签信息
  - `BookmarkFolder` - 书签文件夹
  - `ReadingHistory` - 阅读历史

#### 📄 app/models/comment.py

- **功能**: 评论相关模型

- 包含模型

  :

  - `Comment` - 评论信息
  - `CommentLike` - 评论点赞
  - `CommentReport` - 评论举报

#### 📄 app/models/translation.py

- **功能**: 翻译相关模型

- 包含模型

  :

  - `TranslationProject` - 翻译项目
  - `TranslationConfig` - 翻译配置
  - `TranslatedNovel` - 翻译后小说
  - `TranslatedChapter` - 翻译后章节
  - `CharacterMapping` - 角色映射
  - `TranslationTask` - 翻译任务
  - `TranslationStatistics` - 翻译统计
  - `TranslationQualityCheck` - 翻译质量检查

#### 📄 app/models/ai_model.py

- **功能**: AI模型相关模型

- 包含模型

  :

  - `AIModel` - AI模型配置
  - `AIModelUsage` - 模型使用记录
  - `AIModelStats` - 模型统计信息

------

### 📁 app/schemas/ - Pydantic模式模块

#### 📄 app/schemas/**init**.py

- **功能**: 模式模块初始化
- **内容**: 导出所有模式类

#### 📄 app/schemas/base.py

- **功能**: 基础Pydantic模式

- 实现功能

  :

  - 基础响应模式（成功、错误、分页）
  - 通用字段验证器
  - 时间格式标准化
  - 多语言支持
  - 数据转换辅助函数

#### 📄 app/schemas/auth.py

- **功能**: 认证相关数据模式

- 包含模式

  :

  - `LoginRequest` - 登录请求
  - `RegisterRequest` - 注册请求
  - `TokenResponse` - Token响应
  - `PasswordChangeRequest` - 密码修改请求
  - `SMSCodeRequest` - 短信验证码请求
  - `EmailCodeRequest` - 邮箱验证码请求

#### 📄 app/schemas/user.py

- **功能**: 用户相关数据模式

- 包含模式

  :

  - `UserCreate` - 用户创建
  - `UserUpdate` - 用户更新
  - `UserResponse` - 用户响应
  - `UserProfile` - 用户资料
  - `UserSettings` - 用户设置
  - `UserStats` - 用户统计

#### 📄 app/schemas/novel.py

- **功能**: 小说相关数据模式

- 包含模式

  :

  - `NovelResponse` - 小说响应
  - `NovelListResponse` - 小说列表响应
  - `ChapterResponse` - 章节响应
  - `ChapterListResponse` - 章节列表响应
  - `NovelSearchRequest` - 小说搜索请求
  - `CommentCreate` - 评论创建
  - `CommentResponse` - 评论响应

#### 📄 app/schemas/translation.py

- **功能**: 翻译相关数据模式

- 包含模式

  :

  - `TranslationProjectCreate` - 翻译项目创建
  - `TranslationProjectUpdate` - 翻译项目更新
  - `TranslationProjectResponse` - 翻译项目响应
  - `TranslationConfigCreate` - 翻译配置创建
  - `CharacterMappingCreate` - 角色映射创建
  - `TranslationProgressResponse` - 翻译进度响应
  - `TranslationTaskResponse` - 翻译任务响应
  - `TranslationStatsResponse` - 翻译统计响应

#### 📄 app/schemas/response.py

- **功能**: 标准响应格式

- 实现功能

  :

  - 统一API响应格式
  - 分页响应格式
  - 错误响应格式
  - 成功响应格式
  - 批量操作响应格式

------

### 📁 app/services/ - 业务逻辑层

#### 📄 app/services/**init**.py

- **功能**: 服务模块初始化
- **内容**: 导出所有服务类

#### 📄 app/services/base.py

- **功能**: 基础服务类

- 实现功能

  :

  - CRUD操作基类
  - 事务管理
  - 缓存集成
  - 日志记录
  - 异常处理
  - 分页查询
  - 批量操作

#### 📄 app/services/auth_service.py

- **功能**: 认证服务

- 实现功能

  :

  - 用户注册逻辑
  - 用户登录验证
  - Token生成和验证
  - 密码重置流程
  - 验证码发送和验证
  - 第三方账号绑定
  - 账户安全管理
  - 登录日志记录

#### 📄 app/services/user_service.py

- **功能**: 用户服务

- 实现功能

  :

  - 用户信息管理
  - 用户偏好设置
  - 用户统计计算
  - 签到功能
  - 用户等级计算
  - 积分和金币管理
  - 用户关系管理
  - 数据导入导出

#### 📄 app/services/novel_service.py

- **功能**: 小说服务

- 实现功能

  :

  - 小说信息管理
  - 小说搜索和过滤
  - 推荐算法实现
  - 排行榜计算
  - 小说统计更新
  - 收藏管理
  - 评分系统
  - 内容审核

#### 📄 app/services/chapter_service.py

- **功能**: 章节服务

- 实现功能

  :

  - 章节内容管理
  - 章节购买逻辑
  - 阅读权限控制
  - 章节缓存管理
  - 内容分段和预加载
  - 章节下载服务
  - 阅读统计

#### 📄 app/services/reader_service.py

- **功能**: 阅读服务

- 实现功能

  :

  - 阅读进度管理
  - 书签管理
  - 阅读设置同步
  - 阅读时长统计
  - 阅读历史记录
  - 多端同步
  - 离线阅读支持

#### 📄 app/services/translation_service.py

- **功能**: 翻译服务

- 实现功能

  :

  - 翻译项目管理
  - 翻译任务调度
  - 翻译质量控制
  - 角色映射管理
  - 翻译进度跟踪
  - 翻译结果存储
  - 成本统计和控制
  - 批量翻译处理

#### 📄 app/services/ai_service.py

- **功能**: AI服务

- 实现功能

  :

  - AI模型调用管理
  - 请求负载均衡
  - 错误处理和重试
  - 模型性能监控
  - 成本跟踪
  - 缓存策略
  - 模型选择策略

------

### 📁 app/ai/ - AI相关模块

#### 📄 app/ai/**init**.py

- **功能**: AI模块初始化
- **内容**: 导出AI客户端和工具类

#### 📄 app/ai/base_client.py

- **功能**: AI客户端基类

- 实现功能

  :

  - 统一AI客户端接口定义
  - 基础HTTP请求处理
  - 通用错误处理
  - 请求重试机制
  - 速率限制处理
  - 响应格式标准化
  - 日志记录

#### 📄 app/ai/deepseek_client.py

- **功能**: DeepSeek API客户端

- 实现功能

  :

  - DeepSeek API调用封装
  - 模型参数配置
  - 请求格式转换
  - 响应解析
  - 错误码处理
  - 流式响应支持
  - Token使用统计

#### 📄 app/ai/zhipu_client.py

- **功能**: 智谱AI客户端

- 实现功能

  :

  - 智谱AI API调用封装
  - GLM模型支持
  - 请求认证处理
  - 响应格式适配
  - 异步调用支持
  - 批量请求处理
  - 使用量监控

#### 📄 app/ai/ollama_client.py

- **功能**: Ollama本地模型客户端

- 实现功能

  :

  - Ollama服务连接管理
  - 本地模型调用
  - 模型下载和管理
  - 服务健康检查
  - 并发请求处理
  - 资源使用监控
  - 模型切换支持

#### 📄 app/ai/translation_engine.py

- **功能**: 翻译引擎核心

- 实现功能

  :

  - 翻译任务编排
  - 多模型协作
  - 翻译策略选择
  - 上下文管理
  - 翻译结果合并
  - 质量评估
  - 错误恢复

#### 📄 app/ai/outline_generator.py

- **功能**: 大纲生成器

- 实现功能

  :

  - 章节大纲自动生成
  - 情节结构分析
  - 角色关系提取
  - 关键事件识别
  - 大纲格式化
  - 大纲验证
  - 多语言支持

#### 📄 app/ai/character_mapper.py

- **功能**: 角色名称映射器

- 实现功能

  :

  - 角色名称自动识别
  - 角色关系分析
  - 名称翻译和本地化
  - 角色一致性检查
  - 映射规则管理
  - 手动映射支持
  - 角色出现频率统计

#### 📄 app/ai/quality_checker.py

- **功能**: 翻译质量检查器

- 实现功能

  :

  - 翻译质量自动评估
  - 语法和语义检查
  - 风格一致性验证
  - 术语一致性检查
  - 文化适应性评估
  - 可读性分析
  - 质量评分生成

------

### 📁 app/repositories/ - 数据访问层

#### 📄 app/repositories/**init**.py

- **功能**: 仓库模块初始化
- **内容**: 导出所有仓库类

#### 📄 app/repositories/base.py

- **功能**: 基础仓库类

- 实现功能

  :

  - 通用CRUD操作
  - 异步数据库操作
  - 查询条件构建
  - 分页查询支持
  - 批量操作
  - 事务支持
  - 缓存集成
  - 软删除支持

#### 📄 app/repositories/user_repo.py

- **功能**: 用户数据仓库

- 实现功能

  :

  - 用户基础CRUD操作
  - 用户查询和搜索
  - 用户关系查询
  - 登录历史记录
  - 用户统计查询
  - 批量用户操作
  - 用户设置管理

#### 📄 app/repositories/novel_repo.py

- **功能**: 小说数据仓库

- 实现功能

  :

  - 小说基础CRUD操作
  - 复杂搜索查询
  - 排行榜查询
  - 推荐算法数据支持
  - 小说统计查询
  - 分类和标签查询
  - 收藏关系管理

#### 📄 app/repositories/chapter_repo.py

- **功能**: 章节数据仓库

- 实现功能

  :

  - 章节基础CRUD操作
  - 章节列表查询
  - 章节内容管理
  - 阅读进度查询
  - 章节购买记录
  - 批量章节操作
  - 章节统计查询

#### 📄 app/repositories/translation_repo.py

- **功能**: 翻译数据仓库

- 实现功能

  :

  - 翻译项目CRUD操作
  - 翻译任务管理
  - 角色映射查询
  - 翻译进度跟踪
  - 翻译质量数据
  - 翻译统计查询
  - 批量翻译操作

------

### 📁 app/utils/ - 工具函数模块

#### 📄 app/utils/**init**.py

- **功能**: 工具模块初始化
- **内容**: 导出工具函数

#### 📄 app/utils/cache.py

- **功能**: 缓存工具

- 实现功能

  :

  - Redis连接管理
  - 缓存键生成策略
  - 缓存装饰器
  - 分布式锁实现
  - 缓存失效策略
  - 批量缓存操作
  - 缓存统计监控

#### 📄 app/utils/email.py

- **功能**: 邮件工具

- 实现功能

  :

  - SMTP连接管理
  - 邮件模板系统
  - 异步邮件发送
  - 邮件队列管理
  - 发送状态跟踪
  - 邮件内容格式化
  - 附件处理

#### 📄 app/utils/file_storage.py

- **功能**: 文件存储工具

- 实现功能

  :

  - 本地文件存储
  - 云存储集成（可选）
  - 文件上传处理
  - 图片处理和压缩
  - 文件类型验证
  - 存储空间管理
  - 文件访问URL生成

#### 📄 app/utils/pagination.py

- **功能**: 分页工具

- 实现功能

  :

  - 分页参数处理
  - 分页响应格式化
  - 游标分页支持
  - 分页缓存优化
  - 分页链接生成
  - 大数据集分页优化

#### 📄 app/utils/text_processing.py

- **功能**: 文本处理工具

- 实现功能

  :

  - 文本清理和标准化
  - 关键词提取
  - 文本相似度计算
  - 语言检测
  - 敏感词过滤
  - 文本摘要生成
  - 格式转换

------

### 📁 app/tasks/ - 异步任务模块

#### 📄 app/tasks/**init**.py

- **功能**: 任务模块初始化
- **内容**: 导出任务函数

#### 📄 app/tasks/celery_app.py

- **功能**: Celery应用配置

- 实现功能

  :

  - Celery实例创建和配置
  - 任务路由配置
  - 结果后端配置
  - 任务序列化设置
  - 监控配置
  - 错误处理配置
  - 定时任务配置

#### 📄 app/tasks/email_tasks.py

- **功能**: 邮件相关异步任务

- 实现功能

  :

  - 注册确认邮件发送
  - 密码重置邮件发送
  - 营销邮件发送
  - 系统通知邮件发送
  - 邮件发送失败重试
  - 邮件发送统计

#### 📄 app/tasks/file_tasks.py

- **功能**: 文件处理异步任务

- 实现功能

  :

  - 图片压缩和处理
  - 文件格式转换
  - 批量文件操作
  - 文件清理任务
  - 备份任务
  - 文件病毒扫描

#### 📄 app/tasks/translation_tasks.py

- **功能**: 翻译相关异步任务

- 实现功能

  :

  - 翻译任务执行
  - 大纲生成任务
  - 角色映射任务
  - 质量检查任务
  - 批量翻译处理
  - 翻译结果后处理
  - 翻译统计更新

------

## 📦 其他目录详解

### 📁 migrations/ - 数据库迁移

- **功能**: 数据库版本控制和迁移

- 文件结构

  :

  - `versions/` - 迁移版本文件
  - `env.py` - Alembic环境配置
  - `script.py.mako` - 迁移脚本模板
  - `alembic.ini` - Alembic配置文件

### 📁 tests/ - 测试代码

- **功能**: 单元测试和集成测试

- 文件结构

  :

  - `conftest.py` - pytest配置和fixture
  - `test_auth.py` - 认证功能测试
  - `test_users.py` - 用户功能测试
  - `test_novels.py` - 小说功能测试
  - `test_translation.py` - 翻译功能测试
  - `test_ai_models.py` - AI模型测试
  - `fixtures/` - 测试数据
  - `integration/` - 集成测试

### 📁 scripts/ - 脚本文件

- **功能**: 管理和维护脚本

- 文件结构

  :

  - `init_db.py` - 数据库初始化脚本
  - `create_admin.py` - 创建管理员用户
  - `init_ai_models.py` - 初始化AI模型配置
  - `data_migration.py` - 数据迁移脚本
  - `backup.py` - 数据备份脚本
  - `performance_test.py` - 性能测试脚本

### 📁 docker/ - 容器化配置

- **功能**: Docker部署配置

- 文件结构

  :

  - `Dockerfile` - 应用容器构建文件
  - `docker-compose.yml` - 多服务编排
  - `docker-compose.prod.yml` - 生产环境配置
  - `nginx.conf` - Nginx配置文件
  - `supervisord.conf` - 进程管理配置

### 📁 requirements/ - 依赖管理

- **功能**: Python依赖包管理

- 文件结构

  :

  - `base.txt` - 基础依赖包
  - `dev.txt` - 开发环境依赖
  - `prod.txt` - 生产环境依赖
  - `test.txt` - 测试环境依赖

------

## 🔧 根目录配置文件

### 📄 .env.example

- **功能**: 环境变量配置示例

- 包含内容

  :

  - 数据库连接信息
  - Redis配置
  - JWT密钥
  - AI模型API密钥
  - 邮件服务配置
  - 文件存储配置

### 📄 pyproject.toml

- **功能**: 项目配置和元数据

- 包含内容

  :

  - 项目基本信息
  - 依赖管理配置
  - 代码格式化配置
  - 测试配置
  - 构建配置

### 📄 README.md

- **功能**: 项目说明文档

- 包含内容

  :

  - 项目介绍
  - 安装和运行指南
  - API文档链接
  - 开发指南
  - 部署说明
  - 贡献指南

