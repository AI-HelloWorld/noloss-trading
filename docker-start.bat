@echo off
REM Docker启动脚本（Windows）

echo ========================================
echo 🚀 启动AI加密货币交易平台
echo ========================================
echo.

REM 检查Docker是否运行
docker version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: Docker未运行
    echo 请先启动Docker Desktop
    pause
    exit /b 1
)

REM 检查.env文件
if not exist .env (
    echo ⚠️  警告: .env文件不存在
    echo 📝 正在从env.example创建.env文件...
    copy env.example .env >nul
    echo ✅ 已创建.env文件
    echo 💡 模拟模式下可以直接使用
    echo.
)

REM 停止旧容器
echo 🛑 停止旧容器...
docker-compose down >nul 2>&1

REM 构建镜像
echo 🔨 构建Docker镜像...
docker-compose build

REM 启动服务
echo 🚀 启动服务...
docker-compose up -d

REM 等待服务启动
echo ⏳ 等待服务启动...
timeout /t 10 /nobreak >nul

REM 检查服务状态
echo.
echo 📊 检查服务状态...
docker-compose ps

REM 检查后端健康
echo.
echo 🔍 检查后端健康...
curl -s http://localhost:8001/api/status

echo.
echo ========================================
echo ✅ 启动完成！
echo ========================================
echo.
echo 📡 访问地址:
echo    前端: http://localhost
echo    后端API: http://localhost:8001
echo    后端状态: http://localhost:8001/api/status
echo.
echo 📝 查看日志:
echo    docker-compose logs -f backend
echo    docker-compose logs -f frontend
echo.
echo 🛑 停止服务:
echo    docker-compose down
echo.
pause

