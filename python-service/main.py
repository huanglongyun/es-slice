from fastapi import FastAPI
import uvicorn
from config import SERVICE_PORT
from api.indexes import router as indexes_router
from api.search import router as search_router
from api.documents import router as documents_router

app = FastAPI(title="ES Slice Service", version="1.0.0")
app.include_router(indexes_router)
app.include_router(search_router)
app.include_router(documents_router)

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
