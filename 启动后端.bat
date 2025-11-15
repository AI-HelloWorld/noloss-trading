@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo ========================================
echo   启动后端服务器
echo ========================================
echo.
echo 正在启动...
echo.
cd backend
python main.py
pause

