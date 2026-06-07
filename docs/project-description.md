# ES 索引管理后台 — 项目完整描述

## 背景

公司有 24 个 Elasticsearch 索引，百万级数据，字段结构各不相同。业务人员查数据、改数据需要写 DSL 或者求开发帮忙。需要一个可视化的 Web 管理后台，让业务人员自己搜、自己改、自己导出。

## 做了什么

从零搭建了一个三端全栈的 ES 数据管理平台。浏览器打开就能用，选索引自动加载字段，组合条件搜索，表格展示结果，支持单条增删改、批量 Excel 导入、JSONL 导出。带登录认证、角色权限、操作审计。

## 技术栈选择

- **前端 Vue3 + Element Plus**：页面交互，表格、表单、弹窗全部用 Element Plus 组件
- **中间层 Java Spring Boot**：做门卫，负责 JWT 登录验证、三角色权限控制、操作审计日志。不处理 ES 业务，只管安全和记录，ES 请求全部代理转发给 Python
- **后端 Python FastAPI**：做工人，接收 Java 转发的请求，封装 elasticsearch-py 操作 ES 7.x
- **数据库 MySQL**：只存用户表和审计日志表，不存业务数据
- **部署 Docker Compose**：五个容器（MySQL、ES、Python、Java、前端），一个命令启动

## 核心功能实现

### 1. 搜索

选索引 → 自动调接口拿字段列表填充下拉框 → 一行三个控件（字段名 + 匹配方式 + 输入值）→ 可点 + 增加多行条件 → 字段值变化时实时生成 DSL JSON 显示在下方编辑器 → 用户可以在 DSL 编辑器里手动改 → 搜索时以编辑器里的最终 DSL 为准 → 后端 Python 直接透传给 ES，不做任何翻译 → 分页时 from/size 自动同步到 DSL → 重置恢复默认 DSL。

匹配方式对应 ES 语法：全匹配=term、全词匹配=match_phrase、分词匹配=match，多条件用 bool.must 组合。

搜索接口入参就是 ES 原生查询语句，返回格式和 elasticvue 一致（ES 原生响应格式）。

### 2. 查看和编辑

表格展示搜索结果，列根据当前索引的字段动态生成。点详情弹出一份完整的 JSON（按 _index / _id / _version 元数据 + _source 内容分区展示，元数据只读）。点编辑弹出一个 JSON 编辑器，只能改 _source 部分，保存时只提交改动的字段。

### 3. 导出

导出按钮是个下拉菜单，三种模式：

- **勾选记录**：表格勾选哪些，就导哪些，按 _id 精准匹配
- **当前页**：保留当前分页的 from/size，普通查询导出
- **全部记录**：去掉 from，用 scroll API 遍历全量数据导出

导出文件是 JSONL 格式（每行一个 JSON），带 UTF-8 BOM，Windows 打开不乱码。

### 4. 批量导入

上传 Excel 文件做批量更新。分三步向导：

1. 选择目标索引（可多选）
2. 上传 Excel
3. 预览前 10 条数据，确认后执行

Excel 第一行是字段名，必须包含 _id 列用于匹配文档。Python 端用 openpyxl 解析，逐条取 _id → 查旧值 → bulk 更新 → 查新值 → 返回修改前后对比。

### 5. 权限

登录发 JWT Token，后续每个请求在 Header 里带 Token。Java 端用 JwtAuthFilter 拦截验证，SecurityConfig 配置哪些接口需要什么角色。

三个角色：

| 角色 | 权限 |
|------|------|
| admin | 全部权限（含用户管理、审计查看） |
| editor | 可编辑和导入导出，不能删用户 |
| viewer | 只读，只能搜索和查看 |

### 6. 审计日志

所有增删改操作自动记录。Java 用 AOP 切面拦截 EsGatewayController 和 ImportController 的 PUT/POST/DELETE 请求。操作前先调 Python 接口取旧文档存为 before，操作后再取新文档存为 after。

审计日志页支持按用户、索引、操作类型、时间筛选，详情弹窗左右对比修改前后的完整 JSON。

### 7. 批量导入的审计

导入时 Python 端在 bulk 更新前后分别遍历每个 _id 取文档快照，返回 before_docs 和 after_docs。Java 端从响应中提取并存入审计日志。

## 架构图

```
浏览器 (Vue3 + Element Plus)
  │  HTTP + JWT Token
  ▼
Java Spring Boot (端口 8080)
  │  门卫：认证 + 鉴权 + 审计记录
  │  传话筒：转发请求到 Python
  ▼
Python FastAPI (端口 8081)
  │  工人：操作 Elasticsearch
  ▼
Elasticsearch 7.x (端口 9200)
  │  数据库：存业务数据
  ▼
MySQL 8.0 (端口 3306)
    账本：存用户、审计日志
```

## 全链路请求流程

以一个编辑操作为例：

```
浏览器 → Vite 代理 → Java:8080/api/es/indexes/user_feedback/doc/fb_0001.do
  → JwtAuthFilter 验证 token
  → SecurityConfig 检查角色权限
  → AuditInterceptor 拦截：先 GET Python 取旧文档 → 放行更新 → 再 GET Python 取新文档
  → EsGatewayController 去前缀/.do → 转发 Python:8081/es/indexes/user_feedback/doc/fb_0001
  → Python → ES 执行 update → 返回
  → AuditInterceptor 存 before/after 到 MySQL
  → 结果原路返回到浏览器
```

## 部署方式

Docker Compose 一键全栈：

```bash
docker compose -f docker-compose.dev.yml up -d
```

首次启动约 5-10 分钟（需拉取镜像和构建），之后每次启动只需几秒。五个容器全部就绪后，访问 `http://localhost:5173` 即可使用。

默认管理员：**admin / admin123**

## 测试覆盖

三端共 34 个单元测试全通过：

| 端 | 框架 | 测试数 | 覆盖功能 |
|---|------|-------|---------|
| Python | pytest | 11 | 搜索接口、导出逻辑、Excel 解析 |
| Java | JUnit + Mockito | 9 | JWT 令牌、用户服务 |
| 前端 | vitest | 14 | 字段搜索组件、导入弹窗 |

## API 接口清单

所有接口带 `.do` 后缀，认证接口除外均需 Header: `Authorization: Bearer <token>`

### 认证
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login.do` | 登录 |
| GET | `/api/auth/userinfo.do` | 当前用户信息 |

### ES 操作
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/es/indexes.do` | 索引列表 |
| GET | `/api/es/indexes/{idx}/fields.do` | 字段列表 |
| POST | `/api/es/indexes/{idx}/search.do` | 搜索（body 为 ES DSL） |
| GET | `/api/es/indexes/{idx}/doc/{id}.do` | 文档详情 |
| PUT | `/api/es/indexes/{idx}/doc/{id}.do` | 更新文档 |
| DELETE | `/api/es/indexes/{idx}/doc/{id}.do` | 删除文档 |
| POST | `/api/es/indexes/{idx}/export.do` | 导出 JSONL |
| POST | `/api/es/indexes/import.do` | 导入 Excel (multipart) |

### 管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/audit-logs/list.do` | 审计日志查询 |
| GET/POST/PUT/DELETE | `/api/users/{list,create,id}.do` | 用户管理 (admin) |

## 审计操作类型

| 值 | 含义 |
|---|------|
| `UPDATE` | 单条编辑 |
| `DELETE` | 单条删除 |
| `EXPORT` | 导出 |
| `IMPORT` | 批量导入 |
