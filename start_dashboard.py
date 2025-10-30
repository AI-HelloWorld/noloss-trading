#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
启动脚本 - 同时运行FastAPI后端和Dash前端
"""
import subprocess
import threading
import time
import sys
import os
from pathlib import Path

def run_fastapi():
    """运行FastAPI后端"""
    print("🚀 启动FastAPI后端服务...")
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "backend.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("🛑 FastAPI服务已停止")
    except Exception as e:
        print(f"❌ FastAPI启动失败: {e}")

def run_dash():
    """运行Dash前端"""
    print("📊 启动Dash仪表盘...")
    try:
        # 切换到frontend目录
        frontend_dir = Path(__file__).parent / "frontend"
        os.chdir(frontend_dir)
        
        subprocess.run([
            sys.executable, "dashboard.py"
        ], check=True)
    except KeyboardInterrupt:
        print("🛑 Dash服务已停止")
    except Exception as e:
        print(f"❌ Dash启动失败: {e}")

def main():
    """主函数"""
    print("""
    ============================================================
    
        AI加密货币交易平台 - 完整版启动
    
        后端API: http://localhost:8000
        前端仪表盘: http://localhost:3000
        
        按 Ctrl+C 停止所有服务
        
    ============================================================
    """)
    
    # 检查依赖
    try:
        import fastapi
        import dash
        import plotly
        print("✅ 所有依赖已安装")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return
    
    # 启动FastAPI后端（在后台线程中）
    fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
    fastapi_thread.start()
    
    # 等待FastAPI启动
    print("⏳ 等待FastAPI服务启动...")
    time.sleep(3)
    
    # 启动Dash前端
    try:
        run_dash()
    except KeyboardInterrupt:
        print("\n🛑 正在停止所有服务...")
        sys.exit(0)

if __name__ == "__main__":
    main()
