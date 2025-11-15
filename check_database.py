#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库状态
"""

import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

def check_database():
    try:
        conn = sqlite3.connect('trading_platform.db')
        cursor = conn.cursor()
        
        # 检查表结构
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("📊 数据库表:", [table[0] for table in tables])
        
        # 检查交易记录
        cursor.execute("SELECT COUNT(*) FROM trades")
        trade_count = cursor.fetchone()[0]
        print(f"📈 交易记录数: {trade_count}")
        
        # 检查持仓记录
        cursor.execute("SELECT COUNT(*) FROM positions")
        pos_count = cursor.fetchone()[0]
        print(f"💼 持仓记录数: {pos_count}")
        
        # 检查最新的交易记录
        cursor.execute("SELECT * FROM trades ORDER BY timestamp DESC LIMIT 3")
        recent_trades = cursor.fetchall()
        print(f"🔄 最新交易记录: {len(recent_trades)} 条")
        for trade in recent_trades:
            print(f"  - {trade}")
        
        # 检查最新的持仓记录
        cursor.execute("SELECT * FROM positions ORDER BY created_at DESC LIMIT 3")
        recent_positions = cursor.fetchall()
        print(f"💼 最新持仓记录: {len(recent_positions)} 条")
        for pos in recent_positions:
            print(f"  - {pos}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        return False

if __name__ == "__main__":
    check_database()
