#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动测试交易功能
"""

import sys
import asyncio
import sqlite3
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')

from backend.trading.trading_engine import trading_engine
from backend.database import get_db

async def manual_trade_test():
    print("🧪 手动测试交易功能...")
    
    # 获取数据库连接
    async for db in get_db():
        try:
            # 初始化交易引擎
            await trading_engine.initialize(db)
            print(f"💰 初始余额: ${trading_engine.current_balance:.2f}")
            
            # 手动执行一次交易周期
            print("\n📊 执行交易周期...")
            await trading_engine.execute_trading_cycle(db)
            
            # 等待一下让交易完成
            await asyncio.sleep(2)
            
            # 检查结果
            print("\n📈 检查交易结果...")
            
            # 检查数据库
            conn = sqlite3.connect('trading_platform.db')
            cursor = conn.cursor()
            
            # 检查交易记录
            cursor.execute("SELECT COUNT(*) FROM trades")
            trade_count = cursor.fetchone()[0]
            print(f"📈 交易记录数: {trade_count}")
            
            # 检查持仓记录
            cursor.execute("SELECT COUNT(*) FROM positions")
            pos_count = cursor.fetchone()[0]
            print(f"💼 持仓记录数: {pos_count}")
            
            # 检查最新的投资组合快照
            cursor.execute("SELECT * FROM portfolio_snapshots ORDER BY timestamp DESC LIMIT 1")
            latest_snapshot = cursor.fetchone()
            if latest_snapshot:
                print(f"📊 最新投资组合快照:")
                print(f"  - 时间: {latest_snapshot[1]}")
                print(f"  - 总资产: ${latest_snapshot[2]:.2f}")
                print(f"  - 现金余额: ${latest_snapshot[3]:.2f}")
                print(f"  - 持仓价值: ${latest_snapshot[4]:.2f}")
                print(f"  - 总盈亏: ${latest_snapshot[5]:.2f}")
            
            # 检查持仓详情
            if pos_count > 0:
                cursor.execute("SELECT * FROM positions")
                positions = cursor.fetchall()
                print(f"💼 持仓详情:")
                for pos in positions:
                    print(f"  - {pos[1]}: {pos[2]:.4f} @ ${pos[4]:.2f} (盈亏: ${pos[5]:.2f})")
            
            conn.close()
            
            # 获取投资组合摘要
            portfolio = await trading_engine.get_portfolio_summary(db)
            print(f"\n💼 投资组合摘要:")
            print(f"  - 总资产: ${portfolio['total_balance']:.2f}")
            print(f"  - 现金余额: ${portfolio['cash_balance']:.2f}")
            print(f"  - 持仓价值: ${portfolio['positions_value']:.2f}")
            print(f"  - 总盈亏: ${portfolio['total_pnl']:.2f}")
            print(f"  - 持仓数量: {len(portfolio['positions'])}")
            
            break
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            break

if __name__ == "__main__":
    asyncio.run(manual_trade_test())
