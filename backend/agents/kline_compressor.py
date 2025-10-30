"""
K线数据压缩处理器
将原始K线数据压缩为智能体可分析的关键特征
"""
import numpy as np
from typing import List, Dict, Any
from loguru import logger


class KlineCompressor:
    """K线数据压缩处理器"""
    
    def __init__(self):
        self.supported_intervals = ['1m', '5m', '15m', '1h', '4h', '1d']
        self.compression_ratios = {
            '1m': 0.1,   # 保留10%的1分钟数据
            '5m': 0.2,   # 保留20%的5分钟数据
            '15m': 0.3,
            '1h': 0.5,
            '4h': 0.8,
            '1d': 1.0    # 日线数据全部保留
        }
    
    def compress_kline_data(self, raw_klines: List, interval: str, symbol: str) -> Dict[str, Any]:
        """
        压缩K线数据，提取关键特征
        
        Args:
            raw_klines: 原始K线数据
            interval: K线间隔
            symbol: 交易对
            
        Returns:
            压缩后的K线特征字典
        """
        if not raw_klines:
            return self._empty_compression(symbol, interval)
        
        try:
            # 解析原始K线数据
            parsed_klines = self._parse_raw_klines(raw_klines)
            
            if not parsed_klines:
                return self._empty_compression(symbol, interval)
            
            # 根据时间间隔选择压缩策略
            compression_ratio = self.compression_ratios.get(interval, 0.3)
            
            # 关键特征提取
            compressed_data = {
                'symbol': symbol,
                'interval': interval,
                'timestamp': parsed_klines[-1]['timestamp'] if parsed_klines else 0,
                'summary': self._generate_summary(parsed_klines),
                'technical_features': self._extract_technical_features(parsed_klines),
                'volume_analysis': self._analyze_volume_patterns(parsed_klines),
                'price_action': self._analyze_price_action(parsed_klines),
                'key_levels': self._identify_key_levels(parsed_klines),
                'trend_analysis': self._analyze_trends(parsed_klines),
                'compressed_candles': self._compress_candles(parsed_klines, compression_ratio)
            }
            
            logger.info(f"📊 K线数据压缩完成: {symbol} {interval}, 原始{len(raw_klines)}根 -> 特征{len(compressed_data)}维")
            return compressed_data
            
        except Exception as e:
            logger.error(f"K线数据压缩失败: {e}")
            return self._empty_compression(symbol, interval)
    
    def _parse_raw_klines(self, raw_klines: List) -> List[Dict]:
        """解析原始K线数据"""
        parsed = []
        for kline in raw_klines:
            try:
                # 处理不同格式的K线数据
                if isinstance(kline, dict):
                    # 字典格式
                    parsed.append({
                        'timestamp': kline.get('timestamp', 0),
                        'open': float(kline.get('open', 0)),
                        'high': float(kline.get('high', 0)),
                        'low': float(kline.get('low', 0)),
                        'close': float(kline.get('close', 0)),
                        'volume': float(kline.get('volume', 0)),
                        'close_time': kline.get('close_time', 0),
                        'quote_volume': float(kline.get('quote_volume', 0)),
                        'trades': kline.get('trades', 0),
                        'taker_buy_volume': float(kline.get('taker_buy_volume', 0)),
                        'taker_buy_quote_volume': float(kline.get('taker_buy_quote_volume', 0))
                    })
                elif isinstance(kline, (list, tuple)) and len(kline) >= 6:
                    # 数组格式
                    parsed.append({
                        'timestamp': kline[0],
                        'open': float(kline[1]),
                        'high': float(kline[2]),
                        'low': float(kline[3]),
                        'close': float(kline[4]),
                        'volume': float(kline[5]),
                        'close_time': kline[6] if len(kline) > 6 else 0,
                        'quote_volume': float(kline[7]) if len(kline) > 7 else 0,
                        'trades': kline[8] if len(kline) > 8 else 0,
                        'taker_buy_volume': float(kline[9]) if len(kline) > 9 else 0,
                        'taker_buy_quote_volume': float(kline[10]) if len(kline) > 10 else 0
                    })
            except (IndexError, ValueError, TypeError) as e:
                logger.warning(f"解析K线数据失败: {e}")
                continue
        return parsed
    
    def _generate_summary(self, klines: List[Dict]) -> Dict:
        """生成K线数据摘要"""
        if not klines:
            return {}
        
        closes = [k['close'] for k in klines]
        volumes = [k['volume'] for k in klines]
        highs = [k['high'] for k in klines]
        lows = [k['low'] for k in klines]
        
        current_price = closes[-1]
        start_price = closes[0]
        price_change = current_price - start_price
        price_change_pct = (price_change / start_price) * 100 if start_price > 0 else 0
        
        return {
            'periods': len(klines),
            'start_price': round(start_price, 6),
            'end_price': round(current_price, 6),
            'price_change': round(price_change, 6),
            'price_change_pct': round(price_change_pct, 2),
            'highest_price': round(max(highs), 6),
            'lowest_price': round(min(lows), 6),
            'avg_volume': round(np.mean(volumes), 2),
            'total_volume': round(sum(volumes), 2),
            'volatility': round((max(highs) - min(lows)) / start_price * 100, 2) if start_price > 0 else 0
        }
    
    def _extract_technical_features(self, klines: List[Dict]) -> Dict:
        """提取技术特征"""
        if len(klines) < 20:  # 至少需要20根K线计算技术指标
            return {}
        
        closes = [k['close'] for k in klines]
        highs = [k['high'] for k in klines]
        lows = [k['low'] for k in klines]
        volumes = [k['volume'] for k in klines]
        
        # 移动平均线
        ma_features = self._calculate_moving_averages(closes)
        
        # RSI
        rsi_features = self._calculate_rsi(closes)
        
        # 支撑阻力位
        support_resistance = self._calculate_support_resistance(highs, lows, closes)
        
        # 成交量特征
        volume_features = self._calculate_volume_indicators(volumes, closes)
        
        return {
            'moving_averages': ma_features,
            'rsi': rsi_features,
            'support_resistance': support_resistance,
            'volume_indicators': volume_features,
            'momentum': self._calculate_momentum(closes),
            'volatility_indicators': self._calculate_volatility(highs, lows, closes)
        }
    
    def _calculate_moving_averages(self, closes: List[float]) -> Dict:
        """计算移动平均线"""
        if len(closes) < 50:
            return {}
        
        ma5 = np.mean(closes[-5:])
        ma10 = np.mean(closes[-10:])
        ma20 = np.mean(closes[-20:])
        ma50 = np.mean(closes[-50:])
        
        current_price = closes[-1]
        
        return {
            'ma5': round(ma5, 6),
            'ma10': round(ma10, 6),
            'ma20': round(ma20, 6),
            'ma50': round(ma50, 6),
            'price_vs_ma5': round((current_price - ma5) / ma5 * 100, 2) if ma5 > 0 else 0,
            'price_vs_ma20': round((current_price - ma20) / ma20 * 100, 2) if ma20 > 0 else 0,
            'trend': 'bullish' if ma5 > ma20 > ma50 else 'bearish' if ma5 < ma20 < ma50 else 'neutral'
        }
    
    def _calculate_rsi(self, closes: List[float], period: int = 14) -> Dict:
        """计算RSI指标"""
        if len(closes) < period + 1:
            return {}
        
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gains = np.mean(gains[-period:])
        avg_losses = np.mean(losses[-period:])
        
        if avg_losses == 0:
            rsi = 100
        else:
            rs = avg_gains / avg_losses
            rsi = 100 - (100 / (1 + rs))
        
        rsi_signal = "超买" if rsi > 70 else "超卖" if rsi < 30 else "中性"
        
        return {
            'rsi': round(rsi, 2),
            'signal': rsi_signal,
            'strength': 'strong' if rsi > 80 or rsi < 20 else 'moderate'
        }
    
    def _calculate_support_resistance(self, highs: List[float], lows: List[float], closes: List[float]) -> Dict:
        """计算支撑阻力位"""
        if not highs or not lows or not closes:
            return {}
        
        recent_high = max(highs[-20:])
        recent_low = min(lows[-20:])
        current_price = closes[-1]
        
        return {
            'resistance': round(recent_high, 6),
            'support': round(recent_low, 6),
            'current_position': round((current_price - recent_low) / (recent_high - recent_low) * 100, 2) 
                              if recent_high > recent_low else 50
        }
    
    def _calculate_volume_indicators(self, volumes: List[float], closes: List[float]) -> Dict:
        """计算成交量指标"""
        if not volumes:
            return {}
        
        avg_volume = np.mean(volumes)
        current_volume = volumes[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        # 计算成交量趋势
        if len(volumes) >= 5:
            recent_avg = np.mean(volumes[-5:])
            previous_avg = np.mean(volumes[-10:-5]) if len(volumes) >= 10 else avg_volume
            volume_trend = 'increasing' if recent_avg > previous_avg else 'decreasing'
        else:
            volume_trend = 'unknown'
        
        return {
            'current_volume': round(current_volume, 2),
            'avg_volume': round(avg_volume, 2),
            'volume_ratio': round(volume_ratio, 2),
            'volume_trend': volume_trend,
            'volume_anomaly': 'high' if volume_ratio > 2 else 'low' if volume_ratio < 0.5 else 'normal'
        }
    
    def _calculate_momentum(self, closes: List[float]) -> Dict:
        """计算价格动量"""
        if len(closes) < 10:
            return {'trend': 'unknown', 'strength': 0}
        
        short_term = np.mean(closes[-5:]) - np.mean(closes[-10:-5])
        
        trend = "up" if short_term > 0 else "down"
        strength = abs(short_term) / np.mean(closes[-10:]) * 100 if np.mean(closes[-10:]) > 0 else 0
        
        return {
            'trend': trend,
            'strength': round(strength, 2),
            'direction': 'bullish' if short_term > 0 else 'bearish'
        }
    
    def _calculate_volatility(self, highs: List[float], lows: List[float], closes: List[float]) -> Dict:
        """计算波动率指标"""
        if len(closes) < 20:
            return {}
        
        # ATR (Average True Range)
        true_ranges = []
        for i in range(1, len(closes)):
            high_low = highs[i] - lows[i]
            high_close = abs(highs[i] - closes[i-1])
            low_close = abs(lows[i] - closes[i-1])
            true_ranges.append(max(high_low, high_close, low_close))
        
        atr = np.mean(true_ranges[-14:]) if len(true_ranges) >= 14 else np.mean(true_ranges)
        atr_pct = (atr / closes[-1] * 100) if closes[-1] > 0 else 0
        
        return {
            'atr': round(atr, 6),
            'atr_pct': round(atr_pct, 2),
            'volatility_level': 'high' if atr_pct > 5 else 'medium' if atr_pct > 2 else 'low'
        }
    
    def _analyze_volume_patterns(self, klines: List[Dict]) -> Dict:
        """分析成交量模式"""
        if not klines:
            return {}
        
        volumes = [k['volume'] for k in klines]
        closes = [k['close'] for k in klines]
        
        # 成交量异常检测
        avg_volume = np.mean(volumes)
        std_volume = np.std(volumes) if len(volumes) > 1 else 0
        
        recent_volume = volumes[-1]
        volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
        
        # 量价关系分析
        volume_price_correlation = self._calculate_volume_price_correlation(volumes, closes)
        
        # 成交量集群
        volume_clusters = self._find_volume_clusters(volumes)
        
        return {
            'current_volume': round(recent_volume, 2),
            'avg_volume': round(avg_volume, 2),
            'volume_ratio': round(volume_ratio, 2),
            'volume_trend': 'increasing' if len(volumes) >= 5 and volumes[-1] > np.mean(volumes[-5:]) else 'decreasing',
            'volume_anomaly': 'high' if volume_ratio > 2 else 'low' if volume_ratio < 0.5 else 'normal',
            'volume_price_correlation': volume_price_correlation,
            'volume_clusters': volume_clusters
        }
    
    def _calculate_volume_price_correlation(self, volumes: List[float], closes: List[float]) -> str:
        """计算量价关系"""
        if len(volumes) < 10 or len(closes) < 10:
            return "unknown"
        
        # 计算价格变化
        price_changes = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        recent_volumes = volumes[1:]  # 对齐
        
        if len(price_changes) < 9 or len(recent_volumes) < 9:
            return "unknown"
        
        # 简化版量价分析
        recent_changes = price_changes[-9:]
        recent_vols = recent_volumes[-9:]
        avg_vol = np.mean(recent_vols)
        
        positive_volume = sum(1 for i in range(len(recent_changes)) 
                            if recent_changes[i] > 0 and recent_vols[i] > avg_vol)
        
        if positive_volume > len(recent_changes) * 0.7:
            return "positive"  # 量价齐升
        elif positive_volume < len(recent_changes) * 0.3:
            return "negative"  # 量价背离
        else:
            return "neutral"
    
    def _find_volume_clusters(self, volumes: List[float]) -> List[Dict]:
        """寻找成交量集群"""
        if len(volumes) < 5:
            return []
        
        avg_volume = np.mean(volumes)
        clusters = []
        
        # 找出高成交量区域
        for i in range(len(volumes) - 5):
            window = volumes[i:i+5]
            window_avg = np.mean(window)
            if window_avg > avg_volume * 1.5:
                clusters.append({
                    'index': i,
                    'avg_volume': round(window_avg, 2),
                    'ratio': round(window_avg / avg_volume, 2)
                })
        
        return clusters[-3:] if clusters else []  # 返回最近3个集群
    
    def _analyze_price_action(self, klines: List[Dict]) -> Dict:
        """分析价格行为"""
        if len(klines) < 3:
            return {}
        
        recent_candles = klines[-5:]  # 最近5根K线
        patterns = []
        
        for i in range(len(recent_candles) - 1):
            candle = recent_candles[i]
            next_candle = recent_candles[i + 1]
            
            # 识别基本K线形态
            pattern = self._identify_candle_pattern(candle, next_candle)
            if pattern:
                patterns.append(pattern)
        
        # 计算价格动量
        closes = [c['close'] for c in klines]
        momentum = self._calculate_price_momentum(closes)
        
        # 分析蜡烛实体和影线
        body_sizes = [abs(c['close'] - c['open']) for c in recent_candles]
        wick_analysis = self._analyze_wicks(recent_candles)
        
        # 检测突破信号
        breakout_signals = self._detect_breakouts(klines)
        
        return {
            'recent_patterns': patterns,
            'momentum': momentum,
            'avg_body_size': round(np.mean(body_sizes), 6) if body_sizes else 0,
            'wick_analysis': wick_analysis,
            'breakout_signals': breakout_signals
        }
    
    def _identify_candle_pattern(self, candle: Dict, next_candle: Dict) -> str:
        """识别K线形态"""
        body = abs(candle['close'] - candle['open'])
        total_range = candle['high'] - candle['low']
        
        if total_range == 0:
            return None
        
        body_ratio = body / total_range
        
        # 十字星
        if body_ratio < 0.1:
            return "doji"
        
        # 锤子/倒锤子
        upper_wick = candle['high'] - max(candle['open'], candle['close'])
        lower_wick = min(candle['open'], candle['close']) - candle['low']
        
        if lower_wick > body * 2 and upper_wick < body * 0.3:
            return "hammer"
        if upper_wick > body * 2 and lower_wick < body * 0.3:
            return "shooting_star"
        
        # 吞没形态
        if candle['close'] < candle['open'] and next_candle['close'] > next_candle['open']:
            if next_candle['close'] > candle['open'] and next_candle['open'] < candle['close']:
                return "bullish_engulfing"
        
        if candle['close'] > candle['open'] and next_candle['close'] < next_candle['open']:
            if next_candle['close'] < candle['open'] and next_candle['open'] > candle['close']:
                return "bearish_engulfing"
        
        return None
    
    def _calculate_price_momentum(self, closes: List[float]) -> Dict:
        """计算价格动量"""
        if len(closes) < 10:
            return {'trend': 'unknown', 'strength': 0}
        
        short_term = np.mean(closes[-5:]) - np.mean(closes[-10:-5])
        
        trend = "up" if short_term > 0 else "down"
        strength = abs(short_term) / np.mean(closes[-10:]) * 100 if np.mean(closes[-10:]) > 0 else 0
        
        return {
            'trend': trend,
            'strength': round(strength, 2),
            'acceleration': 'positive' if short_term > 0 else 'negative'
        }
    
    def _analyze_wicks(self, candles: List[Dict]) -> Dict:
        """分析蜡烛影线"""
        if not candles:
            return {}
        
        upper_wicks = []
        lower_wicks = []
        
        for candle in candles:
            upper_wick = candle['high'] - max(candle['open'], candle['close'])
            lower_wick = min(candle['open'], candle['close']) - candle['low']
            upper_wicks.append(upper_wick)
            lower_wicks.append(lower_wick)
        
        avg_upper = np.mean(upper_wicks)
        avg_lower = np.mean(lower_wicks)
        
        return {
            'avg_upper_wick': round(avg_upper, 6),
            'avg_lower_wick': round(avg_lower, 6),
            'wick_balance': 'upper_dominant' if avg_upper > avg_lower * 1.5 else 
                           'lower_dominant' if avg_lower > avg_upper * 1.5 else 'balanced'
        }
    
    def _detect_breakouts(self, klines: List[Dict]) -> Dict:
        """检测突破信号"""
        if len(klines) < 20:
            return {}
        
        highs = [k['high'] for k in klines]
        lows = [k['low'] for k in klines]
        closes = [k['close'] for k in klines]
        
        # 计算阻力和支撑
        resistance = max(highs[-20:-1])  # 排除最后一根
        support = min(lows[-20:-1])
        
        current_close = closes[-1]
        
        # 检测突破
        breakout_up = current_close > resistance
        breakout_down = current_close < support
        
        return {
            'resistance_level': round(resistance, 6),
            'support_level': round(support, 6),
            'breakout_up': breakout_up,
            'breakout_down': breakout_down,
            'breakout_type': 'upward' if breakout_up else 'downward' if breakout_down else 'none'
        }
    
    def _identify_key_levels(self, klines: List[Dict]) -> Dict:
        """识别关键价位"""
        if not klines:
            return {}
        
        highs = [k['high'] for k in klines]
        lows = [k['low'] for k in klines]
        closes = [k['close'] for k in klines]
        
        # 简单的支撑阻力识别
        recent_high = max(highs[-20:])
        recent_low = min(lows[-20:])
        current_price = closes[-1]
        
        # 计算动态支撑阻力
        dynamic_support = np.mean(lows[-10:]) if len(lows) >= 10 else recent_low
        dynamic_resistance = np.mean(highs[-10:]) if len(highs) >= 10 else recent_high
        
        return {
            'support_levels': [
                round(recent_low, 6),
                round(recent_low * 0.99, 6),  # 次级支撑
                round(dynamic_support, 6)  # 动态支撑
            ],
            'resistance_levels': [
                round(recent_high, 6),
                round(recent_high * 1.01, 6),  # 次级阻力
                round(dynamic_resistance, 6)  # 动态阻力
            ],
            'price_position': round((current_price - recent_low) / (recent_high - recent_low) * 100, 2) 
                            if recent_high != recent_low else 50
        }
    
    def _analyze_trends(self, klines: List[Dict]) -> Dict:
        """分析趋势"""
        if len(klines) < 10:
            return {'primary_trend': 'unknown', 'confidence': 0}
        
        closes = [k['close'] for k in klines]
        
        # 简单趋势判断
        short_ma = np.mean(closes[-5:])
        medium_ma = np.mean(closes[-10:])
        long_ma = np.mean(closes[-20:]) if len(closes) >= 20 else medium_ma
        
        if short_ma > medium_ma > long_ma:
            trend = "uptrend"
            confidence = min(100, (short_ma - long_ma) / long_ma * 1000) if long_ma > 0 else 0
        elif short_ma < medium_ma < long_ma:
            trend = "downtrend"
            confidence = min(100, (long_ma - short_ma) / long_ma * 1000) if long_ma > 0 else 0
        else:
            trend = "sideways"
            confidence = 30
        
        return {
            'primary_trend': trend,
            'confidence': round(abs(confidence), 1),
            'short_ma': round(short_ma, 6),
            'medium_ma': round(medium_ma, 6),
            'long_ma': round(long_ma, 6)
        }
    
    def _compress_candles(self, klines: List[Dict], ratio: float) -> List[Dict]:
        """压缩K线数量，保留关键K线"""
        if ratio >= 1.0:
            return klines[-50:]  # 最多返回50根
        
        target_count = max(10, int(len(klines) * ratio))
        step = max(1, len(klines) // target_count)
        
        compressed = []
        for i in range(0, len(klines), step):
            if i < len(klines):
                compressed.append({
                    'timestamp': klines[i]['timestamp'],
                    'open': round(klines[i]['open'], 6),
                    'high': round(klines[i]['high'], 6),
                    'low': round(klines[i]['low'], 6),
                    'close': round(klines[i]['close'], 6),
                    'volume': round(klines[i]['volume'], 2)
                })
        
        # 确保包含最新的K线
        if klines and (not compressed or compressed[-1]['timestamp'] != klines[-1]['timestamp']):
            compressed.append({
                'timestamp': klines[-1]['timestamp'],
                'open': round(klines[-1]['open'], 6),
                'high': round(klines[-1]['high'], 6),
                'low': round(klines[-1]['low'], 6),
                'close': round(klines[-1]['close'], 6),
                'volume': round(klines[-1]['volume'], 2)
            })
        
        return compressed[-20:]  # 最多返回20根压缩后的K线
    
    def _empty_compression(self, symbol: str, interval: str) -> Dict:
        """空压缩结果"""
        return {
            'symbol': symbol,
            'interval': interval,
            'timestamp': 0,
            'summary': {},
            'technical_features': {},
            'volume_analysis': {},
            'price_action': {},
            'key_levels': {},
            'trend_analysis': {},
            'compressed_candles': [],
            'error': 'No kline data available'
        }


# 全局K线压缩器实例
kline_compressor = KlineCompressor()

