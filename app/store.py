"""向量庫。

用 numpy 做 cosine 相似度檢索（向量已正規化 → 內積即 cosine）。
對 demo 規模（數百～數千段）足夠快；要再大才需要 FAISS。
支援存檔／讀檔，讓預載的知識庫能跨重啟保留。
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from app.ingest import Chunk


class VectorStore:
    def __init__(self) -> None:
        self.chunks: list[Chunk] = []
        self.matrix: np.ndarray | None = None  # (N, dim)，已正規化

    @property
    def size(self) -> int:
        return len(self.chunks)

    def sources(self) -> list[str]:
        """目前知識庫裡有哪些來源檔（去重、保留順序）。"""
        seen: dict[str, None] = {}
        for c in self.chunks:
            seen.setdefault(c.source, None)
        return list(seen)

    def add(self, chunks: list[Chunk], embeddings: np.ndarray) -> None:
        if not chunks:
            return
        self.chunks.extend(chunks)
        self.matrix = (
            embeddings if self.matrix is None else np.vstack([self.matrix, embeddings])
        )

    def search(self, query_vec: np.ndarray, k: int = 4) -> list[tuple[Chunk, float]]:
        """回傳最相關的前 k 段，附 cosine 分數。"""
        if self.matrix is None or not self.chunks:
            return []
        scores = self.matrix @ query_vec
        top = np.argsort(-scores)[:k]
        return [(self.chunks[i], float(scores[i])) for i in top]

    def clear(self) -> None:
        self.chunks = []
        self.matrix = None

    # ----------------------------------------------------------- 持久化

    def save(self, dir_path: str | Path) -> None:
        d = Path(dir_path)
        d.mkdir(parents=True, exist_ok=True)
        (d / "chunks.json").write_text(
            json.dumps([asdict(c) for c in self.chunks], ensure_ascii=False),
            encoding="utf-8",
        )
        if self.matrix is not None:
            np.save(d / "matrix.npy", self.matrix)

    def load(self, dir_path: str | Path) -> bool:
        """讀回先前存的知識庫；沒有就回 False。"""
        d = Path(dir_path)
        cj, mn = d / "chunks.json", d / "matrix.npy"
        if not cj.exists() or not mn.exists():
            return False
        raw = json.loads(cj.read_text(encoding="utf-8"))
        self.chunks = [Chunk(**item) for item in raw]
        self.matrix = np.load(mn)
        return True
