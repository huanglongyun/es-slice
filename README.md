# ES 索引管理后台

一个 Web 图形化管理 Elasticsearch 的后台系统，替代命令行操作，面向业务人员使用。

## 项目简介

24 个索引、百万级数据、字段结构各异，提供一个统一的搜索和管理界面。支持字段组合搜索、自定义 DSL、单条编辑删除、Excel 批量导入、JSONL 导出，带多角色权限控制和完整操作审计。

## 技术架构

```
Vue3 + Element Plus  →  Java (Spring Boot)  →  Python (FastAPI)  →  Elasticsearch 7.x
      前端页面              认证/鉴权/审计              ES 操作              数据存储
                                  ↓
                              MySQL
                         用户/审计日志
```

## 功能列表

### 字段搜索
- 下拉选择索引后，自动加载该索引的字段列表到字段选择框
- 一组搜索条件由三个控件组成：**字段选择框 + 匹配方式（全匹配 / 全词匹配 / 分词匹配）+ 输入框**
- 点击右侧 **+** 按钮动态增加一组搜索条件，点击删除按钮移除该组
- 字段值变化时实时同步生成 DSL JSON 到下方编辑器
- 自定义 DSL 支持手动修改，搜索时以最终 DSL 为准
- 默认 DSL：`{"query":{"query_string":{"query":"*"}},"size":20,"from":0,"sort":[]}`
- 重置搜索恢复为默认 DSL，分页切换时 from/size 自动同步
- 搜索、导出接口返回格式与 elasticvue 一致

### 数据管理
- 表格展示搜索结果，列根据索引字段动态生成，后端分页
- 查看详情弹窗，JSON 格式化展示，元数据（_index / _id / _version）只读
- 编辑弹窗，仅 _source 内容可修改，保存后自动记录审计日志
- 单条删除，支持确认弹窗

### 导入导出
- 导出 JSONL：下拉菜单支持三种模式——勾选记录 / 当前页 / 全部记录
- 导出文件带 UTF-8 BOM，Windows 直接打开不乱码
- 导入 Excel：三步向导（选索引 → 上传文件 → 预览确认）
- 按 _id 匹配批量更新，支持同时导入多个索引
- 导入后返回修改前后文档快照，记入审计日志

### 权限控制
- JWT 登录认证，BCrypt 密码加密
- 三角色：admin（全部权限）/ editor（编辑+导入导出）/ viewer（只读）
- 导航菜单、页面按钮根据角色动态显隐

### 审计日志
- 自动记录 UPDATE / DELETE / IMPORT / EXPORT 操作
- 记录操作用户、IP、时间、目标索引、文档 ID
- 详情弹窗左右对比修改前后的完整文档 JSON，格式一致
- 支持按用户、索引、操作类型、时间范围筛选

### 用户管理（admin only）
- 用户增删改，角色分配（admin / editor / viewer），启用/禁用

## 项目结构

```
es-slice/
├── frontend/                 # Vue3 + Element Plus 前端
├── java-gateway/             # Spring Boot 网关 (认证/鉴权/审计)
├── python-service/           # FastAPI ES 操作服务
└── docker-compose.dev.yml    # 一键启动全部服务
```

## 快速启动

### Docker 一键启动（推荐）

```bash
docker compose -f docker-compose.dev.yml up -d
```

首次启动需要拉取/构建镜像，约 5-10 分钟。之后每次启动只需几秒。

访问 `http://localhost:5173`，默认管理员：**admin / admin123**

### 手动启动各服务

**前置条件：** MySQL 8.0、Elasticsearch 7.x、Node.js 16+、JDK 11+、Python 3.10+

```bash
# 1. 初始化 MySQL
mysql -u root -p < java-gateway/src/main/resources/db/migration/V1__init.sql

# 2. 启动 Python 服务 (端口 8081)
cd python-service && pip install -r requirements.txt && python main.py

# 3. 启动 Java 网关 (端口 8080)
cd java-gateway && mvn spring-boot:run

# 4. 启动前端 (端口 5173)
cd frontend && npm install && npm run dev
```

### 创建测试数据

```bash
docker exec es-slice-python python seed_data.py
```

### 运行测试

```bash
# Python
docker exec es-slice-python python -m pytest tests/ -v

# Java
docker run --rm -v "$(pwd)/java-gateway":/build -w //build maven:3.8-eclipse-temurin-11 mvn test

# 前端
docker exec es-slice-frontend npm test
```

## API 接口

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
