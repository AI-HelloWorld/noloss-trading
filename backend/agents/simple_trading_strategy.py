"""
高级交易策略 - 多因子、多币种、高频，带杠杆与风控
当AI模型不可用时，使用高级规则进行交易
"""
from typing import Dict
from loguru import logger


class AdvancedTradingStrategy:
    """高级交易策略 - 多因子、多币种、高频, 带杠杆与风控"""
    
    def __init__(self):
        # 设置参数阈值
        self.min_confidence = 0.65            # 执行交易的最低置信度门槛
        self.base_position_pct = 0.10         # 基础仓位比例（每笔交易占用资金比例，10%）
        self.max_leverage = 3                 # 最大杠杆倍数
        self.min_margin_ratio = 0.5           # 最低保证金充足率（50%可用资金保底）

    def analyze(self, symbol: str, market_data: Dict, portfolio: Dict) -> Dict:
        """综合多因子分析市场数据，对单个币种给出交易决策"""
        price = market_data.get('price', 0)
        change_24h = market_data.get('change_24h', 0)
        high_24h = market_data.get('high_24h', price)
        low_24h = market_data.get('low_24h', price)
        volume_24h = market_data.get('volume_24h', 0)
        volatility = market_data.get('volatility', None)  # 如给定波动率年化或日内波幅百分比
        net_flow = market_data.get('net_flow', 0)         # 资金净流入（正为流入，负为流出）
        sentiment_score = market_data.get('sentiment_score', 0)  # 舆情情绪得分 (-1到1)

        # 计算价格在24h区间的位置 (0到1之间)
        price_position = ((price - low_24h) / (high_24h - low_24h)
                          if high_24h > low_24h else 0.5)

        # 趋势判断
        is_uptrend = (change_24h > 3 and price_position > 0.6)  # 涨幅超过3%且接近高点
        is_downtrend = (change_24h < -3 and price_position < 0.4)  # 跌幅超过3%且接近低点
        is_sideways = abs(change_24h) < 1  # 涨跌不到1%，震荡盘整

        # 交易量强度（相对值0-1，用于辅助判断趋势可信度）
        volume_strength = 0.0
        if 'avg_volume_7d' in market_data:
            # 如果有7日均量，计算当日量相对均量的比例并限定[0,1]
            avg_vol = market_data['avg_volume_7d']
            if avg_vol > 0:
                volume_strength = min(volume_24h / avg_vol, 1.0)
        else:
            # 若无均量，用预估值归一化
            volume_strength = min(volume_24h / 100000000, 1.0)

        # 资金流强度：将净流入流出标准化为[-1,1]区间
        flow_strength = 0.0
        if net_flow:
            # 可根据市值或交易量的比例来归一化，这里假设简化处理
            flow_strength = max(-1.0, min(net_flow / 1000000, 1.0))

        # 情绪强度：假设 sentiment_score 已经是 -1到1（负面到正面）
        senti_strength = sentiment_score

        # 决策变量初始化
        action = "hold"
        confidence = 0.0
        reasoning = ""

        # 获取当前持仓和现金情况
        current_positions = portfolio.get('positions', [])  # 持仓列表，元素包含{'symbol':..., 'amount':..., 'side': 'long/short'}
        has_long = any(pos['symbol'] == symbol and pos.get('side', 'long') == 'long' for pos in current_positions)
        has_short = any(pos['symbol'] == symbol and pos.get('side', 'long') == 'short' for pos in current_positions)
        cash_balance = portfolio.get('cash_balance', 0)
        equity = portfolio.get('equity', cash_balance)  # 账户总权益（现金+持仓市值）

        # 保证金余量计算（假设portfolio给出已用保证金或通过持仓推算）
        used_margin = portfolio.get('used_margin', 0)
        free_margin_ratio = (equity - used_margin) / equity if equity > 0 else 0

        # 交易决策逻辑
        # 1. 判断买入信号
        if is_uptrend:
            # 多头趋势信号基本条件满足
            # 进一步检查其他因子助力
            bullish_factor_count = 0
            if volume_strength > 0.5:
                bullish_factor_count += 1  # 放量上涨
            if flow_strength > 0.1:
                bullish_factor_count += 1  # 资金净流入显著
            if senti_strength > 0.2:
                bullish_factor_count += 1  # 市场情绪积极正面

            if not has_long and free_margin_ratio > self.min_margin_ratio and cash_balance > 100:
                # 没有当前币种多头仓位，资金充足，可以开多
                action = "buy"
                # 置信度基础0.7，附加因子每个加0.1，上限0.95
                confidence = 0.70 + 0.10 * bullish_factor_count
                confidence = min(confidence, 0.95)
                reasoning = f"{symbol}上行趋势明确：24h涨幅{change_24h:.2f}%，" \
                            f"价处于日内高位{price_position*100:.0f}%，" \
                            f"附加指标支持（量能{volume_strength:.2f}, 资金流{flow_strength:.2f}, 情绪{senti_strength:.2f})"
            # 若已经有多头仓位且趋势继续增强，可以考虑加仓（这里简单处理为hold或再评估）
        elif is_downtrend:
            # 空头趋势信号基本条件满足
            bearish_factor_count = 0
            if volume_strength > 0.5:
                bearish_factor_count += 1  # 放量下跌
            if flow_strength < -0.1:
                bearish_factor_count += 1  # 资金净流出明显
            if senti_strength < -0.2:
                bearish_factor_count += 1  # 市场情绪悲观恐慌

            if not has_short and free_margin_ratio > self.min_margin_ratio and cash_balance > 100:
                # 没有当前币种空头仓位，且保证金充足，考虑开空
                action = "short"
                confidence = 0.70 + 0.10 * bearish_factor_count
                confidence = min(confidence, 0.95)
                reasoning = f"{symbol}下行趋势明显：24h跌幅{change_24h:.2f}%，" \
                            f"价处日内低位{price_position*100:.0f}%，" \
                            f"附加指标看空（量能{volume_strength:.2f}, 资金流{flow_strength:.2f}, 情绪{senti_strength:.2f})"
        else:
            # 非明显单边趋势，根据次要信号或观望
            if change_24h > 1 and volume_strength > 0.7 and not has_long:
                # 小幅上涨但放量，很可能是突破前兆，尝试少量买入
                action = "buy"
                confidence = 0.65
                reasoning = f"{symbol}放量上涨小幅{change_24h:.2f}%，可能酝酿突破，可少量建仓观察"
            elif change_24h < -1 and volume_strength > 0.7 and not has_short:
                # 小幅下跌放量，尝试少量做空（逆势反弹风险高，仓位更小）
                action = "short"
                confidence = 0.65
                reasoning = f"{symbol}放量下跌{change_24h:.2f}%，趋势偏空，可轻仓试探做空"
            else:
                # 其他情况观望
                action = "hold"
                confidence = 0.5
                reasoning = f"{symbol}市场横盘/不明确：24h变化{change_24h:.2f}%, 观望等待明确信号"

        # 风险评分（0-1越低越安全）
        # 根据波动率和杠杆情况调整：波动大或杠杆高则风险高
        risk_score = 0.3  # 基础低风险
        if volatility:
            # 若提供波动率数据，例如日内波幅%
            if volatility > 0.05:   # 日波幅大于5%算高波动
                risk_score = 0.7
            elif volatility < 0.01:  # 日波幅小于1%算低波动
                risk_score = 0.2
        # 杠杆风险：检查总杠杆率（假设portfolio给出总资产与总仓位情况）
        total_exposure = portfolio.get('total_exposure', 0)  # 所有仓位名义价值
        if equity > 0 and total_exposure > equity:
            leverage_used = total_exposure / equity
            if leverage_used > 1:
                # 每增加一点杠杆提高风险评分
                risk_score = min(risk_score + 0.1 * (leverage_used - 1), 1.0)

        # 返回决策结果
        return {
            'symbol': symbol,
            'action': action,
            'confidence': round(confidence, 2),
            'reasoning': reasoning,
            'risk_score': round(risk_score, 2),
            'position_size': self.base_position_pct,  # 基础仓位占比，可根据risk_score动态调整
            'leverage': 1 if action in ['hold', 'sell', 'cover'] else self.determine_leverage(confidence, risk_score),
            'key_metrics': {
                'price': price,
                'change_24h': change_24h,
                'price_position': round(price_position, 2),
                'volume_strength': round(volume_strength, 2),
                'flow_strength': round(flow_strength, 2),
                'sentiment': round(senti_strength, 2)
            }
        }

    def determine_leverage(self, confidence: float, risk_score: float) -> float:
        """根据置信度和风险水平决定使用的杠杆倍数"""
        # 简单策略：高置信度且低风险时提高杠杆，其他情况下1倍或低杠杆
        if confidence > 0.8 and risk_score < 0.5:
            return min(self.max_leverage, 2)  # 置信强且风险不高，用2倍杠杆
        elif confidence > 0.9 and risk_score < 0.4:
            return min(self.max_leverage, 3)  # 非常有把握且风险很低，可到3倍
        else:
            return 1  # 默认为无杠杆或1倍


# 全局高级策略实例
advanced_strategy = AdvancedTradingStrategy()

# 兼容性别名（保持向后兼容）
simple_strategy = advanced_strategy
SimpleTradingStrategy = AdvancedTradingStrategy
