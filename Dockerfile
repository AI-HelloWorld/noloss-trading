# 多阶段构建 - 前端
FROM node:18-alpine as frontend-builder

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# 多阶段构建 - 后端
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./backend/

# 从前端构建阶段复制构建产物
COPY --from=frontend-builder /frontend/dist ./frontend/dist

# 创建日志目录
RUN mkdir -p logs

# 暴露端口
EXPOSE 8000

# 启动应用
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

