from fastapi import APIRouter, HTTPException
from services.es_client import search_docs

router = APIRouter(prefix="/es/indexes", tags=["search"])

@router.post("/{index}/search")
def search(index: str, body: dict):
    """搜索指定索引的文档，body 为完整的 ES DSL"""
    try:
        query = body.get("query", {"match_all": {}})
        size = body.get("size", 20)
        from_ = body.get("from", 0)
        sort = body.get("sort", [])

        dsl = {"query": query, "size": size, "from": from_, "sort": sort}
        result = search_docs(index, dsl, from_=from_, size=size)
        return {
            "code": 0,
            "data": {
                "total": result["total"],
                "list": result["hits"],
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
