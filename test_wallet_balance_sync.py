"""
测试钱包余额同步 - 验证所有余额数据是否跟随实时钱包
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.exchanges.aster_dex import aster_client
from backend.trading.trading_engine import trading_engine
from backend.database import get_db
from loguru import logger


async def test_wallet_balance_sync():
    """测试钱包余额同步"""
    logger.info("="*80)
    logger.info("🧪 开始测试钱包余额同步")
    logger.info("="*80)
    
    # 测试1: 直接查询钱包API
    logger.info("\n📊 测试1: 直接查询AsterDEX钱包API")
    logger.info("-"*80)
    balance_info = await aster_client.get_account_balance()
    logger.info(f"API返回结果: {balance_info}")
    
    if balance_info.get('success'):
        balances = balance_info.get('balances', [])
        usdt_balance = next((b for b in balances if b.get('asset') == 'USDT'), None)
        if usdt_balance:
            logger.info(f"✅ USDT余额: {usdt_balance}")
            logger.info(f"   可用余额: {usdt_balance.get('free', 0)} USDT")
            logger.info(f"   锁定余额: {usdt_balance.get('locked', 0)} USDT")
            logger.info(f"   总余额: {usdt_balance.get('total', 0)} USDT")
        else:
            logger.warning("⚠️  未找到USDT余额")
    else:
        logger.error("❌ 获取余额失败")
    
    # 测试2: 通过trading_engine获取余额
    logger.info("\n📊 测试2: 通过trading_engine获取投资组合摘要")
    logger.info("-"*80)
    async for db in get_db():
        portfolio = await trading_engine.get_portfolio_summary(db)
        logger.info(f"投资组合摘要:")
        logger.info(f"   总资产: ${portfolio.get('total_balance', 0):.2f}")
        logger.info(f"   现金余额: ${portfolio.get('cash_balance', 0):.2f}")
        logger.info(f"   持仓价值: ${portfolio.get('positions_value', 0):.2f}")
        logger.info(f"   总盈亏: ${portfolio.get('total_pnl', 0):.2f}")
        logger.info(f"   盈亏百分比: {portfolio.get('total_pnl_percentage', 0):+.2f}%")
        logger.info(f"   持仓数量: {len(portfolio.get('positions', []))}")
        break
    
    # 测试3: 获取持仓信息
    logger.info("\n📊 测试3: 获取持仓信息")
    logger.info("-"*80)
    positions = await aster_client.get_open_positions()
    if positions:
        logger.info(f"✅ 当前持仓: {len(positions)}个")
        for pos in positions:
            logger.info(f"   {pos.get('symbol')}: {pos.get('amount')} @ ${pos.get('current_price'):.2f}")
            logger.info(f"      未实现盈亏: ${pos.get('unrealized_pnl', 0):.2f}")
    else:
        logger.info("ℹ️  当前无持仓")
    
    # 测试4: 验证余额一致性
    logger.info("\n📊 测试4: 验证余额一致性")
    logger.info("-"*80)
    if balance_info.get('success') and usdt_balance:
        wallet_total = usdt_balance.get('free', 0) + usdt_balance.get('locked', 0)
        positions_value = sum(p.get('amount', 0) * p.get('current_price', 0) for p in positions)
        calculated_total = wallet_total + positions_value
        
        logger.info(f"钱包USDT余额: ${wallet_total:.2f}")
        logger.info(f"持仓价值: ${positions_value:.2f}")
        logger.info(f"计算总资产: ${calculated_total:.2f}")
        logger.info(f"系统显示总资产: ${portfolio.get('total_balance', 0):.2f}")
        
        diff = abs(calculated_total - portfolio.get('total_balance', 0))
        if diff < 0.01:  # 允许0.01的误差
            logger.info("✅ 余额一致性验证通过！")
        else:
            logger.warning(f"⚠️  余额差异: ${diff:.2f}")
    
    # 测试5: 多次查询验证实时性
    logger.info("\n📊 测试5: 多次查询验证实时性（连续3次）")
    logger.info("-"*80)
    for i in range(3):
        logger.info(f"\n第{i+1}次查询:")
        async for db in get_db():
            portfolio = await trading_engine.get_portfolio_summary(db)
            logger.info(f"   总资产: ${portfolio.get('total_balance', 0):.2f}")
            logger.info(f"   现金余额: ${portfolio.get('cash_balance', 0):.2f}")
            break
        await asyncio.sleep(1)
    
    logger.info("\n" + "="*80)
    logger.info("✅ 钱包余额同步测试完成！")
    logger.info("="*80)
    
    # 关闭连接
    await aster_client.close()


if __name__ == "__main__":
    logger.info("🚀 启动钱包余额同步测试...")
    asyncio.run(test_wallet_balance_sync())

