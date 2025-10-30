@echo off
chcp 65001 > nul
echo.
echo ============================================================
echo.
echo     AI加密货币交易平台 - 完整版启动
echo.
echo     后端API: http://localhost:8000
echo     前端仪表盘: http://localhost:3000
echo.
echo     按 Ctrl+C 停止所有服务
echo.
echo ============================================================
echo.

echo 检查Python环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

echo.
echo 安装依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo 错误: 依赖安装失败
    pause
    exit /b 1
)

echo.
echo 启动服务...
echo 正在启动FastAPI后端和Dash前端...
echo.

start "FastAPI Backend" cmd /k "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 /nobreak > nul
start "Dash Frontend" cmd /k "cd frontend && python dashboard.py"

echo.
echo 服务已启动！
echo 请访问 http://localhost:3000 查看仪表盘
echo.
pause
