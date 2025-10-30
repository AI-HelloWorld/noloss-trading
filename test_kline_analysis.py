"""
测试K线数据分析功能
"""
import asyncio
import random
from datetime import datetime, timedelta
from loguru import logger

from backend.agents.kline_compressor import kline_compressor
from backend.agents.agent_team import agent_team


def generate_mock_klines(symbol: str, interval: str, count: int = 100):
    """生成模拟K线数据用于测试"""
    logger.info(f"生成模拟K线数据: {symbol} {interval} {count}根")
    
    klines = []
    base_price = 50000.0  # BTC基准价格
    timestamp = int((datetime.now() - timedelta(hours=count)).timestamp() * 1000)
    
    for i in range(count):
        # 模拟价格波动
        open_price = base_price + random.uniform(-1000, 1000)
        close_price = open_price + random.uniform(-500, 500)
        high_price = max(open_price, close_price) + random.uniform(0, 300)
        low_price = min(open_price, close_price) - random.uniform(0, 300)
        volume = random.uniform(100, 1000)
        
        # 创建趋势
        if i > count * 0.6:  # 最后40%的数据显示上涨趋势
            close_price = open_price + random.uniform(50, 200)
            base_price += random.uniform(10, 50)
        elif i > count * 0.3:  # 中间30%的数据显示下跌趋势
            close_price = open_price - random.uniform(50, 200)
            base_price -= random.uniform(10, 50)
        
        # 重新计算高低点
        high_price = max(open_price, close_price) + random.uniform(0, 300)
        low_price = min(open_price, close_price) - random.uniform(0, 300)
        
        kline = [
            timestamp,
            open_price,
            high_price,
            low_price,
            close_price,
            volume,
            timestamp + 3600000,  # close_time
            volume * close_price,  # quote_volume
            random.randint(100, 500),  # trades
            volume * 0.6,  # taker_buy_volume
            volume * close_price * 0.6  # taker_buy_quote_volume
        ]
        
        klines.append(kline)
        timestamp += 3600000  # 1小时
        base_price = close_price
    
    logger.info(f"✅ 模拟K线数据生成完成: {count}根")
    return klines


async def test_kline_compression():
    """测试K线数据压缩"""
    logger.info("=" * 80)
    logger.info("测试1: K线数据压缩功能")
    logger.info("=" * 80)
    
    # 生成模拟K线数据
    symbol = "BTC-USDT"
    interval = "1h"
    raw_klines = generate_mock_klines(symbol, interval, 100)
    
    # 压缩K线数据
    compressed_data = kline_compressor.compress_kline_data(raw_klines, interval, symbol)
    
    # 输出压缩结果
    logger.info("\n📊 K线数据压缩结果:")
    logger.info(f"交易对: {compressed_data['symbol']}")
    logger.info(f"时间间隔: {compressed_data['interval']}")
    logger.info(f"时间戳: {compressed_data['timestamp']}")
    
    logger.info("\n📈 数据摘要:")
    summary = compressed_data['summary']
    for key, value in summary.items():
        logger.info(f"  {key}: {value}")
    
    logger.info("\n🔧 技术特征:")
    tech_features = compressed_data['technical_features']
    
    if tech_features.get('moving_averages'):
        logger.info("  移动平均线:")
        for key, value in tech_features['moving_averages'].items():
            logger.info(f"    {key}: {value}")
    
    if tech_features.get('rsi'):
        logger.info("  RSI指标:")
        for key, value in tech_features['rsi'].items():
            logger.info(f"    {key}: {value}")
    
    if tech_features.get('support_resistance'):
        logger.info("  支撑阻力:")
        for key, value in tech_features['support_resistance'].items():
            logger.info(f"    {key}: {value}")
    
    logger.info("\n📊 成交量分析:")
    volume_analysis = compressed_data['volume_analysis']
    for key, value in volume_analysis.items():
        if key != 'volume_clusters':
            logger.info(f"  {key}: {value}")
    
    logger.info("\n📉 趋势分析:")
    trend_analysis = compressed_data['trend_analysis']
    for key, value in trend_analysis.items():
        logger.info(f"  {key}: {value}")
    
    logger.info("\n🕯️ 压缩后的K线数量:")
    logger.info(f"  原始: {len(raw_klines)}根")
    logger.info(f"  压缩后: {len(compressed_data['compressed_candles'])}根")
    logger.info(f"  压缩比: {len(compressed_data['compressed_candles'])/len(raw_klines)*100:.1f}%")
    
    return compressed_data


async def test_agent_with_kline():
    """测试智能体使用K线数据进行分析"""
    logger.info("\n" + "=" * 80)
    logger.info("测试2: 智能体使用K线数据分析")
    logger.info("=" * 80)
    
    # 生成模拟K线数据
    symbol = "BTC-USDT"
    interval = "1h"
    raw_klines = generate_mock_klines(symbol, interval, 100)
    
    # 模拟市场数据
    last_kline = raw_klines[-1]
    market_data = {
        'symbol': symbol,
        'price': last_kline[4],  # close price
        'high_24h': max([k[2] for k in raw_klines[-24:]]),
        'low_24h': min([k[3] for k in raw_klines[-24:]]),
        'change_24h': ((last_kline[4] - raw_klines[-24][4]) / raw_klines[-24][4] * 100),
        'volume_24h': sum([k[5] for k in raw_klines[-24:]]),
        'timestamp': last_kline[0]
    }
    
    # 模拟投资组合
    portfolio = {
        'total_balance': 10000.0,
        'cash_balance': 8000.0,
        'positions_value': 2000.0,
        'total_pnl': 500.0
    }
    
    positions = []
    
    # 准备额外数据（包含K线数据）
    additional_data = {
        'raw_klines': raw_klines,
        'kline_interval': interval
    }
    
    logger.info(f"\n🔍 开始团队分析 - {symbol}")
    logger.info(f"当前价格: ${market_data['price']:.2f}")
    logger.info(f"24小时变化: {market_data['change_24h']:+.2f}%")
    logger.info(f"K线数据: {len(raw_klines)}根 {interval}")
    
    # 执行团队分析
    decision = await agent_team.conduct_team_analysis(
        symbol=symbol,
        market_data=market_data,
        portfolio=portfolio,
        positions=positions,
        additional_data=additional_data
    )
    
    # 输出分析结果
    logger.info("\n" + "=" * 80)
    logger.info("📋 团队分析结果")
    logger.info("=" * 80)
    
    logger.info(f"\n最终决策: {decision['final_decision']}")
    logger.info(f"建议动作: {decision['action']}")
    logger.info(f"置信度: {decision['confidence']:.2%}")
    logger.info(f"仓位大小: {decision['position_size']:.2%}")
    
    if decision.get('stop_loss'):
        logger.info(f"\n止盈止损:")
        logger.info(f"  止损: ${decision['stop_loss']:.2f}")
        logger.info(f"  止盈: ${decision['take_profit']:.2f}")
    
    logger.info(f"\n决策理由:")
    logger.info(f"  {decision['reasoning']}")
    
    if decision.get('team_analyses'):
        logger.info(f"\n团队成员分析:")
        for analysis in decision['team_analyses']:
            logger.info(f"\n  {analysis['role']}:")
            logger.info(f"    建议: {analysis['recommendation']}")
            logger.info(f"    置信度: {analysis['confidence']:.2%}")
            logger.info(f"    理由: {analysis['reasoning'][:100]}...")
    
    return decision


async def test_kline_features():
    """测试K线特征提取的准确性"""
    logger.info("\n" + "=" * 80)
    logger.info("测试3: K线特征提取准确性")
    logger.info("=" * 80)
    
    # 生成明确趋势的K线数据
    symbol = "ETH-USDT"
    interval = "15m"
    
    logger.info("\n测试场景1: 上升趋势")
    uptrend_klines = []
    base_price = 3000.0
    timestamp = int(datetime.now().timestamp() * 1000)
    
    for i in range(50):
        open_price = base_price
        close_price = base_price + random.uniform(10, 50)  # 持续上涨
        high_price = close_price + random.uniform(0, 20)
        low_price = open_price - random.uniform(0, 10)
        volume = random.uniform(100, 200)
        
        uptrend_klines.append([
            timestamp, open_price, high_price, low_price, close_price,
            volume, timestamp + 900000, volume * close_price,
            random.randint(50, 100), volume * 0.6, volume * close_price * 0.6
        ])
        
        timestamp += 900000
        base_price = close_price
    
    compressed_up = kline_compressor.compress_kline_data(uptrend_klines, interval, symbol)
    
    logger.info(f"  趋势判断: {compressed_up['trend_analysis']['primary_trend']}")
    logger.info(f"  趋势置信度: {compressed_up['trend_analysis']['confidence']:.1f}")
    logger.info(f"  价格变化: {compressed_up['summary']['price_change_pct']:.2f}%")
    
    ma_features = compressed_up['technical_features'].get('moving_averages', {})
    if ma_features:
        logger.info(f"  均线排列: {ma_features.get('trend', 'unknown')}")
    
    logger.info("\n测试场景2: 下降趋势")
    downtrend_klines = []
    base_price = 3000.0
    timestamp = int(datetime.now().timestamp() * 1000)
    
    for i in range(50):
        open_price = base_price
        close_price = base_price - random.uniform(10, 50)  # 持续下跌
        high_price = open_price + random.uniform(0, 10)
        low_price = close_price - random.uniform(0, 20)
        volume = random.uniform(100, 200)
        
        downtrend_klines.append([
            timestamp, open_price, high_price, low_price, close_price,
            volume, timestamp + 900000, volume * close_price,
            random.randint(50, 100), volume * 0.6, volume * close_price * 0.6
        ])
        
        timestamp += 900000
        base_price = close_price
    
    compressed_down = kline_compressor.compress_kline_data(downtrend_klines, interval, symbol)
    
    logger.info(f"  趋势判断: {compressed_down['trend_analysis']['primary_trend']}")
    logger.info(f"  趋势置信度: {compressed_down['trend_analysis']['confidence']:.1f}")
    logger.info(f"  价格变化: {compressed_down['summary']['price_change_pct']:.2f}%")
    
    ma_features = compressed_down['technical_features'].get('moving_averages', {})
    if ma_features:
        logger.info(f"  均线排列: {ma_features.get('trend', 'unknown')}")
    
    logger.info("\n测试场景3: 横盘整理")
    sideways_klines = []
    base_price = 3000.0
    timestamp = int(datetime.now().timestamp() * 1000)
    
    for i in range(50):
        open_price = base_price + random.uniform(-20, 20)
        close_price = base_price + random.uniform(-20, 20)
        high_price = max(open_price, close_price) + random.uniform(0, 15)
        low_price = min(open_price, close_price) - random.uniform(0, 15)
        volume = random.uniform(100, 200)
        
        sideways_klines.append([
            timestamp, open_price, high_price, low_price, close_price,
            volume, timestamp + 900000, volume * close_price,
            random.randint(50, 100), volume * 0.6, volume * close_price * 0.6
        ])
        
        timestamp += 900000
    
    compressed_sideways = kline_compressor.compress_kline_data(sideways_klines, interval, symbol)
    
    logger.info(f"  趋势判断: {compressed_sideways['trend_analysis']['primary_trend']}")
    logger.info(f"  趋势置信度: {compressed_sideways['trend_analysis']['confidence']:.1f}")
    logger.info(f"  价格变化: {compressed_sideways['summary']['price_change_pct']:.2f}%")
    
    ma_features = compressed_sideways['technical_features'].get('moving_averages', {})
    if ma_features:
        logger.info(f"  均线排列: {ma_features.get('trend', 'unknown')}")


async def main():
    """主测试函数"""
    logger.info("🚀 开始K线数据分析功能测试")
    logger.info("=" * 80)
    
    try:
        # 测试1: K线数据压缩
        await test_kline_compression()
        
        # 测试2: 智能体使用K线数据
        await test_agent_with_kline()
        
        # 测试3: K线特征提取准确性
        await test_kline_features()
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ 所有测试完成!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

