import json
import os
import pandas as pd
import numpy as np
import talib
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List

from backend.agents.base_agent import AgentAnalysis, AgentRole, BaseAgent

class EnhancedTradingStrategy (BaseAgent):
    """
    增强版加密货币交易策略
    增加多重因子判断震荡市场逻辑
    """
    def __init__(self, ai_model: str, api_key: str):
        super().__init__(AgentRole.TECHNICAL_ANALYST, ai_model, api_key)
        self.ai_model = ai_model
        self.api_key = api_key
        self.name = self._get_role_name()        
        self.adx_threshold_trend = 25,
        self.adx_threshold_range = 20
        self.bb_squeeze_threshold = 0.08  # 布林带收缩阈值 - 放宽避免长期不交易
        self.ma_tangle_threshold = 0.035   # 均线缠绕阈值 - 放宽避免长期不交易
        
    def calculate_adx(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """计算ADX指标"""
        return talib.ADX(high, low, close, timeperiod=period)
    
    def calculate_ema(self, close: pd.Series, period: int) -> pd.Series:
        """计算指数移动平均线"""
        return talib.EMA(close, timeperiod=period)
    
    def calculate_rsi(self, close: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI指标"""
        return talib.RSI(close, timeperiod=period)
    
    def calculate_macd(self, close: pd.Series, fastperiod: int = 12, slowperiod: int = 26, signalperiod: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算MACD指标"""
        macd, macd_signal, macd_hist = talib.MACD(close, fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod)
        return macd, macd_signal, macd_hist
    
    def calculate_bollinger_bands(self, close: pd.Series, period: int = 20, nbdev: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算布林带"""
        upper, middle, lower = talib.BBANDS(close, timeperiod=period, nbdevup=nbdev, nbdevdn=nbdev)
        return upper, middle, lower
    
    def calculate_bollinger_bandwidth(self, bb_upper: pd.Series, bb_lower: pd.Series, bb_middle: pd.Series) -> pd.Series:
        """计算布林带宽度指标"""
        return (bb_upper - bb_lower) / bb_middle
    
    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """计算ATR用于风险管理"""
        return talib.ATR(high, low, close, timeperiod=period)
    
    def calculate_volume_sma(self, volume: pd.Series, period: int = 5) -> pd.Series:
        """计算成交量移动平均"""
        return talib.SMA(volume, timeperiod=period)
    
    def calculate_obv(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """计算OBV (On-Balance Volume) 指标"""
        return talib.OBV(close, volume)
    
    def calculate_relative_volume(self, volume: pd.Series, period: int = 20) -> pd.Series:
        """
        计算相对成交量（量比）
        当前成交量 / 过去N期平均成交量
        """
        volume_ma = talib.SMA(volume, timeperiod=period)
        return volume / volume_ma
    
    def calculate_vwap(self, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        计算VWAP (Volume Weighted Average Price)
        累积成交额 / 累积成交量
        """
        typical_price = (high + low + close) / 3
        cumulative_tpv = (typical_price * volume).cumsum()
        cumulative_volume = volume.cumsum()
        vwap = cumulative_tpv / cumulative_volume
        return vwap
    
    def identify_price_range(self, high: pd.Series, low: pd.Series, close: pd.Series, lookback_period: int = 50) -> Dict[str, float]:
        """
        识别价格震荡区间
        返回支撑位和阻力位
        """
        recent_high = high.tail(lookback_period).max()
        recent_low = low.tail(lookback_period).min()
        
        # 计算斐波那契回撤水平作为潜在的支撑阻力
        range_height = recent_high - recent_low
        support_levels = [
            recent_low + range_height * 0.236,
            recent_low + range_height * 0.382,
            recent_low + range_height * 0.5
        ]
        resistance_levels = [
            recent_high - range_height * 0.236,
            recent_high - range_height * 0.382,
            recent_high - range_height * 0.5
        ]
        
        # 选择最接近当前价格的关键水平
        current_price = close.iloc[-1] if 'close' in locals() else (high.iloc[-1] + low.iloc[-1]) / 2
        
        closest_support = min(support_levels, key=lambda x: abs(x - current_price))
        closest_resistance = min(resistance_levels, key=lambda x: abs(x - current_price))
        
        return {
            'support': closest_support,
            'resistance': closest_resistance,
            'range_low': recent_low,
            'range_high': recent_high,
            'range_size': (recent_high - recent_low) / recent_low * 100  # 区间大小百分比
        }
    
    def check_ma_tangle(self, ema_fast: pd.Series, ema_medium: pd.Series, ema_slow: pd.Series) -> Dict[str, Any]:
        """
        检查均线是否缠绕（放宽条件，避免长期不交易）
        返回缠绕程度和方向
        """
        current_idx = -1
        
        # 计算均线之间的最大距离（标准化）
        price_level = (ema_fast.iloc[current_idx] + ema_slow.iloc[current_idx]) / 2
        max_ma_spread = max([
            abs(ema_fast.iloc[current_idx] - ema_medium.iloc[current_idx]),
            abs(ema_fast.iloc[current_idx] - ema_slow.iloc[current_idx]),
            abs(ema_medium.iloc[current_idx] - ema_slow.iloc[current_idx])
        ])
        
        normalized_spread = max_ma_spread / price_level
        
        # 判断均线排列
        ma_bullish = ema_fast.iloc[current_idx] > ema_medium.iloc[current_idx] > ema_slow.iloc[current_idx]
        ma_bearish = ema_fast.iloc[current_idx] < ema_medium.iloc[current_idx] < ema_slow.iloc[current_idx]
        ma_tangled = not (ma_bullish or ma_bearish)
        
        # 计算缠绕分数 (0-1, 越高表示缠绕越严重)
        # 放宽阈值，只有在非常紧密缠绕时才标记为缠绕
        tangle_score = min(normalized_spread / self.ma_tangle_threshold, 1.0)
        
        return {
            'is_tangled': ma_tangled and tangle_score > 0.85,  # 从0.7提高到0.85，更宽松
            'tangle_score': tangle_score,
            'normalized_spread': normalized_spread,
            'ma_direction': 'bullish' if ma_bullish else 'bearish' if ma_bearish else 'neutral'
        }
    
    def check_bollinger_squeeze(self, bb_upper: pd.Series, bb_lower: pd.Series, bb_middle: pd.Series, lookback_period: int = 20) -> Dict[str, Any]:
        """
        检查布林带是否收缩（挤压）- 放宽条件，避免长期不交易
        """
        current_idx = -1
        
        # 计算当前布林带宽度
        current_bb_width = (bb_upper.iloc[current_idx] - bb_lower.iloc[current_idx]) / bb_middle.iloc[current_idx]
        
        # 计算历史布林带宽度百分位
        historical_bb_widths = []
        for i in range(1, lookback_period + 1):
            if current_idx - i >= 0:
                width = (bb_upper.iloc[current_idx - i] - bb_lower.iloc[current_idx - i]) / bb_middle.iloc[current_idx - i]
                historical_bb_widths.append(width)
        
        if historical_bb_widths:
            width_percentile = sum(1 for w in historical_bb_widths if w > current_bb_width) / len(historical_bb_widths)
        else:
            width_percentile = 0.5
        
        # 判断是否挤压 - 放宽条件：只有极端挤压才标记为挤压
        is_squeeze = current_bb_width < self.bb_squeeze_threshold or width_percentile < 0.1  # 从0.2提高到0.1
        
        return {
            'is_squeeze': is_squeeze,
            'bb_width': current_bb_width,
            'width_percentile': width_percentile,
            'squeeze_intensity': 1 - (current_bb_width / self.bb_squeeze_threshold) if is_squeeze else 0
        }
    
    def analyze_price_action(self, high: pd.Series, low: pd.Series, close: pd.Series, lookback_period: int = 30) -> Dict[str, Any]:
        """
        分析价格行为，识别震荡特征
        """
        recent_highs = high.tail(lookback_period)
        recent_lows = low.tail(lookback_period)
        recent_closes = close.tail(lookback_period)
        
        # 计算价格在区间内的波动特征
        price_range = recent_highs.max() - recent_lows.min()
        avg_true_range = talib.ATR(high, low, close, timeperiod=14).iloc[-1]
        
        # 计算方向性移动
        upward_moves = 0
        downward_moves = 0
        
        for i in range(1, len(recent_closes)):
            if recent_closes.iloc[i] > recent_closes.iloc[i-1]:
                upward_moves += 1
            elif recent_closes.iloc[i] < recent_closes.iloc[i-1]:
                downward_moves += 1
        
        directional_bias = abs(upward_moves - downward_moves) / len(recent_closes)
        
        # 识别明显的支撑阻力测试
        support_tests = 0
        resistance_tests = 0
        support_level = recent_lows.min()
        resistance_level = recent_highs.max()
        
        for i in range(len(recent_lows)):
            if abs(recent_lows.iloc[i] - support_level) / support_level < 0.002:  # 0.2% 容差
                support_tests += 1
            if abs(recent_highs.iloc[i] - resistance_level) / resistance_level < 0.002:
                resistance_tests += 1
        
        return {
            'price_range_pct': (price_range / recent_lows.min()) * 100,
            'atr_to_range_ratio': avg_true_range / price_range if price_range > 0 else 0,
            'directional_bias': directional_bias,
            'support_tests': support_tests,
            'resistance_tests': resistance_tests,
            'is_ranging': directional_bias < 0.3 and support_tests >= 2 and resistance_tests >= 2,
            'range_quality_score': min(support_tests, resistance_tests) / (lookback_period / 10)  # 标准化分数
        }
    
    def analyze_volume_price_relationship(self, close: pd.Series, volume: pd.Series, 
                                          obv: pd.Series, relative_volume: pd.Series, 
                                          lookback_period: int = 20) -> Dict[str, Any]:
        """
        分析量价关系
        包括：OBV趋势、价格趋势一致性、量价背离、成交量确认等
        """
        current_idx = -1
        
        # 计算价格趋势（使用线性回归斜率）
        price_recent = close.tail(lookback_period)
        price_x = np.arange(len(price_recent))
        price_slope = np.polyfit(price_x, price_recent.values, 1)[0]
        price_trend = 'up' if price_slope > 0 else 'down' if price_slope < 0 else 'neutral'
        
        # 计算OBV趋势
        obv_recent = obv.tail(lookback_period)
        obv_x = np.arange(len(obv_recent))
        obv_slope = np.polyfit(obv_x, obv_recent.values, 1)[0]
        obv_trend = 'up' if obv_slope > 0 else 'down' if obv_slope < 0 else 'neutral'
        
        # 判断趋势一致性
        trend_confirmed = (price_trend == obv_trend) and (price_trend != 'neutral')
        
        # 检测价格新高但OBV未新高（看跌背离）
        price_new_high = close.iloc[current_idx] >= close.tail(lookback_period).max() * 0.999
        obv_new_high = obv.iloc[current_idx] >= obv.tail(lookback_period).max() * 0.999
        bearish_divergence = price_new_high and not obv_new_high
        
        # 检测价格新低但OBV未新低（看涨背离）
        price_new_low = close.iloc[current_idx] <= close.tail(lookback_period).min() * 1.001
        obv_new_low = obv.iloc[current_idx] <= obv.tail(lookback_period).min() * 1.001
        bullish_divergence = price_new_low and not obv_new_low
        
        # 当前相对成交量
        current_relative_volume = relative_volume.iloc[current_idx]
        
        # 量价配合评分
        volume_price_score = 0.5  # 基础分
        if trend_confirmed:
            volume_price_score += 0.3
        if current_relative_volume > 1.5:
            volume_price_score += 0.2
        if bearish_divergence:
            volume_price_score -= 0.3
        if bullish_divergence:
            volume_price_score += 0.3
        
        volume_price_score = max(0, min(1, volume_price_score))  # 限制在0-1之间
        
        return {
            'price_trend': price_trend,
            'obv_trend': obv_trend,
            'trend_confirmed': trend_confirmed,
            'bearish_divergence': bearish_divergence,
            'bullish_divergence': bullish_divergence,
            'current_relative_volume': current_relative_volume,
            'volume_price_score': volume_price_score,
            'price_slope': price_slope,
            'obv_slope': obv_slope
        }
    
    def enhanced_identify_market_regime(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        增强版市场状态识别 - 多重因子判断
        """
        high, low, close = df['high'], df['low'], df['close']
        
        # 计算基础指标
        adx = self.calculate_adx(high, low, close)
        ema_fast = self.calculate_ema(close, 8)
        ema_medium = self.calculate_ema(close, 21)
        ema_slow = self.calculate_ema(close, 55)
        bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(close)
        
        current_adx = adx.iloc[-1]
        
        # 多重因子分析
        ma_analysis = self.check_ma_tangle(ema_fast, ema_medium, ema_slow)
        bb_analysis = self.check_bollinger_squeeze(bb_upper, bb_lower, bb_middle)
        price_action_analysis = self.analyze_price_action(high, low, close)
        price_range_analysis = self.identify_price_range(high, low, close)
        
        # 综合判断市场状态
        ranging_factors = []
        trending_factors = []
        
        # ADX 因子
        if current_adx < self.adx_threshold_range:
            ranging_factors.append(('adx_low', 0.8))
        else:
            trending_factors.append(('adx_high', 0.8))
        
        # 均线缠绕因子
        if ma_analysis['is_tangled']:
            ranging_factors.append(('ma_tangled', 0.9))
        else:
            trending_factors.append(('ma_aligned', 0.7))
        
        # 布林带挤压因子
        if bb_analysis['is_squeeze']:
            ranging_factors.append(('bb_squeeze', 0.7))
        else:
            trending_factors.append(('bb_expanded', 0.6))
        
        # 价格行为因子
        if price_action_analysis['is_ranging']:
            ranging_factors.append(('price_action_ranging', 0.9))
        else:
            trending_factors.append(('price_action_trending', 0.8))
        
        # 价格区间因子
        if price_range_analysis['range_size'] < 10:  # 区间幅度小于10%
            ranging_factors.append(('narrow_range', 0.6))
        
        # 计算综合得分
        ranging_score = sum(weight for _, weight in ranging_factors) / len(ranging_factors) if ranging_factors else 0
        trending_score = sum(weight for _, weight in trending_factors) / len(trending_factors) if trending_factors else 0
        
        # 确定市场状态 - 降低阈值，更容易识别为趋势/震荡状态，避免长期uncertain
        if ranging_score > 0.55 and ranging_score > trending_score:  # 从0.7降低到0.55
            market_regime = 'ranging'
            confidence = ranging_score
        elif trending_score > 0.55 and trending_score > ranging_score:  # 从0.7降低到0.55
            market_regime = 'trending'
            confidence = trending_score
        else:
            # uncertain状态也更容易判断为趋势或震荡
            if ranging_score > trending_score and ranging_score > 0.4:
                market_regime = 'ranging'
                confidence = ranging_score * 0.8
            elif trending_score > ranging_score and trending_score > 0.4:
                market_regime = 'trending'
                confidence = trending_score * 0.8
            else:
                market_regime = 'uncertain'
                confidence = max(ranging_score, trending_score)
        
        return {
            'market_regime': market_regime,
            'confidence': confidence,
            'adx_value': current_adx,
            'ranging_score': ranging_score,
            'trending_score': trending_score,
            'factors': {
                'ranging_factors': ranging_factors,
                'trending_factors': trending_factors
            },
            'detailed_analysis': {
                'ma_analysis': ma_analysis,
                'bb_analysis': bb_analysis,
                'price_action_analysis': price_action_analysis,
                'price_range_analysis': price_range_analysis
            }
        }
    
    def trend_strategy_signal(self, close: pd.Series, volume: pd.Series, 
                            rsi: pd.Series, macd: pd.Series, macd_signal: pd.Series,
                            ema_fast: pd.Series, ema_slow: pd.Series, 
                            volume_sma: pd.Series, 
                            obv: pd.Series, relative_volume: pd.Series,
                            volume_price_analysis: Dict) -> Dict:
        """
        单边趋势策略信号生成 - 以量价比为核心判断依据
        量价配合分析 + MA + RSI + MACD确认
        """
        current_idx = -1
        
        # 趋势方向判断
        trend_direction = 'bullish' if ema_fast.iloc[current_idx] > ema_slow.iloc[current_idx] else 'bearish'
        
        # MACD信号
        macd_bullish = macd.iloc[current_idx] > macd_signal.iloc[current_idx]
        macd_bearish = macd.iloc[current_idx] < macd_signal.iloc[current_idx]
        
        # 成交量确认
        volume_confirmed = volume.iloc[current_idx] > volume_sma.iloc[current_idx]
        
        # 量价关系分析 - 核心判断依据
        trend_confirmed_by_obv = volume_price_analysis.get('trend_confirmed', False)
        bearish_divergence = volume_price_analysis.get('bearish_divergence', False)
        bullish_divergence = volume_price_analysis.get('bullish_divergence', False)
        current_relative_vol = volume_price_analysis.get('current_relative_volume', 1.0)
        volume_price_score = volume_price_analysis.get('volume_price_score', 0.5)
        
        signal = 'hold'
        confidence = 0
        signal_strength = 'normal'
        
        # 量价比评分系统 - 核心逻辑
        vp_confidence_boost = 0
        if volume_price_score > 0.7:
            vp_confidence_boost = 0.3  # 量价配合好，大幅提升置信度
        elif volume_price_score > 0.5:
            vp_confidence_boost = 0.15  # 量价配合一般，适度提升
        else:
            vp_confidence_boost = -0.2  # 量价配合差，降低置信度
        
        if trend_direction == 'bullish':
            # 多头趋势中的买入信号 - 量价比为核心
            base_confidence = 0.4  # 基础置信度
            
            # 量价趋势一致性是最重要的
            if trend_confirmed_by_obv:
                base_confidence += 0.25
            
            # RSI不过热
            if rsi.iloc[current_idx] < 70:
                base_confidence += 0.1
            
            # MACD金叉或向上
            if macd_bullish:
                base_confidence += 0.1
            
            # 如果基础条件满足，生成信号
            if base_confidence >= 0.5:
                signal = 'buy'
                confidence = base_confidence + vp_confidence_boost
                
                # 量比评估 - 决定信号强度
                if current_relative_vol > 2.5:
                    # 放量突破，强信号
                    signal_strength = 'strong'
                    confidence += 0.15
                elif current_relative_vol < 0.5:
                    # 缩量上涨，信号弱，但不完全丢弃（放宽条件）
                    if trend_confirmed_by_obv:
                        # 如果OBV趋势确认，即使缩量也保留信号
                        confidence *= 0.75
                        signal_strength = 'weak'
                    else:
                        # OBV不确认且缩量，丢弃信号
                        signal = 'hold'
                        confidence = 0.3
                        signal_strength = 'weak'
                else:
                    # 正常量能
                    if volume_confirmed:
                        confidence += 0.05
                
                # 看涨背离增强信号
                if bullish_divergence:
                    confidence += 0.1
                
        else:  # bearish trend
            # 空头趋势中的卖出信号 - 量价比为核心
            base_confidence = 0.4  # 基础置信度
            
            # 量价趋势一致性是最重要的
            if trend_confirmed_by_obv:
                base_confidence += 0.25
            
            # RSI不超卖
            if rsi.iloc[current_idx] > 30:
                base_confidence += 0.1
            
            # MACD死叉或向下
            if macd_bearish:
                base_confidence += 0.1
            
            # 如果基础条件满足，生成信号
            if base_confidence >= 0.5:
                signal = 'sell'
                confidence = base_confidence + vp_confidence_boost
                
                # 量比评估 - 决定信号强度
                if current_relative_vol > 2.5:
                    # 放量突破，强信号
                    signal_strength = 'strong'
                    confidence += 0.15
                elif current_relative_vol < 0.5:
                    # 缩量下跌，信号弱，但不完全丢弃（放宽条件）
                    if trend_confirmed_by_obv:
                        # 如果OBV趋势确认，即使缩量也保留信号
                        confidence *= 0.75
                        signal_strength = 'weak'
                    else:
                        # OBV不确认且缩量，丢弃信号
                        signal = 'hold'
                        confidence = 0.3
                        signal_strength = 'weak'
                else:
                    # 正常量能
                    if volume_confirmed:
                        confidence += 0.05
                
                # 看跌背离增强信号
                if bearish_divergence:
                    confidence += 0.1
        
        # 背离信号优先级较高
        if bearish_divergence and signal != 'sell' and current_relative_vol > 1.0:
            # 看跌背离 + 有成交量 -> 卖出信号
            signal = 'sell'
            confidence = 0.7
            signal_strength = 'divergence'
        
        # 限制置信度范围
        confidence = max(0.3, min(confidence, 0.95))
        
        return {
            'signal': signal,
            'trend_direction': trend_direction,
            'confidence': confidence,
            'signal_strength': signal_strength,
            'details': {
                'ema_fast': ema_fast.iloc[current_idx],
                'ema_slow': ema_slow.iloc[current_idx],
                'rsi': rsi.iloc[current_idx],
                'macd': macd.iloc[current_idx],
                'macd_signal': macd_signal.iloc[current_idx],
                'volume_ratio': volume.iloc[current_idx] / volume_sma.iloc[current_idx],
                'obv': obv.iloc[current_idx],
                'relative_volume': current_relative_vol,
                'volume_price_score': volume_price_score,
                'trend_confirmed_by_obv': trend_confirmed_by_obv,
                'bearish_divergence': bearish_divergence,
                'bullish_divergence': bullish_divergence
            }
        }
    
    def range_strategy_signal(self, close: pd.Series, rsi: pd.Series, 
                            bb_upper: pd.Series, bb_lower: pd.Series,
                            price_range_analysis: Dict,
                            relative_volume: pd.Series,
                            volume_price_analysis: Dict) -> Dict:
        """
        震荡策略信号生成 - 以量价比为核心判断依据
        量价配合分析 + RSI + 布林带 + 价格区间确认
        """
        current_idx = -1
        current_close = close.iloc[current_idx]
        current_rsi = rsi.iloc[current_idx]
        
        support = price_range_analysis['support']
        resistance = price_range_analysis['resistance']
        
        # 判断价格相对于支撑阻力的位置
        support_distance_pct = (current_close - support) / support * 100
        resistance_distance_pct = (resistance - current_close) / resistance * 100
        
        # 布林带位置判断
        bb_position = 'middle'
        if current_close <= bb_lower.iloc[current_idx] or support_distance_pct < 1:
            bb_position = 'lower_band'
        elif current_close >= bb_upper.iloc[current_idx] or resistance_distance_pct < 1:
            bb_position = 'upper_band'
        
        # 量价分析 - 核心判断依据
        current_relative_vol = volume_price_analysis.get('current_relative_volume', 1.0)
        bearish_divergence = volume_price_analysis.get('bearish_divergence', False)
        bullish_divergence = volume_price_analysis.get('bullish_divergence', False)
        volume_price_score = volume_price_analysis.get('volume_price_score', 0.5)
        
        signal = 'hold'
        confidence = 0
        trigger = None
        signal_strength = 'normal'
        
        # 量价比评分系统 - 核心逻辑
        vp_confidence_boost = 0
        if volume_price_score > 0.7:
            vp_confidence_boost = 0.25
        elif volume_price_score > 0.5:
            vp_confidence_boost = 0.1
        else:
            vp_confidence_boost = -0.15
        
        # 买入信号：触及下轨/支撑 + RSI超卖 - 放宽条件
        if bb_position == 'lower_band':
            # 放宽RSI条件，避免错过机会
            if current_rsi < 40:  # 从35放宽到40
                signal = 'buy'
                # 基础置信度
                if current_rsi < 25:
                    confidence = 0.75  # 强烈超卖
                    trigger = 'strong_oversold'
                elif current_rsi < 30:
                    confidence = 0.65  # 超卖
                    trigger = 'oversold'
                else:
                    confidence = 0.5  # 偏超卖
                    trigger = 'bb_lower'
                
                # 应用量价配合评分
                confidence += vp_confidence_boost
                
                # 量比评估 - 决定信号强度
                if current_relative_vol > 2.5:
                    # 放量突破，强信号
                    signal_strength = 'strong'
                    confidence += 0.15
                elif current_relative_vol < 0.5:
                    # 缩量，但不完全丢弃（放宽条件）
                    if bullish_divergence or volume_price_score > 0.6:
                        # 有看涨背离或量价配合好，保留信号
                        confidence *= 0.7
                        signal_strength = 'weak'
                    else:
                        # 量价都不好，降低置信度但仍保留信号（避免长期不交易）
                        confidence *= 0.6
                        signal_strength = 'weak'
                else:
                    # 正常量能
                    confidence += 0.05
                
                # 看涨背离增强信号
                if bullish_divergence:
                    confidence += 0.15
                    signal_strength = 'divergence' if signal_strength == 'normal' else signal_strength
            
        # 卖出信号：触及上轨/阻力 + RSI超买 - 放宽条件
        elif bb_position == 'upper_band':
            # 放宽RSI条件，避免错过机会
            if current_rsi > 60:  # 从65放宽到60
                signal = 'sell'
                # 基础置信度
                if current_rsi > 75:
                    confidence = 0.75  # 强烈超买
                    trigger = 'strong_overbought'
                elif current_rsi > 70:
                    confidence = 0.65  # 超买
                    trigger = 'overbought'
                else:
                    confidence = 0.5  # 偏超买
                    trigger = 'bb_upper'
                
                # 应用量价配合评分
                confidence += vp_confidence_boost
                
                # 量比评估 - 决定信号强度
                if current_relative_vol > 2.5:
                    # 放量突破，强信号
                    signal_strength = 'strong'
                    confidence += 0.15
                elif current_relative_vol < 0.5:
                    # 缩量，但不完全丢弃（放宽条件）
                    if bearish_divergence or volume_price_score > 0.6:
                        # 有看跌背离或量价配合好，保留信号
                        confidence *= 0.7
                        signal_strength = 'weak'
                    else:
                        # 量价都不好，降低置信度但仍保留信号（避免长期不交易）
                        confidence *= 0.6
                        signal_strength = 'weak'
                else:
                    # 正常量能
                    confidence += 0.05
                
                # 看跌背离增强信号
                if bearish_divergence:
                    confidence += 0.15
                    signal_strength = 'divergence' if signal_strength == 'normal' else signal_strength
        
        # 限制置信度范围
        confidence = max(0.3, min(confidence, 0.95))
        
        return {
            'signal': signal,
            'bb_position': bb_position,
            'trigger': trigger,
            'confidence': confidence,
            'signal_strength': signal_strength,
            'details': {
                'close': current_close,
                'bb_upper': bb_upper.iloc[current_idx],
                'bb_lower': bb_lower.iloc[current_idx],
                'rsi': current_rsi,
                'support': support,
                'resistance': resistance,
                'support_distance_pct': support_distance_pct,
                'resistance_distance_pct': resistance_distance_pct,
                'relative_volume': current_relative_vol,
                'volume_price_score': volume_price_score,
                'bearish_divergence': bearish_divergence,
                'bullish_divergence': bullish_divergence
            }
        }
    
    def calculate_stop_loss_take_profit(self, signal: str, entry_price: float, 
                                      atr: pd.Series, market_regime: str,
                                      price_range_analysis: Dict = None) -> Tuple[float, float]:
        """
        计算止损止盈位置
        """
        current_atr = atr.iloc[-1]
        
        if market_regime == 'trending':
            # 单边市使用较宽止损
            atr_multiplier_sl = 2.0
            atr_multiplier_tp = 4.0
        else:
            # 震荡市使用较紧止损，基于区间边界
            atr_multiplier_sl = 1.5
            atr_multiplier_tp = 2.5
            
            # 如果有价格区间分析，使用区间边界作为止损参考
            if price_range_analysis and signal == 'buy':
                atr_sl = entry_price - (current_atr * atr_multiplier_sl)
                range_sl = price_range_analysis['range_low']
                # 选择更保守的止损
                stop_loss = min(atr_sl, range_sl)
                return stop_loss, entry_price + (current_atr * atr_multiplier_tp)
            elif price_range_analysis and signal == 'sell':
                atr_sl = entry_price + (current_atr * atr_multiplier_sl)
                range_sl = price_range_analysis['range_high']
                # 选择更保守的止损
                stop_loss = max(atr_sl, range_sl)
                return stop_loss, entry_price - (current_atr * atr_multiplier_tp)
        
        if signal == 'buy':
            stop_loss = entry_price - (current_atr * atr_multiplier_sl)
            take_profit = entry_price + (current_atr * atr_multiplier_tp)
        elif signal == 'sell':
            stop_loss = entry_price + (current_atr * atr_multiplier_sl)
            take_profit = entry_price - (current_atr * atr_multiplier_tp)
        else:
            stop_loss = take_profit = 0
        
        return stop_loss, take_profit
    
    async def analyze(
        self,
        symbol: str,
        market_data: Dict,
        additional_data: Optional[Dict] = None
    ) -> AgentAnalysis:
        """
        综合分析市场并生成交易信号
        df需要包含: ['open', 'high', 'low', 'close', 'volume']
        """
        raw_klines = additional_data.get("raw_klines")
        df = make_df_handle(raw_klines,True)
        
        # 增强版市场状态识别
        regime_analysis = self.enhanced_identify_market_regime(df)
        
        # 计算所有技术指标
        high, low, close, volume = df['high'], df['low'], df['close'], df['volume']
        ema_fast = self.calculate_ema(close, 8)
        ema_slow = self.calculate_ema(close, 21)
        rsi = self.calculate_rsi(close)
        macd, macd_signal, macd_hist = self.calculate_macd(close)
        bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(close)
        atr = self.calculate_atr(high, low, close)
        volume_sma = self.calculate_volume_sma(volume)
        
        # 新增：量价分析指标
        obv = self.calculate_obv(close, volume)
        relative_volume = self.calculate_relative_volume(volume)
        vwap = self.calculate_vwap(high, low, close, volume)
        
        # 新增：量价关系分析
        volume_price_analysis = self.analyze_volume_price_relationship(
            close, volume, obv, relative_volume
        )
        
        result = {
            'market_regime': regime_analysis['market_regime'],
            'regime_confidence': regime_analysis['confidence'],
            'adx_value': regime_analysis['adx_value'],
            'ranging_score': regime_analysis['ranging_score'],
            'trending_score': regime_analysis['trending_score'],
            'regime_factors': regime_analysis['factors'],
            'detailed_analysis': regime_analysis['detailed_analysis'],
            'volume_price_analysis': volume_price_analysis,  # 新增
            'indicators': {
                'ema_fast': ema_fast.iloc[-1],
                'ema_slow': ema_slow.iloc[-1],
                'rsi': rsi.iloc[-1],
                'macd': macd.iloc[-1],
                'macd_signal': macd_signal.iloc[-1],
                'bb_upper': bb_upper.iloc[-1],
                'bb_middle': bb_middle.iloc[-1],
                'bb_lower': bb_lower.iloc[-1],
                'atr': atr.iloc[-1],
                'obv': obv.iloc[-1],  # 新增
                'relative_volume': relative_volume.iloc[-1],  # 新增
                'vwap': vwap.iloc[-1]  # 新增
            }
        }
        
        # 根据市场状态选择策略
        if regime_analysis['market_regime'] == 'trending':
            strategy_result = self.trend_strategy_signal(
                close, volume, rsi, macd, macd_signal, 
                ema_fast, ema_slow, volume_sma,
                obv, relative_volume, volume_price_analysis  # 新增参数
            )
            result['strategy'] = 'trend_strategy'
            
        elif regime_analysis['market_regime'] == 'ranging':
            strategy_result = self.range_strategy_signal(
                close, rsi, bb_upper, bb_lower,
                regime_analysis['detailed_analysis']['price_range_analysis'],
                relative_volume, volume_price_analysis  # 新增参数
            )
            result['strategy'] = 'range_strategy'
            
        else:  # uncertain
            strategy_result = {'signal': 'hold', 'confidence': 0}
            result['strategy'] = 'no_trade'
        
        result['signal'] = strategy_result['signal']
        result['risk_score'] = 0.0
        result['signal_strength'] = strategy_result.get('signal_strength', 'normal')
        
        # 如果有交易信号，计算止损止盈
        if strategy_result['signal'] in ['buy', 'sell']:
            stop_loss, take_profit = self.calculate_stop_loss_take_profit(
                strategy_result['signal'], close.iloc[-1], atr, 
                regime_analysis['market_regime'],
                regime_analysis['detailed_analysis']['price_range_analysis']
            )
            result['stop_loss'] = stop_loss
            result['take_profit'] = take_profit
            result['vwap'] = vwap.iloc[-1]  # 用于执行基准
            
        if strategy_result['signal'] == "sell":
            strategy_result['signal'] = "short"
        
        # 构建推理说明，包含量价分析信息
        reasoning = self._build_reasoning(result, volume_price_analysis, strategy_result)
        
        return AgentAnalysis(
            agent_role=self.role,
            recommendation=result.get('signal', 'hold'),
            confidence=strategy_result.get('confidence', 0),
            reasoning=reasoning,
            key_metrics=result.get('indicators', {}),
            risk_score=0,
            priority=5,
        )
    
    def _build_reasoning(self, result: Dict, volume_price_analysis: Dict, strategy_result: Dict) -> str:
        """构建包含量价分析的推理说明"""
        signal = result.get('signal', 'hold')
        market_regime = result.get('market_regime')
        
        # 基础市场状态
        base_reasoning = f"技术分析: 市场状态: {market_regime}\n"
        
        # 量价分析信息
        vp_info = f"量价分析: "
        if volume_price_analysis.get('trend_confirmed'):
            vp_info += "OBV趋势与价格趋势一致，趋势确认✓ "
        else:
            vp_info += "OBV趋势与价格趋势不一致⚠️ "
        
        if volume_price_analysis.get('bearish_divergence'):
            vp_info += "| 检测到看跌背离（价格新高但OBV未新高）🔻 "
        if volume_price_analysis.get('bullish_divergence'):
            vp_info += "| 检测到看涨背离（价格新低但OBV未新低）🔺 "
        
        rel_vol = volume_price_analysis.get('current_relative_volume', 1.0)
        if rel_vol > 2.5:
            vp_info += f"| 放量突破（量比: {rel_vol:.2f}）📈"
        elif rel_vol < 0.5:
            vp_info += f"| 缩量（量比: {rel_vol:.2f}）📉"
        else:
            vp_info += f"| 成交量正常（量比: {rel_vol:.2f}）"
        
        base_reasoning += vp_info + "\n"
        
        # 策略信息
        if market_regime == "trending":
            strategy_info = f"采用：趋势策略 (EMA + MACD + 成交量 + OBV确认)\n"
        else:
            strategy_info = f"采用：震荡策略 (RSI + 布林带 + 价格区间 + 量价配合)\n"
        
        base_reasoning += strategy_info
        
        # 信号强度
        signal_strength = strategy_result.get('signal_strength', 'normal')
        if signal_strength == 'strong':
            base_reasoning += f"信号强度: 强💪 (放量确认)\n"
        elif signal_strength == 'weak':
            base_reasoning += f"信号强度: 弱⚠️ (缩量警示)\n"
        elif signal_strength == 'divergence':
            base_reasoning += f"信号强度: 背离信号🔄\n"
        
        base_reasoning += f"最终信号: {signal}"
        
        # 如果有VWAP，添加执行建议
        if 'vwap' in result.get('indicators', {}):
            vwap = result['indicators']['vwap']
            current_price = result['indicators'].get('bb_middle', 0)
            if signal == 'buy' and current_price < vwap:
                base_reasoning += f"\n执行建议: 当前价格低于VWAP({vwap:.2f})，可考虑执行买入"
            elif signal == 'buy' and current_price > vwap:
                base_reasoning += f"\n执行建议: 当前价格高于VWAP({vwap:.2f})，建议等待回调"
        
        return base_reasoning

class OptimizedTradingStrategy(EnhancedTradingStrategy):
    """
    优化参数版本的交易策略
    """
    
    # def __init__(self):
    #     # 基于测试结果优化的参数
    #     super().__init__(
    #         adx_threshold_trend=25,  # 提高趋势阈值，减少误判
    #         adx_threshold_range=20,   # 降低震荡阈值
    #         bb_squeeze_threshold=0.03,  # 更严格的布林带收缩判断
    #         ma_tangle_threshold=0.015   # 更严格的均线缠绕判断
    #     )
    
    def enhanced_identify_market_regime(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        优化版市场状态识别 - 放宽过滤条件，避免长期不交易
        """
        result = super().enhanced_identify_market_regime(df)
        
        # 放宽额外的过滤条件，更容易识别为可交易状态
        if result['market_regime'] == 'ranging':
            # 在震荡市中，要求至少1个强信号因子（从2个降低到1个）
            strong_ranging_factors = [f for f, w in result['factors']['ranging_factors'] if w >= 0.7]
            if len(strong_ranging_factors) < 1:
                result['market_regime'] = 'uncertain'
                result['confidence'] *= 0.8  # 从0.7提高到0.8，更宽松
        
        elif result['market_regime'] == 'trending':
            # 在趋势市中，放宽ADX和均线要求
            if result['adx_value'] < 20 or result['detailed_analysis']['ma_analysis']['ma_direction'] == 'neutral':  # 从25降低到20
                result['market_regime'] = 'uncertain'
                result['confidence'] *= 0.7  # 从0.6提高到0.7
        
        return result
    
    def trend_strategy_signal(self, close: pd.Series, volume: pd.Series, 
                            rsi: pd.Series, macd: pd.Series, macd_signal: pd.Series,
                            ema_fast: pd.Series, ema_slow: pd.Series, 
                            volume_sma: pd.Series,
                            obv: pd.Series, relative_volume: pd.Series,
                            volume_price_analysis: Dict) -> Dict:
        """
        优化版趋势策略 - 以量价比为核心 + 放宽条件避免长期不交易
        """
        current_idx = -1
        
        # 基础条件
        trend_direction = 'bullish' if ema_fast.iloc[current_idx] > ema_slow.iloc[current_idx] else 'bearish'
        macd_bullish = macd.iloc[current_idx] > macd_signal.iloc[current_idx]
        macd_bearish = macd.iloc[current_idx] < macd_signal.iloc[current_idx]
        volume_confirmed = volume.iloc[current_idx] > volume_sma.iloc[current_idx] * 1.1  # 从1.2降低到1.1，放宽要求
        
        # 量价关系分析 - 核心判断依据
        trend_confirmed_by_obv = volume_price_analysis.get('trend_confirmed', False)
        bearish_divergence = volume_price_analysis.get('bearish_divergence', False)
        bullish_divergence = volume_price_analysis.get('bullish_divergence', False)
        current_relative_vol = volume_price_analysis.get('current_relative_volume', 1.0)
        volume_price_score = volume_price_analysis.get('volume_price_score', 0.5)
        
        signal = 'hold'
        confidence = 0
        signal_strength = 'normal'
        
        # 趋势强度过滤 - 放宽要求
        trend_strength = abs(ema_fast.iloc[current_idx] - ema_slow.iloc[current_idx]) / ema_slow.iloc[current_idx]
        
        # 量价比评分系统 - 核心逻辑
        vp_confidence_boost = 0
        if volume_price_score > 0.7:
            vp_confidence_boost = 0.3
        elif volume_price_score > 0.5:
            vp_confidence_boost = 0.15
        else:
            vp_confidence_boost = -0.15
        
        if trend_direction == 'bullish' and trend_strength > 0.003:  # 从0.005降低到0.003，更宽松
            # 优化买入条件 - 放宽要求
            if (rsi.iloc[current_idx] < 70 and  # 从35-65放宽到<70
                macd_bullish):  # 移除MACD>0和volume_confirmed的硬性要求
                
                base_confidence = 0.35
                
                # 量价趋势一致性
                if trend_confirmed_by_obv:
                    base_confidence += 0.25
                
                # RSI位置
                if 40 < rsi.iloc[current_idx] < 60:
                    base_confidence += 0.15
                elif rsi.iloc[current_idx] < 40:
                    base_confidence += 0.1
                
                # MACD在零轴上方额外加分
                if macd.iloc[current_idx] > 0:
                    base_confidence += 0.1
                
                # 成交量确认
                if volume_confirmed:
                    base_confidence += 0.1
                
                # 趋势强度
                if trend_strength > 0.008:
                    base_confidence += 0.1
                
                # 如果基础条件满足，生成信号
                if base_confidence >= 0.45:  # 从0.5降低到0.45，更容易生成信号
                    signal = 'buy'
                    confidence = base_confidence + vp_confidence_boost
                    
                    # 量比评估
                    if current_relative_vol > 2.5:
                        signal_strength = 'strong'
                        confidence += 0.15
                    elif current_relative_vol < 0.5:
                        # 缩量但不完全丢弃
                        if trend_confirmed_by_obv or volume_price_score > 0.6:
                            confidence *= 0.75
                            signal_strength = 'weak'
                        else:
                            confidence *= 0.65
                            signal_strength = 'weak'
                    else:
                        if volume_confirmed:
                            confidence += 0.05
                    
                    # 看涨背离增强
                    if bullish_divergence:
                        confidence += 0.1
                
        elif trend_direction == 'bearish' and trend_strength > 0.003:  # 从0.005降低到0.003
            # 优化卖出条件 - 放宽要求
            if (rsi.iloc[current_idx] > 30 and  # 从35-65放宽到>30
                macd_bearish):  # 移除MACD<0和volume_confirmed的硬性要求
                
                base_confidence = 0.35
                
                # 量价趋势一致性
                if trend_confirmed_by_obv:
                    base_confidence += 0.25
                
                # RSI位置
                if 40 < rsi.iloc[current_idx] < 60:
                    base_confidence += 0.15
                elif rsi.iloc[current_idx] > 60:
                    base_confidence += 0.1
                
                # MACD在零轴下方额外加分
                if macd.iloc[current_idx] < 0:
                    base_confidence += 0.1
                
                # 成交量确认
                if volume_confirmed:
                    base_confidence += 0.1
                
                # 趋势强度
                if trend_strength > 0.008:
                    base_confidence += 0.1
                
                # 如果基础条件满足，生成信号
                if base_confidence >= 0.45:  # 从0.5降低到0.45
                    signal = 'sell'
                    confidence = base_confidence + vp_confidence_boost
                    
                    # 量比评估
                    if current_relative_vol > 2.5:
                        signal_strength = 'strong'
                        confidence += 0.15
                    elif current_relative_vol < 0.5:
                        # 缩量但不完全丢弃
                        if trend_confirmed_by_obv or volume_price_score > 0.6:
                            confidence *= 0.75
                            signal_strength = 'weak'
                        else:
                            confidence *= 0.65
                            signal_strength = 'weak'
                    else:
                        if volume_confirmed:
                            confidence += 0.05
                    
                    # 看跌背离增强
                    if bearish_divergence:
                        confidence += 0.1
        
        # 背离信号优先级较高
        if bearish_divergence and signal != 'sell' and current_relative_vol > 0.8:  # 从1.0降低到0.8
            signal = 'sell'
            confidence = 0.7
            signal_strength = 'divergence'
        
        # 限制置信度范围
        confidence = max(0.3, min(confidence, 0.9))
        
        return {
            'signal': signal,
            'trend_direction': trend_direction,
            'confidence': confidence,
            'signal_strength': signal_strength,
            'details': {
                'ema_fast': ema_fast.iloc[current_idx],
                'ema_slow': ema_slow.iloc[current_idx],
                'rsi': rsi.iloc[current_idx],
                'macd': macd.iloc[current_idx],
                'macd_signal': macd_signal.iloc[current_idx],
                'volume_ratio': volume.iloc[current_idx] / volume_sma.iloc[current_idx],
                'trend_strength': trend_strength,
                'obv': obv.iloc[current_idx],
                'relative_volume': current_relative_vol,
                'volume_price_score': volume_price_score,
                'trend_confirmed_by_obv': trend_confirmed_by_obv,
                'bearish_divergence': bearish_divergence,
                'bullish_divergence': bullish_divergence
            }
        }
    
    def range_strategy_signal(self, close: pd.Series, rsi: pd.Series, 
                            bb_upper: pd.Series, bb_lower: pd.Series,
                            price_range_analysis: Dict,
                            relative_volume: pd.Series,
                            volume_price_analysis: Dict) -> Dict:
        """
        优化版震荡策略 - 以量价比为核心 + 放宽条件避免长期不交易
        """
        current_idx = -1
        current_close = close.iloc[current_idx]
        current_rsi = rsi.iloc[current_idx]
        
        support = price_range_analysis['support']
        resistance = price_range_analysis['resistance']
        
        # 判断价格位置（增加容差）- 更宽松
        support_distance_pct = (current_close - support) / support * 100
        resistance_distance_pct = (resistance - current_close) / resistance * 100
        
        bb_position = 'middle'
        if current_close <= bb_lower.iloc[current_idx] * 1.008 or support_distance_pct < 2:  # 从1.005和1.5放宽到1.008和2
            bb_position = 'lower_band'
        elif current_close >= bb_upper.iloc[current_idx] * 0.992 or resistance_distance_pct < 2:  # 从0.995和1.5放宽
            bb_position = 'upper_band'
        
        # 量价分析 - 核心判断依据
        current_relative_vol = volume_price_analysis.get('current_relative_volume', 1.0)
        bearish_divergence = volume_price_analysis.get('bearish_divergence', False)
        bullish_divergence = volume_price_analysis.get('bullish_divergence', False)
        volume_price_score = volume_price_analysis.get('volume_price_score', 0.5)
        
        signal = 'hold'
        confidence = 0
        trigger = None
        signal_strength = 'normal'
        
        # 量价比评分系统 - 核心逻辑
        vp_confidence_boost = 0
        if volume_price_score > 0.7:
            vp_confidence_boost = 0.25
        elif volume_price_score > 0.5:
            vp_confidence_boost = 0.1
        else:
            vp_confidence_boost = -0.1
        
        # 优化买入条件 - 大幅放宽
        if bb_position == 'lower_band':
            # 放宽RSI条件
            if current_rsi < 45:  # 从25/32/35大幅放宽到45
                signal = 'buy'
                # 分级置信度
                if current_rsi < 20:
                    confidence = 0.8
                    trigger = 'extreme_oversold'
                elif current_rsi < 28:
                    confidence = 0.7
                    trigger = 'strong_oversold'
                elif current_rsi < 35:
                    confidence = 0.6
                    trigger = 'oversold'
                else:
                    confidence = 0.5
                    trigger = 'bb_lower'
                
                # 应用量价配合评分
                confidence += vp_confidence_boost
                
                # 量比评估
                if current_relative_vol > 2.5:
                    signal_strength = 'strong'
                    confidence += 0.15
                elif current_relative_vol < 0.5:
                    # 缩量但不完全丢弃
                    if bullish_divergence or volume_price_score > 0.55:  # 从0.6降低到0.55
                        confidence *= 0.75
                        signal_strength = 'weak'
                    else:
                        # 仍保留信号，只是降低置信度
                        confidence *= 0.65
                        signal_strength = 'weak'
                else:
                    confidence += 0.05
                
                # 看涨背离增强
                if bullish_divergence:
                    confidence += 0.15
                    signal_strength = 'divergence' if signal_strength == 'normal' else signal_strength
                
        # 优化卖出条件 - 大幅放宽
        elif bb_position == 'upper_band':
            # 放宽RSI条件
            if current_rsi > 55:  # 从75/68/65大幅放宽到55
                signal = 'sell'
                # 分级置信度
                if current_rsi > 80:
                    confidence = 0.8
                    trigger = 'extreme_overbought'
                elif current_rsi > 72:
                    confidence = 0.7
                    trigger = 'strong_overbought'
                elif current_rsi > 65:
                    confidence = 0.6
                    trigger = 'overbought'
                else:
                    confidence = 0.5
                    trigger = 'bb_upper'
                
                # 应用量价配合评分
                confidence += vp_confidence_boost
                
                # 量比评估
                if current_relative_vol > 2.5:
                    signal_strength = 'strong'
                    confidence += 0.15
                elif current_relative_vol < 0.5:
                    # 缩量但不完全丢弃
                    if bearish_divergence or volume_price_score > 0.55:  # 从0.6降低到0.55
                        confidence *= 0.75
                        signal_strength = 'weak'
                    else:
                        # 仍保留信号，只是降低置信度
                        confidence *= 0.65
                        signal_strength = 'weak'
                else:
                    confidence += 0.05
                
                # 看跌背离增强
                if bearish_divergence:
                    confidence += 0.15
                    signal_strength = 'divergence' if signal_strength == 'normal' else signal_strength
        
        # 限制置信度范围
        confidence = max(0.3, min(confidence, 0.95))
        
        return {
            'signal': signal,
            'bb_position': bb_position,
            'trigger': trigger,
            'confidence': confidence,
            'signal_strength': signal_strength,
            'details': {
                'close': current_close,
                'bb_upper': bb_upper.iloc[current_idx],
                'bb_lower': bb_lower.iloc[current_idx],
                'rsi': current_rsi,
                'support': support,
                'resistance': resistance,
                'support_distance_pct': support_distance_pct,
                'resistance_distance_pct': resistance_distance_pct,
                'relative_volume': current_relative_vol,
                'volume_price_score': volume_price_score,
                'bearish_divergence': bearish_divergence,
                'bullish_divergence': bullish_divergence
            }
        }


HIGH_WIN_RATE_PROMPT_TEMPLATE = """
# 加密货币交易决策分析报告

## 📊 市场状态概览
- **交易品种**: {symbol}
- **时间框架**: {timeframe}
- **分析时间**: {timestamp}
- **当前价格**: {current_price:.2f}
- **市场状态**: {market_regime} (置信度: {regime_confidence:.1%})

## 🎯 技术指标信号

### 趋势强度分析
- **ADX趋势强度**: {adx_value:.1f} ({adx_interpretation})
- **均线排列**: {ma_direction} (缠绕强度: {ma_tangle_intensity:.1%})
- **布林带状态**: {bb_status} (宽度: {bb_width:.3f})

### 动量指标
- **RSI动量**: {rsi_value:.1f} ({rsi_status})
- **MACD信号**: {macd_signal}
- **成交量确认**: {volume_status}

### 价格位置分析
- **相对布林带**: {bb_position}
- **支撑位**: {support_level:.2f} (距离: {support_distance:.2f}%)
- **阻力位**: {resistance_level:.2f} (距离: {resistance_distance:.2f}%)

## 📈 交易信号详情

### 核心信号
- **交易方向**: {trade_signal}
- **信号类型**: {signal_type}
- **信号强度**: {signal_confidence:.1%}
- **触发条件**: {trigger_conditions}

### 策略匹配度
- **市场环境匹配**: {market_fit_score}/10
- **指标一致性**: {indicator_consistency}/10
- **时间框架确认**: {timeframe_confirmation}/10

## ⚠️ 风险管理

### 关键参数
- **入场价格**: {entry_price:.2f}
- **止损价格**: {stop_loss:.2f} (风险: {risk_pct:.2f}%)
- **止盈价格**: {take_profit:.2f} (回报: {reward_pct:.2f}%)
- **风险回报比**: {risk_reward_ratio:.2f}:1

### 仓位建议
- **建议仓位**: {position_size}%
- **最大亏损**: {max_loss_percent:.1f}% of capital
- **持仓时间**: {holding_period}

## 🔍 关键确认因素

### 支持交易的积极因素
{positive_factors}

### 需要注意的风险因素
{risk_factors}

### 需要监控的关键水平
{key_levels_to_watch}

## 🤖 AI Agent 决策指导

### 决策框架
请基于以下维度评估此交易机会：

1. **信号质量评估** (0-10分):
   - 技术指标一致性: {indicator_consistency}
   - 市场环境匹配度: {market_fit_score}
   - 风险管理合理性: {risk_management_score}

2. **时机评估** (0-10分):
   - 当前市场周期位置
   - 重大事件影响
   - 多时间框架确认

3. **风险评估** (0-10分):
   - 潜在下行风险
   - 波动率影响
   - 黑天鹅事件可能性

### 最终决策要求
分别提供五种方向（buy/sell/hold/short/cover）以下格式的决策:

**最终决策**: [buy/sell/hold/short/cover]
**信心程度**: [0-100%]
**主要依据**: [简要说明3个关键因素]
**风险管理**: [具体的仓位和止损建议]
**监控要点**: [需要重点关注的2-3个指标]


"""

class TradingDecisionRenderer:
    """
    交易决策结果渲染器
    将策略分析结果渲染到高胜率提示词模板中
    """
    
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def render_decision_prompt(self, strategy_result: Dict, df: pd.DataFrame, 
                             symbol: str = "BTCUSDT", timeframe: str = "1h") -> str:
        """
        将策略结果渲染到提示词模板中
        """
        # 提取基础数据
        current_price = df['close'].iloc[-1] if not df.empty else 0
        
        # 渲染所有模板变量
        template_vars = self._prepare_template_variables(strategy_result, df, symbol, timeframe)
        
        # 使用模板渲染
        prompt = HIGH_WIN_RATE_PROMPT_TEMPLATE.format(**template_vars)
        
        return prompt
    
    def _prepare_template_variables(self, result: Dict, df: pd.DataFrame, 
                                  symbol: str, timeframe: str) -> Dict[str, any]:
        """
        准备模板变量
        """
        current_price = df['close'].iloc[-1] if not df.empty else 0
        
        # 提取指标数据
        indicators = result.get('indicators', {})
        details = result.get('details', {})
        regime_analysis = result.get('detailed_analysis', {})
        
        # ADX 分析
        adx_value = result.get('adx_value', 0)
        adx_interpretation = self._get_adx_interpretation(adx_value)
        
        # 均线分析
        ma_analysis = regime_analysis.get('ma_analysis', {})
        ma_direction = ma_analysis.get('ma_direction', 'neutral').capitalize()
        ma_tangle_intensity = ma_analysis.get('tangle_score', 0)
        
        # 布林带分析
        bb_analysis = regime_analysis.get('bb_analysis', {})
        bb_status = "收缩挤压" if bb_analysis.get('is_squeeze', False) else "正常宽度"
        bb_width = bb_analysis.get('bb_width', 0)
        
        # RSI 分析
        rsi_value = details.get('rsi', 50)
        rsi_status = self._get_rsi_status(rsi_value)
        
        # MACD 分析
        macd_signal = self._get_macd_signal(indicators.get('macd'), indicators.get('macd_signal'))
        
        # 成交量分析
        volume_ratio = details.get('volume_ratio', 1)
        volume_status = "放量确认" if volume_ratio > 1.2 else "缩量谨慎" if volume_ratio < 0.8 else "正常量能"
        
        # 价格位置分析
        bb_position = result.get('bb_position', 'middle')
        support_level = details.get('support', current_price * 0.98)
        resistance_level = details.get('resistance', current_price * 1.02)
        support_distance = ((current_price - support_level) / support_level * 100) if support_level > 0 else 0
        resistance_distance = ((resistance_level - current_price) / resistance_level * 100) if resistance_level > 0 else 0
        
        # 交易信号
        trade_signal = result.get('signal', 'hold').upper()
        signal_type = result.get('type', 'no_signal').replace('_', ' ').title()
        signal_confidence = result.get('confidence', 0)
        
        # 触发条件
        trigger_conditions = self._get_trigger_conditions(result)
        
        # 风险管理
        stop_loss = result.get('stop_loss', 0)
        take_profit = result.get('take_profit', 0)
        risk_pct = abs((current_price - stop_loss) / current_price * 100) if stop_loss else 0
        reward_pct = abs((take_profit - current_price) / current_price * 100) if take_profit else 0
        risk_reward_ratio = reward_pct / risk_pct if risk_pct > 0 else 0
        
        # 评分计算
        market_fit_score = self._calculate_market_fit_score(result)
        indicator_consistency = self._calculate_indicator_consistency(result)
        risk_management_score = self._calculate_risk_management_score(risk_reward_ratio, risk_pct)
        
        # 准备模板变量字典
        template_vars = {
            'symbol': symbol,
            'timeframe': timeframe,
            'timestamp': self.timestamp,
            'current_price': current_price,
            'market_regime': result.get('market_regime', 'unknown').capitalize(),
            'regime_confidence': result.get('regime_confidence', 0),
            'adx_value': adx_value,
            'adx_interpretation': adx_interpretation,
            'ma_direction': ma_direction,
            'ma_tangle_intensity': ma_tangle_intensity,
            'bb_status': bb_status,
            'bb_width': bb_width,
            'rsi_value': rsi_value,
            'rsi_status': rsi_status,
            'macd_signal': macd_signal,
            'volume_status': volume_status,
            'bb_position': bb_position,
            'support_level': support_level,
            'resistance_level': resistance_level,
            'support_distance': support_distance,
            'resistance_distance': resistance_distance,
            'trade_signal': trade_signal,
            'signal_type': signal_type,
            'signal_confidence': signal_confidence,
            'trigger_conditions': trigger_conditions,
            'market_fit_score': market_fit_score,
            'indicator_consistency': indicator_consistency,
            'timeframe_confirmation': 7,  # 假设值，可根据多时间框架分析计算
            'entry_price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_pct': risk_pct,
            'reward_pct': reward_pct,
            'risk_reward_ratio': risk_reward_ratio,
            'position_size': self._calculate_position_size(signal_confidence, risk_pct),
            'max_loss_percent': min(risk_pct * 2, 5),  # 最大亏损限制在5%
            'holding_period': self._get_holding_period(timeframe, result.get('market_regime')),
            'positive_factors': self._get_positive_factors(result),
            'risk_factors': self._get_risk_factors(result),
            'key_levels_to_watch': self._get_key_levels_to_watch(result, support_level, resistance_level),
            'risk_management_score': risk_management_score
        }
        
        return template_vars
    
    def _get_adx_interpretation(self, adx_value: float) -> str:
        """获取ADX解读"""
        if adx_value > 25:
            return "强趋势市场"
        elif adx_value > 20:
            return "中等趋势"
        elif adx_value > 15:
            return "弱趋势"
        else:
            return "震荡市场"
    
    def _get_rsi_status(self, rsi_value: float) -> str:
        """获取RSI状态"""
        if rsi_value > 70:
            return "超买"
        elif rsi_value > 60:
            return "偏多"
        elif rsi_value > 40:
            return "中性"
        elif rsi_value > 30:
            return "偏空"
        else:
            return "超卖"
    
    def _get_macd_signal(self, macd_line, macd_signal) -> str:
        """获取MACD信号"""
        if macd_line is None or macd_signal is None:
            return "等待信号"
        
        current_macd = macd_line.iloc[-1] if not macd_line.empty else 0
        current_signal = macd_signal.iloc[-1] if not macd_signal.empty else 0
        
        if current_macd > current_signal and current_macd > 0:
            return "强势金叉"
        elif current_macd > current_signal:
            return "金叉"
        elif current_macd < current_signal and current_macd < 0:
            return "强势死叉"
        elif current_macd < current_signal:
            return "死叉"
        else:
            return "信号模糊"
    
    def _get_trigger_conditions(self, result: Dict) -> str:
        """获取触发条件描述"""
        signal = result.get('signal')
        signal_type = result.get('type', '')
        details = result.get('details', {})
        
        if signal == 'buy':
            if 'range' in signal_type:
                return f"价格触及支撑位 + RSI超卖({details.get('rsi', 0):.1f})"
            elif 'trend' in signal_type:
                return f"趋势回调 + 指标金叉 + 成交量确认"
            elif 'breakout' in signal_type:
                return f"布林带突破 + 放量确认"
            else:
                return "多重技术指标确认"
        elif signal == 'sell':
            if 'range' in signal_type:
                return f"价格触及阻力位 + RSI超买({details.get('rsi', 0):.1f})"
            elif 'trend' in signal_type:
                return f"趋势反弹 + 指标死叉 + 成交量确认"
            elif 'breakout' in signal_type:
                return f"布林带跌破 + 放量确认"
            else:
                return "多重技术指标确认"
        else:
            return "等待更明确信号"
    
    def _calculate_market_fit_score(self, result: Dict) -> int:
        """计算市场环境匹配度评分"""
        regime = result.get('market_regime')
        signal_type = result.get('type', '')
        
        # 策略与市场状态匹配度
        if regime == 'trending' and 'trend' in signal_type:
            return 9
        elif regime == 'ranging' and 'range' in signal_type:
            return 9
        elif regime == 'transition' and 'breakout' in signal_type:
            return 8
        else:
            return 6  # 基本匹配
    
    def _calculate_indicator_consistency(self, result: Dict) -> int:
        """计算指标一致性评分"""
        score = 6  # 基础分
        
        # 基于信号强度
        confidence = result.get('confidence', 0)
        if confidence > 0.8:
            score += 2
        elif confidence > 0.6:
            score += 1
        
        # 基于市场状态置信度
        regime_confidence = result.get('regime_confidence', 0)
        if regime_confidence > 0.8:
            score += 2
        elif regime_confidence > 0.6:
            score += 1
        
        return min(score, 10)
    
    def _calculate_risk_management_score(self, risk_reward_ratio: float, risk_pct: float) -> int:
        """计算风险管理评分"""
        score = 6  # 基础分
        
        # 风险回报比评分
        if risk_reward_ratio > 2:
            score += 2
        elif risk_reward_ratio > 1.5:
            score += 1
        
        # 风险控制评分
        if risk_pct < 2:
            score += 2
        elif risk_pct < 3:
            score += 1
        
        return min(score, 10)
    
    def _calculate_position_size(self, signal_confidence: float, risk_pct: float) -> float:
        """计算建议仓位"""
        if signal_confidence > 0.8:
            base_size = 5
        elif signal_confidence > 0.6:
            base_size = 3
        elif signal_confidence > 0.4:
            base_size = 2
        else:
            base_size = 1
        
        # 根据风险调整
        if risk_pct > 3:
            return base_size * 0.5
        elif risk_pct > 2:
            return base_size * 0.8
        else:
            return base_size
    
    def _get_holding_period(self, timeframe: str, market_regime: str) -> str:
        """获取建议持仓时间"""
        base_hours = {
            '1h': 4,
            '4h': 16,
            '15m': 2
        }.get(timeframe, 8)
        
        if market_regime == 'trending':
            return f"{base_hours}-{base_hours * 3}小时"
        else:
            return f"{base_hours}-{base_hours * 2}小时"
    
    def _get_positive_factors(self, result: Dict) -> str:
        """获取积极因素"""
        factors = []
        
        signal_confidence = result.get('confidence', 0)
        regime_confidence = result.get('regime_confidence', 0)
        details = result.get('details', {})
        
        if signal_confidence > 0.7:
            factors.append("✅ 信号强度高，置信度超过70%")
        
        if regime_confidence > 0.7:
            factors.append("✅ 市场状态明确，策略匹配度高")
        
        if details.get('volume_ratio', 1) > 1.2:
            factors.append("✅ 成交量放大确认信号有效性")
        
        rsi = details.get('rsi', 50)
        if (result.get('signal') == 'buy' and rsi < 35) or (result.get('signal') == 'sell' and rsi > 65):
            factors.append("✅ RSI处于极值区域，反转概率高")
        
        if not factors:
            factors.append("⏳ 等待更多确认信号")
        
        return "\n".join(factors)
    
    def _get_risk_factors(self, result: Dict) -> str:
        """获取风险因素"""
        factors = []
        
        signal_confidence = result.get('confidence', 0)
        regime_confidence = result.get('regime_confidence', 0)
        adx_value = result.get('adx_value', 0)
        
        if signal_confidence < 0.5:
            factors.append("⚠️ 信号强度不足，建议谨慎")
        
        if regime_confidence < 0.6:
            factors.append("⚠️ 市场状态不明确，存在不确定性")
        
        if adx_value < 15:
            factors.append("⚠️ 趋势强度弱，可能继续震荡")
        
        if result.get('market_regime') == 'transition':
            factors.append("⚠️ 市场处于过渡期，方向可能突变")
        
        if not factors:
            factors.append("✅ 风险因素相对可控")
        
        return "\n".join(factors)
    
    def _get_key_levels_to_watch(self, result: Dict, support: float, resistance: float) -> str:
        """获取需要监控的关键水平"""
        levels = []
        
        stop_loss = result.get('stop_loss')
        take_profit = result.get('take_profit')
        
        if stop_loss:
            levels.append(f"🔴 止损位: {stop_loss:.2f}")
        
        if take_profit:
            levels.append(f"🟢 止盈位: {take_profit:.2f}")
        
        levels.append(f"📉 支撑位: {support:.2f}")
        levels.append(f"📈 阻力位: {resistance:.2f}")
        
        # 添加移动止损位（如果适用）
        if result.get('signal') == 'buy':
            trailing_stop = support * 0.995  # 0.5% below support
            levels.append(f"🎯 移动止损: {trailing_stop:.2f} (跌破支撑)")
        elif result.get('signal') == 'sell':
            trailing_stop = resistance * 1.005  # 0.5% above resistance
            levels.append(f"🎯 移动止损: {trailing_stop:.2f} (突破阻力)")
        
        return "\n".join(levels)

# 获取当前文件路径
current_file_path = os.path.dirname(os.path.abspath(__file__))
# 使用示例
def fetch_market_data(symbol: str, timeframe: str):
    symbol = symbol.replace("/", "")
    symbol = symbol.replace("USDT", "")
    symbol = symbol.replace("USDC", "")
    symbol = symbol.replace("USDC", "")
    with open(f"{current_file_path}/check_data/{symbol}.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    # 按 t 升序排序
    data.sort(key=lambda x: x["T"])
    index = -240
    return make_df_handle_test(data=data[index:index+100],rename=True)
def make_df_handle_test(data:list,rename = False):
    df = pd.DataFrame(data)
    if rename:
        df = df.rename(columns={"t": "time", "c": "close", "h": "high", "l": "low", "o": "open", "v": "volume"})
        df = df[["time", "close", "high", "low", "open", "volume"]]
    df["time"] = pd.to_datetime(df["time"], unit="ms")
    df = df.set_index("time")
    df = df.sort_index()
    return df
def make_df_handle(data:list,rename = False):
    df = pd.DataFrame(data)
    if rename:
        df = df.rename(columns={"timestamp": "time", "close": "close", "high": "high", "low": "low", "open": "open", "volume": "volume"})
        df = df[["time", "close", "high", "low", "open", "volume"]]
    df["time"] = pd.to_datetime(df["time"], unit="ms")
    df = df.set_index("time")
    df = df.sort_index()
    return df  
def make_df_handle(data:list,rename = False):
    df = pd.DataFrame(data)
    if rename:
        df = df.rename(columns={"timestamp": "time", "close": "close", "high": "high", "low": "low", "open": "open", "volume": "volume"})
        df = df[["time", "close", "high", "low", "open", "volume"]]
    df["time"] = pd.to_datetime(df["time"], unit="ms")
    df = df.set_index("time")
    df = df.sort_index()
    return df
def improved_backtest(strategy, df, hold_periods=[1, 3, 5, 10], stop_loss_pct=0.02, take_profit_pct=0.04):
    """
    改进的回测方法
    """
    total_trades = 0
    successful_trades = 0
    trade_results = []
    
    for i in range(100, len(df) - max(hold_periods)):
        window = df.iloc[i-100:i+1]
        analysis_df = window.iloc[:-1]  # 用于分析的数据
        signal_data = window.iloc[-1:]  # 信号发生时的数据
        
        result = strategy.analyze_market(analysis_df)
        
        if result.get('signal') in ('buy', 'sell'):
            entry_price = signal_data['close'].iloc[0]
            entry_time = signal_data.index[0]
            
            # 为每个持仓周期分别测试
            for hold_period in hold_periods:
                if i + hold_period < len(df):
                    future_data = df.iloc[i+1:i+1+hold_period]
                    
                    # 检查期间是否触发止损止盈
                    stop_loss_price = entry_price * (1 - stop_loss_pct) if result['signal'] == 'buy' else entry_price * (1 + stop_loss_pct)
                    take_profit_price = entry_price * (1 + take_profit_pct) if result['signal'] == 'buy' else entry_price * (1 - take_profit_pct)
                    
                    exit_reason = "hold_period"
                    exit_price = future_data['close'].iloc[-1]
                    
                    # 检查期间是否触发止损止盈
                    for j, (idx, row) in enumerate(future_data.iterrows()):
                        if result['signal'] == 'buy':
                            if row['low'] <= stop_loss_price:
                                exit_price = stop_loss_price
                                exit_reason = "stop_loss"
                                break
                            elif row['high'] >= take_profit_price:
                                exit_price = take_profit_price
                                exit_reason = "take_profit"
                                break
                        else:  # sell
                            if row['high'] >= stop_loss_price:
                                exit_price = stop_loss_price
                                exit_reason = "stop_loss"
                                break
                            elif row['low'] <= take_profit_price:
                                exit_price = take_profit_price
                                exit_reason = "take_profit"
                                break
                    
                    # 判断交易结果
                    if result['signal'] == 'buy':
                        is_profitable = exit_price > entry_price
                        profit_pct = (exit_price - entry_price) / entry_price
                    else:  # sell
                        is_profitable = exit_price < entry_price
                        profit_pct = (entry_price - exit_price) / entry_price
                    
                    total_trades += 1
                    if is_profitable:
                        successful_trades += 1
                    
                    trade_results.append({
                        'entry_time': entry_time,
                        'signal': result['signal'],
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'hold_period': hold_period,
                        'exit_reason': exit_reason,
                        'profit_pct': profit_pct,
                        'successful': is_profitable,
                        'market_regime': result.get('market_regime', 'unknown'),
                        'confidence': result.get('confidence', 0)
                    })
                    
                    print(f"信号: {result['signal']}, 持仓: {hold_period}根K线, 结果: {'盈利' if is_profitable else '亏损'}, 收益率: {profit_pct:.2%}, 退出原因: {exit_reason}")
    
    return total_trades, successful_trades, trade_results

def comprehensive_backtest_analysis(strategy, df, symbol="BTCUSDT"):
    """
    综合回测分析
    """
    print("开始综合回测分析...")
    
    # 测试不同参数组合
    test_scenarios = [
        {"hold_periods": [1], "stop_loss_pct": 0.01, "take_profit_pct": 0.02},
        {"hold_periods": [2], "stop_loss_pct": 0.01, "take_profit_pct": 0.02},
        {"hold_periods": [3], "stop_loss_pct": 0.01, "take_profit_pct": 0.02},
        {"hold_periods": [4], "stop_loss_pct": 0.015, "take_profit_pct": 0.03},
        {"hold_periods": [5], "stop_loss_pct": 0.015, "take_profit_pct": 0.03},
        {"hold_periods": [6], "stop_loss_pct": 0.015, "take_profit_pct": 0.03},
        # {"hold_periods": [5, 10], "stop_loss_pct": 0.02, "take_profit_pct": 0.04},
        # {"hold_periods": [1, 3, 5, 10], "stop_loss_pct": 0.01, "take_profit_pct": 0.02},
    ]
    
    best_scenario = None
    best_success_rate = 0
    best_results = None
    
    for i, scenario in enumerate(test_scenarios):
        print(f"\n=== 测试场景 {i+1} ===")
        print(f"持仓周期: {scenario['hold_periods']}, 止损: {scenario['stop_loss_pct']:.1%}, 止盈: {scenario['take_profit_pct']:.1%}")
        
        total_trades, successful_trades, trade_results = improved_backtest(
            strategy, df, 
            hold_periods=scenario['hold_periods'],
            stop_loss_pct=scenario['stop_loss_pct'],
            take_profit_pct=scenario['take_profit_pct']
        )
        
        if total_trades > 0:
            success_rate = successful_trades / total_trades
            avg_profit = np.mean([r['profit_pct'] for r in trade_results]) * 100
            win_rate = sum(1 for r in trade_results if r['profit_pct'] > 0) / len(trade_results)
            
            print(f"总交易次数: {total_trades}")
            print(f"成功次数: {successful_trades}")
            print(f"成功率: {success_rate:.2%}")
            print(f"平均收益率: {avg_profit:.2f}%")
            print(f"胜率: {win_rate:.2%}")
            
            # 按市场状态分析
            for regime in ['trending', 'ranging', 'uncertain']:
                regime_trades = [r for r in trade_results if r['market_regime'] == regime]
                if regime_trades:
                    regime_success = sum(1 for r in regime_trades if r['successful']) / len(regime_trades)
                    print(f"  {regime}市场成功率: {regime_success:.2%} ({len(regime_trades)}次交易)")
            
            if success_rate > best_success_rate and total_trades >= 20:  # 至少20次交易才考虑
                best_success_rate = success_rate
                best_scenario = scenario
                best_results = trade_results
    
    # 输出最佳结果分析
    if best_scenario:
        print(f"\n*** 最佳场景 ***")
        print(f"参数: {best_scenario}")
        print(f"最佳成功率: {best_success_rate:.2%}")
        
        # 进一步分析最佳场景
        analyze_trading_patterns(best_results)
    
    return best_scenario, best_results

def analyze_trading_patterns(trade_results):
    """
    分析交易模式
    """
    print("\n--- 交易模式分析 ---")
    
    # 按信号类型分析
    buy_trades = [r for r in trade_results if r['signal'] == 'buy']
    sell_trades = [r for r in trade_results if r['signal'] == 'sell']
    
    if buy_trades:
        buy_success = sum(1 for r in buy_trades if r['successful']) / len(buy_trades)
        avg_buy_profit = np.mean([r['profit_pct'] for r in buy_trades]) * 100
        print(f"买入信号: {len(buy_trades)}次, 成功率: {buy_success:.2%}, 平均收益: {avg_buy_profit:.2f}%")
    
    if sell_trades:
        sell_success = sum(1 for r in sell_trades if r['successful']) / len(sell_trades)
        avg_sell_profit = np.mean([r['profit_pct'] for r in sell_trades]) * 100
        print(f"卖出信号: {len(sell_trades)}次, 成功率: {sell_success:.2%}, 平均收益: {avg_sell_profit:.2f}%")
    
    # 按持仓时间分析
    print("\n按持仓时间分析:")
    for hold_period in sorted(set(r['hold_period'] for r in trade_results)):
        period_trades = [r for r in trade_results if r['hold_period'] == hold_period]
        if period_trades:
            success_rate = sum(1 for r in period_trades if r['successful']) / len(period_trades)
            avg_profit = np.mean([r['profit_pct'] for r in period_trades]) * 100
            print(f"  持仓{hold_period}根K线: {len(period_trades)}次, 成功率: {success_rate:.2%}, 平均收益: {avg_profit:.2f}%")
    
    # 按退出原因分析
    print("\n按退出原因分析:")
    for reason in set(r['exit_reason'] for r in trade_results):
        reason_trades = [r for r in trade_results if r['exit_reason'] == reason]
        if reason_trades:
            success_rate = sum(1 for r in reason_trades if r['successful']) / len(reason_trades)
            avg_profit = np.mean([r['profit_pct'] for r in reason_trades]) * 100
            print(f"  {reason}: {len(reason_trades)}次, 成功率: {success_rate:.2%}, 平均收益: {avg_profit:.2f}%")
# 使用示例
def main():
    # 使用优化后的策略
    strategy = OptimizedTradingStrategy()
    
    df = fetch_market_data('DTHUSDT', '1h')
    
    print("开始优化回测...")
    best_scenario, best_results = comprehensive_backtest_analysis(strategy, df)
    
    if best_scenario:
        print(f"\n🎯 推荐使用以下参数:")
        print(f"持仓周期: {best_scenario['hold_periods']}")
        print(f"止损: {best_scenario['stop_loss_pct']:.1%}")
        print(f"止盈: {best_scenario['take_profit_pct']:.1%}")
        
        # 计算预期年化收益
        total_return = np.sum([r['profit_pct'] for r in best_results])
        avg_trade_return = total_return / len(best_results)
        trades_per_mon = 90  # 1小时线，每年大约交易次数
        expected_annual_return = avg_trade_return * trades_per_mon
        
        print(f"预期月化收益率: {expected_annual_return:.1%}")
def trade():
    # 1. 初始化策略和渲染器
    strategy = EnhancedTradingStrategy()
    renderer = TradingDecisionRenderer()
    
    # 2. 获取市场数据
    df = fetch_market_data('BTCUSDT', '1h')
    
    # 3. 分析市场并生成信号
    print("正在分析市场...")
    strategy_result = strategy.analyze_market(df)
    
    # 4. 渲染到提示词模板
    print("生成AI Agent决策提示词...")
    ai_prompt = renderer.render_decision_prompt(
        strategy_result, df, 
        symbol='BTCUSDT', 
        timeframe='1h'
    )
    
    # 5. 输出结果
    print("\n" + "="*80)
    print("AI AGENT 交易决策提示词")
    print("="*80)
    print(ai_prompt)
if __name__ == "__main__":
    trade()