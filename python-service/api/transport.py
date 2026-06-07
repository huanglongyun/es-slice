from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from services.es_client import bulk_update
from services.export_service import export_jsonl
from services.import_service import parse_excel_to_docs

router = APIRouter(prefix="/es/indexes", tags=["transport"])

@router.post("/{index}/export")
def export_docs(index: str, body: dict):
    """导出搜索结果为 JSONL 文件，body 为完整的 ES DSL"""
    try:
        query = body.get("query", {"match_all": {}})
        size = body.get("size", 20)
        from_ = body.get("from")
        sort = body.get("sort", [])
        dsl = {"query": query, "size": size, "from": from_, "sort": sort}
        # 有 from → 当前页导出，用普通查询；无 from → 全部/勾选，用 scroll
        use_scroll = from_ is None
        buffer = export_jsonl(index, dsl, use_scroll=use_scroll)
        filename = f"{index}_export.jsonl"
        return StreamingResponse(
            buffer,
            media_type="text/plain; charset=utf-8",
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
async def import_excel(
    file: UploadFile = File(...),
    indexes: str = Form(default=""),
    preview: str = Form(default="false")
):
    """
    上传 Excel 批量更新。indexes 为逗号分隔的索引列表。
    Excel 第一行是字段名，其中 _id 列用于匹配文档。
    preview=true 时仅解析并返回预览数据，不写入 ES。
    """
    try:
        contents = await file.read()
        docs = parse_excel_to_docs(contents)

        if preview.lower() == "true":
            missing_fields = []
            for i, doc in enumerate(docs):
                if "_id" not in doc:
                    missing_fields.append(i + 2)  # Excel 行号（第1行是表头）
            return {
                "code": 0,
                "data": {
                    "rows": docs,
                    "total": len(docs),
                    "has_id": "_id" in docs[0] if docs else False,
                    "missing_id_rows": missing_fields,
                }
            }

        target_indexes = [i.strip() for i in indexes.split(",") if i.strip()]
        if not target_indexes:
            raise HTTPException(status_code=400, detail="至少选择一个索引")
        if not docs:
            raise HTTPException(status_code=400, detail="Excel 中没有有效数据")
        if not docs[0].get("_id"):
            raise HTTPException(status_code=400, detail="Excel 第一行缺少 _id 列，无法匹配文档")

        import copy
        all_results = []
        total_success = 0
        for idx in target_indexes:
            result = bulk_update(idx, [copy.deepcopy(d) for d in docs])
            total_success += result["success"]
            all_results.append({"index": idx, **result})
        return {
            "code": 0,
            "data": {
                "total": len(docs) * len(target_indexes),
                "success": total_success,
                "results": all_results,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
