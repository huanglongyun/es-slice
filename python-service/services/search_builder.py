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
