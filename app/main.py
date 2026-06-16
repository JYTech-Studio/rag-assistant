"""RAG 知識庫助手 — FastAPI 入口。

- GET  /            內建 demo 問答介面
- GET  /health      健康檢查
- GET  /api/status  知識庫現況（幾段、哪些來源）
- POST /api/upload  上傳文件、建索引
- POST /api/ask     提問 → 回答 + 來源 + 命中段落
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

load_dotenv()  # 讀取 .env 裡的 GEMINI_API_KEY（雲端用環境變數時這行不影響）

from app.ingest import SUPPORTED
from app.rag import RagEngine

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"
SAMPLES_DIR = BASE_DIR / "sample_docs"

engine = RagEngine(DATA_DIR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動時：知識庫為空就載入範例（同時把 embedding 模型預熱好）
    engine.seed_if_empty(SAMPLES_DIR)
    yield


app = FastAPI(title="RAG 知識庫助手", version="0.1.0", lifespan=lifespan)


class AskRequest(BaseModel):
    question: str
    k: int = 4


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/status")
def status() -> dict:
    return engine.status()


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)) -> dict:
    filename = file.filename or ""
    if not filename.lower().endswith(tuple(SUPPORTED)):
        raise HTTPException(
            status_code=400,
            detail=f"不支援的格式。支援：{sorted(SUPPORTED)}",
        )
    data = await file.read()
    try:
        added = engine.add_document(filename, data)
    except Exception as exc:  # 解析失敗等
        raise HTTPException(status_code=400, detail=f"處理失敗：{exc}") from exc
    return {"filename": filename, "chunks": added, **engine.status()}


@app.post("/api/ask")
def ask(req: AskRequest) -> dict:
    return engine.ask(req.question, k=req.k)
