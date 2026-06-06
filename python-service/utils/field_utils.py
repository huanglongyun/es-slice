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
