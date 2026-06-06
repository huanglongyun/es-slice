from fastapi import APIRouter, HTTPException
from services.es_client import get_index_list, get_index_fields

router = APIRouter(prefix="/es/indexes", tags=["indexes"])

@router.get("")
def list_indexes():
    """返回所有索引名称列表"""
    try:
        indexes = get_index_list()
        return {"code": 0, "data": indexes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{index}/fields")
def get_fields(index: str):
    """返回指定索引的字段列表"""
    try:
        fields = get_index_fields(index)
        return {"code": 0, "data": fields}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
