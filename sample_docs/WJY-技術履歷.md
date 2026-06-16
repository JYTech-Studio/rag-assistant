# WJY — 軟體工程師 技術履歷

## 關於我

我是 WJY，24 歲、役畢，淡江大學歷史學系畢業——**非資工本科，靠自學轉職**進入軟體開發。
目前以**接案工程師 / 全端工程師**身分在職，已具備「一人從需求訪談、系統設計、前後端開發、部署到維運」的完整實戰經驗。

- 期望職務：**AI 工程師 / 後端工程師 / 全端工程師**
- 工作型態：**只能遠端工作（Remote）**；可全職或兼職
- 希望待遇：月薪 50,000 元以上
- 所在地：新北市林口區
- Email：wjycompany@gmail.com
- 作品集網站：portfolio-sage-six-44.vercel.app
- GitHub：github.com/JYTech-Studio（工作室名稱 JYTech-Studio）

## 技術棧

**前端**
- React、Next.js（App Router）、TypeScript
- RWD 響應式網頁、獨立切版與 API 串接
- 具備將舊系統（Express + 原生 HTML）重構遷移至 Next.js 的經驗

**後端**
- Node.js / Express：設計 RESTful API、商業邏輯、第三方服務串接（Email 通知、雲端儲存）
- PHP / Laravel：Eloquent ORM、Blade、Migration、route-model binding；以 DB transaction + lockForUpdate 處理點數／金流的並發一致性；PHPUnit 撰寫測試
- Python / FastAPI：打造 AI / RAG 微服務

**資料庫**
- PostgreSQL（Supabase）：資料表設計、索引與查詢優化、RLS 權限控管

**AI / LLM**
- RAG（檢索增強生成）：文件解析 → 切塊 → embedding → 向量檢索 → LLM 作答並標來源
- LLM 串接：Google Gemini、Claude（Anthropic）
- 向量檢索：fastembed（ONNX 本機推論，中文模型 bge-small-zh）、numpy cosine 相似度
- AI 輔助開發：熟練以 Claude Code、Codex 輔助撰寫、除錯、重構與技術文件，並能設計 prompt、用 CLAUDE.md 管理專案上下文

**DevOps / 工程實踐**
- Docker（多階段建置）、Render、Vercel 雲端部署
- GitHub Actions CI/CD 自動化排程與部署
- 資安：CORS 白名單、API 流量限制（Rate Limiting）、RLS、移除日誌個資（PII）
- 撰寫 README 與技術文件，以版本化方式記錄系統遷移（migration）歷程

## 工作經驗

### 接案工程師 / 全端工程師（電腦軟體服務業，2026/2 ~ 仍在職）

獨立承接**旅行社 ERP 系統**開發案，一人完成需求訪談、系統設計、開發、上線到維運的完整流程，協助客戶將原本的紙本與 Excel 作業全面數位化，大幅降低人工作業與資料出錯率。

- **系統架構**：後端以 Node.js / Express 建置 RESTful API，資料庫與檔案儲存採用 Supabase（PostgreSQL + Storage），部署於 Render、Vercel；前端以 React / Next.js（App Router）開發 RWD 介面，並將系統由原本的 Express + 原生 HTML 架構重構遷移至 Next.js。
- **核心功能**：獨立開發行程管理、訂單與旅客資料管理、財務追蹤、Email 自動通知、操作日誌、Excel 匯出等模組，完整覆蓋旅行社日常營運流程。
- **效能優化**：針對關鍵查詢進行資料庫索引優化，將 API 回應時間由約 4 秒縮短至 600 毫秒，效能提升約 85%。
- **資安強化**：實作 CORS 白名單、API 流量限制、資料庫 RLS 權限控管，並移除日誌中的個資（PII）。

**跨技術棧能力（PHP / Laravel）**：除旅行社 ERP（Node.js）外，另以 PHP / Laravel 獨立開發一套**補習班行政管理系統**，含 9 大後台模組與家長 Portal、13 張資料表，涵蓋報名點數帳戶、刷卡扣點與並發一致性控制（DB transaction + row lock）；撰寫 56 個 PHPUnit 測試把關核心邏輯，並以 Docker 多階段建置部署上線。能依專案情境選用技術——對外重 SEO／互動的前台用 Next.js，對內重資料維護與長期維運的後台用 Laravel。

## 代表作品

### 1. 旅行社 ERP 系統（接案，營運中）
Next.js（App Router）+ Node.js/Express + Supabase 的全端 ERP，含行程、訂單、旅客、財務、Email 通知、Excel 匯出等模組；一人從需求到維運。

### 2. 補習班行政管理系統（PHP / Laravel）
Laravel 後台系統，9 大模組 + 家長 Portal、13 張資料表；點數帳戶以 DB transaction + row lock 保證刷卡扣點的並發一致性，56 個 PHPUnit 測試把關，Docker 部署上線。

### 3. RAG 知識庫問答助手 / AI 分身（本專案，就是你正在用的這個）
為了把 **Python 與 LLM/RAG 能力**補進作品集、瞄準 AI 工程師職缺而做的獨立微服務：

- **做什麼**：上傳文件（PDF / Word / txt / md）後，可用自然語言提問，AI **只根據文件內容**回答並標出引用來源；找不到就明說、絕不亂掰。
- **RAG 流程**：文件解析 → 切塊 → 用 fastembed 轉成向量 → numpy cosine 相似度檢索最相關段落 → 連同問題交給 Google Gemini 生成答案 + 來源。
- **技術選型考量**：embedding 選用 fastembed（ONNX 本機推論、中文模型 bge-small-zh），不依賴 GPU、記憶體小，適合部署在 Render 免費方案的 512MB 容器；LLM 用 Gemini 免費方案控制成本。
- **工程細節**：用 Docker 多階段建置、build 時預載 embedding 模型加速冷啟動；LLM 呼叫加上自動重試與優雅降級，處理冷啟動 socket 未就緒、額度限制等暫時性錯誤；前端處理中文輸入法 Enter 誤送與重複提問。
- **這個 demo 本身**：知識庫就是「我的技術履歷」，所以你現在等於在跟我的 AI 分身對談。

### 4. 個人作品集網站
Next.js（App Router）+ MDX，案例以 MDX 撰寫、網站自動列出。

## 我的工作流程（AI 輔助開發）

1. **釐清需求**：先把「要解決什麼問題、給誰用」講清楚再動手。
2. **設計結構**：規劃資料模型、頁面 / API 結構，先想清楚再寫。
3. **AI 輔助開發**：以 Claude Code、Codex 加速撰寫、除錯、重構與文件整理，但**架構決策、code review、diff 檢查、build 驗證都由我負責**——AI 是工具，最終的技術決定與交付責任在我。
4. **測試與除錯**：本機實測、看 log 定位問題（例如冷啟動的暫時性錯誤就加重試處理）。
5. **容器化與部署**：用 Docker 打包，部署到 Vercel / Render，處理環境變數、冷啟動等實務細節。
6. **重視可維護性**：命名、結構、README、migration 記錄都顧到，讓專案能長期維護與交接。

## 學歷

淡江大學 歷史學系，大學畢業（2020/9 ~ 2024/6）。
非資工本科，這反而讓我更主動學習、查證問題、靠實作補齊能力。

## 證照

- MOS Excel Expert 2019（專家級）
- MOS Word Expert 2019（專家級）
- MOS PowerPoint 2019（助理級）

## 語言能力

- 英文：聽、說、讀、寫 中等
- 台語：精通
- 粵語：精通

## 我的特質

- **自學與轉職能力**：歷史系出身，靠自學從零到能獨立交付全端 + AI 專案並上線營運。
- **跨技術棧的工程思維**：相信「框架語言會更替，但資料設計、交易一致性、權限控管、上線維運才是通用能力」，因此依情境選工具。
- **重視誠實與可信**：做 AI 應用特別在意「不亂掰」，寧可說找不到也不給假資訊。
- **從頭包到尾**：不只寫功能，也處理效能、資安、部署、文件這些「最後一哩路」。
- **目標**：加入重視工程品質與成長的團隊，持續累積後端開發、系統設計與產品工程能力。
