@echo off
chcp 65001 >nul
cls
echo ========================================
echo   Backend Diagnostic Tool
echo ========================================
echo.

echo [1/5] Checking Python version...
python --version
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.10 or higher
    goto :end
)
echo OK
echo.

echo [2/5] Checking if port 8001 is free...
netstat -ano | findstr :8001 >nul
if errorlevel 1 (
    echo OK - Port 8001 is available
) else (
    echo WARNING - Port 8001 is in use:
    netstat -ano | findstr :8001
    echo You may need to kill the process
)
echo.

echo [3/5] Checking backend directory...
if exist "backend\main.py" (
    echo OK - backend\main.py found
) else (
    echo ERROR - backend\main.py not found!
    echo Are you in the correct directory?
    goto :end
)
echo.

echo [4/5] Checking database...
if exist "trading_platform.db" (
    echo OK - Database exists
) else (
    echo INFO - Database will be created on first run
)
echo.

echo [5/5] Testing backend connection...
curl -s http://127.0.0.1:8001/api/status >nul 2>&1
if errorlevel 1 (
    echo BACKEND NOT RUNNING
    echo.
    echo To start backend:
    echo   1. cd backend
    echo   2. python main.py
) else (
    echo OK - Backend is responding!
    echo.
    echo Testing market data...
    curl http://127.0.0.1:8001/api/market-data | findstr "price"
)
echo.

:end
echo ========================================
echo   Diagnostic Complete
echo ========================================
echo.
pause

