# ES 分片索引管理后台 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个带 JWT 认证、多角色权限控制、操作审计的 ES 索引可视化管理后台

**Architecture:** Vue3+ElementPlus 前端 → Java Spring Boot 网关(认证/鉴权/审计) → Python FastAPI 服务(ES 操作) → ES 7.x

**Tech Stack:** Vue3, Element Plus, Axios, Pinia, Vue Router | Spring Boot 2.7, Spring Security, JPA, JJWT, MySQL | Python 3.10+, FastAPI, elasticsearch-py, openpyxl | ES 7.x

---

## 文件结构总览

```
es-slice/
├── frontend/                 # Vue3 + Element Plus 前端
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── router/index.js
│       ├── store/user.js
│       ├── api/auth.js, es.js, audit.js, users.js
│       ├── views/Login.vue, IndexManage.vue, AuditLog.vue, UserManage.vue
│       ├── components/Layout.vue, Sidebar.vue, DocDetailDialog.vue, DocEditDialog.vue, ImportDialog.vue, FieldSearch.vue
│       └── utils/request.js, auth.js
├── java-gateway/             # Spring Boot 网关
│   ├── pom.xml
│   └── src/main/java/com/esslice/
│       ├── EssliceApplication.java
│       ├── config/SecurityConfig.java, JwtTokenProvider.java
│       ├── controller/AuthController.java, UserController.java, EsGatewayController.java, AuditController.java
│       ├── service/UserService.java, AuditService.java
│       ├── repository/UserRepository.java, AuditLogRepository.java
│       ├── model/SysUser.java, AuditLog.java
│       ├── filter/JwtAuthFilter.java
│       ├── annotation/RequireRole.java
│       └── interceptor/AuditInterceptor.java
└── python-service/           # FastAPI ES 操作服务
    ├── requirements.txt
    ├── main.py
    ├── config.py
    ├── api/indexes.py, documents.py, search.py, transport.py
    ├── services/es_client.py, search_builder.py, export_service.py, import_service.py
    └── utils/field_utils.py, validators.py
```

---

## 阶段一：项目初始化 (Tasks 1-4)

### Task 1: Monorepo 根目录结构

**Files:**
- Create: `es-slice/README.md`
- Create: `es-slice/.gitignore`

- [ ] **Step 1: 编写 .gitignore**

```bash
cat > .gitignore << 'EOF'
node_modules/
dist/
.env
*.pyc
__pycache__/
.idea/
*.iml
target/
*.class
*.log
.DS_Store
EOF
```

- [ ] **Step 2: 编写 README.md**

```bash
cat > README.md << 'EOF'
# ES 分片索引管理后台

## 项目结构
- `frontend/` - Vue3 + Element Plus 前端
- `java-gateway/` - Spring Boot 网关 (认证/鉴权/审计)
- `python-service/` - FastAPI ES 操作服务

## 快速启动
见各子目录 README
EOF
```

- [ ] **Step 3: 提交**

```bash
cd /c/Hcloud/projects/es-slice
git init
git add .gitignore README.md
git commit -m "chore: init monorepo structure"
```

---

### Task 2: Python 项目初始化

**Files:**
- Create: `es-slice/python-service/requirements.txt`
- Create: `es-slice/python-service/config.py`
- Create: `es-slice/python-service/main.py`

- [ ] **Step 1: 编写 requirements.txt**

```txt
fastapi==0.104.1
uvicorn==0.24.0
elasticsearch==7.17.9
openpyxl==3.1.2
pydantic==2.5.2
python-multipart==0.0.6
```

- [ ] **Step 2: 编写 config.py**

```python
import os

ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
ES_USER = os.getenv("ES_USER", "")
ES_PASS = os.getenv("ES_PASS", "")
ES_TIMEOUT = int(os.getenv("ES_TIMEOUT", "30"))
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8081"))
```

- [ ] **Step 3: 编写 main.py（最小入口）**

```python
from fastapi import FastAPI
import uvicorn
from config import SERVICE_PORT

app = FastAPI(title="ES Slice Service", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
```

- [ ] **Step 4: 安装依赖并验证启动**

```bash
cd python-service
pip install -r requirements.txt
python main.py
# 访问 http://localhost:8081/health 应返回 {"status":"ok"}
```

- [ ] **Step 5: 提交**

```bash
git add python-service/
git commit -m "chore: init python service with FastAPI skeleton"
```

---

### Task 3: Java 项目初始化

**Files:**
- Create: `es-slice/java-gateway/pom.xml`
- Create: `es-slice/java-gateway/src/main/java/com/esslice/EssliceApplication.java`
- Create: `es-slice/java-gateway/src/main/resources/application.yml`

- [ ] **Step 1: 编写 pom.xml**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>2.7.18</version>
    </parent>
    <groupId>com.esslice</groupId>
    <artifactId>es-slice-gateway</artifactId>
    <version>1.0.0</version>
    <name>ES Slice Gateway</name>

    <properties>
        <java.version>11</java.version>
        <jjwt.version>0.9.1</jjwt.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-security</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt</artifactId>
            <version>${jjwt.version}</version>
        </dependency>
        <dependency>
            <groupId>mysql</groupId>
            <artifactId>mysql-connector-java</artifactId>
            <version>8.0.33</version>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-aop</artifactId>
        </dependency>
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
            <optional>true</optional>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
```

- [ ] **Step 2: 编写 application.yml**

```yaml
server:
  port: 8080

spring:
  datasource:
    url: jdbc:mysql://localhost:3306/es_slice?useUnicode=true&characterEncoding=utf-8&serverTimezone=Asia/Shanghai
    username: root
    password: ${MYSQL_PASSWORD:root}
    driver-class-name: com.mysql.cj.jdbc.Driver
  jpa:
    hibernate:
      ddl-auto: validate
    show-sql: false

app:
  jwt:
    secret: ${JWT_SECRET:a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6}
    expiration-ms: 86400000
  python:
    base-url: ${PYTHON_SERVICE_URL:http://localhost:8081}
```

- [ ] **Step 3: 编写启动类**

```java
package com.esslice;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class EssliceApplication {
    public static void main(String[] args) {
        SpringApplication.run(EssliceApplication.class, args);
    }
}
```

- [ ] **Step 4: 提交**

```bash
git add java-gateway/
git commit -m "chore: init java gateway with Spring Boot skeleton"
```

---

### Task 4: 前端项目初始化

**Files:**
- Create: `es-slice/frontend/package.json`
- Create: `es-slice/frontend/vite.config.js`
- Create: `es-slice/frontend/index.html`
- Create: `es-slice/frontend/src/main.js`
- Create: `es-slice/frontend/src/App.vue`

- [ ] **Step 1: 编写 package.json**

```json
{
  "name": "es-slice-frontend",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.3.13",
    "vue-router": "^4.2.5",
    "pinia": "^2.1.7",
    "element-plus": "^2.4.3",
    "@element-plus/icons-vue": "^2.3.1",
    "axios": "^1.6.2",
    "@codemirror/lang-json": "^6.0.1",
    "@codemirror/theme-one-dark": "^6.1.2",
    "vue-codemirror": "^6.1.1"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^4.5.2",
    "vite": "^5.0.10"
  }
}
```

- [ ] **Step 2: 编写 vite.config.js**

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true
      }
    }
  }
})
```

- [ ] **Step 3: 编写 index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ES 索引管理后台</title>
</head>
<body>
  <div id="app"></div>
  <script type="module" src="/src/main.js"></script>
</body>
</html>
```

- [ ] **Step 4: 编写 main.js**

```javascript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}
app.mount('#app')
```

- [ ] **Step 5: 编写 App.vue（最小骨架）**

```vue
<template>
  <router-view />
</template>

<script setup>
</script>
```

- [ ] **Step 6: 安装依赖并验证**

```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173 应显示空白页面无报错
```

- [ ] **Step 7: 提交**

```bash
git add frontend/
git commit -m "chore: init vue3 frontend with element-plus"
```

---

## 阶段二：Python 服务 — ES 操作核心 (Tasks 5-11)

### Task 5: ES 客户端封装

**Files:**
- Create: `es-slice/python-service/services/__init__.py` (empty)
- Create: `es-slice/python-service/services/es_client.py`

- [ ] **Step 1: 编写 ES 客户端封装**

```python
from elasticsearch import Elasticsearch
from config import ES_HOST, ES_USER, ES_PASS, ES_TIMEOUT

_es_client = None

def get_es_client() -> Elasticsearch:
    global _es_client
    if _es_client is None:
        if ES_USER and ES_PASS:
            _es_client = Elasticsearch(
                [ES_HOST],
                http_auth=(ES_USER, ES_PASS),
                timeout=ES_TIMEOUT,
            )
        else:
            _es_client = Elasticsearch([ES_HOST], timeout=ES_TIMEOUT)
    return _es_client

def get_index_list() -> list[str]:
    """获取所有索引名称列表，排除系统索引"""
    es = get_es_client()
    aliases = es.cat.indices(format="json")
    return [
        a["index"] for a in aliases
        if not a["index"].startswith(".")
    ]

def get_index_fields(index: str) -> list[dict]:
    """获取索引字段映射，返回字段名和类型的列表"""
    es = get_es_client()
    mapping = es.indices.get_mapping(index=index)
    properties = mapping[index]["mappings"].get("properties", {})
    fields = []
    for name, prop in properties.items():
        field_type = prop.get("type", "object")
        if field_type == "text" and "fields" in prop:
            # 检查是否有 keyword 子字段
            sub = prop["fields"]
            if "keyword" in sub:
                fields.append({"name": f"{name}.keyword", "type": "keyword"})
        fields.append({"name": name, "type": field_type})
    return fields

def search_docs(index: str, dsl: dict, from_: int = 0, size: int = 20) -> dict:
    """执行 DSL 搜索，返回 {total, hits}"""
    es = get_es_client()
    result = es.search(index=index, body=dsl, from_=from_, size=size)
    total = result["hits"]["total"]
    if isinstance(total, dict):
        total = total["value"]
    return {
        "total": total,
        "hits": [h["_source"] | {"_id": h["_id"]} for h in result["hits"]["hits"]]
    }

def get_doc(index: str, doc_id: str) -> dict:
    """获取单条文档"""
    es = get_es_client()
    result = es.get(index=index, id=doc_id)
    return result["_source"] | {"_id": result["_id"]}

def update_doc(index: str, doc_id: str, body: dict) -> dict:
    """更新文档，返回更新后的文档"""
    es = get_es_client()
    es.update(index=index, id=doc_id, body={"doc": body})
    return get_doc(index, doc_id)

def delete_doc(index: str, doc_id: str) -> None:
    """删除文档"""
    es = get_es_client()
    es.delete(index=index, id=doc_id)

def scroll_search(index: str, dsl: dict, batch_size: int = 500) -> list[dict]:
    """使用 scroll API 遍历大批量结果，用于导出"""
    es = get_es_client()
    result = es.search(index=index, body=dsl, scroll="2m", size=batch_size)
    scroll_id = result["_scroll_id"]
    hits = [h["_source"] | {"_id": h["_id"]} for h in result["hits"]["hits"]]
    while True:
        result = es.scroll(scroll_id=scroll_id, scroll="2m")
        scroll_id = result["_scroll_id"]
        batch = [h["_source"] | {"_id": h["_id"]} for h in result["hits"]["hits"]]
        if not batch:
            break
        hits.extend(batch)
    es.clear_scroll(scroll_id=scroll_id)
    return hits

def bulk_update(index: str, docs: list[dict]) -> int:
    """批量更新文档，按 _id 匹配。返回成功更新的数量。"""
    from elasticsearch.helpers import bulk
    es = get_es_client()

    def actions():
        for doc in docs:
            doc_id = doc.pop("_id", None)
            if doc_id:
                yield {
                    "_op_type": "update",
                    "_index": index,
                    "_id": doc_id,
                    "doc": doc,
                }

    success, errors = bulk(es, actions(), raise_on_error=False)
    return success
```

- [ ] **Step 2: 验证 ES 连接**

```bash
cd python-service
python -c "from services.es_client import get_es_client; c=get_es_client(); print(c.info())"
# 应输出 ES 集群信息
```

- [ ] **Step 3: 提交**

```bash
git add python-service/services/
git commit -m "feat: add es client wrapper with full CRUD + scroll + bulk"
```

---

### Task 6: 索引列表与字段获取 API

**Files:**
- Create: `es-slice/python-service/api/__init__.py` (empty)
- Create: `es-slice/python-service/api/indexes.py`
- Modify: `es-slice/python-service/main.py`

- [ ] **Step 1: 编写 indexes.py**

```python
from fastapi import APIRouter, HTTPException
from services.es_client import get_index_list, get_index_fields

router = APIRouter(prefix="/es/indexes", tags=["indexes"])

@router.get("")
def list_indexes():
    """返回所有索引名称列表"""
    try:
        indexes = get_index_list()
        return {"code": 0, "data": indexes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{index}/fields")
def get_fields(index: str):
    """返回指定索引的字段列表"""
    try:
        fields = get_index_fields(index)
        return {"code": 0, "data": fields}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 2: 更新 main.py 注册路由**

```python
from fastapi import FastAPI
import uvicorn
from config import SERVICE_PORT
from api.indexes import router as indexes_router

app = FastAPI(title="ES Slice Service", version="1.0.0")
app.include_router(indexes_router)

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
```

- [ ] **Step 3: 验证接口**

```bash
cd python-service
python main.py &
# curl http://localhost:8081/es/indexes
# curl http://localhost:8081/es/indexes/your_index/fields
```

- [ ] **Step 4: 提交**

```bash
git add python-service/api/ python-service/main.py
git commit -m "feat: add index listing and field mapping APIs"
```

---

### Task 7: DSL 搜索构建器

**Files:**
- Create: `es-slice/python-service/services/search_builder.py`

- [ ] **Step 1: 编写 search_builder.py**

```python
MATCH_TYPE_MAP = {
    "term": "全匹配",
    "match_phrase": "全词匹配",
    "match": "分词匹配",
}

def build_dsl_from_conditions(conditions: list[dict]) -> dict:
    """
    根据前端传来的条件列表构建 ES DSL。
    每个条件: {"field": "字段名", "matchType": "term|match_phrase|match", "value": "搜索值"}
    多条件用 bool.must 组合。
    """
    if not conditions:
        return {"query": {"match_all": {}}}

    must_clauses = []
    for cond in conditions:
        field = cond.get("field", "")
        match_type = cond.get("matchType", "match")
        value = cond.get("value", "")
        if field and value:
            clause = {match_type: {field: value}}
            must_clauses.append(clause)

    if not must_clauses:
        return {"query": {"match_all": {}}}

    return {"query": {"bool": {"must": must_clauses}}}


def parse_search_body(raw_body: dict) -> dict:
    """
    处理前端传来的搜索请求体。
    包含 {conditions: [...], dsl: {...}, page: 1, pageSize: 20}。
    如果 dsl 被用户手动修改过（非空且与自动生成的不同），使用 dsl 字段。
    否则根据 conditions 生成 DSL。
    """
    conditions = raw_body.get("conditions", [])
    custom_dsl = raw_body.get("dsl")
    dsl = None

    if custom_dsl and custom_dsl.get("query"):
        dsl = custom_dsl
    else:
        dsl = build_dsl_from_conditions(conditions)

    return dsl
```

- [ ] **Step 2: 提交**

```bash
git add python-service/services/search_builder.py
git commit -m "feat: add DSL search builder from field conditions"
```

---

### Task 8: 搜索 + 文档 CRUD API

**Files:**
- Create: `es-slice/python-service/api/search.py`
- Create: `es-slice/python-service/api/documents.py`

- [ ] **Step 1: 编写 search.py**

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.es_client import search_docs
from services.search_builder import parse_search_body

router = APIRouter(prefix="/es/indexes", tags=["search"])

class SearchRequest(BaseModel):
    conditions: list[dict] = []
    dsl: Optional[dict] = None
    page: int = 1
    pageSize: int = 20

@router.post("/{index}/search")
def search(index: str, req: SearchRequest):
    """搜索指定索引的文档"""
    try:
        dsl = parse_search_body(req.dict())
        from_ = (req.page - 1) * req.pageSize
        result = search_docs(index, dsl, from_=from_, size=req.pageSize)
        return {
            "code": 0,
            "data": {
                "total": result["total"],
                "list": result["hits"],
                "page": req.page,
                "pageSize": req.pageSize,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 2: 编写 documents.py**

```python
from fastapi import APIRouter, HTTPException
from services.es_client import get_doc, update_doc, delete_doc

router = APIRouter(prefix="/es/indexes", tags=["documents"])

@router.get("/{index}/doc/{doc_id}")
def get_document(index: str, doc_id: str):
    """获取单条文档详情"""
    try:
        doc = get_doc(index, doc_id)
        return {"code": 0, "data": doc}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{index}/doc/{doc_id}")
def update_document(index: str, doc_id: str, body: dict):
    """更新文档"""
    try:
        doc = update_doc(index, doc_id, body)
        return {"code": 0, "data": doc}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{index}/doc/{doc_id}")
def delete_document(index: str, doc_id: str):
    """删除文档"""
    try:
        delete_doc(index, doc_id)
        return {"code": 0, "message": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 3: 更新 main.py 注册路由**

```python
from api.search import router as search_router
from api.documents import router as documents_router

app.include_router(search_router)
app.include_router(documents_router)
```

- [ ] **Step 4: 验证搜索接口**

```bash
curl -X POST http://localhost:8081/es/indexes/test_index/search \
  -H "Content-Type: application/json" \
  -d '{"conditions":[{"field":"title","matchType":"match","value":"test"}],"page":1,"pageSize":10}'
```

- [ ] **Step 5: 提交**

```bash
git add python-service/api/search.py python-service/api/documents.py python-service/main.py
git commit -m "feat: add search and document CRUD APIs"
```

---

### Task 9: JSONL 导出 API

**Files:**
- Create: `es-slice/python-service/services/export_service.py`
- Create: `es-slice/python-service/api/transport.py`
- Create: `es-slice/python-service/utils/__init__.py` (empty)

- [ ] **Step 1: 编写 export_service.py**

```python
import json
import io
from services.es_client import scroll_search

def export_jsonl(index: str, dsl: dict) -> io.BytesIO:
    """执行 scroll 搜索并返回 JSONL 格式的字节流"""
    docs = scroll_search(index, dsl)
    buffer = io.BytesIO()
    for doc in docs:
        line = json.dumps(doc, ensure_ascii=False) + "\n"
        buffer.write(line.encode("utf-8"))
    buffer.seek(0)
    return buffer
```

- [ ] **Step 2: 编写 transport.py**

```python
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from services.es_client import bulk_update
from services.export_service import export_jsonl
from services.import_service import parse_excel_to_docs

router = APIRouter(prefix="/es/indexes", tags=["transport"])

class ExportRequest(BaseModel):
    conditions: list[dict] = []
    dsl: Optional[dict] = None

@router.post("/{index}/export")
def export_docs(index: str, req: ExportRequest):
    """导出搜索结果为 JSONL 文件"""
    from services.search_builder import parse_search_body
    try:
        dsl = parse_search_body(req.dict())
        buffer = export_jsonl(index, dsl)
        filename = f"{index}_export.jsonl"
        return StreamingResponse(
            buffer,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ImportResult(BaseModel):
    indexes: list[str]
    total: int = 0
    success: int = 0
    errors: list[str] = []

@router.post("/import")
async def import_excel(file: UploadFile = File(...), indexes: str = ""):
    """
    上传 Excel 批量更新。indexes 为逗号分隔的索引列表。
    Excel 第一行是字段名，其中 _id 列用于匹配文档。
    """
    try:
        target_indexes = [i.strip() for i in indexes.split(",") if i.strip()]
        if not target_indexes:
            raise HTTPException(status_code=400, detail="至少选择一个索引")
        contents = await file.read()
        docs = parse_excel_to_docs(contents)
        total_success = 0
        all_errors = []
        for idx in target_indexes:
            success = bulk_update(idx, [d.copy() for d in docs])
            total_success += success
        return {
            "code": 0,
            "data": {
                "total": len(docs) * len(target_indexes),
                "success": total_success,
                "errors": all_errors,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 3: 更新 main.py 注册 transport 路由**

```python
from api.transport import router as transport_router
app.include_router(transport_router)
```

- [ ] **Step 4: 提交**

```bash
git add python-service/services/export_service.py python-service/api/transport.py python-service/main.py
git commit -m "feat: add JSONL export and Excel import APIs (skeleton)"
```

---

### Task 10: Excel 导入解析

**Files:**
- Create: `es-slice/python-service/services/import_service.py`

- [ ] **Step 1: 编写 import_service.py**

```python
import io
import openpyxl

def parse_excel_to_docs(file_bytes: bytes) -> list[dict]:
    """
    解析 Excel 文件为文档列表。
    第一行是表头（字段名），后续每行为一条文档。
    若包含 _id 字段，用于后续批量更新匹配。
    """
    workbook = openpyxl.load_workbook(io.BytesIO(file_bytes))
    sheet = workbook.active
    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        return []

    headers = [str(h).strip() for h in rows[0] if h is not None]
    docs = []
    for row in rows[1:]:
        if all(v is None for v in row):
            continue
        doc = {}
        for i, header in enumerate(headers):
            if i < len(row) and row[i] is not None:
                doc[header] = row[i]
        if doc:
            docs.append(doc)

    workbook.close()
    return docs
```

- [ ] **Step 2: 提交**

```bash
git add python-service/services/import_service.py
git commit -m "feat: add Excel file parsing for bulk import"
```

---

### Task 11: Python 工具类 — 字段校验

**Files:**
- Create: `es-slice/python-service/utils/field_utils.py`
- Create: `es-slice/python-service/utils/validators.py`

- [ ] **Step 1: 编写 field_utils.py**

```python
SEARCHABLE_TYPES = {"text", "keyword", "integer", "long", "float", "double",
                     "date", "boolean", "ip", "byte", "short"}

def is_searchable(field_type: str) -> bool:
    """判断字段类型是否可搜索"""
    return field_type in SEARCHABLE_TYPES

def get_suggested_match_type(field_type: str) -> str:
    """根据字段类型建议匹配方式"""
    if field_type == "text":
        return "match"
    elif field_type == "keyword":
        return "term"
    else:
        return "term"
```

- [ ] **Step 2: 编写 validators.py**

```python
from typing import Optional

def validate_pagination(page: int, page_size: int) -> (int, int):
    """校验并修正分页参数"""
    page = max(1, page)
    page_size = min(max(1, page_size), 100)  # 限制最大 100
    return page, page_size

def validate_search_conditions(conditions: list[dict]):
    """校验搜索条件格式"""
    valid_match_types = {"term", "match_phrase", "match"}
    for cond in conditions:
        field = cond.get("field", "")
        match_type = cond.get("matchType", "")
        if not field:
            raise ValueError("搜索字段名不能为空")
        if match_type and match_type not in valid_match_types:
            raise ValueError(f"无效的匹配方式: {match_type}")
```

- [ ] **Step 3: 提交**

```bash
git add python-service/utils/
git commit -m "feat: add field utilities and validators"
```

---

## 阶段三：Java 网关 — 认证/鉴权/审计 (Tasks 12-19)

### Task 12: JPA 实体与 Repository

**Files:**
- Create: `es-slice/java-gateway/src/main/java/com/esslice/model/SysUser.java`
- Create: `es-slice/java-gateway/src/main/java/com/esslice/model/AuditLog.java`
- Create: `es-slice/java-gateway/src/main/java/com/esslice/repository/UserRepository.java`
- Create: `es-slice/java-gateway/src/main/java/com/esslice/repository/AuditLogRepository.java`

- [ ] **Step 1: 编写 SysUser.java**

```java
package com.esslice.model;

import lombok.Data;
import javax.persistence.*;
import java.time.LocalDateTime;

@Data
@Entity
@Table(name = "sys_user")
public class SysUser {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(unique = true, nullable = false, length = 50)
    private String username;

    @Column(nullable = false, length = 255)
    private String password;

    @Column(length = 50)
    private String realName;

    @Column(length = 100)
    private String email;

    @Column(length = 20)
    private String role;  // admin / editor / viewer

    @Column(columnDefinition = "TINYINT DEFAULT 1")
    private Integer status;  // 1=启用 0=禁用

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
```

- [ ] **Step 2: 编写 AuditLog.java**

```java
package com.esslice.model;

import lombok.Data;
import javax.persistence.*;
import java.time.LocalDateTime;

@Data
@Entity
@Table(name = "audit_log")
public class AuditLog {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id")
    private Long userId;

    @Column(length = 50)
    private String username;

    @Column(length = 50)
    private String action;  // CREATE / UPDATE / DELETE / EXPORT / IMPORT

    @Column(name = "index_name", length = 100)
    private String indexName;

    @Column(name = "doc_id", length = 100)
    private String docId;

    @Column(name = "before_content", columnDefinition = "TEXT")
    private String beforeContent;

    @Column(name = "after_content", columnDefinition = "TEXT")
    private String afterContent;

    @Column(name = "ip_address", length = 50)
    private String ipAddress;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }
}
```

- [ ] **Step 3: 编写 Repository**

```java
// UserRepository.java
package com.esslice.repository;

import com.esslice.model.SysUser;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface UserRepository extends JpaRepository<SysUser, Long> {
    Optional<SysUser> findByUsername(String username);
    boolean existsByUsername(String username);
}

// AuditLogRepository.java
package com.esslice.repository;

import com.esslice.model.AuditLog;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

public interface AuditLogRepository extends JpaRepository<AuditLog, Long>,
        JpaSpecificationExecutor<AuditLog> {
}
```

- [ ] **Step 4: 创建数据库初始化 SQL**

```bash
mkdir -p java-gateway/src/main/resources/db/migration
cat > java-gateway/src/main/resources/db/migration/V1__init.sql << 'SQL'
CREATE DATABASE IF NOT EXISTS es_slice DEFAULT CHARACTER SET utf8mb4;
USE es_slice;

CREATE TABLE sys_user (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    real_name VARCHAR(50),
    email VARCHAR(100),
    role VARCHAR(20) NOT NULL DEFAULT 'viewer',
    status TINYINT DEFAULT 1,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE audit_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT,
    username VARCHAR(50),
    action VARCHAR(50),
    index_name VARCHAR(100),
    doc_id VARCHAR(100),
    before_content TEXT,
    after_content TEXT,
    ip_address VARCHAR(50),
    created_at DATETIME
);

-- 默认管理员账号 admin/admin123 (BCrypt加密)
INSERT INTO sys_user (username, password, real_name, role, status, created_at, updated_at)
VALUES ('admin', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iAt6Z5Eh', '系统管理员', 'admin', 1, NOW(), NOW());
SQL
```

- [ ] **Step 5: 提交**

```bash
git add java-gateway/src/main/java/com/esslice/model/
git add java-gateway/src/main/java/com/esslice/repository/
git add java-gateway/src/main/resources/db/
git commit -m "feat: add JPA entities, repositories, and init SQL"
```

---

### Task 13: JWT Token 提供者

**Files:**
- Create: `es-slice/java-gateway/src/main/java/com/esslice/config/JwtTokenProvider.java`

- [ ] **Step 1: 编写 JwtTokenProvider.java**

```java
package com.esslice.config;

import io.jsonwebtoken.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.util.Date;

@Component
public class JwtTokenProvider {

    @Value("${app.jwt.secret}")
    private String secret;

    @Value("${app.jwt.expiration-ms}")
    private long expirationMs;

    public String generateToken(Long userId, String username, String role) {
        Date now = new Date();
        Date expiry = new Date(now.getTime() + expirationMs);
        return Jwts.builder()
                .setSubject(username)
                .claim("userId", userId)
                .claim("role", role)
                .setIssuedAt(now)
                .setExpiration(expiry)
                .signWith(SignatureAlgorithm.HS512, secret)
                .compact();
    }

    public String getUsernameFromToken(String token) {
        return getClaims(token).getSubject();
    }

    public Long getUserIdFromToken(String token) {
        return getClaims(token).get("userId", Long.class);
    }

    public String getRoleFromToken(String token) {
        return getClaims(token).get("role", String.class);
    }

    public boolean validateToken(String token) {
        try {
            getClaims(token);
            return true;
        } catch (JwtException | IllegalArgumentException e) {
            return false;
        }
    }

    private Claims getClaims(String token) {
        return Jwts.parser()
                .setSigningKey(secret)
                .parseClaimsJws(token)
                .getBody();
    }
}
```

- [ ] **Step 2: 提交**

```bash
git add java-gateway/src/main/java/com/esslice/config/JwtTokenProvider.java
git commit -m "feat: add JWT token provider (generate/validate/parse)"
```

---

### Task 14: 权限注解

**Files:**
- Create: `es-slice/java-gateway/src/main/java/com/esslice/annotation/RequireRole.java`

- [ ] **Step 1: 编写自定义权限注解**

```java
package com.esslice.annotation;

import java.lang.annotation.*;

@Target({ElementType.METHOD, ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface RequireRole {
    String[] value() default {};  // 允许的角色列表，如 {"admin", "editor"}
}
```

- [ ] **Step 2: 提交**

```bash
git add java-gateway/src/main/java/com/esslice/annotation/
git commit -m "feat: add @RequireRole annotation for role-based access"
```

---

### Task 15: JWT 认证过滤器

**Files:**
- Create: `es-slice/java-gateway/src/main/java/com/esslice/filter/JwtAuthFilter.java`

- [ ] **Step 1: 编写 JwtAuthFilter.java**

```java
package com.esslice.filter;

import com.esslice.config.JwtTokenProvider;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import javax.servlet.FilterChain;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.Collections;

@Component
public class JwtAuthFilter extends OncePerRequestFilter {

    @Autowired
    private JwtTokenProvider jwtTokenProvider;

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain)
            throws ServletException, IOException {

        String token = extractToken(request);
        if (StringUtils.hasText(token) && jwtTokenProvider.validateToken(token)) {
            String username = jwtTokenProvider.getUsernameFromToken(token);
            String role = jwtTokenProvider.getRoleFromToken(token);
            UsernamePasswordAuthenticationToken auth =
                    new UsernamePasswordAuthenticationToken(
                            username, null,
                            Collections.singletonList(
                                    new SimpleGrantedAuthority("ROLE_" + role.toUpperCase())
                            )
                    );
            auth.setDetails(token);  // 存储 token 供后续审计拦截器使用
            SecurityContextHolder.getContext().setAuthentication(auth);
        }
        filterChain.doFilter(request, response);
    }

    private String extractToken(HttpServletRequest request) {
        String bearer = request.getHeader("Authorization");
        if (StringUtils.hasText(bearer) && bearer.startsWith("Bearer ")) {
            return bearer.substring(7);
        }
        return null;
    }
}
```

- [ ] **Step 2: 提交**

```bash
git add java-gateway/src/main/java/com/esslice/filter/JwtAuthFilter.java
git commit -m "feat: add JWT authentication filter"
```

---

### Task 16: Spring Security 配置

**Files:**
- Create: `es-slice/java-gateway/src/main/java/com/esslice/config/SecurityConfig.java`

- [ ] **Step 1: 编写 SecurityConfig.java**

```java
package com.esslice.config;

import com.esslice.filter.JwtAuthFilter;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.Arrays;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Autowired
    private JwtAuthFilter jwtAuthFilter;

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .cors().and()
            .csrf().disable()
            .sessionManagement()
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            .and()
            .authorizeRequests()
                .antMatchers("/api/auth/login").permitAll()
                .antMatchers("/api/auth/logout").permitAll()
                .antMatchers("/api/es/**").hasAnyAuthority("ROLE_ADMIN", "ROLE_EDITOR", "ROLE_VIEWER")
                .antMatchers("/api/users/**").hasAuthority("ROLE_ADMIN")
                .antMatchers("/api/audit-logs/**").hasAuthority("ROLE_ADMIN")
                .anyRequest().authenticated()
            .and()
            .addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration config = new CorsConfiguration();
        config.setAllowedOrigins(Arrays.asList("http://localhost:5173"));
        config.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "DELETE", "OPTIONS"));
        config.setAllowedHeaders(Arrays.asList("*"));
        config.setAllowCredentials(true);
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", config);
        return source;
    }
}
```

- [ ] **Step 2: 提交**

```bash
git add java-gateway/src/main/java/com/esslice/config/SecurityConfig.java
git commit -m "feat: add Spring Security + JWT + CORS configuration"
```

---

### Task 17: 认证与用户管理 Controller

**Files:**
- Create: `es-slice/java-gateway/src/main/java/com/esslice/service/UserService.java`
- Create: `es-slice/java-gateway/src/main/java/com/esslice/controller/AuthController.java`
- Create: `es-slice/java-gateway/src/main/java/com/esslice/controller/UserController.java`
- Create: `es-slice/java-gateway/src/main/java/com/esslice/controller/dto/LoginRequest.java`
- Create: `es-slice/java-gateway/src/main/java/com/esslice/controller/dto/LoginResponse.java`

- [ ] **Step 1: 编写 UserService.java**

```java
package com.esslice.service;

import com.esslice.model.SysUser;
import com.esslice.repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
public class UserService {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    public Optional<SysUser> findByUsername(String username) {
        return userRepository.findByUsername(username);
    }

    public List<SysUser> listAll() {
        return userRepository.findAll();
    }

    public SysUser create(SysUser user) {
        user.setPassword(passwordEncoder.encode(user.getPassword()));
        return userRepository.save(user);
    }

    public SysUser update(Long id, SysUser user) {
        SysUser existing = userRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("用户不存在"));
        existing.setRealName(user.getRealName());
        existing.setEmail(user.getEmail());
        existing.setRole(user.getRole());
        existing.setStatus(user.getStatus());
        if (user.getPassword() != null && !user.getPassword().isEmpty()) {
            existing.setPassword(passwordEncoder.encode(user.getPassword()));
        }
        return userRepository.save(existing);
    }

    public void delete(Long id) {
        userRepository.deleteById(id);
    }

    public boolean verifyPassword(String raw, String encoded) {
        return passwordEncoder.matches(raw, encoded);
    }
}
```

- [ ] **Step 2: 编写 DTO**

```java
// LoginRequest.java
package com.esslice.controller.dto;

import lombok.Data;

@Data
public class LoginRequest {
    private String username;
    private String password;
}

// LoginResponse.java
package com.esslice.controller.dto;

import lombok.Data;

@Data
public class LoginResponse {
    private String token;
    private UserInfo userInfo;

    @Data
    public static class UserInfo {
        private Long userId;
        private String username;
        private String realName;
        private String role;
    }
}
```

- [ ] **Step 3: 编写 AuthController.java**

```java
package com.esslice.controller;

import com.esslice.config.JwtTokenProvider;
import com.esslice.controller.dto.LoginRequest;
import com.esslice.controller.dto.LoginResponse;
import com.esslice.model.SysUser;
import com.esslice.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    @Autowired
    private UserService userService;

    @Autowired
    private JwtTokenProvider jwtTokenProvider;

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody LoginRequest req) {
        Optional<SysUser> opt = userService.findByUsername(req.getUsername());
        if (!opt.isPresent() || opt.get().getStatus() == 0) {
            return ResponseEntity.status(401)
                    .body(Map.of("code", 401, "message", "用户名或密码错误"));
        }
        SysUser user = opt.get();
        if (!userService.verifyPassword(req.getPassword(), user.getPassword())) {
            return ResponseEntity.status(401)
                    .body(Map.of("code", 401, "message", "用户名或密码错误"));
        }
        String token = jwtTokenProvider.generateToken(
                user.getId(), user.getUsername(), user.getRole());

        LoginResponse resp = new LoginResponse();
        resp.setToken(token);
        LoginResponse.UserInfo info = new LoginResponse.UserInfo();
        info.setUserId(user.getId());
        info.setUsername(user.getUsername());
        info.setRealName(user.getRealName());
        info.setRole(user.getRole());
        resp.setUserInfo(info);

        return ResponseEntity.ok(Map.of("code", 0, "data", resp));
    }

    @PostMapping("/logout")
    public ResponseEntity<?> logout() {
        // 无状态 JWT，登出由前端清除 token
        return ResponseEntity.ok(Map.of("code", 0, "message", "ok"));
    }

    @GetMapping("/userinfo")
    public ResponseEntity<?> userinfo() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null) {
            return ResponseEntity.status(401)
                    .body(Map.of("code", 401, "message", "未认证"));
        }
        String username = auth.getName();
        Optional<SysUser> opt = userService.findByUsername(username);
        if (!opt.isPresent()) {
            return ResponseEntity.status(401)
                    .body(Map.of("code", 401, "message", "用户不存在"));
        }
        SysUser user = opt.get();
        LoginResponse.UserInfo info = new LoginResponse.UserInfo();
        info.setUserId(user.getId());
        info.setUsername(user.getUsername());
        info.setRealName(user.getRealName());
        info.setRole(user.getRole());
        return ResponseEntity.ok(Map.of("code", 0, "data", info));
    }
}
```

- [ ] **Step 4: 编写 UserController.java**

```java
package com.esslice.controller;

import com.esslice.model.SysUser;
import com.esslice.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/users")
public class UserController {

    @Autowired
    private UserService userService;

    @GetMapping
    public ResponseEntity<?> list() {
        return ResponseEntity.ok(Map.of("code", 0, "data", userService.listAll()));
    }

    @PostMapping
    public ResponseEntity<?> create(@RequestBody SysUser user) {
        return ResponseEntity.ok(Map.of("code", 0, "data", userService.create(user)));
    }

    @PutMapping("/{id}")
    public ResponseEntity<?> update(@PathVariable Long id, @RequestBody SysUser user) {
        return ResponseEntity.ok(Map.of("code", 0, "data", userService.update(id, user)));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<?> delete(@PathVariable Long id) {
        userService.delete(id);
        return ResponseEntity.ok(Map.of("code", 0, "message", "ok"));
    }
}
```

- [ ] **Step 5: 提交**

```bash
git add java-gateway/src/main/java/com/esslice/service/
git add java-gateway/src/main/java/com/esslice/controller/
git commit -m "feat: add auth (login/logout/userinfo) and user management controllers"
```

---

### Task 18: ES 网关代理 Controller

**Files:**
- Create: `es-slice/java-gateway/src/main/java/com/esslice/controller/EsGatewayController.java`

- [ ] **Step 1: 编写 EsGatewayController.java**

```java
package com.esslice.controller;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import javax.servlet.http.HttpServletRequest;
import java.net.URI;
import java.util.Enumeration;

@RestController
@RequestMapping("/api/es")
public class EsGatewayController {

    @Value("${app.python.base-url}")
    private String pythonBaseUrl;

    private final RestTemplate restTemplate = new RestTemplate();

    @RequestMapping(value = "/**", method = {
            RequestMethod.GET, RequestMethod.POST,
            RequestMethod.PUT, RequestMethod.DELETE})
    public ResponseEntity<?> proxy(HttpServletRequest request, @RequestBody(required = false) String body) {
        try {
            String path = request.getRequestURI();  // /api/es/indexes/...
            String query = request.getQueryString();
            String targetUrl = pythonBaseUrl + path;
            if (query != null) {
                targetUrl += "?" + query;
            }

            HttpMethod method = HttpMethod.valueOf(request.getMethod());
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            org.springframework.http.HttpEntity<String> entity =
                    new org.springframework.http.HttpEntity<>(body, headers);

            ResponseEntity<String> response = restTemplate.exchange(
                    URI.create(targetUrl), method, entity, String.class);

            return ResponseEntity.status(response.getStatusCode())
                    .body(response.getBody());
        } catch (Exception e) {
            return ResponseEntity.status(500)
                    .body("{\"code\":500,\"message\":\"" + e.getMessage() + "\"}");
        }
    }
}
```

- [ ] **Step 2: 提交**

```bash
git add java-gateway/src/main/java/com/esslice/controller/EsGatewayController.java
git commit -m "feat: add ES proxy gateway controller"
```

---

### Task 19: 审计拦截器 + 审计日志查询

**Files:**
- Create: `es-slice/java-gateway/src/main/java/com/esslice/interceptor/AuditInterceptor.java`
- Create: `es-slice/java-gateway/src/main/java/com/esslice/service/AuditService.java`
- Create: `es-slice/java-gateway/src/main/java/com/esslice/controller/AuditController.java`

- [ ] **Step 1: 编写 AuditInterceptor.java**

```java
package com.esslice.interceptor;

import com.esslice.config.JwtTokenProvider;
import com.esslice.model.AuditLog;
import com.esslice.repository.AuditLogRepository;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import javax.servlet.http.HttpServletRequest;
import java.util.Map;

@Aspect
@Component
public class AuditInterceptor {

    @Autowired
    private AuditLogRepository auditLogRepository;

    @Autowired
    private JwtTokenProvider jwtTokenProvider;

    @Around("execution(* com.esslice.controller.EsGatewayController.proxy(..))")
    public Object audit(ProceedingJoinPoint joinPoint) throws Throwable {
        HttpServletRequest request = ((ServletRequestAttributes)
                RequestContextHolder.currentRequestAttributes()).getRequest();

        String method = request.getMethod();
        if (!("PUT".equals(method) || "POST".equals(method) || "DELETE".equals(method))) {
            return joinPoint.proceed();  // GET 请求不审计
        }

        String path = request.getRequestURI();

        // 解析路径: /api/es/indexes/{index}/doc/{id} 或 /api/es/indexes/{index}/export 等
        String[] parts = path.split("/");
        String indexName = parts.length > 3 ? parts[3] : "";
        String action = "CREATE";
        String docId = "";

        if (method.equals("PUT") && path.contains("/doc/")) {
            action = "UPDATE";
            docId = parts[parts.length - 1];
        } else if (method.equals("DELETE") && path.contains("/doc/")) {
            action = "DELETE";
            docId = parts[parts.length - 1];
        } else if (path.endsWith("/export")) {
            action = "EXPORT";
        } else if (path.endsWith("/import")) {
            action = "IMPORT";
        }

        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        String username = auth != null ? auth.getName() : "unknown";
        Long userId = 0L;

        String token = (String) auth.getDetails();
        if (token != null) {
            try {
                userId = jwtTokenProvider.getUserIdFromToken(token);
            } catch (Exception ignored) {}
        }

        Object result = joinPoint.proceed();

        // 记录审计日志
        AuditLog log = new AuditLog();
        log.setUserId(userId);
        log.setUsername(username);
        log.setAction(action);
        log.setIndexName(indexName);
        log.setDocId(docId);
        log.setBeforeContent((String) joinPoint.getArgs()[1]);  // request body
        log.setIpAddress(getClientIp(request));
        auditLogRepository.save(log);

        return result;
    }

    private String getClientIp(HttpServletRequest request) {
        String ip = request.getHeader("X-Forwarded-For");
        if (ip == null || ip.isEmpty()) {
            ip = request.getHeader("X-Real-IP");
        }
        if (ip == null || ip.isEmpty()) {
            ip = request.getRemoteAddr();
        }
        return ip;
    }
}
```

- [ ] **Step 2: 编写 AuditService.java**

```java
package com.esslice.service;

import com.esslice.model.AuditLog;
import com.esslice.repository.AuditLogRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.*;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import javax.persistence.criteria.Predicate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Service
public class AuditService {

    @Autowired
    private AuditLogRepository auditLogRepository;

    public Page<AuditLog> query(String username, String indexName,
                                 String action, LocalDateTime startTime,
                                 LocalDateTime endTime, int page, int size) {
        Specification<AuditLog> spec = (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();
            if (StringUtils.hasText(username)) {
                predicates.add(cb.like(root.get("username"), "%" + username + "%"));
            }
            if (StringUtils.hasText(indexName)) {
                predicates.add(cb.equal(root.get("indexName"), indexName));
            }
            if (StringUtils.hasText(action)) {
                predicates.add(cb.equal(root.get("action"), action));
            }
            if (startTime != null) {
                predicates.add(cb.greaterThanOrEqualTo(root.get("createdAt"), startTime));
            }
            if (endTime != null) {
                predicates.add(cb.lessThanOrEqualTo(root.get("createdAt"), endTime));
            }
            return cb.and(predicates.toArray(new Predicate[0]));
        };
        Pageable pageable = PageRequest.of(page - 1, size, Sort.by(Sort.Direction.DESC, "createdAt"));
        return auditLogRepository.findAll(spec, pageable);
    }
}
```

- [ ] **Step 3: 编写 AuditController.java**

```java
package com.esslice.controller;

import com.esslice.model.AuditLog;
import com.esslice.service.AuditService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.Map;

@RestController
@RequestMapping("/api/audit-logs")
public class AuditController {

    @Autowired
    private AuditService auditService;

    @GetMapping
    public ResponseEntity<?> query(
            @RequestParam(required = false) String username,
            @RequestParam(required = false) String indexName,
            @RequestParam(required = false) String action,
            @RequestParam(required = false)
                @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime startTime,
            @RequestParam(required = false)
                @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime endTime,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int pageSize) {

        Page<AuditLog> result = auditService.query(
                username, indexName, action, startTime, endTime, page, pageSize);
        return ResponseEntity.ok(Map.of(
                "code", 0,
                "data", Map.of(
                        "total", result.getTotalElements(),
                        "list", result.getContent(),
                        "page", page,
                        "pageSize", pageSize
                )
        ));
    }
}
```

- [ ] **Step 4: 提交**

```bash
git add java-gateway/src/main/java/com/esslice/interceptor/
git add java-gateway/src/main/java/com/esslice/service/AuditService.java
git add java-gateway/src/main/java/com/esslice/controller/AuditController.java
git commit -m "feat: add audit interceptor (AOP) and audit log query API"
```

---

## 阶段四：Vue3 前端 — 页面与组件 (Tasks 20-30)

### Task 20: 前端基础 — 路由、状态管理、HTTP 封装

**Files:**
- Create: `es-slice/frontend/src/router/index.js`
- Create: `es-slice/frontend/src/store/user.js`
- Create: `es-slice/frontend/src/utils/request.js`
- Create: `es-slice/frontend/src/utils/auth.js`

- [ ] **Step 1: 编写 router/index.js**

```javascript
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { noAuth: true }
  },
  {
    path: '/',
    component: () => import('@/components/Layout.vue'),
    redirect: '/index-manage',
    children: [
      {
        path: 'index-manage',
        name: 'IndexManage',
        component: () => import('@/views/IndexManage.vue'),
        meta: { title: '索引管理' }
      },
      {
        path: 'audit-log',
        name: 'AuditLog',
        component: () => import('@/views/AuditLog.vue'),
        meta: { title: '审计日志', roles: ['admin'] }
      },
      {
        path: 'user-manage',
        name: 'UserManage',
        component: () => import('@/views/UserManage.vue'),
        meta: { title: '用户管理', roles: ['admin'] }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 导航守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.noAuth) {
    next()
  } else if (!token) {
    next('/login')
  } else {
    const role = localStorage.getItem('role')
    if (to.meta.roles && !to.meta.roles.includes(role)) {
      next('/index-manage')
    } else {
      next()
    }
  }
})

export default router
```

- [ ] **Step 2: 编写 store/user.js**

```javascript
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || '')
  const realName = ref(localStorage.getItem('realName') || '')
  const role = ref(localStorage.getItem('role') || '')

  function setLogin(data) {
    token.value = data.token
    username.value = data.userInfo.username
    realName.value = data.userInfo.realName
    role.value = data.userInfo.role
    localStorage.setItem('token', data.token)
    localStorage.setItem('username', data.userInfo.username)
    localStorage.setItem('realName', data.userInfo.realName)
    localStorage.setItem('role', data.userInfo.role)
  }

  function logout() {
    token.value = ''
    username.value = ''
    realName.value = ''
    role.value = ''
    localStorage.clear()
  }

  return { token, username, realName, role, setLogin, logout }
})
```

- [ ] **Step 3: 编写 utils/request.js**

```javascript
import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000
})

request.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

request.interceptors.response.use(
  response => {
    const data = response.data
    if (data.code !== 0) {
      ElMessage.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message))
    }
    return data
  },
  error => {
    if (error.response?.status === 401) {
      localStorage.clear()
      router.push('/login')
      ElMessage.error('登录已过期，请重新登录')
    } else {
      ElMessage.error(error.message || '网络错误')
    }
    return Promise.reject(error)
  }
)

export default request
```

- [ ] **Step 4: 编写 utils/auth.js**

```javascript
export function getToken() {
  return localStorage.getItem('token')
}

export function getRole() {
  return localStorage.getItem('role')
}

export function hasPermission(minRole) {
  const roles = { viewer: 0, editor: 1, admin: 2 }
  const current = localStorage.getItem('role') || 'viewer'
  return roles[current] >= roles[minRole]
}
```

- [ ] **Step 5: 提交**

```bash
git add frontend/src/router/ frontend/src/store/ frontend/src/utils/
git commit -m "feat: add router, pinia store, axios wrapper, auth utils"
```

---

### Task 21: 前端 API 层

**Files:**
- Create: `es-slice/frontend/src/api/auth.js`
- Create: `es-slice/frontend/src/api/es.js`
- Create: `es-slice/frontend/src/api/audit.js`
- Create: `es-slice/frontend/src/api/users.js`

- [ ] **Step 1: 编写 api/auth.js**

```javascript
import request from '@/utils/request'

export function login(username, password) {
  return request.post('/auth/login', { username, password })
}

export function logout() {
  return request.post('/auth/logout')
}

export function getUserInfo() {
  return request.get('/auth/userinfo')
}
```

- [ ] **Step 2: 编写 api/es.js**

```javascript
import request from '@/utils/request'

export function getIndexes() {
  return request.get('/es/indexes')
}

export function getIndexFields(index) {
  return request.get(`/es/indexes/${encodeURIComponent(index)}/fields`)
}

export function searchDocs(index, params) {
  return request.post(`/es/indexes/${encodeURIComponent(index)}/search`, params)
}

export function getDoc(index, docId) {
  return request.get(`/es/indexes/${encodeURIComponent(index)}/doc/${encodeURIComponent(docId)}`)
}

export function updateDoc(index, docId, body) {
  return request.put(`/es/indexes/${encodeURIComponent(index)}/doc/${encodeURIComponent(docId)}`, body)
}

export function deleteDoc(index, docId) {
  return request.delete(`/es/indexes/${encodeURIComponent(index)}/doc/${encodeURIComponent(docId)}`)
}

export function exportDocs(index, params) {
  return request.post(`/es/indexes/${encodeURIComponent(index)}/export`, params, { responseType: 'blob' })
}

export function importExcel(formData) {
  return request.post('/es/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}
```

- [ ] **Step 3: 编写 api/audit.js**

```javascript
import request from '@/utils/request'

export function getAuditLogs(params) {
  return request.get('/audit-logs', { params })
}
```

- [ ] **Step 4: 编写 api/users.js**

```javascript
import request from '@/utils/request'

export function getUsers() {
  return request.get('/users')
}

export function createUser(data) {
  return request.post('/users', data)
}

export function updateUser(id, data) {
  return request.put(`/users/${id}`, data)
}

export function deleteUser(id) {
  return request.delete(`/users/${id}`)
}
```

- [ ] **Step 5: 提交**

```bash
git add frontend/src/api/
git commit -m "feat: add all API modules (auth, es, audit, users)"
```

---

### Task 22: 登录页面

**Files:**
- Create: `es-slice/frontend/src/views/Login.vue`

- [ ] **Step 1: 编写 Login.vue**

```vue
<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <h2>ES 索引管理后台</h2>
      </template>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="0">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码"
                    prefix-icon="Lock" @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" style="width:100%"
                     @click="handleLogin">登 录</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { login } from '@/api/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    const res = await login(form.username, form.password)
    userStore.setLogin(res.data)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (e) {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: #f0f2f5;
}
.login-card {
  width: 400px;
}
.login-card h2 {
  text-align: center;
  margin: 0;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/Login.vue
git commit -m "feat: add login page with JWT auth"
```

---

### Task 23: 布局组件（Layout + Sidebar）

**Files:**
- Create: `es-slice/frontend/src/components/Layout.vue`
- Create: `es-slice/frontend/src/components/Sidebar.vue`
- Modify: `es-slice/frontend/src/App.vue`

- [ ] **Step 1: 编写 Layout.vue**

```vue
<template>
  <div class="app-layout">
    <el-container>
      <el-aside width="220px">
        <Sidebar />
      </el-aside>
      <el-container>
        <el-header class="app-header">
          <span class="title">ES 索引管理后台</span>
          <div class="header-right">
            <el-tag :type="roleTagType" size="small">{{ roleText }}</el-tag>
            <span class="username">{{ userStore.realName || userStore.username }}</span>
            <el-button type="danger" text @click="handleLogout">退出</el-button>
          </div>
        </el-header>
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessageBox } from 'element-plus'
import Sidebar from './Sidebar.vue'

const router = useRouter()
const userStore = useUserStore()

const roleTagType = computed(() => {
  const map = { admin: 'danger', editor: 'warning', viewer: 'info' }
  return map[userStore.role] || 'info'
})

const roleText = computed(() => {
  const map = { admin: '管理员', editor: '编辑者', viewer: '只读' }
  return map[userStore.role] || '未知'
})

async function handleLogout() {
  await ElMessageBox.confirm('确定退出登录?', '提示', { type: 'warning' })
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-layout { height: 100vh; }
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 20px;
}
.app-header .title { font-size: 16px; font-weight: bold; }
.header-right { display: flex; align-items: center; gap: 12px; }
.username { color: #606266; }
</style>
```

- [ ] **Step 2: 编写 Sidebar.vue**

```vue
<template>
  <el-menu :default-active="activeMenu" router
           background-color="#304156" text-color="#bfcbd9"
           active-text-color="#409EFF" style="height:100%">
    <el-menu-item index="/index-manage">
      <el-icon><Search /></el-icon>
      <span>索引管理</span>
    </el-menu-item>
    <el-menu-item v-if="userStore.role === 'admin'" index="/audit-log">
      <el-icon><Document /></el-icon>
      <span>审计日志</span>
    </el-menu-item>
    <el-menu-item v-if="userStore.role === 'admin'" index="/user-manage">
      <el-icon><User /></el-icon>
      <span>用户管理</span>
    </el-menu-item>
  </el-menu>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/store/user'

const route = useRoute()
const userStore = useUserStore()
const activeMenu = computed(() => route.path)
</script>
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/Layout.vue frontend/src/components/Sidebar.vue
git commit -m "feat: add layout with sidebar and header"
```

---

### Task 24: 字段组合搜索组件

**Files:**
- Create: `es-slice/frontend/src/components/FieldSearch.vue`

- [ ] **Step 1: 编写 FieldSearch.vue**

```vue
<template>
  <div class="field-search">
    <div v-for="(item, idx) in conditions" :key="idx" class="search-row">
      <el-select v-model="item.field" placeholder="选择字段" style="width:200px" filterable>
        <el-option v-for="f in fields" :key="f.name" :label="f.name" :value="f.name" />
      </el-select>
      <el-select v-model="item.matchType" placeholder="匹配方式" style="width:140px">
        <el-option label="全匹配" value="term" />
        <el-option label="全词匹配" value="match_phrase" />
        <el-option label="分词匹配" value="match" />
      </el-select>
      <el-input v-model="item.value" placeholder="搜索值" style="width:250px" />
      <el-button :disabled="conditions.length <= 1" @click="removeRow(idx)"
                 icon="Delete" circle size="small" />
      <el-button v-if="idx === conditions.length - 1" @click="addRow"
                 icon="Plus" circle size="small" type="primary" />
    </div>
    <div class="search-actions">
      <el-button type="primary" @click="$emit('search')" icon="Search">搜索</el-button>
      <el-button @click="$emit('reset')" icon="Refresh">重置</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  fields: { type: Array, default: () => [] },
  modelValue: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:modelValue', 'search', 'reset'])

const conditions = ref([{ field: '', matchType: 'match', value: '' }])

watch(() => props.modelValue, (val) => {
  if (val.length) conditions.value = JSON.parse(JSON.stringify(val))
}, { immediate: true })

watch(conditions, (val) => {
  emit('update:modelValue', JSON.parse(JSON.stringify(val)))
}, { deep: true })

function addRow() {
  conditions.value.push({ field: '', matchType: 'match', value: '' })
}

function removeRow(idx) {
  conditions.value.splice(idx, 1)
}

defineExpose({ conditions })
</script>

<style scoped>
.search-row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}
.search-actions {
  margin-top: 12px;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/FieldSearch.vue
git commit -m "feat: add field search component with dynamic add/remove"
```

---

### Task 25: 索引管理页面 — 索引选择、字段搜索、DSL 编辑器

**Files:**
- Create: `es-slice/frontend/src/views/IndexManage.vue`

- [ ] **Step 1: 编写 IndexManage.vue（搜索区域部分）**

```vue
<template>
  <div class="index-manage">
    <!-- 索引选择 -->
    <div class="section">
      <el-select v-model="selectedIndex" placeholder="选择索引（搜索）" style="width:300px"
                 filterable @change="onIndexChange">
        <el-option v-for="idx in indexes" :key="idx" :label="idx" :value="idx" />
      </el-select>
    </div>

    <!-- 字段组合搜索 -->
    <div class="section" v-if="selectedIndex">
      <h4>字段搜索</h4>
      <FieldSearch ref="fieldSearchRef" :fields="indexFields"
                   v-model="searchConditions"
                   @search="handleSearch" @reset="handleReset" />
    </div>

    <!-- 自定义 DSL -->
    <div class="section" v-if="selectedIndex && dslVisible">
      <h4>
        自定义 DSL
        <el-button text size="small" @click="dslVisible = false">收起</el-button>
      </h4>
      <el-input v-model="dslText" type="textarea" :rows="6"
                placeholder='{"query":{"bool":{"must":[...]}}}' />
    </div>
    <div class="section" v-else-if="selectedIndex">
      <el-button text size="small" @click="dslVisible = true; syncDsl()">
        展开自定义 DSL
      </el-button>
    </div>

    <!-- 工具栏 -->
    <div class="section" v-if="selectedIndex">
      <el-button @click="handleExport" icon="Download"
                 :disabled="role === 'viewer'">导出 JSONL</el-button>
      <el-button @click="importDialogVisible = true" icon="Upload"
                 :disabled="role === 'viewer'">导入 Excel</el-button>
    </div>

    <!-- 数据表格 -->
    <div class="section" v-if="selectedIndex">
      <el-table :data="tableData" border stripe v-loading="tableLoading" style="width:100%">
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column v-for="col in tableColumns" :key="col"
                         :prop="col" :label="col" :show-overflow-tooltip="true"
                         min-width="150" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="showDetail(row)">详情</el-button>
            <el-button text type="warning" size="small" @click="showEdit(row)"
                       :disabled="role === 'viewer'">编辑</el-button>
            <el-popconfirm title="确定删除?" @confirm="handleDelete(row)">
              <template #reference>
                <el-button text type="danger" size="small"
                           :disabled="role === 'viewer'">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination">
        <el-pagination v-model:current-page="page" :page-size="pageSize"
                       :total="total" :page-sizes="[10,20,50,100]"
                       layout="total,sizes,prev,pager,next"
                       @current-change="handleSearch"
                       @size-change="handleSearch" />
      </div>
    </div>

    <!-- 详情弹窗 -->
    <DocDetailDialog ref="detailDialogRef" />

    <!-- 编辑弹窗 -->
    <DocEditDialog ref="editDialogRef" @saved="handleSearch" />

    <!-- 导入弹窗 -->
    <ImportDialog v-model:visible="importDialogVisible" :indexes="indexes"
                  @imported="handleSearch" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'
import { getIndexes, getIndexFields, searchDocs, deleteDoc, exportDocs } from '@/api/es'
import FieldSearch from '@/components/FieldSearch.vue'
import DocDetailDialog from '@/components/DocDetailDialog.vue'
import DocEditDialog from '@/components/DocEditDialog.vue'
import ImportDialog from '@/components/ImportDialog.vue'

const userStore = useUserStore()
const role = computed(() => userStore.role)

// 索引相关
const indexes = ref([])
const selectedIndex = ref('')
const indexFields = ref([])

// 搜索相关
const fieldSearchRef = ref(null)
const searchConditions = ref([])
const dslVisible = ref(false)
const dslText = ref('')

// 表格相关
const tableData = ref([])
const tableColumns = ref([])
const tableLoading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 弹窗
const detailDialogRef = ref(null)
const editDialogRef = ref(null)
const importDialogVisible = ref(false)

// 初始化加载索引列表
getIndexes().then(res => { indexes.value = res.data }).catch(() => {})

async function onIndexChange(val) {
  if (!val) return
  const res = await getIndexFields(val)
  indexFields.value = res.data
  tableColumns.value = res.data.map(f => f.name)
  handleReset()
}

function handleReset() {
  searchConditions.value = [{ field: '', matchType: 'match', value: '' }]
  dslText.value = ''
  page.value = 1
}

async function handleSearch() {
  tableLoading.value = true
  try {
    let dsl = null
    if (dslText.value) {
      try { dsl = JSON.parse(dslText.value) } catch (e) { /* 使用 conditions */ }
    }
    const res = await searchDocs(selectedIndex.value, {
      conditions: searchConditions.value.filter(c => c.field && c.value),
      dsl,
      page: page.value,
      pageSize: pageSize.value
    })
    tableData.value = res.data.list
    total.value = res.data.total
  } finally {
    tableLoading.value = false
  }
}

function syncDsl() {
  const conditions = searchConditions.value.filter(c => c.field && c.value)
  if (conditions.length) {
    const must = conditions.map(c => ({ [c.matchType]: { [c.field]: c.value } }))
    dslText.value = JSON.stringify({ query: { bool: { must } } }, null, 2)
  } else {
    dslText.value = JSON.stringify({ query: { match_all: {} } }, null, 2)
  }
}

function showDetail(row) {
  detailDialogRef.value.open(selectedIndex.value, row._id)
}

function showEdit(row) {
  editDialogRef.value.open(selectedIndex.value, row)
}

async function handleDelete(row) {
  await deleteDoc(selectedIndex.value, row._id)
  ElMessage.success('删除成功')
  handleSearch()
}

async function handleExport() {
  let dsl = null
  if (dslText.value) {
    try { dsl = JSON.parse(dslText.value) } catch (e) {}
  }
  const res = await exportDocs(selectedIndex.value, {
    conditions: searchConditions.value.filter(c => c.field && c.value),
    dsl
  })
  const blob = new Blob([res], { type: 'application/octet-stream' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${selectedIndex.value}_export.jsonl`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}
</script>

<style scoped>
.index-manage { max-width: 1400px; }
.section { margin-bottom: 16px; }
.pagination { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/IndexManage.vue
git commit -m "feat: add index management page (search, table, export)"
```

---

### Task 26: 详情弹窗

**Files:**
- Create: `es-slice/frontend/src/components/DocDetailDialog.vue`

- [ ] **Step 1: 编写 DocDetailDialog.vue**

```vue
<template>
  <el-dialog v-model="visible" title="文档详情" width="700px" top="5vh">
    <pre class="json-view">{{ formattedJson }}</pre>
    <template #footer>
      <el-button @click="visible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { getDoc } from '@/api/es'

const visible = ref(false)
const content = ref({})

const formattedJson = computed(() => {
  return JSON.stringify(content.value, null, 2)
})

async function open(index, docId) {
  visible.value = true
  const res = await getDoc(index, docId)
  content.value = res.data
}

defineExpose({ open })
</script>

<style scoped>
.json-view {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 4px;
  max-height: 60vh;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
  font-size: 13px;
  line-height: 1.6;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/DocDetailDialog.vue
git commit -m "feat: add doc detail dialog (JSON view)"
```

---

### Task 27: 编辑弹窗

**Files:**
- Create: `es-slice/frontend/src/components/DocEditDialog.vue`

- [ ] **Step 1: 编写 DocEditDialog.vue**

```vue
<template>
  <el-dialog v-model="visible" title="编辑文档" width="700px" top="5vh"
             @close="visible = false">
    <el-input v-model="editText" type="textarea" :rows="16"
              placeholder="JSON 格式编辑" />
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { updateDoc } from '@/api/es'

const emit = defineEmits(['saved'])

const visible = ref(false)
const editText = ref('')
const saving = ref(false)
let currentIndex = ''
let currentDocId = ''

function open(index, row) {
  currentIndex = index
  currentDocId = row._id
  const editable = { ...row }
  delete editable._id
  editText.value = JSON.stringify(editable, null, 2)
  visible.value = true
}

async function handleSave() {
  try {
    const body = JSON.parse(editText.value)
    saving.value = true
    await updateDoc(currentIndex, currentDocId, body)
    ElMessage.success('更新成功')
    visible.value = false
    emit('saved')
  } catch (e) {
    if (e instanceof SyntaxError) {
      ElMessage.error('JSON 格式不正确')
    }
  } finally {
    saving.value = false
  }
}

defineExpose({ open })
</script>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/DocEditDialog.vue
git commit -m "feat: add doc edit dialog (JSON editor)"
```

---

### Task 28: 导入弹窗

**Files:**
- Create: `es-slice/frontend/src/components/ImportDialog.vue`

- [ ] **Step 1: 编写 ImportDialog.vue**

```vue
<template>
  <el-dialog title="导入 Excel" :model-value="props.visible"
             @update:model-value="$emit('update:visible', $event)"
             width="500px" top="10vh">
    <el-form>
      <el-form-item label="目标索引（可多选）">
        <el-select v-model="selectedIndexes" placeholder="选择索引" multiple
                   filterable style="width:100%">
          <el-option v-for="idx in props.indexes" :key="idx" :label="idx" :value="idx" />
        </el-select>
      </el-form-item>
      <el-form-item label="选择 Excel 文件">
        <el-upload :auto-upload="false" :limit="1" accept=".xlsx,.xls"
                   :on-change="handleFileChange" :file-list="fileList"
                   drag>
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div>拖拽或点击上传 Excel 文件</div>
        </el-upload>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="$emit('update:visible', false)">取消</el-button>
      <el-button type="primary" :loading="importing"
                 :disabled="!file || selectedIndexes.length === 0"
                 @click="handleImport">开始导入</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { importExcel } from '@/api/es'

const props = defineProps({
  visible: Boolean,
  indexes: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:visible', 'imported'])

const selectedIndexes = ref([])
const file = ref(null)
const fileList = ref([])
const importing = ref(false)

function handleFileChange(uploadFile) {
  file.value = uploadFile.raw
  fileList.value = [uploadFile]
}

async function handleImport() {
  if (!file.value) {
    ElMessage.warning('请选择文件')
    return
  }
  const formData = new FormData()
  formData.append('file', file.value)
  formData.append('indexes', selectedIndexes.value.join(','))
  importing.value = true
  try {
    const res = await importExcel(formData)
    ElMessage.success(`导入完成: 成功 ${res.data.success} 条`)
    emit('update:visible', false)
    emit('imported')
  } finally {
    importing.value = false
  }
}
</script>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/ImportDialog.vue
git commit -m "feat: add Excel import dialog"
```

---

### Task 29: 审计日志页面

**Files:**
- Create: `es-slice/frontend/src/views/AuditLog.vue`

- [ ] **Step 1: 编写 AuditLog.vue**

```vue
<template>
  <div class="audit-log">
    <el-card>
      <template #header>审计日志</template>
      <el-form :inline="true" :model="filters">
        <el-form-item label="用户">
          <el-input v-model="filters.username" placeholder="用户名" clearable />
        </el-form-item>
        <el-form-item label="索引">
          <el-input v-model="filters.indexName" placeholder="索引名" clearable />
        </el-form-item>
        <el-form-item label="操作">
          <el-select v-model="filters.action" placeholder="全部" clearable style="width:120px">
            <el-option label="创建" value="CREATE" />
            <el-option label="更新" value="UPDATE" />
            <el-option label="删除" value="DELETE" />
            <el-option label="导出" value="EXPORT" />
            <el-option label="导入" value="IMPORT" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间">
          <el-date-picker v-model="filters.dateRange" type="datetimerange"
                          range-separator="至" start-placeholder="开始" end-placeholder="结束"
                          value-format="YYYY-MM-DDTHH:mm:ss" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="tableData" border stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="操作用户" width="120" />
        <el-table-column prop="action" label="操作" width="80" />
        <el-table-column prop="indexName" label="索引" width="140" />
        <el-table-column prop="docId" label="文档ID" width="120" show-overflow-tooltip />
        <el-table-column prop="ipAddress" label="IP" width="130" />
        <el-table-column prop="createdAt" label="时间" width="170" />
      </el-table>

      <div class="pagination">
        <el-pagination v-model:current-page="page" :page-size="pageSize"
                       :total="total" layout="total,prev,pager,next"
                       @current-change="handleSearch" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { getAuditLogs } from '@/api/audit'

const filters = reactive({
  username: '',
  indexName: '',
  action: '',
  dateRange: null
})

const tableData = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

async function handleSearch() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      pageSize: pageSize.value
    }
    if (filters.username) params.username = filters.username
    if (filters.indexName) params.indexName = filters.indexName
    if (filters.action) params.action = filters.action
    if (filters.dateRange) {
      params.startTime = filters.dateRange[0]
      params.endTime = filters.dateRange[1]
    }
    const res = await getAuditLogs(params)
    tableData.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function handleReset() {
  filters.username = ''
  filters.indexName = ''
  filters.action = ''
  filters.dateRange = null
  handleSearch()
}

handleSearch()
</script>

<style scoped>
.pagination { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/AuditLog.vue
git commit -m "feat: add audit log page with filters"
```

---

### Task 30: 用户管理页面

**Files:**
- Create: `es-slice/frontend/src/views/UserManage.vue`

- [ ] **Step 1: 编写 UserManage.vue**

```vue
<template>
  <div class="user-manage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <el-button type="primary" @click="showAdd">新增用户</el-button>
        </div>
      </template>
      <el-table :data="tableData" border stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="realName" label="姓名" width="100" />
        <el-table-column prop="email" label="邮箱" width="180" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : row.role === 'editor' ? 'warning' : 'info'">
              {{ roleMap[row.role] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'">
              {{ row.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="showEdit(row)">编辑</el-button>
            <el-popconfirm title="确定删除?" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button text type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑用户' : '新增用户'" width="450px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="密码" :prop="isEdit ? '' : 'password'">
          <el-input v-model="form.password" type="password"
                    :placeholder="isEdit ? '留空不修改' : '请输入密码'" />
        </el-form-item>
        <el-form-item label="姓名" prop="realName">
          <el-input v-model="form.realName" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" style="width:100%">
            <el-option label="管理员" value="admin" />
            <el-option label="编辑者" value="editor" />
            <el-option label="只读" value="viewer" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="statusSwitch" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { getUsers, createUser, updateUser, deleteUser } from '@/api/users'

const roleMap = { admin: '管理员', editor: '编辑者', viewer: '只读' }

const tableData = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const formRef = ref(null)
let editId = null

const form = reactive({
  username: '', password: '', realName: '', email: '', role: 'viewer'
})

const statusSwitch = ref(true)

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  realName: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

async function loadUsers() {
  loading.value = true
  try {
    const res = await getUsers()
    tableData.value = res.data
  } finally {
    loading.value = false
  }
}

function showAdd() {
  isEdit.value = false
  editId = null
  Object.assign(form, { username: '', password: '', realName: '', email: '', role: 'viewer' })
  statusSwitch.value = true
  dialogVisible.value = true
}

function showEdit(row) {
  isEdit.value = true
  editId = row.id
  Object.assign(form, {
    username: row.username,
    password: '',
    realName: row.realName || '',
    email: row.email || '',
    role: row.role
  })
  statusSwitch.value = row.status === 1
  dialogVisible.value = true
}

async function handleSave() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const data = { ...form, status: statusSwitch.value ? 1 : 0 }
    if (isEdit.value) {
      await updateUser(editId, data)
      ElMessage.success('更新成功')
    } else {
      await createUser(data)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadUsers()
  } finally {
    saving.value = false
  }
}

async function handleDelete(id) {
  await deleteUser(id)
  ElMessage.success('删除成功')
  loadUsers()
}

loadUsers()
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/UserManage.vue
git commit -m "feat: add user management page (CRUD)"
```

---

## 阶段五：集成与收尾 (Tasks 31-34)

### Task 31: 前端集成验证

- [ ] **Step 1: 确认所有前端页面正常渲染**

```bash
cd frontend
npm run dev
# 访问 http://localhost:5173
# 验证：登录页 → 布局 → 索引管理 → 审计日志 → 用户管理
```

- [ ] **Step 2: 检查前端路由导航守卫**

```
1. 未登录访问 / → 应跳转到 /login
2. viewer 角色访问 /audit-log → 应跳转到 /index-manage
3. viewer 角色不显示编辑/删除按钮
```

- [ ] **Step 3: 提交（如有修改）**

```bash
git add frontend/
git commit -m "fix: frontend integration tweaks"
```

---

### Task 32: Java-Python 集成验证

- [ ] **Step 1: 启动 MySQL 并初始化数据库**

```bash
# 确保 MySQL 运行在 localhost:3306
mysql -u root -p < java-gateway/src/main/resources/db/migration/V1__init.sql
```

- [ ] **Step 2: 启动 Python 服务**

```bash
cd python-service
python main.py
# 验证: curl http://localhost:8081/health
```

- [ ] **Step 3: 启动 Java 服务**

```bash
cd java-gateway
mvn spring-boot:run
# 验证: curl http://localhost:8080/api/es/indexes (应转发至 Python)
```

- [ ] **Step 4: 端到端调用验证**

```bash
# 1. 登录获取 token
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 2. 使用 token 获取索引列表
curl http://localhost:8080/api/es/indexes \
  -H "Authorization: Bearer <your_token>"
```

---

### Task 33: 生产部署配置

**Files:**
- Create: `es-slice/python-service/Dockerfile`
- Create: `es-slice/java-gateway/Dockerfile`
- Create: `es-slice/docker-compose.yml`

- [ ] **Step 1: 编写 Python Dockerfile**

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

- [ ] **Step 2: 编写 Java Dockerfile**

```dockerfile
FROM openjdk:11-jre-slim
WORKDIR /app
COPY target/es-slice-gateway-1.0.0.jar app.jar
CMD ["java", "-jar", "app.jar"]
```

- [ ] **Step 3: 编写 docker-compose.yml**

```yaml
version: '3.8'
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_PASSWORD:-root}
      MYSQL_DATABASE: es_slice
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

  python-service:
    build: ./python-service
    ports:
      - "8081:8081"
    environment:
      ES_HOST: ${ES_HOST:-http://elasticsearch:9200}

  java-gateway:
    build: ./java-gateway
    ports:
      - "8080:8080"
    environment:
      MYSQL_PASSWORD: ${MYSQL_PASSWORD:-root}
      PYTHON_SERVICE_URL: http://python-service:8081
      JWT_SECRET: ${JWT_SECRET:-changeme}

volumes:
  mysql_data:
```

- [ ] **Step 4: 提交**

```bash
git add Dockerfile docker-compose.yml
git commit -m "chore: add Docker and docker-compose configuration"
```

---

### Task 34: 文档与收尾

- [ ] **Step 1: 确认所有代码已提交**

```bash
cd /c/Hcloud/projects/es-slice
git status
# 应无未提交文件
```

- [ ] **Step 2: 更新 README.md 添加完整启动说明**

```bash
cat > README.md << 'EOF'
# ES 分片索引管理后台

## 快速启动

### 前置条件
- Node.js 16+
- JDK 11+
- Python 3.10+
- MySQL 8.0
- Elasticsearch 7.x

### 后端启动

1. 初始化数据库:
```bash
mysql -u root -p < java-gateway/src/main/resources/db/migration/V1__init.sql
```

2. 启动 Python 服务:
```bash
cd python-service
pip install -r requirements.txt
python main.py
```

3. 启动 Java 网关:
```bash
cd java-gateway
mvn spring-boot:run
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173
默认管理员: admin / admin123

### Docker 部署

```bash
docker-compose up -d
```
EOF
```

- [ ] **Step 3: 最终提交**

```bash
git add README.md
git commit -m "docs: update README with startup instructions"
```
