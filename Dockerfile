FROM python:3.11-slim

# 安装Node.js（用于构建前端）
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装后端依赖
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# 构建前端
COPY frontend/package.json frontend/package-lock.json* frontend/
RUN cd frontend && npm install
COPY frontend/ frontend/
RUN cd frontend && npm run build

# 复制后端代码
COPY backend/ backend/

# 将前端构建产物复制到后端目录（供 FastAPI 静态文件服务使用）
RUN mkdir -p backend/frontend && cp -r frontend/dist backend/frontend/dist

# 创建数据目录
RUN mkdir -p backend/data/uploads

# 设置环境变量
ENV PYTHONPATH=/app/backend
ENV DATABASE_PATH=data/rag_knowledge.db
ENV UPLOAD_DIR=data/uploads
ENV CORS_ORIGINS=["*"]

EXPOSE 8000

COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

CMD ["/app/docker-entrypoint.sh"]
