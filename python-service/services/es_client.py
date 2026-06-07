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
    """获取索引字段映射，返回字段名和类型的列表。
    text 类型字段本身支持搜索，不再重复暴露 .keyword 子字段"""
    es = get_es_client()
    mapping = es.indices.get_mapping(index=index)
    properties = mapping[index]["mappings"].get("properties", {})
    fields = []
    for name, prop in properties.items():
        field_type = prop.get("type", "object")
        if field_type != "object":
            fields.append({"name": name, "type": field_type})
    return fields

def search_docs(index: str, dsl: dict) -> dict:
    """执行 DSL 搜索，返回 ES 原生格式（和 elasticvue 一致）"""
    es = get_es_client()
    result = es.search(index=index, body=dsl)
    return dict(result)

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
    scroll_dsl = {k: v for k, v in dsl.items() if k != "from"}
    result = es.search(index=index, body=scroll_dsl, scroll="2m", size=batch_size)
    hits = [h["_source"] | {"_id": h["_id"]} for h in result["hits"]["hits"]]
    scroll_id = result.get("_scroll_id")
    try:
        while scroll_id:
            result = es.scroll(scroll_id=scroll_id, scroll="2m")
            scroll_id = result.get("_scroll_id")
            batch = [h["_source"] | {"_id": h["_id"]} for h in result["hits"]["hits"]]
            if not batch:
                break
            hits.extend(batch)
    finally:
        if scroll_id:
            es.clear_scroll(scroll_id=scroll_id)
    return hits

def bulk_update(index: str, docs: list[dict]) -> dict:
    """批量更新文档，按 _id 匹配。返回 {success, errors, total}。"""
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
                    "doc_as_upsert": False,  # 仅更新，不创建新文档
                }

    success, errors = bulk(es, actions(), raise_on_error=False, raise_on_exception=False)
    error_details = []
    if errors:
        for err in errors:
            err_action = err.get("update", {})
            error_details.append({
                "id": err_action.get("_id", ""),
                "error": str(err_action.get("error", err)),
            })
    return {"success": success, "errors": error_details, "total": len(docs)}
