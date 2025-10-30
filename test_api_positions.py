#!/usr/bin/env python3
"""
测试API持仓接口
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import init_db, get_db, Position
from backend.exchanges.aster_dex import aster_client
from backend.main import get_portfolio, get_positions
from loguru import logger
from sqlalchemy import select

async def test_api_positions():
    """测试API持仓接口"""
    logger.info("🧪 开始测试API持仓接口...")
    
    # 初始化数据库
    await init_db()
    
    async for db in get_db():
        # 1. 先进行一些交易来创建持仓
        logger.info("💰 创建测试持仓...")
        
        # 买入BTC
        btc_order = await aster_client.place_order("BTCUSDT", "buy", "market", 0.001)
        logger.info(f"BTC买入结果: {btc_order.get('success', False)}")
        
        # 买入ETH
        eth_order = await aster_client.place_order("ETHUSDT", "buy", "market", 0.1)
        logger.info(f"ETH买入结果: {eth_order.get('success', False)}")
        
        # 2. 同步持仓到数据库
        logger.info("🔄 同步持仓到数据库...")
        exchange_positions = await aster_client.get_open_positions()
        
        for pos in exchange_positions:
            new_pos = Position(
                symbol=pos['symbol'],
                amount=pos['amount'],
                average_price=pos['average_price'],
                current_price=pos['current_price'],
                unrealized_pnl=pos['unrealized_pnl'],
                position_type=pos.get('position_type', 'long')
            )
            db.add(new_pos)
        
        await db.commit()
        
        # 3. 测试get_portfolio API
        logger.info("📊 测试get_portfolio API...")
        portfolio_data = await get_portfolio(db)
        logger.info(f"投资组合数据:")
        logger.info(f"  总资产: ${portfolio_data['total_balance']:.2f}")
        logger.info(f"  现金余额: ${portfolio_data['cash_balance']:.2f}")
        logger.info(f"  持仓价值: ${portfolio_data['positions_value']:.2f}")
        logger.info(f"  持仓数量: {len(portfolio_data['positions'])}")
        
        for pos in portfolio_data['positions']:
            logger.info(f"    - {pos['symbol']}: {pos['amount']:.6f} @ ${pos['current_price']:.2f}")
        
        # 4. 测试get_positions API
        logger.info("📈 测试get_positions API...")
        positions_data = await get_positions(db)
        logger.info(f"持仓分布数据:")
        
        for pos in positions_data:
            logger.info(f"  - {pos['symbol']}: {pos['size_pct']:.2f}% (${pos['value_usd']:.2f})")
        
        # 5. 模拟部分卖出，测试持仓更新
        logger.info("💸 模拟部分卖出...")
        if len(exchange_positions) > 0:
            sell_symbol = exchange_positions[0]['symbol']
            sell_amount = exchange_positions[0]['amount'] * 0.3  # 卖出30%
            
            sell_result = await aster_client.place_order(sell_symbol, "sell", "market", sell_amount)
            logger.info(f"卖出结果: {sell_result.get('success', False)}")
            
            if sell_result.get('success'):
                # 更新数据库持仓
                updated_positions = await aster_client.get_open_positions()
                
                # 获取数据库中的持仓记录
                db_result = await db.execute(select(Position))
                db_positions_dict = {p.symbol: p for p in db_result.scalars().all()}
                
                # 更新数据库中的持仓
                for pos in updated_positions:
                    symbol = pos['symbol']
                    if symbol in db_positions_dict:
                        db_pos = db_positions_dict[symbol]
                        db_pos.amount = pos['amount']
                        db_pos.current_price = pos['current_price']
                        db_pos.unrealized_pnl = pos['unrealized_pnl']
                
                # 删除已平仓的持仓
                current_symbols = {p['symbol'] for p in updated_positions}
                for symbol, db_pos in db_positions_dict.items():
                    if symbol not in current_symbols:
                        db.delete(db_pos)
                
                await db.commit()
                
                # 再次测试API
                logger.info("📊 卖出后测试API...")
                updated_portfolio = await get_portfolio(db)
                updated_positions_api = await get_positions(db)
                
                logger.info(f"更新后投资组合:")
                logger.info(f"  总资产: ${updated_portfolio['total_balance']:.2f}")
                logger.info(f"  持仓价值: ${updated_portfolio['positions_value']:.2f}")
                logger.info(f"  持仓数量: {len(updated_portfolio['positions'])}")
                
                logger.info(f"更新后持仓分布:")
                for pos in updated_positions_api:
                    logger.info(f"  - {pos['symbol']}: {pos['size_pct']:.2f}% (${pos['value_usd']:.2f})")
        
        break
    
    logger.info("✅ API持仓接口测试完成!")

if __name__ == "__main__":
    asyncio.run(test_api_positions())
