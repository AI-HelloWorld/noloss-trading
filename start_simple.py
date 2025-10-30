#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化启动脚本 - 专注于DEEPSEEK和ASTER API
"""
import asyncio
import sys
from loguru import logger
from backend.database import init_db, get_db
from backend.trading.trading_engine import trading_engine
from backend.config import settings

# 配置日志
logger.remove()
logger.add(sys.stdout, colorize=True, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>")

async def main():
    """主函数"""
    print("=" * 60)
    print("AI加密货币交易平台 - 简化版")
    print("专注于DEEPSEEK和ASTER API集成")
    print("=" * 60)
    
    # 检查API配置
    print("\n检查API配置...")
    if not settings.deepseek_api_key or settings.deepseek_api_key == "your_deepseek_api_key_here":
        print("DEEPSEEK API密钥未配置，将使用模拟模式")
    else:
        print("DEEPSEEK API密钥已配置")
    
    if not settings.aster_dex_api_key or settings.aster_dex_api_key == "your_aster_api_key_here":
        print("ASTER API密钥未配置，将使用模拟模式")
    else:
        print("ASTER API密钥已配置")
    
    # 初始化数据库
    print("\n初始化数据库...")
    await init_db()
    
    # 初始化交易引擎
    print("初始化交易引擎...")
    async for db in get_db():
        await trading_engine.initialize(db)
        break
    
    # 运行一个交易周期
    print("\n运行交易周期...")
    async for db in get_db():
        await trading_engine.execute_trading_cycle(db)
        
        # 显示投资组合状态
        portfolio = await trading_engine.get_portfolio_summary(db)
        print(f"\n投资组合状态:")
        print(f"  总资产: ${portfolio['total_balance']:.2f}")
        print(f"  现金: ${portfolio['cash_balance']:.2f}")
        print(f"  持仓价值: ${portfolio['positions_value']:.2f}")
        print(f"  总盈亏: ${portfolio['total_pnl']:.2f}")
        print(f"  交易次数: {portfolio['total_trades']}")
        
        if portfolio['positions']:
            print(f"\n当前持仓:")
            for pos in portfolio['positions']:
                print(f"  {pos['symbol']}: {pos['amount']:.6f} @ ${pos['average_price']:.2f} (当前: ${pos['current_price']:.2f}, 盈亏: ${pos['unrealized_pnl']:.2f})")
        
        break
    
    print("\n交易周期完成！")
    print("\n要查看完整仪表盘，请运行:")
    print("  python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000")
    print("  cd frontend && python dashboard.py")
    print("\n然后访问: http://localhost:3000")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序已停止")
    except Exception as e:
        print(f"\n错误: {e}")
        sys.exit(1)
