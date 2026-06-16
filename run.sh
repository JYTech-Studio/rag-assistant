#!/usr/bin/env bash
# 啟動 RAG server：自動停掉舊的 process 再重啟。
#
# 用法：
#   ./run.sh              一般啟動
#   ./run.sh --fresh      先清掉 index（data/），重新只載入 sample_docs 裡現有的文件
#   ./run.sh --reload     開發模式：改到 app/ 的程式碼會自動重啟
#   旗標可併用，例如：./run.sh --fresh --reload

set -euo pipefail
cd "$(dirname "$0")"

HOST="127.0.0.1"
PORT="8099"
RELOAD=""

for arg in "$@"; do
  case "$arg" in
    --fresh)
      echo "🧹 清除舊知識庫 index（data/）…"
      rm -f data/chunks.json data/matrix.npy
      ;;
    --reload)
      RELOAD="--reload"
      ;;
    *)
      echo "未知參數：$arg（可用：--fresh、--reload）" >&2
      exit 1
      ;;
  esac
done

# 停掉還在跑的舊 server（沒有也不會報錯）
echo "🛑 停掉舊的 server（如果有）…"
pkill -f "uvicorn app.main:app" 2>/dev/null || true
sleep 1

echo "🚀 啟動 server：http://${HOST}:${PORT}（Ctrl+C 結束）"
exec .venv/bin/uvicorn app.main:app --host "$HOST" --port "$PORT" $RELOAD
