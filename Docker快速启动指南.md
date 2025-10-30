# Docker快速启动指南

## 🚀 一键启动

### Windows
```cmd
docker-start.bat
```

### Linux/Mac
```bash
chmod +x docker-start.sh
./docker-start.sh
```

---

## 📦 文件结构

```
ai-trading/
├── backend/
│   └── Dockerfile              ← 后端容器配置
├── frontend/
│   ├── Dockerfile              ← 前端容器配置（多阶段）
│   └── nginx.conf              ← Nginx配置（API代理）
├── docker-compose.yml          ← 容器编排
├── env.example                 ← 环境变量模板
├── docker-start.bat            ← Windows启动脚本
└── docker-start.sh             ← Linux/Mac启动脚本
```

---

## ⚡ 快速命令

```bash
# 启动
docker-compose up -d

# 停止
docker-compose down

# 查看日志
docker-compose logs -f backend

# 重启
docker-compose restart

# 重新构建
docker-compose up -d --build

# 查看状态
docker-compose ps
```

---

## 🌐 访问地址

- **前端：** http://localhost
- **后端：** http://localhost:8001
- **API（通过Nginx）：** http://localhost/api/status

---

## 🎯 Nginx代理说明

**自动转发：**
```
http://localhost/api/*  → http://backend:8001/api/*
http://localhost/ws     → http://backend:8001/ws (WebSocket)
```

**用户无需关心后端端口，全部通过前端访问！**

---

## ✅ 验证部署

```bash
# 检查容器
docker-compose ps

# 检查后端
curl http://localhost:8001/api/status

# 检查前端
curl http://localhost

# 检查API代理
curl http://localhost/api/status
```

全部返回正常 = 部署成功 ✅

---

## 🎉 已完成

✅ 后端Dockerfile  
✅ 前端Dockerfile（多阶段构建）  
✅ Nginx配置（API代理+WebSocket）  
✅ Docker Compose编排  
✅ 启动脚本（Windows/Linux）  
✅ 环境变量模板  
✅ 数据持久化配置  
✅ 健康检查  

**现在可以一键Docker部署了！** 🚀

