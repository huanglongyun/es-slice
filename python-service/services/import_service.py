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
