#!/bin/bash
# 启动脚本（Linux/Mac）

echo "🚀 启动AI加密货币交易平台..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，请先安装Python 3.11+"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📥 安装依赖..."
pip install -r requirements.txt

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "⚠️  未找到.env文件，从.env.example创建..."
    cp .env.example .env
    echo "⚠️  请编辑.env文件配置你的API密钥"
    exit 1
fi

# 启动应用
echo "✅ 启动应用..."
python run.py

