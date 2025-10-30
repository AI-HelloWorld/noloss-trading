#!/usr/bin/env python3
"""
测试盈亏计算修复
"""
import asyncio
import sys
import os
from datetime import datetime
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import init_db, get_db, Trade, Position, PortfolioSnapshot
from backend.config import settings
from backend.trading.trading_engine import trading_engine
from loguru import logger

async def test_pnl_calculation():
    """测试盈亏计算"""
    logger.info("🧪 开始测试盈亏计算...")
    
    # 初始化数据库
    await init_db()
    
    async for db in get_db():
        try:
            # 1. 获取当前投资组合摘要
            portfolio_summary = await trading_engine.get_portfolio_summary(db)
            
            logger.info("📊 当前投资组合状态:")
            logger.info(f"  总余额: ${portfolio_summary['total_balance']:.2f}")
            logger.info(f"  现金余额: ${portfolio_summary['cash_balance']:.2f}")
            logger.info(f"  持仓价值: ${portfolio_summary['positions_value']:.2f}")
            logger.info(f"  总盈亏: ${portfolio_summary['total_pnl']:.2f}")
            logger.info(f"  盈亏百分比: {portfolio_summary['total_pnl_percentage']:+.2f}%")
            logger.info(f"  初始余额: ${portfolio_summary['initial_balance']:.2f}")
            logger.info(f"  总交易次数: {portfolio_summary['total_trades']}")
            logger.info(f"  胜率: {portfolio_summary['win_rate']*100:.1f}%")
            
            # 2. 验证计算逻辑
            initial_balance = portfolio_summary['initial_balance']
            total_pnl = portfolio_summary['total_pnl']
            total_balance = portfolio_summary['total_balance']
            positions_value = portfolio_summary['positions_value']
            cash_balance = portfolio_summary['cash_balance']
            
            # 验证总余额计算
            expected_total_balance = initial_balance + total_pnl
            balance_correct = abs(total_balance - expected_total_balance) < 0.01
            
            # 验证现金余额计算
            expected_cash_balance = total_balance - positions_value
            cash_correct = abs(cash_balance - expected_cash_balance) < 0.01
            
            # 验证盈亏百分比计算
            expected_pnl_percentage = (total_pnl / initial_balance * 100) if initial_balance > 0 else 0
            pnl_percentage_correct = abs(portfolio_summary['total_pnl_percentage'] - expected_pnl_percentage) < 0.01
            
            logger.info("\n🔍 验证结果:")
            logger.info(f"  总余额计算: {'✅ 正确' if balance_correct else '❌ 错误'}")
            logger.info(f"  现金余额计算: {'✅ 正确' if cash_correct else '❌ 错误'}")
            logger.info(f"  盈亏百分比计算: {'✅ 正确' if pnl_percentage_correct else '❌ 错误'}")
            
            if balance_correct and cash_correct and pnl_percentage_correct:
                logger.info("🎉 所有计算都正确！")
            else:
                logger.warning("⚠️ 部分计算可能有问题")
            
            # 3. 检查是否有交易记录
            trade_result = await db.execute(select(Trade))
            trades = trade_result.scalars().all()
            logger.info(f"\n📈 交易记录: {len(trades)} 笔")
            
            if trades:
                total_realized_pnl = sum(trade.profit_loss for trade in trades if trade.profit_loss is not None)
                logger.info(f"  已实现盈亏: ${total_realized_pnl:.2f}")
            
            # 4. 检查持仓记录
            position_result = await db.execute(select(Position))
            positions = position_result.scalars().all()
            logger.info(f"\n💼 持仓记录: {len(positions)} 个")
            
            if positions:
                total_unrealized_pnl = sum(pos.unrealized_pnl for pos in positions if pos.unrealized_pnl is not None)
                logger.info(f"  未实现盈亏: ${total_unrealized_pnl:.2f}")
            
            # 5. 检查最新的投资组合快照
            snapshot_result = await db.execute(
                select(PortfolioSnapshot).order_by(desc(PortfolioSnapshot.timestamp)).limit(1)
            )
            latest_snapshot = snapshot_result.scalar_one_or_none()
            
            if latest_snapshot:
                logger.info(f"\n📸 最新快照:")
                logger.info(f"  时间: {latest_snapshot.timestamp}")
                logger.info(f"  总余额: ${latest_snapshot.total_balance:.2f}")
                logger.info(f"  总盈亏: ${latest_snapshot.total_profit_loss:.2f}")
                logger.info(f"  盈亏百分比: {latest_snapshot.total_pnl_percentage:+.2f}%")
            
        except Exception as e:
            logger.error(f"❌ 测试过程中出现错误: {e}")
        finally:
            break

if __name__ == "__main__":
    print("开始测试盈亏计算修复...")
    asyncio.run(test_pnl_calculation())
    print("\n测试完成！")
