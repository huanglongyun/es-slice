from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from services.es_client import bulk_update
from services.export_service import export_jsonl
from services.import_service import parse_excel_to_docs

router = APIRouter(prefix="/es/indexes", tags=["transport"])

class ExportRequest(BaseModel):
    conditions: list[dict] = []
    dsl: Optional[dict] = None

@router.post("/{index}/export")
def export_docs(index: str, req: ExportRequest):
    """导出搜索结果为 JSONL 文件"""
    from services.search_builder import parse_search_body
    try:
        dsl = parse_search_body(req.dict())
        buffer = export_jsonl(index, dsl)
        filename = f"{index}_export.jsonl"
        return StreamingResponse(
            buffer,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ImportResult(BaseModel):
    indexes: list[str]
    total: int = 0
    success: int = 0
    errors: list[str] = []

@router.post("/import")
async def import_excel(file: UploadFile = File(...), indexes: str = ""):
    """
    上传 Excel 批量更新。indexes 为逗号分隔的索引列表。
    Excel 第一行是字段名，其中 _id 列用于匹配文档。
    """
    try:
        target_indexes = [i.strip() for i in indexes.split(",") if i.strip()]
        if not target_indexes:
            raise HTTPException(status_code=400, detail="至少选择一个索引")
        contents = await file.read()
        docs = parse_excel_to_docs(contents)
        total_success = 0
        all_errors = []
        for idx in target_indexes:
            success = bulk_update(idx, [d.copy() for d in docs])
            total_success += success
        return {
            "code": 0,
            "data": {
                "total": len(docs) * len(target_indexes),
                "success": total_success,
                "errors": all_errors,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
