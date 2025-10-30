"""
AI团队协同止盈止损决策系统 - 测试脚本
"""
import asyncio
from backend.agents.agent_team import agent_team
from backend.agents.stop_loss_decision_system import stop_decision_system
from loguru import logger


async def test_stop_loss_decision_system():
    """测试止盈止损决策系统"""
    
    logger.info("=" * 80)
    logger.info("🚀 AI团队协同止盈止损决策系统测试")
    logger.info("=" * 80)
    
    # 场景1：做多BTC，价格上涨3%，技术面建议收紧止损
    logger.info("\n📊 场景1：做多BTC盈利3%，技术面建议收紧止损")
    logger.info("-" * 80)
    
    position_id_1 = "BTCUSDT_001"
    stop_decision_system.register_position(
        position_id=position_id_1,
        symbol="BTCUSDT",
        action="buy",
        entry_price=50000.0,
        quantity=0.1,
        stop_loss=49000.0,  # -2%
        take_profit=52000.0,  # +4%
        confidence=0.75,
        strategy_info={"type": "技术突破", "agent": "technical_analyst"}
    )
    
    # 价格上涨到51500（+3%）
    current_price_1 = 51500.0
    stop_decision_system.update_position_price(position_id_1, current_price_1)
    
    market_data_1 = {
        'price': current_price_1,
        'change_24h': 3.0,
        'high_24h': 51800.0,
        'low_24h': 49500.0,
        'volume_24h': 1000000000
    }
    
    position_info_1 = stop_decision_system.get_position_status(position_id_1)
    position_info_1['portfolio'] = {
        'total_balance': 10000.0,
        'cash_balance': 5000.0,
        'positions_value': 5150.0,
        'total_pnl': 150.0
    }
    
    logger.info(f"   持仓: {position_info_1['symbol']} {position_info_1['action']}")
    logger.info(f"   入场价: ${position_info_1['entry_price']:.2f}")
    logger.info(f"   当前价: ${current_price_1:.2f}")
    logger.info(f"   盈亏: ${position_info_1['pnl']:.2f} ({position_info_1['pnl_pct']:.2f}%)")
    logger.info(f"   止损: ${position_info_1['stop_loss']:.2f}")
    logger.info(f"   止盈: ${position_info_1['take_profit']:.2f}")
    
    decision_1 = await agent_team.evaluate_stop_loss_decision(
        position_id=position_id_1,
        symbol="BTCUSDT",
        market_data=market_data_1,
        position_info=position_info_1
    )
    
    logger.info(f"\n   📋 决策结果:")
    logger.info(f"   ├─ 最终决策: {decision_1['final_decision']}")
    logger.info(f"   ├─ 建议操作: {decision_1['action']}")
    logger.info(f"   ├─ 置信度: {decision_1['confidence']:.2f}")
    logger.info(f"   ├─ 紧急度: {decision_1['urgency']:.2f}")
    logger.info(f"   ├─ 决策理由: {decision_1['reasoning']}")
    logger.info(f"   └─ 团队投票: {decision_1.get('team_votes', {})}")
    
    # 场景2：做多BTC，价格下跌2.5%，风险管理经理建议止损
    logger.info("\n" + "=" * 80)
    logger.info("📊 场景2：做多BTC亏损2.5%，风险管理经理强制止损")
    logger.info("-" * 80)
    
    position_id_2 = "BTCUSDT_002"
    stop_decision_system.register_position(
        position_id=position_id_2,
        symbol="BTCUSDT",
        action="buy",
        entry_price=50000.0,
        quantity=0.1,
        stop_loss=49000.0,  # -2%
        take_profit=52000.0,  # +4%
        confidence=0.65,
        strategy_info={"type": "基本面", "agent": "fundamental_analyst"}
    )
    
    # 价格下跌到48750（-2.5%）
    current_price_2 = 48750.0
    stop_decision_system.update_position_price(position_id_2, current_price_2)
    
    market_data_2 = {
        'price': current_price_2,
        'change_24h': -2.5,
        'high_24h': 50200.0,
        'low_24h': 48500.0,
        'volume_24h': 1200000000
    }
    
    position_info_2 = stop_decision_system.get_position_status(position_id_2)
    position_info_2['portfolio'] = {
        'total_balance': 9875.0,
        'cash_balance': 5000.0,
        'positions_value': 4875.0,
        'total_pnl': -125.0
    }
    
    logger.info(f"   持仓: {position_info_2['symbol']} {position_info_2['action']}")
    logger.info(f"   入场价: ${position_info_2['entry_price']:.2f}")
    logger.info(f"   当前价: ${current_price_2:.2f}")
    logger.info(f"   盈亏: ${position_info_2['pnl']:.2f} ({position_info_2['pnl_pct']:.2f}%)")
    logger.info(f"   止损: ${position_info_2['stop_loss']:.2f}")
    logger.info(f"   止盈: ${position_info_2['take_profit']:.2f}")
    
    decision_2 = await agent_team.evaluate_stop_loss_decision(
        position_id=position_id_2,
        symbol="BTCUSDT",
        market_data=market_data_2,
        position_info=position_info_2
    )
    
    logger.info(f"\n   📋 决策结果:")
    logger.info(f"   ├─ 最终决策: {decision_2['final_decision']}")
    logger.info(f"   ├─ 建议操作: {decision_2['action']}")
    logger.info(f"   ├─ 置信度: {decision_2['confidence']:.2f}")
    logger.info(f"   ├─ 紧急度: {decision_2['urgency']:.2f}")
    logger.info(f"   ├─ 决策理由: {decision_2['reasoning']}")
    logger.info(f"   └─ 团队投票: {decision_2.get('team_votes', {})}")
    
    # 场景3：做多BTC，价格上涨5%，建议启用移动止损
    logger.info("\n" + "=" * 80)
    logger.info("📊 场景3：做多BTC盈利5%，建议启用移动止损")
    logger.info("-" * 80)
    
    position_id_3 = "BTCUSDT_003"
    stop_decision_system.register_position(
        position_id=position_id_3,
        symbol="BTCUSDT",
        action="buy",
        entry_price=50000.0,
        quantity=0.1,
        stop_loss=49000.0,  # -2%
        take_profit=52000.0,  # +4%
        confidence=0.80,
        strategy_info={"type": "情绪驱动", "agent": "sentiment_analyst"}
    )
    
    # 价格上涨到52500（+5%）
    current_price_3 = 52500.0
    stop_decision_system.update_position_price(position_id_3, current_price_3)
    
    market_data_3 = {
        'price': current_price_3,
        'change_24h': 5.0,
        'high_24h': 52800.0,
        'low_24h': 49800.0,
        'volume_24h': 1500000000
    }
    
    position_info_3 = stop_decision_system.get_position_status(position_id_3)
    position_info_3['portfolio'] = {
        'total_balance': 10250.0,
        'cash_balance': 5000.0,
        'positions_value': 5250.0,
        'total_pnl': 250.0
    }
    
    logger.info(f"   持仓: {position_info_3['symbol']} {position_info_3['action']}")
    logger.info(f"   入场价: ${position_info_3['entry_price']:.2f}")
    logger.info(f"   当前价: ${current_price_3:.2f}")
    logger.info(f"   盈亏: ${position_info_3['pnl']:.2f} ({position_info_3['pnl_pct']:.2f}%)")
    logger.info(f"   止损: ${position_info_3['stop_loss']:.2f}")
    logger.info(f"   止盈: ${position_info_3['take_profit']:.2f}")
    
    decision_3 = await agent_team.evaluate_stop_loss_decision(
        position_id=position_id_3,
        symbol="BTCUSDT",
        market_data=market_data_3,
        position_info=position_info_3
    )
    
    logger.info(f"\n   📋 决策结果:")
    logger.info(f"   ├─ 最终决策: {decision_3['final_decision']}")
    logger.info(f"   ├─ 建议操作: {decision_3['action']}")
    logger.info(f"   ├─ 置信度: {decision_3['confidence']:.2f}")
    logger.info(f"   ├─ 紧急度: {decision_3['urgency']:.2f}")
    logger.info(f"   ├─ 决策理由: {decision_3['reasoning']}")
    logger.info(f"   ├─ 移动止损: ${decision_3.get('trailing_stop', 0):.2f}")
    logger.info(f"   └─ 团队投票: {decision_3.get('team_votes', {})}")
    
    # 场景4：做空ETH，价格下跌15%，基本面建议止盈
    logger.info("\n" + "=" * 80)
    logger.info("📊 场景4：做空ETH盈利15%，基本面建议止盈")
    logger.info("-" * 80)
    
    position_id_4 = "ETHUSDT_001"
    stop_decision_system.register_position(
        position_id=position_id_4,
        symbol="ETHUSDT",
        action="short",
        entry_price=3000.0,
        quantity=1.0,
        stop_loss=3060.0,  # +2%
        take_profit=2880.0,  # -4%
        confidence=0.85,
        strategy_info={"type": "新闻驱动", "agent": "news_analyst"}
    )
    
    # 价格下跌到2550（-15%）
    current_price_4 = 2550.0
    stop_decision_system.update_position_price(position_id_4, current_price_4)
    
    market_data_4 = {
        'price': current_price_4,
        'change_24h': -15.0,
        'high_24h': 3050.0,
        'low_24h': 2500.0,
        'volume_24h': 800000000
    }
    
    position_info_4 = stop_decision_system.get_position_status(position_id_4)
    position_info_4['portfolio'] = {
        'total_balance': 10450.0,
        'cash_balance': 5000.0,
        'positions_value': 5450.0,
        'total_pnl': 450.0
    }
    
    logger.info(f"   持仓: {position_info_4['symbol']} {position_info_4['action']}")
    logger.info(f"   入场价: ${position_info_4['entry_price']:.2f}")
    logger.info(f"   当前价: ${current_price_4:.2f}")
    logger.info(f"   盈亏: ${position_info_4['pnl']:.2f} ({position_info_4['pnl_pct']:.2f}%)")
    logger.info(f"   止损: ${position_info_4['stop_loss']:.2f}")
    logger.info(f"   止盈: ${position_info_4['take_profit']:.2f}")
    
    decision_4 = await agent_team.evaluate_stop_loss_decision(
        position_id=position_id_4,
        symbol="ETHUSDT",
        market_data=market_data_4,
        position_info=position_info_4
    )
    
    logger.info(f"\n   📋 决策结果:")
    logger.info(f"   ├─ 最终决策: {decision_4['final_decision']}")
    logger.info(f"   ├─ 建议操作: {decision_4['action']}")
    logger.info(f"   ├─ 置信度: {decision_4['confidence']:.2f}")
    logger.info(f"   ├─ 紧急度: {decision_4['urgency']:.2f}")
    logger.info(f"   ├─ 决策理由: {decision_4['reasoning']}")
    logger.info(f"   └─ 团队投票: {decision_4.get('team_votes', {})}")
    
    # 总结
    logger.info("\n" + "=" * 80)
    logger.info("✅ 测试完成!")
    logger.info("=" * 80)
    logger.info("\n📊 系统特性总结:")
    logger.info("   ✅ 多维度分析：技术、基本面、情绪、新闻、风险")
    logger.info("   ✅ 智能决策：风险管理经理否决权 + 团队共识")
    logger.info("   ✅ 六种止盈止损方式：固定、波动率、移动、时间、支撑阻力、置信度")
    logger.info("   ✅ 动态适应：根据市场环境和持仓状态调整策略")
    logger.info("   ✅ 透明可追溯：详细的决策理由和团队投票记录")
    
    logger.info("\n🎯 应用场景:")
    logger.info("   1. 盈利保护：自动收紧止损、启用移动止损")
    logger.info("   2. 风险控制：强制止损、紧急离场")
    logger.info("   3. 利润最大化：基于多维度分析的止盈时机")
    logger.info("   4. 持仓管理：实时监控、动态调整")


if __name__ == "__main__":
    asyncio.run(test_stop_loss_decision_system())

