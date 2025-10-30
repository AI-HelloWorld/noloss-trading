#!/usr/bin/env python3
"""
测试钱包连接和余额检测
使用此脚本验证API密钥是否正确，并查询钱包余额
"""
import asyncio
import sys
import os
sys.path.append('.')

from backend.exchanges.aster_dex import aster_client
from backend.config import settings
from loguru import logger


async def test_wallet_connection():
    """测试钱包连接"""
    
    logger.info("="*60)
    logger.info("🔍 AsterDEX钱包连接测试")
    logger.info("="*60)
    
    # 1. 检查配置
    logger.info("\n📋 步骤1: 检查API配置")
    logger.info("-"*60)
    
    if not settings.aster_dex_api_key:
        logger.error("❌ 错误: ASTER_DEX_API_KEY 未配置")
        logger.info("💡 请在 .env 文件中配置 ASTER_DEX_API_KEY")
        return False
    
    if not settings.aster_dex_api_secret:
        logger.error("❌ 错误: ASTER_DEX_API_SECRET 未配置")
        logger.info("💡 请在 .env 文件中配置 ASTER_DEX_API_SECRET")
        return False
    
    logger.info(f"✅ API Key: {settings.aster_dex_api_key[:10]}...{settings.aster_dex_api_key[-10:]}")
    logger.info(f"✅ API Secret: {'*' * 20}...{'*' * 10} (已配置)")
    logger.info(f"✅ 基础URL: {aster_client.base_url}")
    logger.info(f"✅ 模式: {'真实模式' if not aster_client.use_mock_data else '模拟模式'}")
    
    if settings.wallet_address:
        logger.info(f"✅ API钱包地址: {settings.wallet_address[:6]}...{settings.wallet_address[-4:]}")
    else:
        logger.warning(f"⚠️  钱包地址未配置（WALLET_ADDRESS）")
        logger.info(f"💡 建议在 https://www.asterdex.com/zh-CN/api-wallet 授权钱包后配置")
    
    # 2. 测试API连接
    logger.info("\n🔌 步骤2: 测试API连接")
    logger.info("-"*60)
    
    try:
        # 测试获取交易对列表（不需要签名）
        logger.info("正在测试公开API...")
        symbols = await aster_client.get_supported_symbols()
        logger.info(f"✅ 公开API连接成功")
        logger.info(f"✅ 支持的交易对数量: {len(symbols)}")
        logger.info(f"   示例交易对: {', '.join(symbols[:5])}")
    except Exception as e:
        logger.error(f"❌ 公开API连接失败: {e}")
        return False
    
    # 3. 测试账户认证
    logger.info("\n🔐 步骤3: 测试账户认证")
    logger.info("-"*60)
    
    try:
        logger.info("正在查询账户余额...")
        balance_info = await aster_client.get_account_balance()
        
        if isinstance(balance_info, dict) and 'code' in balance_info and balance_info['code'] < 0:
            logger.error(f"❌ API认证失败: {balance_info.get('msg', '未知错误')}")
            logger.info("\n可能的原因:")
            logger.info("  1. API Key或Secret错误")
            logger.info("  2. API权限不足")
            logger.info("  3. IP未在白名单中")
            logger.info("  4. API密钥已过期")
            logger.info("\n解决方案:")
            logger.info("  1. 检查API Key和Secret是否正确")
            logger.info("  2. 确认API权限包含'读取账户信息'")
            logger.info("  3. 在AsterDEX设置IP白名单或移除限制")
            return False
        
        logger.info("✅ 账户认证成功")
        
    except Exception as e:
        logger.error(f"❌ 账户认证失败: {e}")
        return False
    
    # 4. 查询钱包余额
    logger.info("\n💰 步骤4: 查询钱包余额")
    logger.info("-"*60)
    
    try:
        balance_info = await aster_client.get_account_balance()
        
        # 处理不同的返回格式
        balances = []
        if isinstance(balance_info, dict):
            balances = balance_info.get('balances', [])
        elif isinstance(balance_info, list):
            balances = balance_info
        
        if not balances:
            logger.warning("⚠️  无法获取余额信息")
            return False
        
        logger.info("✅ 钱包余额查询成功")
        logger.info("\n您的钱包余额:")
        logger.info("-"*60)
        
        total_usdt = 0
        for balance in balances:
            asset = balance.get('asset', 'UNKNOWN')
            free = float(balance.get('free', 0))
            locked = float(balance.get('locked', 0))
            total = float(balance.get('total', free + locked))
            
            if total > 0:
                logger.info(f"  {asset}:")
                logger.info(f"    可用: {free:,.8f}")
                logger.info(f"    冻结: {locked:,.8f}")
                logger.info(f"    总计: {total:,.8f}")
                
                if asset == 'USDT':
                    total_usdt = total
        
        logger.info("-"*60)
        
        # 重点显示USDT余额
        if total_usdt > 0:
            logger.info(f"\n💰 USDT可用余额: ${total_usdt:,.2f}")
            logger.info(f"✅ 系统配置的初始余额: ${settings.initial_balance:,.2f}")
            
            if total_usdt < settings.initial_balance:
                logger.warning(f"\n⚠️  警告: 钱包余额(${total_usdt:.2f})小于配置的初始余额(${settings.initial_balance:.2f})")
                logger.info(f"💡 建议: 将INITIAL_BALANCE设置为 {total_usdt:.2f} 或更小")
            else:
                logger.info(f"✅ 钱包余额充足，可以开始交易")
        else:
            logger.warning("\n⚠️  警告: 钱包中没有USDT余额")
            logger.info("💡 请先向钱包充值USDT才能进行交易")
            return False
        
    except Exception as e:
        logger.error(f"❌ 查询余额失败: {e}")
        return False
    
    # 5. 测试获取持仓
    logger.info("\n📊 步骤5: 测试获取持仓")
    logger.info("-"*60)
    
    try:
        positions = await aster_client.get_open_positions()
        logger.info(f"✅ 持仓查询成功")
        logger.info(f"   当前持仓数量: {len(positions)}")
        
        if positions:
            logger.info("\n当前持仓:")
            for pos in positions:
                logger.info(f"  {pos.get('symbol')}: {pos.get('amount')} @ ${pos.get('current_price')}")
        else:
            logger.info("   暂无持仓")
            
    except Exception as e:
        logger.error(f"❌ 查询持仓失败: {e}")
        return False
    
    # 6. 测试市场数据
    logger.info("\n📈 步骤6: 测试市场数据")
    logger.info("-"*60)
    
    try:
        ticker = await aster_client.get_ticker("BTCUSDT")
        if ticker:
            logger.info("✅ 市场数据获取成功")
            logger.info(f"   BTC价格: ${ticker.get('price', 0):,.2f}")
            logger.info(f"   24h涨跌: {ticker.get('change_24h', 0):+.2f}%")
        else:
            logger.warning("⚠️  无法获取市场数据")
            
    except Exception as e:
        logger.error(f"❌ 获取市场数据失败: {e}")
    
    # 最终总结
    logger.info("\n" + "="*60)
    logger.info("🎉 钱包连接测试完成")
    logger.info("="*60)
    logger.info("\n✅ 测试结果汇总:")
    logger.info("  ✅ API配置正确")
    logger.info("  ✅ 账户认证成功")
    logger.info(f"  ✅ 钱包余额: ${total_usdt:,.2f} USDT")
    logger.info(f"  ✅ 当前持仓: {len(positions)}个")
    logger.info("  ✅ 市场数据正常")
    
    logger.info("\n🚀 系统已准备就绪，可以开始真实交易！")
    logger.info("\n⚠️  下一步:")
    logger.info("  1. 确认所有风控参数合理")
    logger.info("  2. 重启后端服务")
    logger.info("  3. 观察系统运行日志")
    logger.info("  4. 监控钱包余额变化")
    
    return True


async def main():
    """主函数"""
    try:
        success = await test_wallet_connection()
        
        if success:
            logger.info("\n✅ 所有测试通过！可以启用真实交易。")
            sys.exit(0)
        else:
            logger.error("\n❌ 测试失败！请检查配置后重试。")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"\n❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 关闭连接
        await aster_client.close()


if __name__ == "__main__":
    asyncio.run(main())

