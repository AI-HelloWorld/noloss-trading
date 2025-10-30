#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试模拟市场数据的持仓管理
"""

import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')

from backend.exchanges.mock_market_data import mock_market

def test_mock_positions():
    print("🧪 测试模拟市场数据持仓管理...")
    
    # 检查初始状态
    print(f"💰 初始USDT余额: ${mock_market.balances['USDT']:.2f}")
    print(f"💼 初始持仓数量: {len(mock_market.positions)}")
    
    # 模拟买入交易
    print("\n📈 模拟买入 BTC/USDT...")
    result = mock_market.place_order("BTC/USDT", "buy", "market", 0.01)  # 买入0.01 BTC
    print(f"交易结果: {result}")
    print(f"💰 交易后USDT余额: ${mock_market.balances['USDT']:.2f}")
    print(f"💰 交易后BTC余额: {mock_market.balances['BTC']:.6f}")
    print(f"💼 交易后持仓数量: {len(mock_market.positions)}")
    
    # 检查持仓详情
    positions = mock_market.get_open_positions()
    print(f"\n💼 持仓详情:")
    for pos in positions:
        print(f"  - {pos['symbol']}: {pos['amount']:.6f} @ ${pos['average_price']:.2f} (类型: {pos['position_type']})")
    
    # 模拟做空交易
    print("\n📉 模拟做空 ETH/USDT...")
    result = mock_market.place_short_order("ETH/USDT", 0.1)  # 做空0.1 ETH
    print(f"交易结果: {result}")
    print(f"💰 做空后USDT余额: ${mock_market.balances['USDT']:.2f}")
    print(f"💼 做空后持仓数量: {len(mock_market.positions)}")
    
    # 再次检查持仓详情
    positions = mock_market.get_open_positions()
    print(f"\n💼 最终持仓详情:")
    for pos in positions:
        print(f"  - {pos['symbol']}: {pos['amount']:.6f} @ ${pos['average_price']:.2f} (类型: {pos['position_type']}, 盈亏: ${pos['unrealized_pnl']:.2f})")
    
    return len(positions) > 0

if __name__ == "__main__":
    success = test_mock_positions()
    if success:
        print("\n✅ 模拟持仓管理正常")
    else:
        print("\n❌ 模拟持仓管理有问题")
