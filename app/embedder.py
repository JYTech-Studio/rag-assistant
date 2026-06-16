"""文字 → 向量（embedding）。

用 fastembed（ONNX，輕量、本機跑、免費、不需額外金鑰）。
選多語模型，中英混合都能處理。模型只載入一次（單例）。
"""

from __future__ import annotations

import os

import numpy as np
from fastembed import TextEmbedding

# 中文小模型：0.09GB、512 維，中文檢索準、又省記憶體（Render 免費方案友善）。
# 內容若以英文為主，可改 multilingual 模型；要再省記憶體可改 embeddings API。
MODEL_NAME = os.getenv("EMBED_MODEL", "BAAI/bge-small-zh-v1.5")

_model: TextEmbedding | None = None


def _get_model() -> TextEmbedding:
    global _model
    if _model is None:
        _model = TextEmbedding(MODEL_NAME)
    return _model


def embed(texts: list[str]) -> np.ndarray:
    """把多段文字轉成「已正規化」的向量矩陣 (N, dim)。

    正規化後，cosine 相似度 == 向量內積，檢索時算起來最快。
    """
    if not texts:
        return np.empty((0, 0), dtype=np.float32)
    vecs = np.array(list(_get_model().embed(texts)), dtype=np.float32)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vecs / norms
