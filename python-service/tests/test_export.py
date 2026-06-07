"""导出功能单元测试"""
import json
import pytest
from unittest.mock import patch
from services.export_service import export_jsonl


class TestExportJsonl:
    def test_scroll_export_returns_bytesio(self):
        """scroll 导出返回 BytesIO"""
        fake_docs = [{"_id": "1", "title": "hello"}, {"_id": "2", "title": "world"}]
        with patch("services.export_service.scroll_search", return_value=fake_docs):
            buf = export_jsonl("test", {"query": {"match_all": {}}}, use_scroll=True)
            content = buf.read().decode("utf-8")
            lines = content.strip().split("\n")
            assert len(lines) == 2

    def test_normal_export_with_from(self):
        """普通导出（当前页）"""
        fake_result = {"hits": {"hits": [
            {"_id": "1", "_source": {"title": "hello"}},
            {"_id": "2", "_source": {"title": "world"}},
        ]}}
        with patch("services.export_service.search_docs", return_value=fake_result):
            buf = export_jsonl("test", {"query": {}, "from": 0, "size": 20}, use_scroll=False)
            content = buf.read().decode("utf-8")
            assert "hello" in content

    def test_utf8_bom(self):
        """导出文件包含 UTF-8 BOM"""
        with patch("services.export_service.scroll_search", return_value=[]):
            buf = export_jsonl("test", {"query": {}}, use_scroll=True)
            content = buf.read()
            assert content[:3] == b'\xef\xbb\xbf'

    def test_jsonl_lines_valid_json(self):
        """每行都是合法 JSON"""
        fake_docs = [{"_id": "1", "name": "测试", "tags": ["a", "b"]}]
        with patch("services.export_service.scroll_search", return_value=fake_docs):
            buf = export_jsonl("test", {"query": {}}, use_scroll=True)
            content = buf.read().decode("utf-8-sig")
            for line in content.strip().split("\n"):
                obj = json.loads(line)
                assert isinstance(obj, dict)
