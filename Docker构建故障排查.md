# Docker构建故障排查指南

## ❌ 常见错误及解决方案

### 错误1: npm run build failed (exit code 127)

**错误信息：**
```
failed to solve: process "/bin/sh -c npm run build" did not complete successfully: exit code: 127
```

**原因：**
- npm install使用了 `--only=production`，没有安装devDependencies
- Vite构建需要devDependencies

**解决方案：✅ 已修复**
```dockerfile
# 改为完整安装
RUN npm install  # 而不是 npm ci --only=production
```

---

### 错误2: 找不到package.json

**错误信息：**
```
COPY failed: file not found in build context
```

**解决方案：**
```bash
# 检查构建上下文
cd frontend
ls -la package.json

# 确保在正确目录运行
docker-compose build frontend
```

---

### 错误3: 端口冲突

**错误信息：**
```
Bind for 0.0.0.0:80 failed: port is already allocated
```

**解决方案：**

**方法1: 停止占用端口的程序**
```bash
# Windows
netstat -ano | findstr :80
taskkill /PID <进程ID> /F

# Linux
sudo lsof -i :80
sudo kill -9 <PID>
```

**方法2: 修改映射端口**
```yaml
# docker-compose.yml
frontend:
  ports:
    - "8080:80"  # 改用8080端口
```

---

### 错误4: Docker daemon未运行

**错误信息：**
```
Cannot connect to the Docker daemon
```

**解决方案：**
```bash
# Windows: 启动Docker Desktop
# Linux: 启动Docker服务
sudo systemctl start docker
```

---

### 错误5: 构建超时

**错误信息：**
```
failed to solve: executor failed running: context canceled
```

**解决方案：**
```bash
# 增加Docker构建超时
export DOCKER_BUILDKIT=1
export COMPOSE_HTTP_TIMEOUT=300

# 或者逐个构建
docker-compose build backend
docker-compose build frontend
```

---

## 🔍 调试命令

### 检查构建过程

```bash
# 查看详细构建日志
docker-compose build --progress=plain

# 只构建后端
docker-compose build backend

# 只构建前端
docker-compose build frontend

# 不使用缓存重新构建
docker-compose build --no-cache
```

### 检查容器状态

```bash
# 查看所有容器
docker-compose ps

# 查看容器日志
docker-compose logs backend
docker-compose logs frontend

# 实时查看日志
docker-compose logs -f backend

# 查看最近50行
docker-compose logs --tail=50 backend
```

### 进入容器调试

```bash
# 进入后端容器
docker-compose exec backend bash

# 进入前端容器
docker-compose exec frontend sh

# 在容器中测试
docker-compose exec backend python -c "import backend; print('OK')"
```

---

## 🛠️ 手动构建测试

### 测试后端构建

```bash
# 进入项目根目录
cd /path/to/ai-trading

# 手动构建后端
docker build -f backend/Dockerfile -t ai-trading-backend .

# 运行测试
docker run --rm ai-trading-backend python -c "import backend; print('Backend OK')"
```

### 测试前端构建

```bash
# 进入前端目录
cd frontend

# 手动构建前端
docker build -t ai-trading-frontend .

# 运行测试
docker run --rm -p 8080:80 ai-trading-frontend
# 浏览器访问 http://localhost:8080
```

---

## 📋 逐步构建指南

### 步骤1: 准备环境

```bash
# 检查Docker
docker --version
docker-compose --version

# 检查文件
ls -la backend/Dockerfile
ls -la frontend/Dockerfile
ls -la docker-compose.yml
```

### 步骤2: 创建.env文件

```bash
# 复制模板
cp env.example .env

# 编辑配置（至少填写DEEPSEEK_API_KEY）
nano .env  # 或使用其他编辑器
```

**最小配置：**
```env
DEEPSEEK_API_KEY=sk-your-key-here
INITIAL_BALANCE=1000.0
```

### 步骤3: 构建后端

```bash
# 单独构建后端（测试）
docker-compose build backend

# 查看构建日志
docker-compose build --progress=plain backend
```

**预期输出：**
```
✅ Collecting packages...
✅ Installing Python dependencies...
✅ Successfully built backend
```

### 步骤4: 构建前端

```bash
# 单独构建前端
docker-compose build frontend

# 查看详细过程
docker-compose build --progress=plain frontend
```

**预期输出：**
```
✅ npm install complete
✅ vite build complete
✅ dist/ folder created
✅ Successfully built frontend
```

### 步骤5: 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看启动日志
docker-compose logs -f
```

**预期输出：**
```
✅ backend container started
✅ frontend container started
✅ Healthcheck passing
```

### 步骤6: 验证部署

```bash
# 检查容器
docker-compose ps

# 测试后端
curl http://localhost:8001/api/status

# 测试前端
curl http://localhost

# 测试API代理
curl http://localhost/api/status
```

---

## 🐛 具体错误解决

### 当前错误: exit code 127

**问题：**
```
exit code 127 = command not found
```

**可能原因：**
1. npm未正确安装
2. package.json中的命令不存在
3. node_modules未正确安装

**已修复方案：**
```dockerfile
# 从 npm ci --only=production
# 改为 npm install
RUN npm install  # 安装所有依赖，包括vite
```

**重新构建：**
```bash
# 清理缓存
docker-compose down
docker system prune -f

# 重新构建
docker-compose build --no-cache frontend

# 启动
docker-compose up -d
```

---

## 🔧 高级调试

### 进入构建阶段调试

```bash
# 构建到指定阶段
docker build --target builder -f frontend/Dockerfile -t debug-frontend ./frontend

# 进入构建阶段容器
docker run -it debug-frontend sh

# 在容器内检查
ls -la
cat package.json
which npm
npm --version
npm run build
```

### 检查构建上下文

```bash
# 查看发送到Docker的文件
docker build --no-cache --progress=plain -f frontend/Dockerfile ./frontend 2>&1 | grep "COPY"
```

---

## ✅ 验证修复

**重新构建前端：**
```bash
docker-compose build --no-cache frontend
```

**预期成功输出：**
```
[+] Building 120.5s (12/12) FINISHED
 => [builder 1/6] FROM docker.io/library/node:18-alpine
 => [builder 2/6] WORKDIR /app
 => [builder 3/6] COPY package*.json ./
 => [builder 4/6] RUN npm install                          ✅
 => [builder 5/6] COPY . .
 => [builder 6/6] RUN npm run build                        ✅
 => [stage-1 2/3] COPY nginx.conf /etc/nginx/conf.d/default.conf
 => [stage-1 3/3] COPY --from=builder /app/dist /usr/share/nginx/html
 => exporting to image
```

---

## 🎯 完整重新部署流程

如果遇到问题，按以下步骤完全重新部署：

```bash
# 1. 停止并清理
docker-compose down -v
docker system prune -f

# 2. 确保.env文件存在
cp env.example .env

# 3. 重新构建（无缓存）
docker-compose build --no-cache

# 4. 启动
docker-compose up -d

# 5. 查看日志
docker-compose logs -f

# 6. 验证
curl http://localhost:8001/api/status
curl http://localhost
```

---

## 📝 快速修复总结

**问题：** npm run build exit code 127

**原因：** `npm ci --only=production` 没有安装构建工具

**修复：** ✅ 已改为 `npm install`

**下一步：**
```bash
# 重新构建前端
docker-compose build --no-cache frontend

# 启动
docker-compose up -d

# 验证
curl http://localhost
```

应该可以成功了！🚀

