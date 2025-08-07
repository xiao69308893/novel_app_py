# 小说阅读APP - API接口文档

## 基础信息

### 服务器地址

- **开发环境**: `https://dev-api.novelapp.com`
- **生产环境**: `https://api.novelapp.com`
- **API版本**: `v1`
- **完整路径**: `{baseUrl}/api/v1`

### 请求头配置

```json
{
  "Content-Type": "application/json",
  "Accept": "application/json",
  "User-Agent": "NovelApp/1.0.0",
  "X-App-Version": "1.0.0",
  "X-Platform": "{platform}",
  "Authorization": "Bearer {token}" // 需要认证的接口
}
```

### 通用响应格式

```json
{
  "success": true,
  "code": 200,
  "message": "操作成功",
  "data": {}, // 响应数据
  "pagination": { // 分页信息（列表接口）
    "page": 1,
    "page_size": 20,
    "total": 100,
    "has_more": true
  }
}
```

------

## 1. 认证模块 (Auth)

### 1.1 用户登录 - 密码登录

**POST** `/auth/login`

**请求参数:**

```json
{
  "username": "string", // 用户名
  "password": "string"  // 密码
}
```

**响应数据:**

```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "string",
    "username": "string",
    "email": "string",
    "avatar": "string"
  }
}
```

### 1.2 用户登录 - 手机验证码登录

**POST** `/auth/login/phone`

**请求参数:**

```json
{
  "phone": "string",           // 手机号
  "verification_code": "string" // 验证码
}
```

### 1.3 用户注册

**POST** `/auth/register`

**请求参数:**

```json
{
  "username": "string",    // 用户名（必填）
  "password": "string",    // 密码（必填）
  "email": "string",       // 邮箱（可选）
  "phone": "string",       // 手机号（可选）
  "invite_code": "string"  // 邀请码（可选）
}
```

### 1.4 发送短信验证码

**POST** `/auth/sms/send`

**请求参数:**

```json
{
  "phone": "string", // 手机号
  "type": "string"   // 验证码类型: login, register, forgot_password
}
```

### 1.5 发送邮箱验证码

**POST** `/auth/email/send`

**请求参数:**

```json
{
  "email": "string", // 邮箱
  "type": "string"   // 验证码类型: login, register, forgot_password
}
```

### 1.6 忘记密码

**POST** `/auth/password/forgot`

**请求参数:**

```json
{
  "account": "string",          // 账号（手机号或邮箱）
  "verification_code": "string", // 验证码
  "new_password": "string"      // 新密码
}
```

### 1.7 刷新Token

**POST** `/auth/token/refresh`

**请求参数:**

```json
{
  "refresh_token": "string"
}
```

### 1.8 获取当前用户信息

**GET** `/auth/user`

**Headers:** `Authorization: Bearer {token}`

### 1.9 用户登出

**POST** `/auth/logout`

**Headers:** `Authorization: Bearer {token}`

### 1.10 修改密码

**PUT** `/auth/password/change`

**Headers:** `Authorization: Bearer {token}`

**请求参数:**

```json
{
  "old_password": "string",
  "new_password": "string"
}
```

### 1.11 绑定手机号

**POST** `/auth/phone/bind`

**Headers:** `Authorization: Bearer {token}`

**请求参数:**

```json
{
  "phone": "string",
  "verification_code": "string"
}
```

### 1.12 绑定邮箱

**POST** `/auth/email/bind`

**Headers:** `Authorization: Bearer {token}`

**请求参数:**

```json
{
  "email": "string",
  "verification_code": "string"
}
```

------

## 2. 首页模块 (Home)

### 2.1 获取首页配置

**GET** `/home/config`

**响应数据:**

```json
{
  "banners_enabled": true,
  "recommendations_enabled": true,
  "rankings_enabled": true,
  "hot_novels_limit": 20,
  "new_novels_limit": 20
}
```

### 2.2 获取轮播图

**GET** `/home/banners`

**响应数据:**

```json
[
  {
    "id": "string",
    "title": "string",
    "image_url": "string",
    "link_url": "string",
    "link_type": "string", // novel, category, external
    "sort_order": 1,
    "status": "active"
  }
]
```

### 2.3 获取推荐内容

**GET** `/home/recommendations`

**查询参数:**

- `type` (string, 可选): 推荐类型
- `page` (int, 默认1): 页码
- `limit` (int, 默认10): 每页数量

### 2.4 获取排行榜

**GET** `/home/ranking`

**查询参数:**

- `type` (string, 必填): 排行榜类型 (hot, new, complete)
- `period` (string, 默认weekly): 时间周期 (daily, weekly, monthly)
- `limit` (int, 默认50): 返回数量

### 2.5 获取热门小说

**GET** `/novels/hot`

**查询参数:**

- `page` (int, 默认1): 页码
- `limit` (int, 默认20): 每页数量

### 2.6 获取最新小说

**GET** `/novels/new`

**查询参数:**

- `page` (int, 默认1): 页码
- `limit` (int, 默认20): 每页数量

### 2.7 获取编辑推荐

**GET** `/novels/editor-recommendations`

**查询参数:**

- `page` (int, 默认1): 页码
- `limit` (int, 默认20): 每页数量

### 2.8 获取个性化推荐

**GET** `/novels/personalized`

**Headers:** `Authorization: Bearer {token}`

**查询参数:**

- `page` (int, 默认1): 页码
- `limit` (int, 默认20): 每页数量

### 2.9 获取分类热门小说

**GET** `/novels/category/{categoryId}/hot`

**路径参数:**

- `categoryId` (string): 分类ID

**查询参数:**

- `page` (int, 默认1): 页码
- `limit` (int, 默认20): 每页数量

### 2.10 搜索小说

**GET** `/novels/search`

**查询参数:**

- `keyword` (string, 必填): 搜索关键词
- `category_id` (string, 可选): 分类ID
- `status` (string, 可选): 小说状态
- `sort_by` (string, 可选): 排序方式
- `page` (int, 默认1): 页码
- `limit` (int, 默认20): 每页数量

### 2.11 获取热门搜索关键词

**GET** `/search/hot-keywords`

**响应数据:**

```json
["关键词1", "关键词2", "关键词3"]
```

### 2.12 获取搜索建议

**GET** `/search/suggestions`

**查询参数:**

- `keyword` (string): 输入的关键词

------

## 3. 小说模块 (Book)

### 3.1 获取小说详情

**GET** `/books/{bookId}`

**路径参数:**

- `bookId` (string): 小说ID

**响应数据:**

```json
{
  "id": "string",
  "title": "string",
  "author": "string",
  "cover_url": "string",
  "description": "string",
  "category": "string",
  "tags": ["string"],
  "status": "string", // ongoing, completed, paused
  "word_count": 100000,
  "chapter_count": 100,
  "rating": 4.5,
  "view_count": 10000,
  "favorite_count": 1000,
  "comment_count": 500,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

### 3.2 获取章节列表

**GET** `/books/{bookId}/chapters`

**路径参数:**

- `bookId` (string): 小说ID

**查询参数:**

- `page` (int, 默认1): 页码
- `limit` (int, 默认50): 每页数量

### 3.3 获取章节详情

**GET** `/chapters/{chapterId}`

**路径参数:**

- `chapterId` (string): 章节ID

**响应数据:**

```json
{
  "id": "string",
  "novel_id": "string",
  "title": "string",
  "content": "string",
  "word_count": 2000,
  "chapter_number": 1,
  "is_vip": false,
  "price": 0,
  "created_at": "2023-01-01T00:00:00Z"
}
```

### 3.4 获取小说评论

**GET** `/books/{bookId}/comments`

**路径参数:**

- `bookId` (string): 小说ID

**查询参数:**

- `page` (int, 默认1): 页码
- `limit` (int, 默认20): 每页数量

### 3.5 获取章节评论

**GET** `/chapters/{chapterId}/comments`

**路径参数:**

- `chapterId` (string): 章节ID

**查询参数:**

- `page` (int, 默认1): 页码
- `limit` (int, 默认20): 每页数量

### 3.6 发表评论

**POST** `/comments`

**Headers:** `Authorization: Bearer {token}`

**请求参数:**

```json
{
  "target_id": "string",    // 目标ID（小说ID或章节ID）
  "type": "string",         // 评论类型: book, chapter
  "content": "string",      // 评论内容
  "parent_id": "string"     // 父评论ID（回复评论时使用）
}
```

### 3.7 点赞评论

**POST** `/comments/{commentId}/like`

**Headers:** `Authorization: Bearer {token}`

**路径参数:**

- `commentId` (string): 评论ID

### 3.8 取消点赞评论

**DELETE** `/comments/{commentId}/like`

**Headers:** `Authorization: Bearer {token}`

### 3.9 删除评论

**DELETE** `/comments/{commentId}`

**Headers:** `Authorization: Bearer {token}`

### 3.10 收藏小说

**POST** `/books/{bookId}/favorite`

**Headers:** `Authorization: Bearer {token}`

### 3.11 取消收藏小说

**DELETE** `/books/{bookId}/favorite`

**Headers:** `Authorization: Bearer {token}`

### 3.12 评分小说

**POST** `/books/{bookId}/rate`

**Headers:** `Authorization: Bearer {token}`

**请求参数:**

```json
{
  "rating": 5,           // 评分 1-5
  "review": "string"     // 评价内容（可选）
}
```

### 3.13 分享小说

**POST** `/books/{bookId}/share`

**Headers:** `Authorization: Bearer {token}`

**请求参数:**

```json
{
  "platform": "string"  // 分享平台
}
```

### 3.14 举报内容

**POST** `/reports`

**Headers:** `Authorization: Bearer {token}`

**请求参数:**

```json
{
  "target_id": "string",      // 目标ID
  "type": "string",           // 举报类型: book, chapter, comment
  "reason": "string",         // 举报原因
  "description": "string"     // 举报描述（可选）
}
```

### 3.15 下载章节

**POST** `/chapters/{chapterId}/download`

**Headers:** `Authorization: Bearer {token}`

**响应数据:**

```json
{
  "task_id": "string"  // 下载任务ID
}
```

### 3.16 下载小说

**POST** `/books/{bookId}/download`

**Headers:** `Authorization: Bearer {token}`

### 3.17 取消下载

**DELETE** `/downloads/{taskId}`

**Headers:** `Authorization: Bearer {token}`

### 3.18 获取阅读进度

**GET** `/books/{bookId}/progress`

**Headers:** `Authorization: Bearer {token}`

### 3.19 更新阅读进度

**PUT** `/books/{bookId}/progress`

**Headers:** `Authorization: Bearer {token}`

**请求参数:**

```json
{
  "chapter_id": "string",
  "position": 100,      // 阅读位置
  "progress": 0.5       // 阅读进度百分比
}
```

### 3.20 获取相似小说

**GET** `/books/{bookId}/similar`

**查询参数:**

- `limit` (int, 默认10): 返回数量

### 3.21 获取作者其他作品

**GET** `/authors/{authorId}/books`

**查询参数:**

- `exclude` (string, 可选): 排除的小说ID
- `limit` (int, 默认10): 返回数量

------

## 4. 书架模块 (Bookshelf)

### 4.1 获取收藏小说列表

**GET** `/user/favorites`

**Headers:** `Authorization: Bearer {token}`

**查询参数:**

- `page` (int, 默认1): 页码
- `limit` (int, 默认20): 每页数量
- `sort_by` (string, 可选): 排序方式
- `filter_by` (string, 可选): 过滤条件

### 4.2 获取推荐小说列表

**GET** `/novels/recommended`

**查询参数:**

- `page` (int, 默认1): 页码
- `limit` (int, 默认20): 每页数量

### 4.3 添加到收藏

**POST** `/user/favorites`

**Headers:** `Authorization: Bearer {token}`

**请求参数:**

```json
{
  "novel_id": "string"
}
```

### 4.4 从收藏中移除

**DELETE** `/user/favorites/{novelId}`

**Headers:** `Authorization: Bearer {token}`

### 4.5 检查收藏状态

**GET** `/user/favorites/{novelId}/status`

**Headers:** `Authorization: Bearer {token}`

### 4.6 批量添加收藏

**POST** `/user/favorites/batch`

**Headers:** `Authorization: Bearer {token}`

**请求参数:**

```json
{
  "novel_ids": ["string"],
  "action": "add"
}
```

### 4.7 批量移除收藏

**POST** `/user/favorites/batch`

**Headers:** `Authorization: Bearer {token}`

**请求参数:**

```json
{
  "novel_ids": ["string"],
  "action": "remove"
}
```

### 4.8 获取用户资料

**GET** `/user/profile`

**Headers:** `Authorization: Bearer {token}`

### 4.9 更新用户资料

**PUT** `/user/profile`

**Headers:** `Authorization: Bearer {token}`

### 4.10 用户签到

**POST** `/user/checkin`

**Headers:** `Authorization: Bearer {token}`

### 4.11 获取签到状态

**GET** `/user/checkin/status`

**Headers:** `Authorization: Bearer {token}`

### 4.12 导出用户数据

**GET** `/user/data/export`

**Headers:** `Authorization: Bearer {token}`

**响应数据:**

```json
{
  "download_url": "string"
}
```

### 4.13 导入用户数据

**POST** `/user/data/import`

**Headers:** `Authorization: Bearer {token}`

**请求参数:**

```json
{
  "data_path": "string"
}
```

### 4.14 同步数据

**POST** `/user/data/sync`

**Headers:** `Authorization: Bearer {token}`

### 4.15 删除账户

**DELETE** `/user/account`

**Headers:** `Authorization: Bearer {token}`

### 4.16 获取阅读历史

**GET** `/user/reading-history`

**Headers:** `Authorization: Bearer {token}`

**查询参数:**

- `page` (int, 默认1): 页码
- `limit` (int, 默认20): 每页数量

### 4.17 添加阅读历史

**POST** `/user/reading-history`

**Headers:** `Authorization: Bearer {token}`

**请求参数:**

```json
{
  "novel_id": "string",
  "chapter_id": "string",
  "reading_time": 300,      // 阅读时长（秒）
  "last_position": "string" // 最后阅读位置（可选）
}
```

### 4.18 清理阅读历史

**DELETE** `/user/reading-history`

**Headers:** `Authorization: Bearer {token}`

**请求参数:**

```json
{
  "novel_ids": ["string"]  // 指定小说ID，为空则清空所有
}
```

### 4.19 获取用户统计

**GET** `/user/stats`

**Headers:** `Authorization: Bearer {token}`

### 4.20 获取用户设置

**GET** `/user/settings`

**Headers:** `Authorization: Bearer {token}`

### 4.21 更新用户设置

**PUT** `/user/settings`

**Headers:** `Authorization: Bearer {token}`

### 4.22 搜索收藏小说

**GET** `/user/favorites/search`

**Headers:** `Authorization: Bearer {token}`

**查询参数:**

- `keyword` (string, 必填): 搜索关键词
- `page` (int, 默认1): 页码
- `limit` (int, 默认20): 每页数量

### 4.23 获取最近阅读小说

**GET** `/user/recently-read`

**Headers:** `Authorization: Bearer {token}`

**查询参数:**

- `limit` (int, 默认10): 返回数量

------

## 5. 阅读器模块 (Reader)

### 5.1 加载章节内容

**GET** `/novels/{novelId}/chapters/{chapterId}`

**路径参数:**

- `novelId` (string): 小说ID
- `chapterId` (string): 章节ID

### 5.2 获取章节列表

**GET** `/novels/{novelId}/chapters`

**路径参数:**

- `novelId` (string): 小说ID

**查询参数:**

- `simple` (boolean): 是否返回简化版

### 5.3 获取小说信息

**GET** `/novels/{novelId}`

**路径参数:**

- `novelId` (string): 小说ID

### 5.4 保存阅读进度

**POST** `/reading/progress`

**Headers:** `Authorization: Bearer {token}`

**请求参数:**

```json
{
  "novelId": "string",
  "chapterId": "string",
  "position": 100,
  "progress": 0.5,
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### 5.5 获取阅读进度

**GET** `/reading/progress/{novelId}`

**Headers:** `Authorization: Bearer {token}`

### 5.6 添加书签

**POST** `/bookmarks`

**Headers:** `Authorization: Bearer {token}`

**请求参数:**

```json
{
  "novelId": "string",
  "chapterId": "string",
  "position": 100,
  "note": "string",
  "content": "string",
  "createdAt": "2023-01-01T00:00:00Z"
}
```

### 5.7 删除书签

**DELETE** `/bookmarks/{bookmarkId}`

**Headers:** `Authorization: Bearer {token}`

### 5.8 获取书签列表

**GET** `/bookmarks`

**Headers:** `Authorization: Bearer {token}`

**查询参数:**

- `novelId` (string, 必填): 小说ID
- `chapterId` (string, 可选): 章节ID

### 5.9 更新阅读时长

**POST** `/reading/time`

**Headers:** `Authorization: Bearer {token}`

**请求参数:**

```json
{
  "novelId": "string",
  "minutes": 30,
  "date": "2023-01-01"
}
```

### 5.10 获取阅读统计

**GET** `/reading/stats`

**Headers:** `Authorization: Bearer {token}`

### 5.11 搜索章节

**GET** `/novels/{novelId}/chapters/search`

**查询参数:**

- `keyword` (string): 搜索关键词

### 5.12 获取相邻章节

**GET** `/novels/{novelId}/chapters/{chapterId}/adjacent`

**响应数据:**

```json
{
  "previous": {
    "id": "string",
    "title": "string",
    "chapter_number": 1
  },
  "next": {
    "id": "string", 
    "title": "string",
    "chapter_number": 3
  }
}
```

### 5.13 购买章节

**POST** `/purchases/chapters`

**Headers:** `Authorization: Bearer {token}`

**请求参数:**

```json
{
  "novelId": "string",
  "chapterId": "string"
}
```

### 5.14 检查章节购买状态

**GET** `/purchases/chapters/status`

**Headers:** `Authorization: Bearer {token}`

**查询参数:**

- `novelId` (string): 小说ID
- `chapterId` (string): 章节ID

**响应数据:**

```json
{
  "purchased": true
}
```

------

## 6. 错误码说明

### 6.1 HTTP状态码

- `200` - 请求成功
- `201` - 创建成功
- `400` - 请求参数错误
- `401` - 未授权/Token无效
- `403` - 权限不足
- `404` - 资源不存在
- `409` - 资源冲突
- `422` - 参数验证失败
- `429` - 请求过于频繁
- `500` - 服务器内部错误
- `502` - 网关错误
- `503` - 服务不可用

### 6.2 业务错误码

- `INVALID_CREDENTIALS` - 登录凭据无效
- `TOKEN_EXPIRED` - Token已过期
- `TOKEN_INVALID` - Token无效
- `ACCOUNT_LOCKED` - 账户被锁定
- `EMAIL_EXISTS` - 邮箱已存在
- `USERNAME_EXISTS` - 用户名已存在
- `USER_NOT_FOUND` - 用户不存在
- `BOOK_NOT_FOUND` - 小说不存在
- `CHAPTER_NOT_FOUND` - 章节不存在
- `NO_PERMISSION` - 无权限
- `VIP_REQUIRED` - 需要VIP权限
- `CHAPTER_LOCKED` - 章节被锁定
- `NETWORK_ERROR` - 网络错误
- `SERVER_ERROR` - 服务器错误

------

## 7. 数据模型说明

### 7.1 用户模型 (User)

```json
{
  "id": "string",
  "username": "string",
  "email": "string",
  "phone": "string",
  "avatar": "string",
  "gender": "string",
  "birthday": "string",
  "level": 1,
  "vip_level": 0,
  "points": 0,
  "coins": 0,
  "created_at": "string",
  "updated_at": "string"
}
```

### 7.2 小说模型 (Novel)

```json
{
  "id": "string",
  "title": "string",
  "author": "string",
  "author_id": "string",
  "cover_url": "string",
  "description": "string",
  "category": "string",
  "category_id": "string",
  "tags": ["string"],
  "status": "string",
  "word_count": 0,
  "chapter_count": 0,
  "rating": 0.0,
  "rating_count": 0,
  "view_count": 0,
  "favorite_count": 0,
  "comment_count": 0,
  "is_vip": false,
  "is_completed": false,
  "last_chapter_title": "string",
  "last_update_time": "string",
  "created_at": "string",
  "updated_at": "string"
}
```

### 7.3 章节模型 (Chapter)

```json
{
  "id": "string",
  "novel_id": "string",
  "title": "string",
  "content": "string",
  "word_count": 0,
  "chapter_number": 0,
  "is_vip": false,
  "price": 0,
  "is_locked": false,
  "created_at": "string",
  "updated_at": "string"
}
```

### 7.4 评论模型 (Comment)

```json
{
  "id": "string",
  "target_id": "string",
  "target_type": "string",
  "user_id": "string",
  "user": {
    "id": "string",
    "username": "string",
    "avatar": "string"
  },
  "content": "string",
  "like_count": 0,
  "reply_count": 0,
  "parent_id": "string",
  "is_liked": false,
  "created_at": "string"
}
```

------

## 8. 分页说明

所有列表接口都支持分页，使用以下参数：

**查询参数:**

- `page` (int, 默认1): 页码，从1开始
- `limit` (int, 默认20): 每页数量，最大100

**响应中的分页信息:**

```json
{
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 100,
    "total_pages": 5,
    "has_more": true,
    "has_next_page": true,
    "has_previous_page": false
  }
}
```