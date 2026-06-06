# ES 分片索引管理后台 — 设计文档

## 一、项目概述

一个 Elasticsearch 索引可视化管理后台，提供索引搜索、数据管理、批量导入导出、多角色权限控制和操作审计功能。

**技术栈：** Vue3 + Element Plus → Java (Spring Boot) → Python (FastAPI) → ES 7.x

## 二、系统架构

```
┌─────────────┐  HTTP/JSON   ┌──────────────────┐  HTTP/JSON   ┌─────────────────┐  ES API   ┌──────────┐
│   Vue3 SPA  │ ───────────→  │ Java Spring Boot │ ───────────→ │  Python FastAPI  │ ────────→ │ ES 7.x   │
│ Element Plus│ ←───────────  │ (Gateway + Auth) │ ←─────────── │ (ES Operation)   │ ←───────  │          │
└─────────────┘               └────────┬─────────┘              └─────────────────┘           └──────────┘
                                       │
                                       │ MySQL
                                       ▼
                              ┌──────────────┐
                              │ sys_user     │
                              │ audit_log    │
                              └──────────────┘
```

### 各层职责

| 层 | 职责 |
|---|------|
| **Vue3 前端** | UI 交互，所有请求发往 Java 层 |
| **Java (Spring Boot)** | JWT 认证、角色鉴权、用户管理、审计日志记录、请求转发至 Python |
| **Python (FastAPI)** | ES 索引管理、DSL 查询构建、数据 CRUD、JSONL 导出、Excel 解析导入 |
| **MySQL** | 仅存储用户、角色、审计日志（不存储 ES 业务数据） |
| **ES 7.x** | 业务数据存储，24 个索引，百万级数据 |

### 请求流向

| 请求类型 | 流转 |
|---------|------|
| 登录/鉴权 | 前端 → Java → MySQL → 前端 |
| ES 数据操作 | 前端 → Java (JWT+审计) → Python → ES → 前端 |

### 部署模式

- 单仓库 Monorepo：`frontend/` + `java-gateway/` + `python-service/`
- Java 与 Python 通过内网 HTTP 通信
- 前端打包为静态资源，由 Nginx 或 Java 嵌入式容器提供

## 三、数据库设计（MySQL）

### 用户表 `sys_user`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK AUTO_INCREMENT | 主键 |
| username | VARCHAR(50) UNIQUE | 登录名 |
| password | VARCHAR(255) | BCrypt 加密 |
| real_name | VARCHAR(50) | 真实姓名 |
| email | VARCHAR(100) | 邮箱 |
| role | VARCHAR(20) | admin / editor / viewer |
| status | TINYINT DEFAULT 1 | 1=启用 0=禁用 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 操作审计表 `audit_log`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK AUTO_INCREMENT | 主键 |
| user_id | BIGINT | 操作人 ID |
| username | VARCHAR(50) | 操作人用户名（冗余方便查询） |
| action | VARCHAR(50) | CREATE / UPDATE / DELETE / EXPORT / IMPORT |
| index_name | VARCHAR(100) | 操作的 ES 索引名 |
| doc_id | VARCHAR(100) | 操作的文档 _id |
| before_content | TEXT | 修改前内容（JSON） |
| after_content | TEXT | 修改后内容（JSON） |
| ip_address | VARCHAR(50) | 操作 IP |
| created_at | DATETIME | 操作时间 |

## 四、API 接口设计

### 4.1 认证接口（Java 直接处理）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 登录，返回 JWT Token |
| POST | `/api/auth/logout` | 登出 |
| GET | `/api/auth/userinfo` | 获取当前用户信息 |

### 4.2 用户管理（仅管理员）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/users` | 用户列表 |
| POST | `/api/users` | 创建用户 |
| PUT | `/api/users/{id}` | 更新用户信息 |
| DELETE | `/api/users/{id}` | 删除用户 |

### 4.3 ES 数据操作（Java → Python 转发）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/es/indexes` | 获取索引列表 |
| GET | `/api/es/indexes/{index}/fields` | 获取指定索引的字段列表 |
| POST | `/api/es/indexes/{index}/search` | 搜索（字段组合 + DSL） |
| GET | `/api/es/indexes/{index}/doc/{id}` | 获取单条文档详情 |
| PUT | `/api/es/indexes/{index}/doc/{id}` | 更新单条文档 |
| DELETE | `/api/es/indexes/{index}/doc/{id}` | 删除单条文档 |
| POST | `/api/es/indexes/{index}/export` | 导出搜索结果（返回 JSONL 文件流） |
| POST | `/api/es/indexes/{index}/import` | 上传 Excel 批量更新（multipart/form-data） |

### 4.4 审计日志

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/audit-logs` | 查询审计日志（筛选：用户/索引/操作类型/时间） |

## 五、前端设计

### 5.1 页面布局

```
┌────────────────────────────────────────────┐
│  顶部导航栏：Logo | 用户信息 | 角色标签 | 退出  │
├──────┬─────────────────────────────────────┤
│ 侧边 │              主内容区                 │
│ 菜单 │                                      │
│      │                                      │
│ ·首页│                                      │
│ ·索引│                                      │
│ 管理 │                                      │
│ ·审计│                                      │
│ 日志 │                                      │
│      │                                      │
│(管理 │                                      │
│员可   │                                      │
│见：   │                                      │
│用户   │                                      │
│管理) │                                      │
└──────┴─────────────────────────────────────┘
```

### 5.2 索引管理页面（核心）

```
┌────────────────────────────────────────────────┐
│  索引管理                                      │
│  ┌───────────┐                                 │
│  │ 选择索引 ▼ │  (单选搜索，导入时可多选)        │
│  └───────────┘                                 │
│ ───────────────────────────────────────────── │
│  字段搜索区域:                                   │
│  ┌───────────┐ ┌──────────┐ ┌──────────┐ [删] │
│  │ 字段名  ▼│ │ 匹配方式▼│ │ 搜索值   │ [+]   │
│  └───────────┘ └──────────┴ └──────────┘       │
│                      [搜索]  [重置]             │
│ ───────────────────────────────────────────── │
│  自定义 DSL:                                    │
│  ┌──────────────────────────────────────────┐  │
│  │ { "query": { "bool": { "must": [...] } }}│  │
│  └──────────────────────────────────────────┘  │
│ ───────────────────────────────────────────── │
│  工具栏: [导出JSONL] [导入Excel]                 │
│ ───────────────────────────────────────────── │
│  数据表格（列根据当前索引字段动态生成）:          │
│  ┌─────┬───────┬───────┬───────┬──────┐       │
│  │ 序号│ 字段1  │ 字段2  │ ...   │ 操作 │       │
│  ├─────┼───────┼───────┼───────┼──────┤       │
│  │  1  │ ...   │ ...   │ ...   │详情  │       │
│  │     │       │       │       │编辑  │       │
│  │     │       │       │       │删除  │       │
│  └─────┴───────┴───────┴───────┴──────┘       │
│            [<] [1] [2] ... [N] [>]             │
└────────────────────────────────────────────────┘
```

### 5.3 交互规则

- **选索引** → 自动请求 `/api/es/indexes/{index}/fields` 加载字段到下拉框
- **字段搜索**：支持多组条件（添加/删除按钮），生成对应 DSL JSON 显示在下方
- **DSL 编辑**：用户可直接修改 DSL 文本，搜索时以最终 DSL 为准
- **详情弹窗**：以 JSON 格式展示文档内容
- **表格分页**：后端分页 + 传统翻页组件
- **导入 Excel**：可选择多个索引，按 `_id` 匹配更新

## 六、匹配方式与 DSL 映射

| 匹配方式 | ES DSL |
|---------|--------|
| 全匹配 | `{"term": {"field": "value"}}` |
| 全词匹配 | `{"match_phrase": {"field": "value"}}` |
| 分词匹配 | `{"match": {"field": "value"}}` |

多条件组合使用 `bool.must`。

## 七、权限矩阵

| 功能 | viewer (只读) | editor (编辑) | admin (管理员) |
|------|:---:|:---:|:---:|
| 索引搜索/查看 | ✅ | ✅ | ✅ |
| 文档详情查看 | ✅ | ✅ | ✅ |
| 导出 JSONL | ❌ | ✅ | ✅ |
| 导入 Excel 批量编辑 | ❌ | ✅ | ✅ |
| 编辑/删除单条文档 | ❌ | ✅ | ✅ |
| 用户管理 | ❌ | ❌ | ✅ |
| 审计日志查看 | ❌ | ❌ | ✅ |

## 八、认证与鉴权

### JWT 流程

```
登录：用户名+密码 → Java验证(MySQL) → 生成JWT(含userId, username, role) → 返回Token
请求：Header: Authorization: Bearer <token> → JwtAuthFilter解析验证 → RequireRole注解鉴权
```

- JWT Token 过期时间：24 小时
- 密码存储：BCrypt 加密
- 角色注入：前端从 `/api/auth/userinfo` 获取当前用户角色，控制菜单与按钮显隐
- 后端二次校验：所有接口根据角色注解强制鉴权

## 九、Python FastAPI 服务结构

```
python-service/
├── main.py                # FastAPI 入口
├── config.py              # ES 连接、CORS 等配置
├── api/
│   ├── indexes.py         # 索引列表、字段获取
│   ├── documents.py       # 文档 CRUD
│   ├── search.py          # 搜索（字段组合 + DSL）
│   └── transport.py       # 导出 JSONL + 导入 Excel
├── services/
│   ├── es_client.py       # ES 客户端封装
│   ├── search_builder.py  # DSL 构建器
│   ├── export_service.py  # JSONL 导出
│   └── import_service.py  # Excel 解析与批量更新
└── utils/
    ├── field_utils.py     # 字段类型推断与映射
    └── validators.py      # 参数校验
```

## 十、Java Spring Boot 层结构

```
java-gateway/
├── src/main/java/com/esslice/
│   ├── EssliceApplication.java
│   ├── config/
│   │   ├── SecurityConfig.java
│   │   └── JwtTokenProvider.java
│   ├── controller/
│   │   ├── AuthController.java
│   │   ├── UserController.java
│   │   ├── EsGatewayController.java
│   │   └── AuditController.java
│   ├── service/
│   │   ├── UserService.java
│   │   └── AuditService.java
│   ├── repository/
│   │   ├── UserRepository.java
│   │   └── AuditLogRepository.java
│   ├── model/
│   │   ├── SysUser.java
│   │   └── AuditLog.java
│   ├── filter/
│   │   └── JwtAuthFilter.java
│   ├── annotation/
│   │   └── RequireRole.java
│   └── interceptor/
│       └── AuditInterceptor.java
└── src/main/resources/
    ├── application.yml
    └── db/migration/
```

### 代理转发

Java 的 `EsGatewayController` 统一接收前端所有 `/api/es/**` 请求，透传 body 和路径至 Python 服务，并将 Python 响应原样返回前端。不处理业务逻辑。

### 审计拦截器

通过 AOP 切面拦截 `/api/es/**` 的 PUT/POST/DELETE 请求：
- 从 JWT 提取操作用户信息
- 捕获请求前后的文档内容
- 写入 `audit_log` 表

## 十一、前端项目结构

```
frontend/
├── src/
│   ├── main.js
│   ├── App.vue
│   ├── router/index.js           # 路由 + 导航守卫
│   ├── store/
│   │   └── user.js               # 用户状态（Pinia）
│   ├── api/
│   │   ├── auth.js               # 认证接口
│   │   ├── es.js                 # ES 操作接口
│   │   ├── audit.js              # 审计日志接口
│   │   └── users.js              # 用户管理接口
│   ├── views/
│   │   ├── Login.vue             # 登录页
│   │   ├── IndexManage.vue       # 索引管理（核心）
│   │   ├── AuditLog.vue          # 审计日志
│   │   └── UserManage.vue        # 用户管理
│   ├── components/
│   │   ├── Layout.vue            # 全局布局
│   │   ├── Sidebar.vue           # 侧边栏
│   │   ├── DocDetailDialog.vue   # 文档详情弹窗
│   │   ├── DocEditDialog.vue     # 文档编辑弹窗
│   │   ├── ImportDialog.vue      # 导入 Excel 弹窗
│   │   └── FieldSearch.vue       # 字段组合搜索组件
│   └── utils/
│       ├── request.js            # Axios 封装 + 拦截器
│       └── auth.js               # Token 管理工具
└── package.json
```

## 十二、非功能性需求

| 项目 | 说明 |
|------|------|
| 分页 | 后端分页，默认每页 20 条，可切换 10/20/50/100 |
| 大数据导出 | 搜索结果导出为 JSONL，流式处理避免 OOM |
| 大数据导入 | Excel 分批解析，逐批 update ES，控制在每批 500 条 |
| ES 查询优化 | 使用 scroll API 处理大数据量 + 限制返回值字段 |
| 错误处理 | 前端统一错误拦截，后端返回标准错误格式 |
| 日志 | Java/Python 各自记录运行日志，审计日志单独存储 |
