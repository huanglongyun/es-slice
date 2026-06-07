import io
import openpyxl

# 常见的中文布尔值映射
BOOL_MAP = {
    "是": True, "否": False,
    "true": True, "false": False,
    "yes": True, "no": False,
    "1": True, "0": False,
    "真": True, "假": False,
    1: True, 0: False,
}

def _normalize_value(value):
    """将值转换为 ES 兼容的类型"""
    # 布尔值标准化
    if isinstance(value, str):
        lower = value.strip().lower()
        if lower in BOOL_MAP:
            return BOOL_MAP[lower]
        # 逗号分隔的字符串可能原来是数组
        # 保持原样，让 bulk update 时 ES 自行处理
    elif isinstance(value, (int, float)):
        if value in BOOL_MAP:
            return BOOL_MAP[value]
    return value

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
                doc[header] = _normalize_value(row[i])
        if doc:
            docs.append(doc)

    workbook.close()
    return docs
