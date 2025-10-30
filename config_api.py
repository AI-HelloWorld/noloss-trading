#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API配置测试脚本
专门用于测试DEEPSEEK和ASTER API连接
"""
import asyncio
import aiohttp
import json
from backend.config import settings
from backend.ai.deepseek_model import DeepSeekModel
from backend.exchanges.aster_dex import aster_client

async def test_deepseek_api():
    """测试DEEPSEEK API"""
    print("=" * 50)
    print("测试DEEPSEEK API")
    print("=" * 50)
    
    if not settings.deepseek_api_key:
        print("DEEPSEEK API密钥未配置")
        return False
    
    print(f"API密钥已配置: {settings.deepseek_api_key[:10]}...")
    
    # 创建DeepSeek模型实例
    deepseek = DeepSeekModel()
    
    # 测试市场分析
    market_data = {
        "price": 50000.0,
        "volume_24h": 1000000,
        "change_24h": 2.5,
        "high_24h": 51000,
        "low_24h": 49000
    }
    
    try:
        result = await deepseek.analyze_market(
            symbol="BTC/USDT",
            market_data=market_data,
            current_positions=[],
            portfolio_value=10000.0
        )
        
        print(f"DEEPSEEK分析成功:")
        print(f"   决策: {result.decision}")
        print(f"   置信度: {result.confidence}")
        print(f"   推理: {result.reasoning}")
        print(f"   建议仓位: {result.suggested_amount}")
        
        return True
        
    except Exception as e:
        print(f"DEEPSEEK分析失败: {e}")
        return False

async def test_aster_api():
    """测试ASTER API"""
    print("=" * 50)
    print("测试ASTER API")
    print("=" * 50)
    
    if not settings.aster_dex_api_key or not settings.aster_dex_api_secret:
        print("ASTER API密钥未配置")
        return False
    
    print(f"API密钥已配置: {settings.aster_dex_api_key[:10]}...")
    print(f"API密钥已配置: {settings.aster_dex_api_secret[:10]}...")
    
    try:
        # 测试获取支持的交易对
        symbols = await aster_client.get_supported_symbols()
        print(f"获取交易对成功: {len(symbols)}个")
        print(f"   前5个交易对: {symbols[:5]}")
        
        # 测试获取行情数据
        ticker = await aster_client.get_ticker("BTC/USDT")
        print(f"获取BTC/USDT行情成功:")
        print(f"   价格: ${ticker.get('price', 0):.2f}")
        print(f"   24h变化: {ticker.get('change_24h', 0):.2f}%")
        
        # 测试获取账户余额
        balance = await aster_client.get_account_balance()
        print(f"获取账户余额成功:")
        print(f"   余额数据: {balance}")
        
        return True
        
    except Exception as e:
        print(f"ASTER API测试失败: {e}")
        return False

async def test_trading_integration():
    """测试交易集成"""
    print("=" * 50)
    print("测试交易集成")
    print("=" * 50)
    
    try:
        # 模拟一个简单的交易决策
        deepseek = DeepSeekModel()
        
        # 获取市场数据
        ticker = await aster_client.get_ticker("BTC/USDT")
        market_data = {
            "price": ticker.get('price', 50000),
            "volume_24h": ticker.get('volume_24h', 1000000),
            "change_24h": ticker.get('change_24h', 0),
            "high_24h": ticker.get('high_24h', 50000),
            "low_24h": ticker.get('low_24h', 50000)
        }
        
        # AI分析
        ai_result = await deepseek.analyze_market(
            symbol="BTC/USDT",
            market_data=market_data,
            current_positions=[],
            portfolio_value=10000.0
        )
        
        print(f"交易集成测试成功:")
        print(f"   AI决策: {ai_result.decision}")
        print(f"   建议仓位: {ai_result.suggested_amount}")
        
        # 如果AI建议买入，模拟下单
        if ai_result.decision == "buy" and ai_result.suggested_amount > 0:
            order_result = await aster_client.place_order(
                symbol="BTC/USDT",
                side="buy",
                order_type="market",
                amount=ai_result.suggested_amount
            )
            print(f"   模拟下单结果: {order_result}")
        
        return True
        
    except Exception as e:
        print(f"交易集成测试失败: {e}")
        return False

async def main():
    """主函数"""
    print("开始API配置测试...")
    print()
    
    # 测试DEEPSEEK
    deepseek_ok = await test_deepseek_api()
    print()
    
    # 测试ASTER
    aster_ok = await test_aster_api()
    print()
    
    # 测试集成
    if deepseek_ok and aster_ok:
        integration_ok = await test_trading_integration()
        print()
        
        if integration_ok:
            print("所有API测试通过！系统已准备就绪。")
        else:
            print("集成测试失败，请检查配置。")
    else:
        print("基础API测试失败，请检查API密钥配置。")
    
    # 关闭连接
    await aster_client.close()

if __name__ == "__main__":
    asyncio.run(main())
