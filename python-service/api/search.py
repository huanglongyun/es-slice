from fastapi import APIRouter, HTTPException
from services.es_client import search_docs

router = APIRouter(prefix="/es/indexes", tags=["search"])

@router.post("/{index}/search")
def search(index: str, body: dict):
    """搜索接口
    入参: { "query":{...}, "size":20, "from":0, "sort":[] }
    这里 query/size/from/sort 就是 ES 原生的 DSL 语法，直接透传给 ES，不做翻译
    """
    try:
        dsl = {
            "query": body.get("query", {"match_all": {}}),
            "size": body.get("size", 20),
            "from": body.get("from", 0),
            "sort": body.get("sort", []),
        }
        result = search_docs(index, dsl)
        return {"code": 0, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
