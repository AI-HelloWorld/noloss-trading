# Docker部署指南

## 📋 概述

本指南将帮助您使用Docker快速部署AI加密货币交易平台。

---

## 🎯 架构说明

### 容器架构

```
┌─────────────────────────────────────────┐
│           Nginx (前端容器)               │
│         Port 80 → 外部访问               │
│                                         │
│  ┌──────────────┐                      │
│  │  静态资源     │                      │
│  │  (React构建)  │                      │
│  └──────────────┘                      │
│         ↓ API代理                       │
└─────────────────┼───────────────────────┘
                  ↓
┌─────────────────┼───────────────────────┐
│         FastAPI (后端容器)               │
│         Port 8001                       │
│                                         │
│  ┌──────────────┐  ┌──────────────┐   │
│  │  AI分析师团队 │  │  交易引擎     │   │
│  └──────────────┘  └──────────────┘   │
│         ↓                  ↓            │
│  ┌──────────────┐  ┌──────────────┐   │
│  │  SQLite数据库 │  │  模拟交易所   │   │
│  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────┘
```

### 网络架构

```
用户浏览器
    ↓
http://localhost (Port 80)
    ↓
Nginx容器
    ├─ 静态资源: /
    ├─ API代理: /api/* → http://backend:8001/api/
    └─ WebSocket: /ws → http://backend:8001/ws
    ↓
FastAPI后端容器 (Port 8001)
    ├─ AI分析师团队
    ├─ 交易引擎
    └─ 数据库
```

---

## 📦 文件清单

### 已创建的Docker文件

1. **`backend/Dockerfile`** - 后端容器构建文件
2. **`frontend/Dockerfile`** - 前端容器构建文件
3. **`frontend/nginx.conf`** - Nginx配置（API代理）
4. **`docker-compose.yml`** - 容器编排配置
5. **`.dockerignore`** - Docker构建忽略文件
6. **`frontend/.dockerignore`** - 前端构建忽略文件
7. **`env.example`** - 环境变量模板
8. **`docker-start.sh`** - Linux/Mac启动脚本
9. **`docker-start.bat`** - Windows启动脚本

---

## 🚀 快速开始

### 前置要求

1. **Docker Desktop**
   - Windows: https://docs.docker.com/desktop/install/windows-install/
   - Mac: https://docs.docker.com/desktop/install/mac-install/
   - Linux: https://docs.docker.com/engine/install/

2. **Docker Compose**
   - 通常随Docker Desktop一起安装
   - Linux需单独安装

### 方法1：使用启动脚本（推荐）

**Windows：**
```cmd
docker-start.bat
```

**Linux/Mac：**
```bash
chmod +x docker-start.sh
./docker-start.sh
```

### 方法2：手动启动

**步骤1：准备环境变量**
```bash
# 复制配置模板
cp env.example .env

# 编辑.env文件，填写API密钥（模拟模式可跳过）
# 至少需要配置 DEEPSEEK_API_KEY
```

**步骤2：构建并启动**
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

**步骤3：验证**
```bash
# 检查容器状态
docker-compose ps

# 检查后端健康
curl http://localhost:8001/api/status

# 访问前端
浏览器打开: http://localhost
```

---

## 🔧 Docker配置详解

### 后端容器 (`backend/Dockerfile`)

**基础镜像：** `python:3.11-slim`

**关键配置：**
```dockerfile
WORKDIR /app                    # 工作目录
EXPOSE 8001                     # 暴露端口
VOLUME /app/logs                # 日志持久化
VOLUME /app/trading_platform.db # 数据库持久化
```

**启动命令：**
```
uvicorn backend.main:app --host 0.0.0.0 --port 8001
```

### 前端容器 (`frontend/Dockerfile`)

**多阶段构建：**

**阶段1：构建（Node 18）**
```dockerfile
FROM node:18-alpine AS builder
RUN npm ci
RUN npm run build
```

**阶段2：运行（Nginx）**
```dockerfile
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

**优势：**
- ✅ 最终镜像体积小（只含nginx和静态文件）
- ✅ 性能优秀
- ✅ 生产级配置

### Nginx配置 (`frontend/nginx.conf`)

**关键特性：**

1. **API代理转发**
```nginx
location /api/ {
    proxy_pass http://backend:8001/api/;
    # 自动转发到后端容器
}
```

2. **WebSocket支持**
```nginx
location /ws {
    proxy_pass http://backend:8001/ws;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

3. **SPA路由支持**
```nginx
location / {
    try_files $uri $uri/ /index.html;
    # 前端路由正常工作
}
```

4. **静态资源缓存**
```nginx
location ~* \.(js|css|png|jpg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### Docker Compose配置

**服务定义：**

```yaml
services:
  backend:
    build: ./backend/Dockerfile
    ports: ["8001:8001"]
    volumes:
      - ./logs:/app/logs          # 日志持久化
      - ./trading_platform.db:/app/trading_platform.db  # 数据库持久化
    networks:
      - ai-trading-network

  frontend:
    build: ./frontend/Dockerfile
    ports: ["80:80"]
    depends_on:
      - backend                    # 依赖后端先启动
    networks:
      - ai-trading-network
```

**网络配置：**
```yaml
networks:
  ai-trading-network:
    driver: bridge                 # 容器间通信
```

---

## 📊 端口说明

| 服务 | 容器端口 | 主机端口 | 说明 |
|------|----------|----------|------|
| 前端 | 80 | 80 | 用户访问入口 |
| 后端 | 8001 | 8001 | API服务（也可以直接访问）|

**访问方式：**
- 前端：`http://localhost` 或 `http://localhost:80`
- 后端：`http://localhost:8001`
- 前端通过Nginx代理访问后端：`http://localhost/api/*`

---

## 🔍 常用Docker命令

### 启动和停止

```bash
# 启动（后台运行）
docker-compose up -d

# 启动（前台运行，查看日志）
docker-compose up

# 停止
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

### 查看日志

```bash
# 查看所有日志
docker-compose logs

# 查看后端日志
docker-compose logs backend

# 实时查看日志
docker-compose logs -f backend

# 查看最近100行
docker-compose logs --tail=100 backend
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 只重启后端
docker-compose restart backend

# 只重启前端
docker-compose restart frontend
```

### 重新构建

```bash
# 重新构建所有镜像
docker-compose build

# 强制重新构建（不使用缓存）
docker-compose build --no-cache

# 重新构建并启动
docker-compose up -d --build
```

### 进入容器

```bash
# 进入后端容器
docker-compose exec backend bash

# 进入前端容器
docker-compose exec frontend sh

# 在后端容器中执行Python命令
docker-compose exec backend python -c "print('Hello')"
```

### 查看状态

```bash
# 查看容器状态
docker-compose ps

# 查看资源使用
docker stats

# 查看网络
docker network ls
docker network inspect ai-trading_ai-trading-network
```

---

## 🛠️ 故障排查

### 问题1：容器启动失败

**检查：**
```bash
# 查看详细日志
docker-compose logs backend
docker-compose logs frontend

# 检查构建过程
docker-compose build --progress=plain
```

**常见原因：**
- 依赖安装失败
- 端口被占用
- 配置文件错误

### 问题2：前端无法访问后端

**检查：**
```bash
# 检查网络连接
docker-compose exec frontend ping backend

# 检查后端服务
curl http://localhost:8001/api/status

# 检查nginx配置
docker-compose exec frontend cat /etc/nginx/conf.d/default.conf
```

**解决：**
- 确保backend容器健康
- 检查nginx.conf配置
- 重启frontend容器

### 问题3：数据丢失

**检查卷挂载：**
```bash
# 查看卷
docker volume ls

# 检查挂载
docker-compose config
```

**确保：**
- `./logs` 目录存在
- `./trading_platform.db` 正确挂载
- `.env` 文件挂载

### 问题4：端口冲突

**解决方法：**

修改 `docker-compose.yml` 中的端口映射：
```yaml
services:
  frontend:
    ports:
      - "8080:80"  # 改为8080端口
  
  backend:
    ports:
      - "8002:8001"  # 改为8002端口
```

---

## 📊 性能优化

### 1. 构建优化

**.dockerignore 作用：**
- 减少构建上下文大小
- 加快构建速度
- 减少镜像体积

### 2. 多阶段构建（前端）

**优势：**
```
构建阶段: Node 18 (约1GB)
    ↓ 编译React
运行阶段: Nginx (约15MB)
    ↓ 只保留静态文件
最终镜像: ~30MB（减少97%）
```

### 3. 健康检查

**作用：**
- 自动检测服务健康
- 失败自动重启
- 确保服务可用

**配置：**
```yaml
healthcheck:
  test: ["CMD", "curl", "http://localhost:8001/api/status"]
  interval: 30s      # 每30秒检查
  timeout: 10s       # 10秒超时
  retries: 3         # 失败3次重启
```

---

## 🔐 生产环境建议

### 1. 环境变量

**不要在docker-compose.yml中硬编码敏感信息！**

**推荐：使用.env文件**
```yaml
# docker-compose.yml
environment:
  - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
  - ASTER_DEX_API_KEY=${ASTER_DEX_API_KEY}
```

### 2. 数据持久化

**关键数据卷：**
```yaml
volumes:
  - ./logs:/app/logs                           # 日志
  - ./trading_platform.db:/app/trading_platform.db  # 数据库
  - ./.env:/app/.env                           # 配置
```

### 3. 网络安全

**生产环境：**
```yaml
# 不暴露后端端口
backend:
  # ports:
  #   - "8001:8001"  # 注释掉，只通过nginx访问
```

### 4. SSL/HTTPS（生产）

**添加SSL证书：**
```nginx
server {
    listen 443 ssl;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
}
```

---

## 📝 使用示例

### 场景1：首次部署

```bash
# 1. 克隆/下载项目
cd /path/to/ai-trading

# 2. 准备配置
cp env.example .env
# 编辑.env，填写DEEPSEEK_API_KEY

# 3. 启动（Windows）
docker-start.bat

# 或（Linux/Mac）
chmod +x docker-start.sh
./docker-start.sh

# 4. 访问
浏览器打开: http://localhost
```

### 场景2：更新代码后重新部署

```bash
# 重新构建并启动
docker-compose up -d --build

# 查看日志确认
docker-compose logs -f backend
```

### 场景3：查看系统运行状态

```bash
# 查看容器状态
docker-compose ps

# 查看后端日志
docker-compose logs --tail=50 backend

# 查看资源使用
docker stats ai-trading-backend ai-trading-frontend
```

### 场景4：备份数据

```bash
# 备份数据库
docker cp ai-trading-backend:/app/trading_platform.db ./backup/

# 备份日志
docker cp ai-trading-backend:/app/logs ./backup/logs/
```

### 场景5：完全清理重新开始

```bash
# 停止并删除容器、网络
docker-compose down

# 删除镜像
docker-compose down --rmi all

# 删除数据卷
docker-compose down -v

# 清理数据库
rm trading_platform.db

# 重新启动
docker-compose up -d --build
```

---

## 🎯 环境变量配置

### 必需配置

**最小配置（模拟模式）：**
```env
DEEPSEEK_API_KEY=sk-your-key-here
INITIAL_BALANCE=1000.0
```

**真实交易配置：**
```env
DEEPSEEK_API_KEY=sk-your-key-here
ASTER_DEX_API_KEY=your-api-key
ASTER_DEX_API_SECRET=your-api-secret
INITIAL_BALANCE=1000.0
```

### 可选配置

**风控参数：**
```env
MAX_WALLET_USAGE=0.5
MARGIN_RESERVE_RATIO=0.3
RISK_THRESHOLD=0.7
```

**交易频率：**
```env
TRADE_CHECK_INTERVAL=300        # 5分钟
DATA_UPDATE_INTERVAL=60         # 1分钟
```

---

## 📊 监控和维护

### 实时监控

```bash
# 方法1: 查看日志
docker-compose logs -f backend

# 方法2: 进入容器查看
docker-compose exec backend tail -f logs/trading_*.log

# 方法3: 通过API监控
watch -n 5 'curl -s http://localhost:8001/api/portfolio | python -m json.tool'
```

### 定期维护

**每天：**
```bash
# 检查容器健康
docker-compose ps

# 查看今日交易
curl http://localhost:8001/api/trades?limit=20
```

**每周：**
```bash
# 备份数据库
cp trading_platform.db backup/trading_$(date +%Y%m%d).db

# 查看日志大小
du -sh logs/
```

**每月：**
```bash
# 清理旧日志（保留30天）
find logs/ -name "*.log" -mtime +30 -delete

# 更新Docker镜像
docker-compose pull
docker-compose up -d --build
```

---

## 🎉 验证部署成功

### 检查清单

运行以下命令验证：

```bash
# 1. 容器运行状态
docker-compose ps
# 预期: backend和frontend都是Up状态

# 2. 后端健康检查
curl http://localhost:8001/api/status
# 预期: {"system":"online","trading_enabled":true}

# 3. 前端访问
curl http://localhost
# 预期: 返回HTML内容

# 4. API代理
curl http://localhost/api/status
# 预期: 与直接访问后端相同

# 5. 投资组合数据
curl http://localhost/api/portfolio
# 预期: 返回投资组合JSON数据

# 6. 查看AI团队
curl http://localhost/api/team
# 预期: 返回7个分析师状态
```

**全部通过 = 部署成功 ✅**

---

## 🚀 生产部署建议

### 1. 使用外部数据库（可选）

**PostgreSQL配置：**
```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: trading_db
      POSTGRES_USER: trading_user
      POSTGRES_PASSWORD: your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    environment:
      - DATABASE_URL=postgresql+asyncpg://trading_user:password@postgres/trading_db
```

### 2. 反向代理（可选）

**Traefik自动SSL：**
```yaml
services:
  traefik:
    image: traefik:v2.10
    command:
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
    ports:
      - "80:80"
      - "443:443"
```

### 3. 日志管理

**使用日志驱动：**
```yaml
backend:
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
```

---

## 📝 总结

### 已创建的文件

✅ **后端Dockerfile** - Python后端容器  
✅ **前端Dockerfile** - React前端容器（多阶段构建）  
✅ **nginx.conf** - API代理和静态资源服务  
✅ **docker-compose.yml** - 容器编排  
✅ **.dockerignore** - 构建优化  
✅ **env.example** - 环境变量模板  
✅ **启动脚本** - Windows和Linux/Mac  

### 关键特性

✅ **一键启动** - docker-start脚本  
✅ **API代理** - Nginx自动转发  
✅ **WebSocket支持** - 实时数据推送  
✅ **数据持久化** - 日志和数据库  
✅ **健康检查** - 自动监控和重启  
✅ **多阶段构建** - 优化镜像大小  
✅ **生产就绪** - 专业级配置  

### 使用方式

**最简单：**
```bash
# Windows
docker-start.bat

# Linux/Mac
./docker-start.sh

# 访问
http://localhost
```

---

**Docker配置已完成！现在可以一键部署整个系统！** 🎉

**下一步：**
1. 运行 `docker-start.bat`（Windows）或 `./docker-start.sh`（Linux/Mac）
2. 等待构建完成（首次需要5-10分钟）
3. 访问 `http://localhost`
4. 享受AI自动交易！

需要我帮您测试Docker部署吗？
