"""RAG 總控：把解析、切塊、embedding、檢索、Claude 作答串起來。

對外只暴露兩個動作：
- add_document(): 餵一份文件進知識庫
- ask():          問一個問題，回答案 + 來源 + 命中段落
"""

from __future__ import annotations

from pathlib import Path

from app import llm
from app.embedder import embed
from app.ingest import SUPPORTED, chunk_text, extract_text
from app.store import VectorStore


class RagEngine:
    def __init__(self, data_dir: str | Path) -> None:
        self.data_dir = Path(data_dir)
        self.store = VectorStore()
        self.store.load(self.data_dir)  # 有預載知識庫就載回來

    # ---------------------------------------------------------- 寫入

    def add_document(self, filename: str, data: bytes) -> int:
        """解析 + 切塊 + embedding + 入庫，回傳新增了幾段。"""
        text = extract_text(filename, data)
        chunks = chunk_text(text, filename)
        if chunks:
            self.store.add(chunks, embed([c.text for c in chunks]))
            self.store.save(self.data_dir)
        return len(chunks)

    def seed_if_empty(self, samples_dir: str | Path) -> int:
        """知識庫為空時，自動載入範例文件夾裡的檔案（部署後一打開就有內容）。"""
        samples = Path(samples_dir)
        if self.store.size > 0 or not samples.exists():
            return 0
        loaded = 0
        for f in sorted(samples.iterdir()):
            if f.suffix.lower() in SUPPORTED:
                self.add_document(f.name, f.read_bytes())
                loaded += 1
        return loaded

    def delete_document(self, source: str) -> int:
        """從知識庫移除某份文件的所有段落，回傳移除幾段；變更即存回磁碟。"""
        removed = self.store.remove_source(source)
        if removed:
            self.store.save(self.data_dir)
        return removed

    # ---------------------------------------------------------- 查詢

    def ask(self, question: str, k: int = 8, provider: str | None = None) -> dict:
        question = (question or "").strip()
        if not question:
            return {"answer": "請輸入問題。", "sources": [], "matches": []}

        query_vec = embed([question])[0]
        hits = self.store.search(query_vec, k=k)
        answer_text = llm.answer(question, hits, provider=provider)

        sources = list(dict.fromkeys(chunk.source for chunk, _ in hits))
        matches = [
            {
                "source": chunk.source,
                "score": round(score, 3),
                "preview": chunk.text[:80],
            }
            for chunk, score in hits
        ]
        return {"answer": answer_text, "sources": sources, "matches": matches}

    # ---------------------------------------------------------- 狀態

    def status(self) -> dict:
        return {"chunks": self.store.size, "sources": self.store.sources()}
