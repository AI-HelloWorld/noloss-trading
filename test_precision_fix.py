#!/usr/bin/env python3
"""
测试交易精度修复
"""
import asyncio
import sys
import os
from decimal import Decimal

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.trading.trading_engine import TradingEngine
from loguru import logger

async def test_precision_adjustment():
    """测试精度调整功能"""
    logger.info("🧪 开始测试交易精度调整...")
    
    # 创建交易引擎实例
    trading_engine = TradingEngine()
    
    # 测试用例
    test_cases = [
        {
            "symbol": "ASTERUSDT",
            "amount": 17.94687724,
            "expected_precision": 1,
            "description": "ASTERUSDT 精度调整"
        },
        {
            "symbol": "BTCUSDT", 
            "amount": 0.000123456789,
            "expected_precision": 6,
            "description": "BTCUSDT 精度调整"
        },
        {
            "symbol": "ETHUSDT",
            "amount": 1.23456789,
            "expected_precision": 4,
            "description": "ETHUSDT 精度调整"
        },
        {
            "symbol": "SOLUSDT",
            "amount": 12.3456789,
            "expected_precision": 2,
            "description": "SOLUSDT 精度调整"
        },
        {
            "symbol": "UNKNOWNUSDT",
            "amount": 123.456789,
            "expected_precision": 2,
            "description": "未知币种 精度调整"
        }
    ]
    
    logger.info("📊 测试结果:")
    logger.info("=" * 80)
    
    for i, case in enumerate(test_cases, 1):
        symbol = case["symbol"]
        amount = case["amount"]
        expected_precision = case["expected_precision"]
        description = case["description"]
        
        # 调用精度调整方法
        adjusted_amount = trading_engine._adjust_trade_precision(symbol, amount)
        
        # 计算实际精度
        decimal_places = len(str(adjusted_amount).split('.')[-1]) if '.' in str(adjusted_amount) else 0
        
        # 检查结果
        is_correct = decimal_places <= expected_precision
        status = "✅ 通过" if is_correct else "❌ 失败"
        
        logger.info(f"{i}. {description}")
        logger.info(f"   币种: {symbol}")
        logger.info(f"   原始数量: {amount}")
        logger.info(f"   调整后数量: {adjusted_amount}")
        logger.info(f"   实际精度: {decimal_places} 位小数")
        logger.info(f"   期望精度: ≤ {expected_precision} 位小数")
        logger.info(f"   结果: {status}")
        logger.info("-" * 60)
    
    # 特别测试ASTERUSDT的精度问题
    logger.info("🔍 特别测试 ASTERUSDT 精度问题:")
    aster_amount = 17.94687724
    aster_adjusted = trading_engine._adjust_trade_precision("ASTERUSDT", aster_amount)
    
    logger.info(f"   原始数量: {aster_amount}")
    logger.info(f"   调整后数量: {aster_adjusted}")
    logger.info(f"   调整后精度: {len(str(aster_adjusted).split('.')[-1])} 位小数")
    
    # 检查是否满足AsterDEX的要求
    if len(str(aster_adjusted).split('.')[-1]) <= 2:
        logger.info("✅ ASTERUSDT 精度调整符合要求")
    else:
        logger.warning("⚠️ ASTERUSDT 精度调整可能仍然过高")
    
    logger.info("🎉 精度调整测试完成！")

if __name__ == "__main__":
    print("开始测试交易精度修复...")
    asyncio.run(test_precision_adjustment())
    print("\n测试完成！")
