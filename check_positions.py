#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查持仓表结构
"""

import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

def check_positions():
    try:
        conn = sqlite3.connect('trading_platform.db')
        cursor = conn.cursor()
        
        # 检查positions表结构
        cursor.execute("PRAGMA table_info(positions)")
        columns = cursor.fetchall()
        print("📊 positions表结构:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # 检查持仓记录
        cursor.execute("SELECT * FROM positions LIMIT 5")
        positions = cursor.fetchall()
        print(f"\n💼 持仓记录: {len(positions)} 条")
        for pos in positions:
            print(f"  - {pos}")
        
        # 检查投资组合快照
        cursor.execute("SELECT * FROM portfolio_snapshots ORDER BY timestamp DESC LIMIT 3")
        snapshots = cursor.fetchall()
        print(f"\n📈 投资组合快照: {len(snapshots)} 条")
        for snap in snapshots:
            print(f"  - {snap}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

if __name__ == "__main__":
    check_positions()
