"""RAG 知識庫助手 — FastAPI 入口。

- GET  /            內建 demo 問答介面
- GET  /health      健康檢查
- GET  /api/status  知識庫現況（幾段、哪些來源）
- POST /api/upload  上傳文件、建索引（設了 ADMIN_TOKEN 時需帶 X-Admin-Token 標頭）
- DELETE /api/document  刪除某份文件（?source=檔名；同樣需管理密鑰）
- GET  /api/auth/check  驗證管理密碼
- POST /api/ask     提問 → 回答 + 來源 + 命中段落
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

load_dotenv()  # 讀取 .env 裡的 GEMINI_API_KEY（雲端用環境變數時這行不影響）

from app import llm
from app.ingest import SUPPORTED
from app.rag import RagEngine

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"
SAMPLES_DIR = BASE_DIR / "sample_docs"

# 管理密鑰：設了才需要密碼才能上傳/刪除（雲端務必設）；沒設則不限制（本機開發方便）
ADMIN_TOKEN = (os.getenv("ADMIN_TOKEN") or "").strip()

engine = RagEngine(DATA_DIR)


def _require_admin(token: str | None) -> None:
    """未設 ADMIN_TOKEN 時不限制；設了就要帶對的密鑰。"""
    if ADMIN_TOKEN and token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="需要管理密碼才能上傳或刪除文件。")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動時：知識庫為空就載入範例（同時把 embedding 模型預熱好）
    engine.seed_if_empty(SAMPLES_DIR)
    yield


app = FastAPI(title="RAG 知識庫助手", version="0.1.0", lifespan=lifespan)


class AskRequest(BaseModel):
    question: str
    k: int = 8
    provider: str | None = None  # 僅管理員可指定（gemini / claude），否則用預設


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


def _is_protected(source: str) -> bool:
    """預載的範例文件（sample_docs 裡帶的）不可刪。"""
    return (SAMPLES_DIR / Path(source).name).is_file()


@app.get("/api/status")
def status() -> dict:
    st = engine.status()
    st["protected"] = [s for s in st["sources"] if _is_protected(s)]
    st["auth_required"] = bool(ADMIN_TOKEN)
    # 供前端管理模式切換 LLM 用：可用供應商清單 + 友善名稱 + 預設
    st["providers"] = llm.available_providers()
    st["provider_labels"] = llm.PROVIDER_LABELS
    st["default_provider"] = llm.DEFAULT_PROVIDER
    return st


@app.get("/api/auth/check")
def auth_check(x_admin_token: str | None = Header(default=None)) -> dict:
    """驗證管理密碼是否正確（前端解鎖管理模式時用）。"""
    _require_admin(x_admin_token)
    return {"ok": True}


@app.post("/api/upload")
async def upload(
    file: UploadFile = File(...),
    x_admin_token: str | None = Header(default=None),
) -> dict:
    _require_admin(x_admin_token)
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


@app.delete("/api/document")
def delete_document(
    source: str, x_admin_token: str | None = Header(default=None)
) -> dict:
    _require_admin(x_admin_token)
    if _is_protected(source):
        raise HTTPException(
            status_code=403, detail=f"「{source}」是預載的範例文件，不可刪除。"
        )
    removed = engine.delete_document(source)
    if removed == 0:
        raise HTTPException(status_code=404, detail=f"找不到文件：{source}")
    return {"removed": removed, "source": source, **engine.status()}


@app.post("/api/ask")
def ask(
    req: AskRequest, x_admin_token: str | None = Header(default=None)
) -> dict:
    # 指定 provider 屬管理員權限；訪客一律用伺服器預設供應商
    if req.provider:
        _require_admin(x_admin_token)
        if req.provider not in llm.available_providers():
            raise HTTPException(
                status_code=400, detail=f"供應商不可用：{req.provider}"
            )
    return engine.ask(req.question, k=req.k, provider=req.provider)
