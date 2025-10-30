@echo off
REM 启动脚本（Windows）

echo 🚀 启动AI加密货币交易平台...

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请先安装Python 3.11+
    exit /b 1
)

REM 检查虚拟环境
if not exist "venv" (
    echo 📦 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo 🔧 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo 📥 安装依赖...
pip install -r requirements.txt

REM 检查.env文件
if not exist ".env" (
    echo ⚠️  未找到.env文件，从.env.example创建...
    copy .env.example .env
    echo ⚠️  请编辑.env文件配置你的API密钥
    exit /b 1
)

REM 启动应用
echo ✅ 启动应用...
python run.py

