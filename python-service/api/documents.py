from fastapi import APIRouter, HTTPException
from services.es_client import get_doc, update_doc, delete_doc

router = APIRouter(prefix="/es/indexes", tags=["documents"])

@router.get("/{index}/doc/{doc_id}")
def get_document(index: str, doc_id: str):
    """获取单条文档详情"""
    try:
        doc = get_doc(index, doc_id)
        return {"code": 0, "data": doc}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{index}/doc/{doc_id}")
def update_document(index: str, doc_id: str, body: dict):
    """更新文档"""
    try:
        doc = update_doc(index, doc_id, body)
        return {"code": 0, "data": doc}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{index}/doc/{doc_id}")
def delete_document(index: str, doc_id: str):
    """删除文档"""
    try:
        delete_doc(index, doc_id)
        return {"code": 0, "message": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
