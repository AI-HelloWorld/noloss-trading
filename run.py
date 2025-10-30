#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
启动脚本
"""
import sys
import uvicorn
from backend.config import settings

# 确保Windows下也能正确显示
if sys.platform == 'win32':
    import os
    os.system('chcp 65001 > nul 2>&1')

if __name__ == "__main__":
    print("""
    ============================================================
    
        AI Cryptocurrency Trading Platform
        
        Starting server...
        
    ============================================================
    """)
    
    uvicorn.run(
        "backend.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug_mode,
        log_level="info"
    )

