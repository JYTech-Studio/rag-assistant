"""呼叫 LLM，根據檢索到的內容作答。

支援兩家供應商，用環境變數 LLM_PROVIDER 切換（預設 gemini）：

  LLM_PROVIDER=gemini   # Google Gemini，免費方案不需綁卡
      GEMINI_API_KEY    # https://aistudio.google.com/apikey
      GEMINI_MODEL      # 預設 gemini-2.5-flash-lite

  LLM_PROVIDER=claude   # Anthropic Claude，需綁卡儲值
      ANTHROPIC_API_KEY # https://console.anthropic.com/
      CLAUDE_MODEL      # 預設 claude-haiku-4-5-20251001（最便宜）

（這支是唯一跟 LLM 供應商耦合的檔案；要換供應商只改這裡。）
"""

from __future__ import annotations

import os
import time

from app.ingest import Chunk

DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
MAX_OUTPUT_TOKENS = 1024

# 各供應商的友善名稱（給前端下拉用）
PROVIDER_LABELS = {"gemini": "Gemini", "claude": "Claude"}


def available_providers() -> list[str]:
    """回傳「有設定金鑰、目前可用」的供應商清單；預設那家排最前面。"""
    avail = []
    if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        avail.append("gemini")
    if os.getenv("ANTHROPIC_API_KEY"):
        avail.append("claude")
    avail.sort(key=lambda p: p != DEFAULT_PROVIDER)  # 預設那家排第一
    return avail

SYSTEM_PROMPT = """你是WJY（JYTech-Studio）的「AI 分身」，代表他回答訪客（通常是面試官或潛在客戶）的提問。
你只能根據提供的「參考資料」（包含他的技術履歷與專案資料）回答。

規則：
- 只依據參考資料作答，不要使用參考資料以外的知識，更不要編造他的經歷、技能或數字。
- 若參考資料中找不到答案，誠實地說「這部分我的資料裡沒有提到，建議直接問本人」，不要硬湊。
- 用繁體中文，語氣自然、誠懇、精簡。提到WJY時用第三人稱「他」。
- 不要在答案裡重複「參考資料」這幾個字，自然作答即可。"""

_gemini_client = None
_claude_client = None


def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        from google import genai

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("未設定 GEMINI_API_KEY")
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client


def _get_claude_client():
    global _claude_client
    if _claude_client is None:
        import anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("未設定 ANTHROPIC_API_KEY")
        _claude_client = anthropic.Anthropic(api_key=api_key)
    return _claude_client


def build_user_prompt(question: str, contexts: list[tuple[Chunk, float]]) -> str:
    """把檢索到的段落組成 prompt。"""
    blocks = [
        f"[資料 {i}｜來源：{chunk.source}]\n{chunk.text}"
        for i, (chunk, _score) in enumerate(contexts, 1)
    ]
    joined = "\n\n".join(blocks)
    return f"參考資料：\n{joined}\n\n問題：{question}"


def _answer_gemini(prompt: str) -> str:
    from google.genai import types

    resp = _get_gemini_client().models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=MAX_OUTPUT_TOKENS,
        ),
    )
    return (resp.text or "").strip()


def _answer_claude(prompt: str) -> str:
    resp = _get_claude_client().messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_OUTPUT_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(
        block.text for block in resp.content if block.type == "text"
    ).strip()


def _reset_client() -> None:
    """連線壞掉就丟掉重建（如 Bad file descriptor）。"""
    global _gemini_client, _claude_client
    _gemini_client = None
    _claude_client = None


def answer(
    question: str,
    contexts: list[tuple[Chunk, float]],
    provider: str | None = None,
) -> str:
    """根據檢索內容產生答案文字。

    provider 可單次覆寫供應商（僅管理員會傳）；None 則用 DEFAULT_PROVIDER。
    """
    if not contexts:
        return "目前知識庫是空的，請先上傳文件再提問。"

    resolved = (provider or DEFAULT_PROVIDER).lower()
    prompt = build_user_prompt(question, contexts)
    generate = _answer_claude if resolved == "claude" else _answer_gemini

    last_exc: Exception | None = None
    for attempt in range(3):  # 冷啟動 socket 未就緒、503 等暫時性錯誤 → 自動重試
        try:
            return generate(prompt)
        except Exception as exc:
            last_exc = exc
            _reset_client()
            if attempt < 2:
                time.sleep(0.8 * (attempt + 1))

    # 三次都失敗 → 優雅降級，下方仍可看到檢索段落
    key_hint = "ANTHROPIC_API_KEY" if resolved == "claude" else "GEMINI_API_KEY"
    return (
        "⚠️ 暫時無法生成 AI 答案："
        f"{last_exc}\n（請確認已設定 {key_hint}；下方仍可看到檢索到的相關段落。）"
    )
