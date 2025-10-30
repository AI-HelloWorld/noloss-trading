#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模拟交易测试脚本
运行几轮交易周期，测试AI策略是否能自主交易
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
logger.add("logs/test_trading_{time}.log", rotation="10 MB")


async def run_trading_cycles(num_cycles: int = 5):
    """运行指定次数的交易周期"""
    logger.info(f"🚀 开始运行模拟交易测试 - 初始余额: ${settings.initial_balance}")
    logger.info(f"📊 将运行 {num_cycles} 个交易周期")
    
    # 初始化数据库
    await init_db()
    
    # 初始化交易引擎
    async for db in get_db():
        await trading_engine.initialize(db)
        break
    
    # 运行交易周期
    for cycle in range(1, num_cycles + 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"🔄 交易周期 {cycle}/{num_cycles}")
        logger.info(f"{'='*60}")
        
        async for db in get_db():
            # 执行交易周期
            await trading_engine.execute_trading_cycle(db)
            
            # 显示投资组合状态
            portfolio = await trading_engine.get_portfolio_summary(db)
            logger.info(f"\n📈 投资组合状态:")
            logger.info(f"  总资产: ${portfolio['total_balance']:.2f}")
            logger.info(f"  现金: ${portfolio['cash_balance']:.2f}")
            logger.info(f"  持仓价值: ${portfolio['positions_value']:.2f}")
            logger.info(f"  总盈亏: ${portfolio['total_pnl']:.2f}")
            logger.info(f"  交易次数: {portfolio['total_trades']}")
            logger.info(f"  胜率: {portfolio['win_rate']*100:.1f}%")
            
            if portfolio['positions']:
                logger.info(f"\n💼 当前持仓:")
                for pos in portfolio['positions']:
                    logger.info(f"  {pos['symbol']}: {pos['amount']:.6f} @ ${pos['average_price']:.2f} (当前: ${pos['current_price']:.2f}, 盈亏: ${pos['unrealized_pnl']:.2f})")
            
            break
        
        # 等待一下再进行下一个周期
        if cycle < num_cycles:
            await asyncio.sleep(2)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"✅ 模拟交易测试完成！")
    logger.info(f"{'='*60}")
    
    # 最终总结
    async for db in get_db():
        final_portfolio = await trading_engine.get_portfolio_summary(db)
        
        initial_balance = settings.initial_balance
        final_balance = final_portfolio['total_balance']
        profit = final_balance - initial_balance
        profit_percent = (profit / initial_balance) * 100
        
        logger.info(f"\n📊 最终统计:")
        logger.info(f"  初始资金: ${initial_balance:.2f}")
        logger.info(f"  最终资产: ${final_balance:.2f}")
        logger.info(f"  总盈亏: ${profit:.2f} ({profit_percent:+.2f}%)")
        logger.info(f"  总交易次数: {final_portfolio['total_trades']}")
        logger.info(f"  胜率: {final_portfolio['win_rate']*100:.1f}%")
        
        break


if __name__ == "__main__":
    # 运行5个交易周期进行测试
    asyncio.run(run_trading_cycles(num_cycles=5))

