#!/bin/bash
# Docker启动脚本（Linux/Mac）

echo "🚀 启动AI加密货币交易平台..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: Docker未安装"
    echo "请先安装Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查docker-compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ 错误: docker-compose未安装"
    echo "请先安装docker-compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# 检查.env文件
if [ ! -f .env ]; then
    echo "⚠️  警告: .env文件不存在"
    echo "📝 正在从env.example创建.env文件..."
    cp env.example .env
    echo "✅ 已创建.env文件，请编辑填写您的API密钥"
    echo "💡 模拟模式下可以直接使用，真实交易需要配置API密钥"
fi

# 停止旧容器（如果存在）
echo "🛑 停止旧容器..."
docker-compose down

# 构建镜像
echo "🔨 构建Docker镜像..."
docker-compose build

# 启动服务
echo "🚀 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose ps

# 检查后端健康
echo "🔍 检查后端健康..."
curl -s http://localhost:8001/api/status | python -m json.tool

echo ""
echo "✅ 启动完成！"
echo ""
echo "📡 访问地址:"
echo "   前端: http://localhost"
echo "   后端API: http://localhost:8001"
echo "   后端状态: http://localhost:8001/api/status"
echo ""
echo "📝 查看日志:"
echo "   docker-compose logs -f backend"
echo "   docker-compose logs -f frontend"
echo ""
echo "🛑 停止服务:"
echo "   docker-compose down"
echo ""

