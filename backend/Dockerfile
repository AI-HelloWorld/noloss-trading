# 后端Dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖（包括bash）
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    bash \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制Docker入口脚本（先复制并设置权限）
COPY backend/docker-entrypoint.sh /docker-entrypoint.sh
# 移除可能的Windows行结束符并设置执行权限
RUN sed -i 's/\r$//' /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh && \
    test -f /docker-entrypoint.sh && \
    echo "✅ 入口脚本已准备好"

# 复制后端代码
COPY backend/ ./backend/

# 创建日志目录和数据库目录
RUN mkdir -p logs && \
    mkdir -p /app/data && \
    chmod 755 /app/data

# 暴露端口
EXPOSE 8001

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8001/api/status')"

# 使用入口脚本
ENTRYPOINT ["/docker-entrypoint.sh"]

# 启动命令
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001"]

