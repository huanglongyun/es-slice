"""搜索接口单元测试"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

fake_es_response = {
    "took": 5,
    "timed_out": False,
    "_shards": {"total": 1, "successful": 1, "skipped": 0, "failed": 0},
    "hits": {
        "total": {"value": 2, "relation": "eq"},
        "max_score": 1.0,
        "hits": [
            {"_index": "test", "_id": "1", "_score": 1.0, "_source": {"title": "hello", "rating": 5}},
            {"_index": "test", "_id": "2", "_score": 0.8, "_source": {"title": "world", "rating": 3}},
        ]
    }
}

class TestSearch:
    def test_search_returns_raw_es_format(self):
        """搜索返回 ES 原生格式"""
        with patch("api.search.search_docs") as mock_search:
            mock_search.return_value = fake_es_response
            resp = client.post("/es/indexes/test/search", json={"query": {"match_all": {}}})
            assert resp.status_code == 200
            data = resp.json()
            assert data["code"] == 0
            assert data["data"]["hits"]["total"]["value"] == 2
            assert len(data["data"]["hits"]["hits"]) == 2

    def test_search_default_query(self):
        """不传 query 时默认 match_all"""
        with patch("api.search.search_docs") as mock_search:
            mock_search.return_value = fake_es_response
            resp = client.post("/es/indexes/test/search", json={})
            assert resp.status_code == 200

    def test_search_with_pagination(self):
        """支持 from/size"""
        with patch("api.search.search_docs") as mock_search:
            mock_search.return_value = fake_es_response
            resp = client.post("/es/indexes/test/search",
                               json={"query": {}, "size": 50, "from": 100})
            assert resp.status_code == 200
            # 验证传入的 dsl 包含正确的 from/size
            called_dsl = mock_search.call_args[0][1]
            assert called_dsl["from"] == 100
            assert called_dsl["size"] == 50
