"""
测试 AsterDEX 官方SDK集成
"""
import asyncio
from loguru import logger
from backend.exchanges.aster_dex import aster_client

async def test_sdk():
    """测试官方SDK功能"""
    
    logger.info("=" * 60)
    logger.info("AsterDEX 官方SDK 集成测试")
    logger.info("=" * 60)
    
    # 1. 测试账户余额查询
    logger.info("\n📊 测试1：查询账户余额")
    logger.info("-" * 60)
    try:
        balance = await aster_client.get_account_balance()
        if balance.get('success'):
            logger.success("✅ 账户余额查询成功")
            balances = balance.get('balances', [])
            logger.info(f"   资产数量: {len(balances)}")
            
            # 显示USDT余额
            usdt_balance = next((b for b in balances if b.get('asset') == 'USDT'), None)
            if usdt_balance:
                free = float(usdt_balance.get('free', 0))
                locked = float(usdt_balance.get('locked', 0))
                total = free + locked
                logger.info(f"   💵 USDT余额: 可用={free:.2f}, 锁定={locked:.2f}, 总计={total:.2f}")
        else:
            logger.error(f"❌ 账户余额查询失败: {balance.get('error')}")
    except Exception as e:
        logger.error(f"❌ 账户余额查询异常: {e}")
    
    # 2. 测试行情查询
    logger.info("\n📈 测试2：查询BTC行情")
    logger.info("-" * 60)
    try:
        ticker = await aster_client.get_ticker("BTCUSDT")
        if ticker:
            logger.success("✅ BTC行情查询成功")
            logger.info(f"   价格: ${ticker.get('price', 0):,.2f}")
            logger.info(f"   24h涨跌: {ticker.get('change_24h', 0):.2f}%")
            logger.info(f"   24h最高: ${ticker.get('high_24h', 0):,.2f}")
            logger.info(f"   24h最低: ${ticker.get('low_24h', 0):,.2f}")
        else:
            logger.error("❌ BTC行情查询失败")
    except Exception as e:
        logger.error(f"❌ BTC行情查询异常: {e}")
    
    # 3. 测试持仓查询
    logger.info("\n📊 测试3：查询持仓信息")
    logger.info("-" * 60)
    try:
        positions = await aster_client.get_open_positions()
        logger.success(f"✅ 持仓查询成功")
        if positions:
            logger.info(f"   持仓数量: {len(positions)}")
            for pos in positions:
                logger.info(f"   {pos['symbol']}: {pos['amount']:.6f} @ ${pos['average_price']:.2f}")
                logger.info(f"      未实现盈亏: ${pos['unrealized_pnl']:.2f}")
        else:
            logger.info("   当前无持仓")
    except Exception as e:
        logger.error(f"❌ 持仓查询异常: {e}")
    
    # 4. 测试支持的交易对
    logger.info("\n📋 测试4：查询支持的交易对")
    logger.info("-" * 60)
    try:
        symbols = await aster_client.get_supported_symbols()
        logger.success(f"✅ 交易对查询成功")
        logger.info(f"   支持的交易对数量: {len(symbols)}")
        logger.info(f"   前10个交易对: {symbols[:10]}")
    except Exception as e:
        logger.error(f"❌ 交易对查询异常: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("测试完成")
    logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_sdk())

