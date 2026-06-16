"""文件解析與切塊。

把上傳的 PDF / Word / 純文字抽成文字，再切成一段一段（chunk），
方便後續做 embedding 與檢索。
"""

from __future__ import annotations

import io
from dataclasses import dataclass

from docx import Document as DocxDocument
from pypdf import PdfReader

SUPPORTED = {".pdf", ".docx", ".txt", ".md"}


# ---------------------------------------------------------------- 解析

def extract_text(filename: str, data: bytes) -> str:
    """依副檔名把檔案內容抽成純文字。"""
    name = filename.lower()
    if name.endswith(".pdf"):
        return _from_pdf(data)
    if name.endswith(".docx"):
        return _from_docx(data)
    if name.endswith((".txt", ".md")):
        return data.decode("utf-8", errors="ignore")
    raise ValueError(f"不支援的檔案格式：{filename}（支援 {sorted(SUPPORTED)}）")


def _from_pdf(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages)


def _from_docx(data: bytes) -> str:
    doc = DocxDocument(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


# ---------------------------------------------------------------- 切塊

@dataclass
class Chunk:
    """一段文字 + 它來自哪份文件。"""

    text: str
    source: str  # 來源檔名
    index: int   # 該文件中的第幾段


def chunk_text(
    text: str,
    source: str,
    *,
    chunk_size: int = 320,
    overlap: int = 60,
) -> list[Chunk]:
    """把長文字切成有重疊的小段。

    重疊是為了避免把一句話從中間切斷後、語意在邊界遺失。
    以字元數切，對中英文都夠用。
    """
    text = _normalize(text)
    if not text:
        return []

    chunks: list[Chunk] = []
    start = 0
    idx = 0
    step = max(1, chunk_size - overlap)
    while start < len(text):
        piece = text[start : start + chunk_size].strip()
        if piece:
            chunks.append(Chunk(text=piece, source=source, index=idx))
            idx += 1
        start += step
    return chunks


def _normalize(text: str) -> str:
    """壓掉多餘空白與空行。"""
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)
