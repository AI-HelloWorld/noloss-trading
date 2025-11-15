@echo off
chcp 65001 >nul
echo 🚀 启动AI交易平台...

REM 创建必要的目录
echo 📁 创建必要的目录...
if not exist "logs" mkdir logs
if not exist "data" mkdir data

REM 检查.env文件
if not exist ".env" (
    echo ⚠️  未找到.env文件，从模板创建...
    if exist "env.example" (
        copy env.example .env
        echo ✅ 已创建.env文件，请编辑配置后重新启动
        echo 📝 请编辑.env文件，至少配置DEEPSEEK_API_KEY
        pause
        exit /b 1
    ) else (
        echo ❌ 未找到env.example模板文件
        pause
        exit /b 1
    )
)

REM 停止现有容器
echo 🛑 停止现有容器...
docker-compose down

REM 清理旧容器
echo 🧹 清理旧容器...
docker-compose rm -f

REM 构建并启动服务
echo 🔨 构建并启动服务...
docker-compose up --build -d

REM 等待服务启动
echo ⏳ 等待服务启动...
timeout /t 10 /nobreak >nul

REM 检查服务状态
echo 🔍 检查服务状态...
docker-compose ps

REM 显示日志
echo 📋 显示后端日志...
docker-compose logs backend

echo ✅ 启动完成！
echo 🌐 前端访问: http://localhost
echo 🔧 后端API: http://localhost:8001
echo 📊 查看日志: docker-compose logs -f
pause
