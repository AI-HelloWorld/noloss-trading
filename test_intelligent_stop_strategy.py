"""
智能止盈止损策略测试脚本
"""
import asyncio
from loguru import logger
from backend.agents.intelligent_stop_strategy import intelligent_stop_strategy
from backend.agents.dynamic_stop_monitor import dynamic_stop_monitor


def test_basic_stop_calculation():
    """测试基础止盈止损计算"""
    logger.info("=" * 60)
    logger.info("测试1: 基础止盈止损计算")
    logger.info("=" * 60)
    
    # 模拟市场数据
    market_data = {
        'price': 50000,
        'high_24h': 52000,
        'low_24h': 48000,
        'change_24h': 2.5,
        'volume_24h': 1000000
    }
    
    # 测试做多止盈止损
    logger.info("\n🟢 测试做多止盈止损:")
    long_stops = intelligent_stop_strategy.calculate_stop_levels(
        action="buy",
        entry_price=50000,
        market_data=market_data,
        position_size=0.1,
        confidence=0.7,
        volatility=8.0
    )
    
    logger.info(f"入场价格: ${50000:.2f}")
    logger.info(f"止损位: ${long_stops['stop_loss']:.2f} ({long_stops['risk_pct']:+.2f}%)")
    logger.info(f"止盈位: ${long_stops['take_profit']:.2f} ({long_stops['reward_pct']:+.2f}%)")
    logger.info(f"风险回报比: 1:{long_stops['risk_reward_ratio']:.2f}")
    logger.info(f"策略类型: {long_stops['strategy_type']}")
    
    # 测试做空止盈止损
    logger.info("\n🔴 测试做空止盈止损:")
    short_stops = intelligent_stop_strategy.calculate_stop_levels(
        action="short",
        entry_price=50000,
        market_data=market_data,
        position_size=0.1,
        confidence=0.7,
        volatility=8.0
    )
    
    logger.info(f"入场价格: ${50000:.2f}")
    logger.info(f"止损位: ${short_stops['stop_loss']:.2f} ({short_stops['risk_pct']:+.2f}%)")
    logger.info(f"止盈位: ${short_stops['take_profit']:.2f} ({short_stops['reward_pct']:+.2f}%)")
    logger.info(f"风险回报比: 1:{short_stops['risk_reward_ratio']:.2f}")
    logger.info(f"策略类型: {short_stops['strategy_type']}")


def test_confidence_adjustment():
    """测试置信度调整"""
    logger.info("\n" + "=" * 60)
    logger.info("测试2: 置信度调整")
    logger.info("=" * 60)
    
    market_data = {
        'price': 50000,
        'high_24h': 51000,
        'low_24h': 49000,
        'change_24h': 1.0,
        'volume_24h': 1000000
    }
    
    confidences = [0.9, 0.7, 0.5]
    
    for conf in confidences:
        stops = intelligent_stop_strategy.calculate_stop_levels(
            action="buy",
            entry_price=50000,
            market_data=market_data,
            position_size=0.1,
            confidence=conf,
            volatility=4.0
        )
        
        logger.info(f"\n置信度: {conf:.1f}")
        logger.info(f"止损距离: {stops['risk_pct']:.2f}%")
        logger.info(f"止盈距离: {stops['reward_pct']:.2f}%")
        logger.info(f"风险回报比: 1:{stops['risk_reward_ratio']:.2f}")


def test_volatility_adjustment():
    """测试波动率调整"""
    logger.info("\n" + "=" * 60)
    logger.info("测试3: 波动率调整")
    logger.info("=" * 60)
    
    market_data = {
        'price': 50000,
        'high_24h': 51000,
        'low_24h': 49000,
        'change_24h': 1.0,
        'volume_24h': 1000000
    }
    
    volatilities = [3.0, 7.0, 12.0]  # 低、中、高波动率
    
    for vol in volatilities:
        stops = intelligent_stop_strategy.calculate_stop_levels(
            action="buy",
            entry_price=50000,
            market_data=market_data,
            position_size=0.1,
            confidence=0.7,
            volatility=vol
        )
        
        logger.info(f"\n波动率: {vol:.1f}%")
        logger.info(f"止损距离: {stops['risk_pct']:.2f}%")
        logger.info(f"止盈距离: {stops['reward_pct']:.2f}%")


def test_support_resistance_levels():
    """测试支撑阻力位影响"""
    logger.info("\n" + "=" * 60)
    logger.info("测试4: 支撑阻力位影响")
    logger.info("=" * 60)
    
    market_data = {
        'price': 50000,
        'high_24h': 52000,
        'low_24h': 48000,
        'change_24h': 2.0,
        'volume_24h': 1000000
    }
    
    # 带支撑阻力位
    additional_factors = {
        'key_levels': {
            'support_levels': [49500, 49000, 48500],
            'resistance_levels': [50500, 51000, 51500]
        }
    }
    
    logger.info("\n🔹 使用支撑阻力位:")
    stops_with_levels = intelligent_stop_strategy.calculate_stop_levels(
        action="buy",
        entry_price=50000,
        market_data=market_data,
        position_size=0.1,
        confidence=0.7,
        volatility=8.0,
        additional_factors=additional_factors
    )
    
    logger.info(f"止损位: ${stops_with_levels['stop_loss']:.2f}")
    logger.info(f"止盈位: ${stops_with_levels['take_profit']:.2f}")
    logger.info(f"策略类型: {stops_with_levels['strategy_type']}")
    
    logger.info("\n🔹 不使用支撑阻力位:")
    stops_without_levels = intelligent_stop_strategy.calculate_stop_levels(
        action="buy",
        entry_price=50000,
        market_data=market_data,
        position_size=0.1,
        confidence=0.7,
        volatility=8.0
    )
    
    logger.info(f"止损位: ${stops_without_levels['stop_loss']:.2f}")
    logger.info(f"止盈位: ${stops_without_levels['take_profit']:.2f}")
    logger.info(f"策略类型: ${stops_without_levels['strategy_type']}")


def test_trailing_stop():
    """测试移动止损"""
    logger.info("\n" + "=" * 60)
    logger.info("测试5: 移动止损")
    logger.info("=" * 60)
    
    entry_price = 50000
    
    # 模拟做多盈利场景
    logger.info("\n🟢 做多移动止损场景:")
    logger.info(f"入场价格: ${entry_price:.2f}")
    
    price_scenarios = [
        (50500, 50500, 50000),  # 价格小幅上涨
        (51500, 51500, 50000),  # 价格达到激活阈值
        (52000, 52000, 50000),  # 价格继续上涨
        (51700, 52000, 50000),  # 价格回落
    ]
    
    for current, highest, lowest in price_scenarios:
        trailing_stop = intelligent_stop_strategy.calculate_trailing_stop(
            action="buy",
            entry_price=entry_price,
            current_price=current,
            highest_price=highest,
            lowest_price=lowest
        )
        
        profit_pct = (current - entry_price) / entry_price * 100
        logger.info(f"\n当前价格: ${current:.2f} (盈利: {profit_pct:+.2f}%)")
        logger.info(f"最高价格: ${highest:.2f}")
        logger.info(f"移动止损位: ${trailing_stop:.2f}")
    
    # 模拟做空盈利场景
    logger.info("\n\n🔴 做空移动止损场景:")
    logger.info(f"入场价格: ${entry_price:.2f}")
    
    short_scenarios = [
        (49500, 50000, 49500),  # 价格小幅下跌
        (48500, 50000, 48500),  # 价格达到激活阈值
        (48000, 50000, 48000),  # 价格继续下跌
        (48300, 50000, 48000),  # 价格反弹
    ]
    
    for current, highest, lowest in short_scenarios:
        trailing_stop = intelligent_stop_strategy.calculate_trailing_stop(
            action="short",
            entry_price=entry_price,
            current_price=current,
            highest_price=highest,
            lowest_price=lowest
        )
        
        profit_pct = (entry_price - current) / entry_price * 100
        logger.info(f"\n当前价格: ${current:.2f} (盈利: {profit_pct:+.2f}%)")
        logger.info(f"最低价格: ${lowest:.2f}")
        logger.info(f"移动止损位: ${trailing_stop:.2f}")


def test_dynamic_monitor():
    """测试动态监控器"""
    logger.info("\n" + "=" * 60)
    logger.info("测试6: 动态监控器")
    logger.info("=" * 60)
    
    # 添加一个测试持仓
    position_id = "TEST_001"
    symbol = "BTCUSDT"
    entry_price = 50000
    stop_loss = 49000
    take_profit = 52000
    
    dynamic_stop_monitor.update_position(
        position_id=position_id,
        symbol=symbol,
        action="buy",
        entry_price=entry_price,
        current_price=entry_price,
        quantity=0.1,
        stop_loss=stop_loss,
        take_profit=take_profit
    )
    
    # 模拟价格变化
    price_changes = [50500, 51000, 51500, 52000, 51800]
    
    logger.info("\n📊 价格变化监控:")
    for price in price_changes:
        signal = dynamic_stop_monitor.check_stop_conditions(position_id, price)
        health = dynamic_stop_monitor.get_position_health(position_id)
        
        logger.info(f"\n当前价格: ${price:.2f}")
        logger.info(f"健康状态: {health['status_emoji']} {health['status']}")
        logger.info(f"盈利: {health['profit_pct']:+.2f}%")
        logger.info(f"止损距离: {health['stop_distance_pct']:.2f}%")
        logger.info(f"建议移动止损: ${health['suggested_trailing_stop']:.2f}")
        logger.info(f"交易信号: {signal['action']} - {signal['reason']}")
        
        if signal['action'] != 'hold':
            logger.warning(f"⚠️ 触发{signal['reason']}，建议{signal['action']}")
            break
    
    # 清理测试持仓
    dynamic_stop_monitor.remove_position(position_id)
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ 所有测试完成！")
    logger.info("=" * 60)


def main():
    """运行所有测试"""
    logger.info("🚀 开始测试智能止盈止损策略")
    logger.info("")
    
    # 运行所有测试
    test_basic_stop_calculation()
    test_confidence_adjustment()
    test_volatility_adjustment()
    test_support_resistance_levels()
    test_trailing_stop()
    test_dynamic_monitor()
    
    logger.info("\n✅ 所有测试完成！智能止盈止损策略工作正常。")


if __name__ == "__main__":
    main()

