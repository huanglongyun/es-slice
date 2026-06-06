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
