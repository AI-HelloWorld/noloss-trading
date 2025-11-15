#!/bin/bash

# AI交易平台 - Docker启动脚本（修复数据库问题）

echo "🚀 启动AI交易平台..."

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p logs
mkdir -p data

# 设置权限
echo "🔐 设置目录权限..."
chmod 755 data
chmod 755 logs

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "⚠️  未找到.env文件，从模板创建..."
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "✅ 已创建.env文件，请编辑配置后重新启动"
        echo "📝 请编辑.env文件，至少配置DEEPSEEK_API_KEY"
        exit 1
    else
        echo "❌ 未找到env.example模板文件"
        exit 1
    fi
fi

# 停止现有容器
echo "🛑 停止现有容器..."
docker-compose down

# 清理旧容器和镜像（可选）
echo "🧹 清理旧容器..."
docker-compose rm -f

# 构建并启动服务
echo "🔨 构建并启动服务..."
docker-compose up --build -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose ps

# 显示日志
echo "📋 显示后端日志..."
docker-compose logs backend

echo "✅ 启动完成！"
echo "🌐 前端访问: http://localhost"
echo "🔧 后端API: http://localhost:8001"
echo "📊 查看日志: docker-compose logs -f"
