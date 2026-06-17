# RAG 知識庫問答助手

用 **Python + FastAPI + Gemini** 打造的檢索增強生成（RAG）微服務：上傳文件 → 用自然語言提問 → AI 依據文件內容回答，並標出引用來源。

> 內建 demo 介面可直接操作，也提供 JSON API 供其他系統（例如 Next.js 前台）呼叫。

## 功能

- 📄 上傳 **PDF / Word / txt / md**，自動解析、切塊、建立向量索引
- 💬 自然語言問答，答案**只根據上傳的文件**，找不到就明說、不亂掰
- 📎 每則回答標出**引用來源**，並可展開實際檢索到的段落與相似度分數
- 🚀 開箱即用：啟動時自動載入範例知識庫，一打開就能問
- 🗑️ 可刪除單一文件，**即時生效不需重啟**；預載的範例文件受保護不可刪（顯示 🔒）
- 🔑 **管理密碼保護**：設了 `ADMIN_TOKEN` 後，上傳／刪除需密碼，問答仍對所有人開放（適合公開 demo）
- 🧠 **可切換 LLM 供應商**：支援 **Gemini** 與 **Claude**；兩家金鑰都設好時，管理員可在前端問答區即時切換比較（訪客一律用伺服器預設，避免成本暴露）

## 運作原理（RAG）

```
上傳文件 → 解析文字 → 切塊 → embedding 轉向量 → 存入向量庫
提問 → 問題轉向量 → 向量庫找最相關的段落 → 連同問題交給 LLM（Gemini / Claude）→ 生成答案 + 來源
```

「檢索增強生成」的重點：讓 LLM **根據你的私有資料**回答，而不是只靠它自己的訓練知識，藉此降低幻覺、並能引用來源。

## 技術架構

| 層面 | 技術 |
|------|------|
| Web 框架 | FastAPI（API + 靜態 demo 介面） |
| 文件解析 | pypdf、python-docx |
| Embedding | fastembed（ONNX，本機推論，模型 `bge-small-zh`，中文檢索佳又輕量） |
| 向量檢索 | numpy cosine 相似度（demo 規模足夠；可換 FAISS 擴充） |
| LLM | Google Gemini（預設，免費）或 Anthropic Claude（`claude-haiku-4-5`）；用 `LLM_PROVIDER` 切換，前端管理員可即時改 |
| 部署 | Docker（多階段相依預載）+ Render |

## 專案結構

```
app/
  main.py      FastAPI 入口與路由
  ingest.py    文件解析 + 切塊
  embedder.py  文字 → 向量（fastembed）
  store.py     向量庫（cosine 檢索 + 存讀）
  rag.py       總控：串起檢索與 LLM 作答
  llm.py       呼叫 LLM（Gemini / Claude，唯一與供應商耦合處）
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

**環境變數**（見 `.env.example`）：

| 變數 | 說明 |
|------|------|
| `LLM_PROVIDER` | 預設供應商：`gemini`（預設）或 `claude` |
| `GEMINI_API_KEY` | Gemini 金鑰；未設則無法生成 AI 答案 |
| `GEMINI_MODEL`   | Gemini 模型，預設 `gemini-2.5-flash-lite` |
| `ANTHROPIC_API_KEY` | Claude 金鑰（選用）；申請：<https://console.anthropic.com/> |
| `CLAUDE_MODEL`   | Claude 模型，預設 `claude-haiku-4-5-20251001` |
| `ADMIN_TOKEN`    | 管理密碼。**設了**才需密碼才能上傳／刪除；**留空**則不限制（本機開發方便）。公開部署務必設定 |

> **切換 LLM**：`LLM_PROVIDER` 決定全站預設用哪家。若 `GEMINI_API_KEY` 與 `ANTHROPIC_API_KEY` 都設好，解鎖管理模式後，前端問答區右上會出現下拉，可即時切換 Gemini / Claude 比較答案。訪客一律用預設供應商，不會動到你的付費額度。

### 用 `run.sh` 快速重啟

啟動後若改了知識庫文件，需重啟 server 才會生效（執行中的 process 不會自動重載資料）。`run.sh` 會自動停掉舊 process 再啟動（port `8099`）：

```bash
./run.sh            # 一般重啟（停舊的 → 啟動）
./run.sh --fresh    # 順便清掉 index（data/），換過 sample_docs 文件後用這個
./run.sh --reload   # 開發模式，改 app/ 程式碼自動重啟
./run.sh --fresh --reload   # 可併用
```

**停止 server**：前台執行時在該視窗按 `Ctrl + C`；若是背景執行（如 `./run.sh &`），用以下指令關閉：

```bash
pkill -f "uvicorn app.main"
```

## API

| 方法 | 路徑 | 說明 |
|------|------|------|
| `GET`    | `/api/status`     | 知識庫現況（段數、來源、受保護文件、是否需密碼、可用 LLM 供應商） |
| `POST`   | `/api/upload`     | 上傳文件（multipart `file`），建索引 🔑 |
| `DELETE` | `/api/document`   | 刪除某份文件（`?source=檔名`）🔑 |
| `GET`    | `/api/auth/check` | 驗證管理密碼 |
| `POST`   | `/api/ask`        | `{"question": "..."}` → `{answer, sources, matches}`；可選 `"provider": "claude"` 指定 LLM（需管理密鑰）🔑 |

🔑 標記的端點在設了 `ADMIN_TOKEN` 時，需帶 `X-Admin-Token: <密碼>` 標頭。

其他系統（如 Next.js）可直接 `fetch` 這些端點整合，不需共用程式碼。

## 部署（Render）

1. 推上 GitHub。
2. Render → New Web Service → 連這個 repo，選 **Docker**。
3. 環境變數設 `GEMINI_API_KEY`（可另設 `GEMINI_MODEL`，預設 `gemini-2.5-flash-lite`）。
   - 想在線上也用 Claude：另設 `ANTHROPIC_API_KEY`（兩家都設好，管理員即可在前端切換）。只想用 Gemini 則略過即可。
4. **設 `ADMIN_TOKEN`**＝自訂密碼，否則公開站台任何人都能上傳／刪除文件。
5. 完成。Dockerfile 已在 build 時預載 embedding 模型，冷啟動較快。

> 免費方案閒置會休眠，首次載入需數十秒喚醒。
> 本機 `.env` 不會上傳到雲端，Render 的環境變數需在 Dashboard → Environment 另外設定。

## 授權

範例文件為虛構測試資料。地圖／模型等第三方資源依其各自授權。
