#!/usr/bin/env python3
"""
重置盈亏计算 - 修复总盈亏计算问题
"""
import asyncio
import sys
import os
from datetime import datetime
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import init_db, get_db, Trade, Position, PortfolioSnapshot
from backend.config import settings
from loguru import logger

async def reset_pnl_calculation():
    """重置盈亏计算"""
    logger.info("🔄 开始重置盈亏计算...")
    
    # 初始化数据库
    await init_db()
    
    async for db in get_db():
        try:
            # 1. 获取所有交易记录
            result = await db.execute(select(Trade).order_by(Trade.timestamp))
            trades = result.scalars().all()
            
            logger.info(f"📊 找到 {len(trades)} 笔交易记录")
            
            # 2. 计算实际的总盈亏（基于交易记录）
            total_realized_pnl = 0.0
            total_trades = 0
            winning_trades = 0
            
            for trade in trades:
                if trade.profit_loss is not None:
                    total_realized_pnl += trade.profit_loss
                    total_trades += 1
                    if trade.profit_loss > 0:
                        winning_trades += 1
            
            # 3. 获取当前持仓的未实现盈亏
            result = await db.execute(select(Position))
            positions = result.scalars().all()
            
            total_unrealized_pnl = 0.0
            total_positions_value = 0.0
            
            for position in positions:
                if position.unrealized_pnl is not None:
                    total_unrealized_pnl += position.unrealized_pnl
                total_positions_value += position.amount * position.current_price
            
            # 4. 计算正确的总盈亏
            correct_total_pnl = total_realized_pnl + total_unrealized_pnl
            correct_total_balance = settings.initial_balance + correct_total_pnl
            correct_cash_balance = correct_total_balance - total_positions_value
            
            # 5. 计算盈亏百分比
            correct_pnl_percentage = (correct_total_pnl / settings.initial_balance * 100) if settings.initial_balance > 0 else 0
            win_rate = (winning_trades / total_trades) if total_trades > 0 else 0
            
            logger.info(f"💰 计算结果显示:")
            logger.info(f"  初始余额: ${settings.initial_balance:.2f}")
            logger.info(f"  已实现盈亏: ${total_realized_pnl:.2f}")
            logger.info(f"  未实现盈亏: ${total_unrealized_pnl:.2f}")
            logger.info(f"  总盈亏: ${correct_total_pnl:.2f}")
            logger.info(f"  正确总余额: ${correct_total_balance:.2f}")
            logger.info(f"  持仓价值: ${total_positions_value:.2f}")
            logger.info(f"  现金余额: ${correct_cash_balance:.2f}")
            logger.info(f"  盈亏百分比: {correct_pnl_percentage:+.2f}%")
            logger.info(f"  总交易次数: {total_trades}")
            logger.info(f"  胜率: {win_rate*100:.1f}%")
            
            # 6. 创建新的投资组合快照
            new_snapshot = PortfolioSnapshot(
                timestamp=datetime.now(),
                total_balance=correct_total_balance,
                cash_balance=correct_cash_balance,
                positions_value=total_positions_value,
                total_profit_loss=correct_total_pnl,
                total_pnl_percentage=correct_pnl_percentage,
                daily_profit_loss=0.0,  # 重置每日盈亏
                total_trades=total_trades,
                win_rate=win_rate
            )
            
            db.add(new_snapshot)
            await db.commit()
            
            logger.info("✅ 新的投资组合快照已创建")
            
            # 7. 更新交易引擎的状态（如果存在）
            try:
                from backend.trading.trading_engine import trading_engine
                trading_engine.current_balance = correct_total_balance
                trading_engine.total_pnl = correct_total_pnl
                trading_engine.trade_count = total_trades
                trading_engine.winning_trades = winning_trades
                logger.info("✅ 交易引擎状态已更新")
            except Exception as e:
                logger.warning(f"⚠️ 无法更新交易引擎状态: {e}")
            
            logger.info("🎉 盈亏计算重置完成！")
            
        except Exception as e:
            logger.error(f"❌ 重置过程中出现错误: {e}")
            await db.rollback()
        finally:
            break

async def verify_calculation():
    """验证计算是否正确"""
    logger.info("🔍 验证计算结果...")
    
    async for db in get_db():
        try:
            # 获取最新的投资组合快照
            result = await db.execute(
                select(PortfolioSnapshot).order_by(desc(PortfolioSnapshot.timestamp)).limit(1)
            )
            latest_snapshot = result.scalar_one_or_none()
            
            if latest_snapshot:
                logger.info(f"📊 最新快照验证:")
                logger.info(f"  总余额: ${latest_snapshot.total_balance:.2f}")
                logger.info(f"  现金余额: ${latest_snapshot.cash_balance:.2f}")
                logger.info(f"  持仓价值: ${latest_snapshot.positions_value:.2f}")
                logger.info(f"  总盈亏: ${latest_snapshot.total_profit_loss:.2f}")
                logger.info(f"  盈亏百分比: {latest_snapshot.total_pnl_percentage:+.2f}%")
                
                # 验证计算是否正确
                expected_balance = settings.initial_balance + latest_snapshot.total_profit_loss
                expected_cash = latest_snapshot.total_balance - latest_snapshot.positions_value
                
                balance_correct = abs(latest_snapshot.total_balance - expected_balance) < 0.01
                cash_correct = abs(latest_snapshot.cash_balance - expected_cash) < 0.01
                
                if balance_correct and cash_correct:
                    logger.info("✅ 计算验证通过！")
                else:
                    logger.warning("⚠️ 计算验证失败，可能需要重新计算")
            else:
                logger.warning("⚠️ 未找到投资组合快照")
                
        except Exception as e:
            logger.error(f"❌ 验证过程中出现错误: {e}")
        finally:
            break

if __name__ == "__main__":
    print("开始重置盈亏计算...")
    asyncio.run(reset_pnl_calculation())
    print("\n验证计算结果...")
    asyncio.run(verify_calculation())
    print("\n重置完成！请重启后端服务以应用更改。")
