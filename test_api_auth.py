"""
AsterDEX API 认证测试脚本
测试标准API和专业API两种认证方式
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.exchanges.aster_dex import aster_client
from backend.config import settings
from loguru import logger


async def test_api_authentication():
    """测试API认证和余额查询"""
    logger.info("="*80)
    logger.info("🧪 AsterDEX API 认证测试")
    logger.info("="*80)
    
    # 显示当前配置
    logger.info("\n📋 当前配置:")
    logger.info("-"*80)
    logger.info(f"使用模拟数据: {aster_client.use_mock_data}")
    logger.info(f"Base URL: {aster_client.base_url}")
    if settings.aster_dex_api_key:
        logger.info(f"API Key: {settings.aster_dex_api_key[:20]}..." if len(settings.aster_dex_api_key) > 20 else f"API Key: {settings.aster_dex_api_key}")
    if settings.aster_dex_api_secret:
        logger.info(f"API Secret: {'*' * len(settings.aster_dex_api_secret)}")
    if settings.wallet_address:
        logger.info(f"钱包地址: {settings.wallet_address}")
    
    # 测试1: 获取交易对信息（公开API，无需签名）
    logger.info("\n" + "="*80)
    logger.info("📊 测试1: 获取交易对信息（公开API）")
    logger.info("-"*80)
    try:
        symbols = await aster_client.get_supported_symbols()
        if symbols:
            logger.info(f"✅ 成功获取{len(symbols)}个交易对")
            logger.info(f"前10个交易对: {symbols[:10]}")
        else:
            logger.warning("⚠️  未获取到交易对")
    except Exception as e:
        logger.error(f"❌ 获取交易对失败: {e}")
    
    # 测试2: 获取市场行情（公开API，无需签名）
    logger.info("\n" + "="*80)
    logger.info("📊 测试2: 获取市场行情（公开API）")
    logger.info("-"*80)
    try:
        ticker = await aster_client.get_ticker("BTCUSDT")
        if ticker and ticker.get('price'):
            logger.info(f"✅ 成功获取BTC行情")
            logger.info(f"   价格: ${ticker.get('price', 0):,.2f}")
            logger.info(f"   24h涨跌: {ticker.get('change_24h', 0):+.2f}%")
            logger.info(f"   24h成交量: ${ticker.get('volume_24h', 0):,.0f}")
        else:
            logger.warning("⚠️  未获取到行情数据")
    except Exception as e:
        logger.error(f"❌ 获取行情失败: {e}")
    
    # 测试3: 获取账户余额（私有API，需要签名）⭐ 关键测试
    logger.info("\n" + "="*80)
    logger.info("📊 测试3: 获取账户余额（私有API）⭐ 关键测试")
    logger.info("-"*80)
    try:
        balance_info = await aster_client.get_account_balance()
        
        if balance_info.get('success'):
            balances = balance_info.get('balances', [])
            logger.info(f"✅ 成功获取钱包余额！")
            logger.info(f"   共{len(balances)}项资产")
            
            # 显示所有非零余额
            for b in balances:
                if float(b.get('free', 0)) > 0 or float(b.get('locked', 0)) > 0:
                    logger.info(f"   {b.get('asset')}: 可用={b.get('free', 0)}, 锁定={b.get('locked', 0)}, 总计={b.get('total', 0)}")
            
            # 重点显示USDT余额
            usdt = next((b for b in balances if b.get('asset') == 'USDT'), None)
            if usdt:
                logger.info(f"\n💰 USDT余额详情:")
                logger.info(f"   可用余额: {usdt.get('free', 0)} USDT")
                logger.info(f"   锁定余额: {usdt.get('locked', 0)} USDT")
                logger.info(f"   总余额: {usdt.get('total', 0)} USDT")
            else:
                logger.warning("⚠️  未找到USDT余额")
        else:
            error = balance_info.get('error', '未知错误')
            logger.error(f"❌ 获取余额失败: {error}")
            
    except Exception as e:
        logger.error(f"❌ 获取余额异常: {e}")
    
    # 测试4: 获取持仓信息（私有API，需要签名）
    logger.info("\n" + "="*80)
    logger.info("📊 测试4: 获取持仓信息（私有API）")
    logger.info("-"*80)
    try:
        positions = await aster_client.get_open_positions()
        
        if positions:
            logger.info(f"✅ 成功获取持仓信息！")
            logger.info(f"   当前持仓数量: {len(positions)}")
            for pos in positions:
                logger.info(f"   {pos.get('symbol')}: 数量={pos.get('positionAmt', 0)}, 入场价={pos.get('entryPrice', 0)}")
        else:
            logger.info("ℹ️  当前无持仓（或获取失败）")
            
    except Exception as e:
        logger.error(f"❌ 获取持仓异常: {e}")
    
    # 测试总结
    logger.info("\n" + "="*80)
    logger.info("📊 测试总结")
    logger.info("="*80)
    
    if aster_client.use_mock_data:
        logger.warning("⚠️  系统运行在模拟模式")
        logger.info("\n要启用真实交易，请配置：")
        logger.info("    ASTER_DEX_API_KEY=你的API密钥")
        logger.info("    ASTER_DEX_API_SECRET=你的API密钥Secret")
        logger.info("    WALLET_ADDRESS=你的钱包地址（可选）")
    else:
        logger.info(f"✅ 使用官方SDK认证")
        logger.info("\n如果上述测试3和测试4失败，可能原因：")
        logger.info("  1. API密钥权限不足（需要余额查询和持仓查询权限）")
        logger.info("  2. API密钥格式不正确")
        logger.info("  3. 网络连接问题")
        logger.info("\n请检查AsterDEX后台的API密钥设置！")
    
    logger.info("="*80)
    
    # 关闭连接
    await aster_client.close()


if __name__ == "__main__":
    logger.info("🚀 启动API认证测试...")
    asyncio.run(test_api_authentication())

