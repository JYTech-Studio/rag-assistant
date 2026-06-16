# RAG 知識庫問答助手

用 **Python + FastAPI + Gemini** 打造的檢索增強生成（RAG）微服務：上傳文件 → 用自然語言提問 → AI 依據文件內容回答，並標出引用來源。

> 內建 demo 介面可直接操作，也提供 JSON API 供其他系統（例如 Next.js 前台）呼叫。

## 功能

- 📄 上傳 **PDF / Word / txt / md**，自動解析、切塊、建立向量索引
- 💬 自然語言問答，答案**只根據上傳的文件**，找不到就明說、不亂掰
- 📎 每則回答標出**引用來源**，並可展開實際檢索到的段落與相似度分數
- 🚀 開箱即用：啟動時自動載入範例知識庫，一打開就能問

## 運作原理（RAG）

```
上傳文件 → 解析文字 → 切塊 → embedding 轉向量 → 存入向量庫
提問 → 問題轉向量 → 向量庫找最相關的段落 → 連同問題交給 LLM（Gemini）→ 生成答案 + 來源
```

「檢索增強生成」的重點：讓 LLM **根據你的私有資料**回答，而不是只靠它自己的訓練知識，藉此降低幻覺、並能引用來源。

## 技術架構

| 層面 | 技術 |
|------|------|
| Web 框架 | FastAPI（API + 靜態 demo 介面） |
| 文件解析 | pypdf、python-docx |
| Embedding | fastembed（ONNX，本機推論，模型 `bge-small-zh`，中文檢索佳又輕量） |
| 向量檢索 | numpy cosine 相似度（demo 規模足夠；可換 FAISS 擴充） |
| LLM | Google Gemini（`google-genai` SDK，預設 `gemini-2.5-flash-lite`，免費方案） |
| 部署 | Docker（多階段相依預載）+ Render |

## 專案結構

```
app/
  main.py      FastAPI 入口與路由
  ingest.py    文件解析 + 切塊
  embedder.py  文字 → 向量（fastembed）
  store.py     向量庫（cosine 檢索 + 存讀）
  rag.py       總控：串起檢索與 Claude 作答
  llm.py       呼叫 LLM（Gemini）
static/index.html  內建 demo 問答介面
sample_docs/       預載的範例知識庫
```

## 本地執行

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # 填入 GEMINI_API_KEY
uvicorn app.main:app --reload
# 開 http://127.0.0.1:8000
```

申請金鑰（免費、免綁信用卡）：<https://aistudio.google.com/apikey>。
未設金鑰時仍可上傳與檢索，只是無法生成 AI 答案。

## API

| 方法 | 路徑 | 說明 |
|------|------|------|
| `GET`  | `/api/status` | 知識庫現況（段數、來源） |
| `POST` | `/api/upload` | 上傳文件（multipart `file`），建索引 |
| `POST` | `/api/ask`    | `{"question": "..."}` → `{answer, sources, matches}` |

其他系統（如 Next.js）可直接 `fetch` 這些端點整合，不需共用程式碼。

## 部署（Render）

1. 推上 GitHub。
2. Render → New Web Service → 連這個 repo，選 **Docker**。
3. 環境變數設 `GEMINI_API_KEY`（可另設 `GEMINI_MODEL`，預設 `gemini-2.5-flash-lite`）。
4. 完成。Dockerfile 已在 build 時預載 embedding 模型，冷啟動較快。

> 免費方案閒置會休眠，首次載入需數十秒喚醒。

## 授權

範例文件為虛構測試資料。地圖／模型等第三方資源依其各自授權。
