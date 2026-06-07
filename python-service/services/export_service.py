import json
import io
from services.es_client import scroll_search, search_docs

def export_jsonl(index: str, dsl: dict, use_scroll: bool = True) -> io.BytesIO:
    """执行搜索并返回 JSONL 格式的字节流
    use_scroll=True: 全量导出（scroll API）
    use_scroll=False: 当前页导出（普通查询，保留 from）
    """
    if use_scroll:
        docs = scroll_search(index, dsl)
    else:
        result = search_docs(index, dsl)
        docs = result["hits"]

    buffer = io.BytesIO()
    buffer.write(b'\xef\xbb\xbf')  # UTF-8 BOM for Windows compatibility
    for doc in docs:
        line = json.dumps(doc, ensure_ascii=False) + "\n"
        buffer.write(line.encode("utf-8"))
    buffer.seek(0)
    return buffer
