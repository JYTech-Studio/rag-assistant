# Python 3.12（ML 生態最穩；本機 3.14 開發、部署用 3.12）
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# onnxruntime（fastembed 底層）在 slim 映像需要 libgomp
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# build 時先把 embedding 模型抓進映像，避免冷啟動時才下載（加快首次回應）
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('BAAI/bge-small-zh-v1.5')"

# Render 會以 $PORT 注入埠號
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
