from fastapi import FastAPI
import uvicorn
from config import SERVICE_PORT

app = FastAPI(title="ES Slice Service", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
