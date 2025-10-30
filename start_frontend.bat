@echo off
chcp 65001 > nul
echo.
echo ============================================================
echo.
echo    启动AI交易平台前端
echo.
echo    后端API: http://localhost:8000
echo    前端仪表盘: http://localhost:3000
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
echo 启动FastAPI后端...
start "FastAPI Backend" cmd /k "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

echo 等待后端启动...
timeout /t 5 /nobreak > nul

echo.
echo 启动Dash前端...
cd frontend
python dashboard.py

pause
