@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   Restarting Backend and Frontend
echo ========================================
echo.

echo Stopping all processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
timeout /t 2 >nul

echo.
echo Starting Backend...
start "Backend Server" cmd /k "cd /d %~dp0backend && python main.py"
timeout /t 5 >nul

echo Starting Frontend...
start "Frontend Server" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo   Services starting in new windows
echo ========================================
echo.
echo Backend: Check "Backend Server" window
echo Frontend: Check "Frontend Server" window
echo.
echo Wait 30 seconds, then open:
echo   http://localhost:3000
echo.
pause

