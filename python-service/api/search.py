from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.es_client import search_docs
from services.search_builder import parse_search_body

router = APIRouter(prefix="/es/indexes", tags=["search"])

class SearchRequest(BaseModel):
    conditions: list[dict] = []
    dsl: Optional[dict] = None
    page: int = 1
    pageSize: int = 20

@router.post("/{index}/search")
def search(index: str, req: SearchRequest):
    """搜索指定索引的文档"""
    try:
        dsl = parse_search_body(req.dict())
        from_ = (req.page - 1) * req.pageSize
        result = search_docs(index, dsl, from_=from_, size=req.pageSize)
        return {
            "code": 0,
            "data": {
                "total": result["total"],
                "list": result["hits"],
                "page": req.page,
                "pageSize": req.pageSize,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
