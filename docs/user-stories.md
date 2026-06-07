# ES 索引管理后台 — 用户故事设计文档

## 角色定义

| 角色 | 标识 | 说明 |
|------|------|------|
| 管理员 | admin | 系统最高权限，可管理用户、查看审计日志、操作数据 |
| 编辑者 | editor | 可搜索、编辑、删除数据，可导入导出 |
| 只读用户 | viewer | 仅可搜索和查看数据，不能修改 |

---

## US-001 用户登录

**作为** 系统用户
**我想要** 通过用户名和密码登录系统
**以便** 访问我权限范围内的功能

**页面交互：**
- 打开系统跳转到登录页，登录表单包含用户名输入框和密码输入框
- 默认预填管理员账号密码，方便开发测试
- 登录成功后跳转到索引管理页面
- 登录失败提示"用户名或密码错误"
- Token 过期或未登录访问功能页面时，自动跳转到登录页

**技术要点：**
- POST `/api/auth/login.do`，入参 `{username, password}`
- 返回 JWT Token + 用户信息（角色、姓名），前端存 localStorage
- 后续所有请求 Header 带 `Authorization: Bearer <token>`
- BCrypt 加密存储密码

---

## US-002 权限与导航

**作为** 系统用户
**我想要** 根据我的角色看到不同的菜单和按钮
**以便** 只能操作我有权限的功能

**页面布局：**
```
┌────────────────────────────────────────────┐
│  顶部栏：系统名称 | 角色标签 | 用户名 | 退出  │
├──────┬─────────────────────────────────────┤
│ 侧边 │              主内容区                │
│ 菜单 │                                     │
├──────┤                                     │
│ 索引 │                                     │
│ 管理 │                                     │
│      │                                     │
│(admin│                                     │
│ 可见)│                                     │
│ 审计 │                                     │
│ 日志 │                                     │
│ 用户 │                                     │
│ 管理 │                                     │
└──────┴─────────────────────────────────────┘
```

**权限矩阵：**

| 功能 | viewer | editor | admin |
|------|:------:|:------:|:-----:|
| 索引搜索/查看 | ✅ | ✅ | ✅ |
| 文档详情查看 | ✅ | ✅ | ✅ |
| 编辑文档 | ❌ | ✅ | ✅ |
| 删除文档 | ❌ | ✅ | ✅ |
| 导出 JSONL | ❌ | ✅ | ✅ |
| 导入 Excel | ❌ | ✅ | ✅ |
| 审计日志查看 | ❌ | ❌ | ✅ |
| 用户管理 | ❌ | ❌ | ✅ |

**技术要点：**
- 前端导航守卫根据 localStorage 中的 role 控制路由访问
- 页面按钮通过 `v-if="role !== 'viewer'"` 控制显隐
- 后端 SecurityConfig 二次校验，防止绕过前端直接调接口

---

## US-003 索引管理与字段搜索

**作为** 业务用户
**我想要** 选择一个索引后，动态加载该索引的字段，通过组合条件搜索数据
**以便** 不需要写 ES 查询语句就能找到需要的数据

**页面交互：**

第一步：**选择索引**
- 页面顶部有一个索引下拉选择框，列出所有可用的索引名称
- 选择索引后，自动加载该索引的字段列表到字段选择框中

第二步：**字段组合搜索**
- 一组搜索条件由三个控件组成：
  - **字段选择框**：下拉列出当前索引的所有字段
  - **匹配方式选择框**：全匹配 / 全词匹配 / 分词匹配
  - **输入框**：输入搜索值
- 点击行尾 **+ 按钮** 动态增加一组搜索条件
- 点击行尾 **删除按钮** 移除该组条件（至少保留一行）
- 点击 **搜索按钮** 执行查询
- 点击 **重置按钮** 清空所有条件恢复默认

第三步：**自定义 DSL**
- 搜索条件下方展示 DSL JSON 编辑器
- 字段条件变化时 **实时同步** 到 DSL 编辑器（字段值变化即更新，不需要点按钮）
- 用户可 **手动修改** DSL 内容
- 搜索时以 DSL 编辑器中的最终内容为准
- 默认 DSL 内容：
  ```json
  {
    "query": { "query_string": { "query": "*" } },
    "size": 20,
    "from": 0,
    "sort": []
  }
  ```
- 重置时恢复为默认 DSL
- 切换分页（页码或每页条数）时，DSL 中的 from/size **自动同步更新**

**字段匹配规则：**

| 匹配方式 | ES 语法 | 适用场景 |
|---------|---------|---------|
| 全匹配 | `term` | keyword 字段精确匹配 |
| 全词匹配 | `match_phrase` | text 字段短语匹配 |
| 分词匹配 | `match` | text 字段分词搜索 |

多条件用 `bool.must` 组合。

**技术要点：**
- GET `/api/es/indexes.do` 获取索引列表
- GET `/api/es/indexes/{index}/fields.do` 获取字段列表（返回字段名+类型）
- POST `/api/es/indexes/{index}/search.do` 执行搜索
- 入参为完整 ES DSL（query + size + from + sort），Python 直接透传
- 返回格式与 elasticvue 一致（ES 原生响应格式）
- 后端分页，前端通过 v-model 双向绑定 page/pageSize

---

## US-004 数据表格与分页

**作为** 业务用户
**我想要** 在表格中查看搜索结果，并能翻页浏览
**以便** 快速浏览大量数据

**页面交互：**
- 表格列根据当前索引的字段**动态生成**
- 支持多选勾选框（用于导出勾选记录）
- 序号列展示行号
- 操作列固定在右侧：详情 / 编辑 / 删除
- 底部传统分页组件：总条数、每页条数（10/20/50/100）、上一页/下一页/页码
- 切换页码或每页条数时**自动触发搜索**

**技术要点：**
- ES 分页通过 from/size 实现
- `total` 适配 ES 7.x 格式（total 可能是数字或 `{value, relation}` 对象）

---

## US-005 查看文档详情

**作为** 业务用户
**我想要** 查看某条数据的完整 JSON 内容
**以便** 了解该文档的所有字段信息

**页面交互：**
- 点击表格行操作列的 **「详情」** 按钮，弹出详情弹窗
- 弹窗上半部分展示**元数据**（只读、不可修改）：
  - `_index`：所属索引
  - `_id`：文档 ID
  - `_version`：版本号
- 弹窗下半部分展示 `_source` 内容，JSON 格式化显示
- 弹窗底部有**「关闭」**和**「编辑」**按钮（viewer 不显示编辑按钮）
- 点击「编辑」跳转到编辑弹窗

**技术要点：**
- GET `/api/es/indexes/{idx}/doc/{id}.do` 返回 ES 原生格式 `{_index, _id, _version, _source}`
- 与 elasticvue 格式一致

---

## US-006 编辑文档

**作为** 编辑者
**我想要** 修改某条文档的内容
**以便** 修正错误数据或更新信息

**页面交互：**
- 从详情弹窗点「编辑」或表格行点「编辑」，弹出编辑弹窗
- 弹窗上方展示 `_index` 和 `_id`（只读，不可修改）
- 弹窗下方为 `_source` 的 JSON 编辑器（textarea，可修改）
- 点击「保存」提交更新
- 保存成功后关闭弹窗、刷新表格数据
- 若 JSON 格式错误，提示"JSON 格式不正确"不提交

**技术要点：**
- PUT `/api/es/indexes/{idx}/doc/{id}.do`，body 为要更新的字段
- 只更新传入的字段，未传的保持原样
- 操作自动记入审计日志，记录修改前后的完整文档

---

## US-007 删除文档

**作为** 编辑者
**我想要** 删除不需要的数据
**以便** 清理无效或过时的记录

**页面交互：**
- 点击表格行操作列的 **「删除」** 按钮
- 弹出确认弹窗"确定删除?"
- 确认后执行删除，成功后刷新表格

**技术要点：**
- DELETE `/api/es/indexes/{idx}/doc/{id}.do`
- 操作自动记入审计日志，记录被删除的文档内容

---

## US-008 导出数据

**作为** 编辑者
**我想要** 将搜索结果导出为文件
**以便** 离线分析或在 Excel 中处理

**页面交互：**
- 导出按钮为**下拉菜单**，包含三个选项：
  - **勾选记录**：导出当前表格中勾选的行（按 _id 精确匹配）
  - **当前页**：导出当前分页的数据（保留 from/size）
  - **全部记录**：导出所有匹配搜索条件的数据（不限制分页）

- 点击后下载 JSONL 文件，文件名格式：`{索引名}_export.jsonl`
- 导出前校验：勾选记录模式需至少勾选一条
- viewer 角色导出按钮禁用

**文件格式：**
```
{"_id":"fb_0001","title":"...","content":"...",...}
{"_id":"fb_0002","title":"...","content":"...",...}
```
每行一个完整 JSON 对象，带 UTF-8 BOM，Windows 直接打开不乱码。

**技术要点：**
- POST `/api/es/indexes/{idx}/export.do`，body 为当前 DSL
- 当前页导出：普通 search，保留 from/size
- 全量/勾选导出：scroll API 遍历，去掉 from
- StreamingResponse 流式返回，不占内存

---

## US-009 批量导入

**作为** 编辑者
**我想要** 通过上传 Excel 文件批量更新数据
**以便** 一次性修改多条记录，提高操作效率

**页面交互：**

**三步向导流程：**

第一步：**选择目标索引**
- 下拉多选框，可选择多个索引
- 提示 Excel 格式要求（第一行为字段名，需包含 _id 列）
- 下一步按钮，需先选索引才能继续

第二步：**上传 Excel 文件**
- 拖拽或点击上传，支持 .xlsx / .xls
- 点击「预览」解析并预览数据

第三步：**预览确认**
- 展示前 10 行数据，超过 10 行显示"...共 N 行"
- 若缺少 _id 列给出警告提示
- 点击「确认导入」执行批量更新
- 点击「上一步」返回修改文件

**导入规则：**
- 按 _id 匹配已有文档进行更新，**不会新增文档**
- 只更新 Excel 中有的字段，其他字段保持原样
- 支持同时向多个索引导入（各索引独立更新）
- 导入完成后提示"导入完成: 成功 X 条"
- 导入失败显示具体错误原因

**Excel 格式示例：**

| _id | title | content | rating | resolved |
|-----|-------|---------|--------|----------|
| fb_0001 | 新标题 | 新内容 | 5 | 是 |
| fb_0002 | 另一标题 | 另一内容 | 3 | 否 |

**技术要点：**
- POST `/api/es/indexes/import.do`（multipart/form-data）
- `preview=true`：解析 Excel 返回预览数据，不写入
- `preview=false`：解析 → 逐条取旧值 → bulk update → 逐条取新值 → 返回修改前后对比
- Java ImportController 单独处理 multipart 文件代理
- 导入操作自动记入审计日志

---

## US-010 审计日志

**作为** 管理员
**我想要** 查看系统中所有数据修改操作的记录
**以便** 追溯谁在什么时间修改了什么数据

**页面交互：**
- 筛选条件：用户名、索引名、操作类型（UPDATE/DELETE/EXPORT/IMPORT）、时间范围
- 表格列：ID、操作用户、操作类型、索引名、文档 ID、IP 地址、操作时间
- 每行 **「详情」** 按钮，点击弹出详情弹窗
- 详情弹窗**左右对比**展示修改前后的完整文档 JSON
- 修改前和修改后的数据**格式一致**，均为完整的文档 JSON（非差异对比）
- 分页查询，按时间倒序排列

**记录规则：**
- 自动拦截所有 PUT/POST/DELETE 请求
- 更新操作：记录修改前的完整文档 + 修改后的完整文档
- 删除操作：记录删除前的完整文档
- 导入操作：记录每个 _id 对应的修改前后文档
- 导出操作：记录导出时的 DSL 条件

**技术要点：**
- Java AuditInterceptor AOP 切面拦截
- 操作前 GET Python 取旧文档 → 执行操作 → 操作后 GET Python 取新文档
- 导入通过 Python 返回的 before_docs/after_docs 记录
- 数据存 MySQL audit_log 表

---

## US-011 用户管理

**作为** 管理员
**我想要** 创建、修改、删除系统用户并分配角色
**以便** 控制不同人员的操作权限

**页面交互：**
- 用户列表表格：ID、用户名、姓名、邮箱、角色、状态（启用/禁用）
- 「新增用户」按钮弹出新增弹窗
- 每行「编辑」「删除」按钮
- 新增/编辑弹窗字段：
  - 用户名（创建后不可修改）
  - 密码（编辑时留空表示不修改）
  - 姓名、邮箱
  - 角色下拉：管理员 / 编辑者 / 只读
  - 状态开关：启用/禁用

**技术要点：**
- GET/POST/PUT/DELETE `/api/users/{list,create,id}.do`
- 密码 BCrypt 加密存储
- 首次启动自动创建默认管理员 admin/admin123

---

## 非功能性需求

| 项目 | 说明 |
|------|------|
| 分页 | 后端分页，默认每页 20 条，可切换 10/20/50/100 |
| 大数据导出 | scroll API + StreamingResponse 流式处理 |
| 大数据导入 | 分批解析，逐批 bulk update |
| 安全 | JWT 24h 过期，密码 BCrypt，角色二次校验 |
| 日志 | Java/Python 运行日志 + MySQL 审计日志 |

---

## 部署架构

```
┌─────────────────────────────────────────────────────┐
│                   Docker Compose                     │
│                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────┐ ┌──────┐ ┌────┐│
│  │ frontend │ │  java    │ │python│ │  es  │ │mysql││
│  │  :5173   │ │  :8080   │ │:8081 │ │:9200 │ │:3306││
│  │  Vue3    │→│  Spring  │→│FastAPI│→│ES 7.x│ │    ││
│  │Element+  │ │  Boot    │ │      │ │      │ │    ││
│  └──────────┘ └────┬─────┘ └──────┘ └──────┘ └────┘│
│                    │                                │
│                    └──→ MySQL (用户/审计)            │
└─────────────────────────────────────────────────────┘
```

一键启动：`docker compose -f docker-compose.dev.yml up -d`

访问：`http://localhost:5173`

---

## 附录 A：Java 网关层功能设计

### A.1 认证模块

**JWT Token 管理（JwtTokenProvider）**

| 方法 | 功能 | 说明 |
|------|------|------|
| `generateToken(id, username, role)` | 生成令牌 | payload 含 userId、username、role，24h 过期 |
| `validateToken(token)` | 验证令牌 | 校验签名和过期时间 |
| `getUsernameFromToken(token)` | 解析用户名 | 从 token 提取 subject |
| `getRoleFromToken(token)` | 解析角色 | 用于权限判断 |
| `getUserIdFromToken(token)` | 解析用户 ID | 用于审计日志关联 |

**请求拦截（JwtAuthFilter）**
- 每个请求到达时从 Header 取 `Authorization: Bearer <token>`
- 验证 token 有效性，解析出用户名和角色
- 注入 Spring Security 上下文，后续 Controller 和 Interceptor 均可获取当前用户

**安全配置（SecurityConfig）**
- 登录接口 `/api/auth/login.do` 无需认证
- `/api/es/**` 需要 admin/editor/viewer 任一角色
- `/api/users/**` 和 `/api/audit-logs/**` 仅 admin
- 禁用 CSRF、启用 CORS、无状态 Session

### A.2 代理转发模块

**通用 JSON 代理（EsGatewayController）**
- 路径匹配 `/api/es/**`，接收 GET/POST/PUT/DELETE
- 处理逻辑：
  1. 从 request 取 URI 路径
  2. 去掉 `/api` 前缀（Python 路由不带）
  3. 去掉 `.do` 后缀
  4. 拼接到 `python-service:8081` 后面
  5. 用 RestTemplate 转发，原样返回 Python 的响应
- 不做业务处理，纯传话筒

**文件导入代理（ImportController）**
- 独立 Controller，单独匹配 `/api/es/indexes/import.do`
- 分离原因：导入是 multipart/form-data 文件上传，不能用 `@RequestBody String`
- 接收参数：`@RequestParam MultipartFile file`、`@RequestParam String indexes`、`@RequestParam String preview`
- 用 `ByteArrayResource` 包装文件，以 `MultiValueMap` 形式转发给 Python
- 配置 `spring.servlet.multipart.max-file-size=50MB`

### A.3 审计拦截模块（AuditInterceptor）

**拦截规则**
- AOP 切面 `@Around`，拦截 `EsGatewayController.proxy()` 和 `ImportController.proxyImport()`
- 只拦截 PUT/POST/DELETE 请求，GET 不审计

**操作类型识别**

| 请求特征 | 操作类型 |
|---------|---------|
| PUT + 路径含 `/doc/` | UPDATE |
| DELETE + 路径含 `/doc/` | DELETE |
| 路径以 `/export` 结尾 | EXPORT |
| 路径以 `/import` 结尾 | IMPORT |
| 其他 POST | CREATE |

**修改前后文档获取**

| 操作 | beforeContent | afterContent |
|------|-------------|-------------|
| UPDATE | 操作前 GET Python 取旧文档 | 操作后 GET Python 取新文档 |
| DELETE | 操作前 GET Python 取旧文档 | 空 |
| IMPORT | 从响应体解析 before_docs | 从响应体解析 after_docs |
| EXPORT | 导出请求的 DSL（截断 200 字符） | 空 |

**路径解析**
- URL 格式：`/api/es/indexes/{索引名}/doc/{文档ID}`
- 去掉 `.do` 后缀后按 `/` 分割
- `parts[4]` = 索引名，`parts[6]` = 文档 ID

### A.4 数据初始化模块（DataInitializer）

- Spring Boot 启动时自动执行 `CommandLineRunner`
- 检查 MySQL 中是否存在 admin 用户
- 不存在则创建：用户名 admin、密码 admin123（BCrypt 加密）、角色 admin

### A.5 用户服务（UserService）

- `findByUsername()` — 按用户名查找，登录用
- `create()` — 创建用户，密码自动 BCrypt 加密
- `update()` — 更新用户信息，密码为空时不修改
- `delete()` — 删除用户
- `verifyPassword()` — 用 BCrypt 比对明文和密文

### A.6 数据模型

**sys_user 表**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 自增主键 |
| username | VARCHAR(50) UNIQUE | 登录名 |
| password | VARCHAR(255) | BCrypt 密文 |
| real_name | VARCHAR(50) | 真实姓名 |
| email | VARCHAR(100) | 邮箱 |
| role | VARCHAR(20) | admin / editor / viewer |
| status | TINYINT | 1=启用 0=禁用 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

**audit_log 表**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 自增主键 |
| user_id | BIGINT | 操作人 ID |
| username | VARCHAR(50) | 操作人用户名（冗余） |
| action | VARCHAR(50) | UPDATE / DELETE / EXPORT / IMPORT |
| index_name | VARCHAR(100) | 操作的 ES 索引 |
| doc_id | VARCHAR(100) | 操作的文档 _id |
| before_content | TEXT | 修改前的完整文档 JSON |
| after_content | TEXT | 修改后的完整文档 JSON |
| ip_address | VARCHAR(50) | 操作 IP |
| created_at | DATETIME | 操作时间 |

---

## 附录 B：Python 服务层功能设计

### B.1 ES 连接管理（es_client.py）

**核心设计：单例模式**
- `get_es_client()` 全局持有一个 Elasticsearch 实例
- 首次调用时创建连接，后续复用
- 支持 HTTP Basic Auth（通过环境变量配置用户名密码）

**函数清单**

| 函数 | 入参 | 出参 | 说明 |
|------|------|------|------|
| `get_index_list()` | 无 | `["idx1","idx2"]` | 取所有索引名，过滤 `.` 开头的系统索引 |
| `get_index_fields(idx)` | 索引名 | `[{name,type}]` | 从 mapping 提取字段名和类型，排除 object 嵌套 |
| `search_docs(idx, dsl)` | 索引名 + DSL | ES 原生响应 | body 中已含 size/from，直接透传 |
| `get_doc(idx, id)` | 索引名 + _id | ES 原生格式 | 返回 `{_index,_id,_version,_source}` |
| `update_doc(idx, id, body)` | 索引名 + _id + 字段 | 更新后完整文档 | `{"doc": body}` 只更新传入字段，再 get 返回 |
| `delete_doc(idx, id)` | 索引名 + _id | 无 | 直接删除 |
| `scroll_search(idx, dsl)` | 索引名 + DSL | `[{...docs}]` | 去掉 from，2 分钟 scroll 超时，try/finally 清理 |
| `bulk_update(idx, docs)` | 索引名 + 文档列表 | `{success,errors,total}` | 按 _id bulk update，doc_as_upsert=false，不新增 |

**scroll_search 与 search_docs 的区别**

| 特性 | search_docs | scroll_search |
|------|------------|--------------|
| 用途 | 搜索 + 当前页导出 | 全量导出 |
| from 参数 | 支持 | 不支持（自动去掉） |
| 遍历方式 | 单次查询 | 分批 scroll |
| 上下文清理 | 不需要 | try/finally clear_scroll |

### B.2 搜索接口（api/search.py）

```
POST /es/indexes/{index}/search
入参: {"query":{...}, "size":20, "from":0, "sort":[]}
处理: 取出 query/size/from/sort → 拼成 DSL → search_docs → 透传 ES
出参: {"code":0, "data":{ES 原生响应}}
```

- 不翻译、不转换、不做映射——前端 DSL 就是 ES 语法
- 响应格式与 elasticvue 一致

### B.3 索引接口（api/indexes.py）

```
GET /es/indexes          → get_index_list()   → ["news_articles","product_docs","user_feedback"]
GET /es/indexes/{}/fields → get_index_fields() → [{name:"title",type:"text"},{name:"rating",type:"integer"}]
```

### B.4 文档接口（api/documents.py）

```
GET    /es/indexes/{}/doc/{} → get_doc()    → {_index, _id, _version, _source}
PUT    /es/indexes/{}/doc/{} → update_doc() → 更新后完整文档
DELETE /es/indexes/{}/doc/{} → delete_doc() → {code:0, message:"ok"}
```

### B.5 导出接口（api/transport.py）

```
POST /es/indexes/{index}/export
入参: {"query":{...}, "size":20, "from":0, "sort":[]}
```

**导出模式判断逻辑：**

| 条件 | 模式 | 使用函数 | 说明 |
|------|------|---------|------|
| body 中没有 `from` 字段 | 全量导出 | scroll_search | 去掉 from，scroll 遍历所有数据 |
| body 中有 `from` 字段 | 当前页导出 | search_docs | 保留 from/size，只取当前页 |
| body 为 `{terms:{_id:[...]}}` | 勾选导出 | scroll_search | terms 查询精确匹配，无 from |

**响应：** StreamingResponse，content-type 为 `text/plain; charset=utf-8`
**文件内容：** UTF-8 BOM + 每行一个 JSON（JSONL 格式）

### B.6 导入接口（api/transport.py）

```
POST /es/indexes/import
Content-Type: multipart/form-data
入参:
  file=<Excel文件>
  indexes="user_feedback,news_articles"
  preview="true" | "false"
```

**preview=true（预览模式）：**
- 解析 Excel → 返回前 10 行数据
- 检查 _id 列是否存在，列出缺失的行
- 不写入 ES

**preview=false（导入模式）：**
1. 解析 Excel 得到文档列表
2. 校验：indexes 不为空、有数据、有 _id 列
3. 取 before_docs：遍历每个 _id 调 get_doc 取旧文档
4. 对每个目标索引执行 bulk_update（deepcopy 避免引用污染）
5. 取 after_docs：再次遍历取新文档
6. 返回 `{success, total, results, before_docs, after_docs}`

### B.7 Excel 解析（import_service.py）

```
Excel 文件
  ↓ openpyxl.load_workbook
  ↓ sheet.iter_rows(values_only=True)
  ↓ 第 1 行 → headers（字段名列表）
  ↓ 第 2 行起 → 每行拼成 {header: value} 字典
  ↓ 跳过全空行
返回 [{_id, field1, field2, ...}]
```

### B.8 接口路由汇总

| 路径 | 文件 | 函数 |
|------|------|------|
| `GET /es/indexes` | api/indexes.py | list_indexes |
| `GET /es/indexes/{}/fields` | api/indexes.py | get_fields |
| `POST /es/indexes/{}/search` | api/search.py | search |
| `GET /es/indexes/{}/doc/{}` | api/documents.py | get_document |
| `PUT /es/indexes/{}/doc/{}` | api/documents.py | update_document |
| `DELETE /es/indexes/{}/doc/{}` | api/documents.py | delete_document |
| `POST /es/indexes/{}/export` | api/transport.py | export_docs |
| `POST /es/indexes/import` | api/transport.py | import_excel |
| `GET /health` | main.py | health |

### B.9 项目文件结构

```
python-service/
├── main.py              # FastAPI 入口，注册路由，uvicorn 启动
├── config.py            # ES 地址、服务端口（支持环境变量）
├── requirements.txt     # 依赖清单
├── seed_data.py         # 造测试数据工具
├── Dockerfile           # Docker 镜像
├── api/
│   ├── indexes.py       # 索引列表 + 字段查询
│   ├── search.py        # DSL 搜索
│   ├── documents.py     # 单条文档 CRUD
│   └── transport.py     # 导出 JSONL + 导入 Excel
├── services/
│   ├── es_client.py     # ES 连接管理（核心）
│   ├── export_service.py # 导出为 JSONL 字节流
│   └── import_service.py # Excel 解析
├── utils/
│   └── field_utils.py   # 字段类型判断
└── tests/
    ├── test_search.py   # 搜索接口测试
    ├── test_export.py   # 导出功能测试
    └── test_import.py   # Excel 解析测试
