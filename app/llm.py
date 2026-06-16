"""呼叫 LLM，根據檢索到的內容作答。

使用 Google Gemini（免費方案不需綁卡）。
金鑰請至 Google AI Studio 申請：https://aistudio.google.com/apikey
放進環境變數 GEMINI_API_KEY。

（這支是唯一跟 LLM 供應商耦合的檔案；想換回 Claude 或其他供應商只改這裡。）
"""

from __future__ import annotations

import os
import time

from google import genai
from google.genai import types

from app.ingest import Chunk

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

SYSTEM_PROMPT = """你是一個知識庫問答助手。你只能根據使用者提供的「參考資料」回答問題。

規則：
- 只依據參考資料作答，不要使用參考資料以外的知識，也不要憑空編造。
- 若參考資料中找不到答案，直接說「根據目前的資料，我找不到相關內容」，不要硬湊。
- 用繁體中文、條理清楚但精簡地回答。
- 不要在答案裡重複「參考資料」這幾個字，自然作答即可。"""

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("未設定 GEMINI_API_KEY")
        _client = genai.Client(api_key=api_key)
    return _client


def build_user_prompt(question: str, contexts: list[tuple[Chunk, float]]) -> str:
    """把檢索到的段落組成 prompt。"""
    blocks = [
        f"[資料 {i}｜來源：{chunk.source}]\n{chunk.text}"
        for i, (chunk, _score) in enumerate(contexts, 1)
    ]
    joined = "\n\n".join(blocks)
    return f"參考資料：\n{joined}\n\n問題：{question}"


def answer(question: str, contexts: list[tuple[Chunk, float]]) -> str:
    """根據檢索內容產生答案文字。"""
    if not contexts:
        return "目前知識庫是空的，請先上傳文件再提問。"

    prompt = build_user_prompt(question, contexts)
    last_exc: Exception | None = None
    for attempt in range(3):  # 冷啟動 socket 未就緒、503 等暫時性錯誤 → 自動重試
        try:
            resp = _get_client().models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    max_output_tokens=1024,
                ),
            )
            return (resp.text or "").strip()
        except Exception as exc:
            last_exc = exc
            global _client
            _client = None  # 連線壞掉就丟掉重建（如 Bad file descriptor）
            if attempt < 2:
                time.sleep(0.8 * (attempt + 1))

    # 三次都失敗 → 優雅降級，下方仍可看到檢索段落
    return (
        "⚠️ 暫時無法生成 AI 答案："
        f"{last_exc}\n（請確認已設定 GEMINI_API_KEY；下方仍可看到檢索到的相關段落。）"
    )
