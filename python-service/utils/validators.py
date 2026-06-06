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
