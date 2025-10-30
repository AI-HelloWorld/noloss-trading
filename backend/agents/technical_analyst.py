"""
技术分析师智能体
"""
import json
import re
from typing import Dict, Optional
from loguru import logger
import openai
import aiohttp

from backend.agents.base_agent import BaseAgent, AgentRole, AgentAnalysis
from backend.agents.prompts import TECHNICAL_ANALYST_PROMPT, get_risk_control_context


class TechnicalAnalyst(BaseAgent):
    """技术分析师 - 利用技术指标检测交易模式并预测价格走势"""
    
    def __init__(self, ai_model: str, api_key: str):
        super().__init__(AgentRole.TECHNICAL_ANALYST, ai_model, api_key)
        if "GPT" in ai_model.upper():
            openai.api_key = self.api_key
        
        # 根据不同的AI模型设置API URL
        if "DeepSeek" in ai_model:
            self.api_url = "https://api.deepseek.com/v1/chat/completions"
            self.model_name = "deepseek-chat"
        elif "Qwen" in ai_model or "千问" in ai_model:
            self.api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
            self.model_name = "qwen-plus"
        elif "Grok" in ai_model:
            self.api_url = "https://api.x.ai/v1/chat/completions"
            self.model_name = "grok-beta"
        else:
            self.api_url = "https://api.deepseek.com/v1/chat/completions"
            self.model_name = "deepseek-chat"
    
    async def analyze(
        self,
        symbol: str,
        market_data: Dict,
        additional_data: Optional[Dict] = None
    ) -> AgentAnalysis:
        """进行技术分析"""
        try:
            # 获取K线数据（如果有）
            kline_data = additional_data.get('kline_compressed', {}) if additional_data else {}
            
            # 计算技术指标（这里可以使用真实的技术指标库）
            technical_indicators = self._calculate_indicators(market_data, kline_data)
            
            # 构建分析上下文（注入风控配置）
            kline_summary = ""
            if kline_data and kline_data.get('summary'):
                kline_summary = f"""
K线数据分析 ({kline_data.get('interval', 'unknown')}):
- 周期数: {kline_data['summary'].get('periods', 0)}
- 价格变化: {kline_data['summary'].get('price_change_pct', 0):.2f}%
- 波动率: {kline_data['summary'].get('volatility', 0):.2f}%
- 趋势: {kline_data.get('trend_analysis', {}).get('primary_trend', 'unknown')}
- 技术特征: {json.dumps(kline_data.get('technical_features', {}), ensure_ascii=False, indent=2)}
"""
            
            analysis_context = f"""
{get_risk_control_context()}

当前交易对：{symbol}
市场数据：{json.dumps(market_data, ensure_ascii=False, indent=2)}

{kline_summary}

技术指标：
{json.dumps(technical_indicators, ensure_ascii=False, indent=2)}

请基于以上数据（包括K线数据）进行深度技术分析，给出交易建议。
注意：建议的仓位大小必须符合系统风控规则！
"""
            
            prompt = analysis_context
            
            # 使用DeepSeek API
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": TECHNICAL_ANALYST_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
                
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    data = await response.json()
                    
                    # 检查API响应格式
                    if 'choices' not in data:
                        logger.error(f"API响应格式错误: {data}")
                        raise Exception(f"API响应缺少choices字段: {data}")
                    
                    if not data['choices'] or len(data['choices']) == 0:
                        logger.error(f"API响应choices为空: {data}")
                        raise Exception("API响应choices为空")
                    
                    content = data['choices'][0]['message']['content']
            
            result = self._parse_response(content)
            
            return AgentAnalysis(
                agent_role=self.role,
                recommendation=result.get('recommendation', 'hold'),
                confidence=float(result.get('confidence', 0.5)),
                reasoning=result.get('reasoning', '技术分析'),
                key_metrics=result.get('key_metrics', technical_indicators),
                risk_score=float(result.get('risk_score', 0.5)),
                priority=1  # 技术分析对短期交易最重要
            )
            
        except Exception as e:
            logger.error(f"技术分析失败: {e}")
            return AgentAnalysis(
                agent_role=self.role,
                recommendation="hold",
                confidence=0.0,
                reasoning=f"分析失败: {str(e)}",
                key_metrics={},
                risk_score=0.5,
                priority=1
            )
    
    def _calculate_indicators(self, market_data: Dict, kline_data: Dict = None) -> Dict:
        """改进的技术指标计算 - 平衡多空信号，集成K线数据"""
        price = market_data.get('price', 0)
        high = market_data.get('high_24h', price)
        low = market_data.get('low_24h', price)
        change = market_data.get('change_24h', 0)
        volume = market_data.get('volume_24h', 0)
        
        # 如果有K线数据，使用K线数据的技术特征
        if kline_data and kline_data.get('technical_features'):
            tech_features = kline_data['technical_features']
            
            # 使用K线数据的RSI
            if tech_features.get('rsi'):
                rsi = tech_features['rsi'].get('rsi', 50)
            else:
                rsi = self._calculate_rsi(price, change)
            
            # 使用K线数据的趋势
            trend_analysis = kline_data.get('trend_analysis', {})
            trend_direction = trend_analysis.get('primary_trend', 'unknown')
            if trend_direction == 'uptrend':
                trend_direction = 'uptrend'
            elif trend_direction == 'downtrend':
                trend_direction = 'downtrend'
            else:
                trend_direction = self._assess_trend(market_data)
            
            # 使用K线数据的支撑阻力
            if tech_features.get('support_resistance'):
                support_resistance = tech_features['support_resistance']
            else:
                support_resistance = self._analyze_support_resistance(market_data)
        else:
            # 没有K线数据，使用原始计算
            rsi = self._calculate_rsi(price, change)
            trend_direction = self._assess_trend(market_data)
            support_resistance = self._analyze_support_resistance(market_data)
        
        # 计算关键支撑阻力位（用于止盈止损）
        # 优先使用K线数据的关键位
        if kline_data and kline_data.get('key_levels'):
            key_levels = kline_data['key_levels']
        else:
            key_levels = self._calculate_key_levels(market_data)
        
        # 多空信号平衡计算（集成K线数据）
        bullish_signals = self._identify_bullish_signals_advanced(market_data, rsi, trend_direction, kline_data)
        bearish_signals = self._identify_bearish_signals_advanced(market_data, rsi, trend_direction, kline_data)
        
        # 净信号强度（正值看多，负值看空）
        net_signal = bullish_signals - bearish_signals
        
        # 波动率计算
        volatility = round(((high - low) / price) * 100, 2) if price > 0 else 0
        
        indicators = {
            "price": price,
            "rsi": round(rsi, 2),
            "rsi_signal": "超买" if rsi > 70 else "超卖" if rsi < 30 else "中性",
            "trend_direction": trend_direction,
            "trend_strength": self._calculate_trend_strength(market_data),
            "bullish_signals": round(bullish_signals, 3),
            "bearish_signals": round(bearish_signals, 3),
            "net_signal": round(net_signal, 3),
            "momentum": self._calculate_momentum(market_data),
            "volatility": volatility,
            "volume_trend": self._analyze_volume_trend(market_data),
            "key_levels": key_levels,
            "support_resistance": support_resistance,
            "stop_suggestions": self._suggest_stop_levels(price, volatility, key_levels),
            "kline_based": bool(kline_data)  # 标记是否使用了K线数据
        }
        
        # 如果有K线数据，添加K线分析摘要
        if kline_data:
            indicators["kline_summary"] = {
                "interval": kline_data.get('interval', 'unknown'),
                "periods": kline_data.get('summary', {}).get('periods', 0),
                "price_action": kline_data.get('price_action', {}),
                "volume_analysis": kline_data.get('volume_analysis', {})
            }
        
        return indicators
    
    def _calculate_rsi(self, price: float, change: float) -> float:
        """改进的RSI计算"""
        # 基于价格变化的RSI简化计算
        rsi = 50 + (change * 2)  # 简化计算
        rsi = max(0, min(100, rsi))
        return rsi
    
    def _assess_trend(self, market_data: Dict) -> str:
        """判断趋势方向"""
        change = market_data.get('change_24h', 0)
        
        # 基于24小时变化判断趋势
        if change > 2:  # 上涨超过2%
            return "uptrend"
        elif change < -2:  # 下跌超过2%
            return "downtrend"
        else:
            return "sideways"
    
    def _calculate_trend_strength(self, market_data: Dict) -> float:
        """计算趋势强度 (-1到1，负值表示下跌趋势)"""
        change = market_data.get('change_24h', 0)
        # 标准化到-1到1之间
        return max(-1, min(1, change / 10))
    
    def _analyze_support_resistance(self, market_data: Dict) -> Dict:
        """支撑阻力分析"""
        price = market_data.get('price', 0)
        high = market_data.get('high_24h', price)
        low = market_data.get('low_24h', price)
        
        return {
            "resistance": round(high, 2),
            "support": round(low, 2),
            "current_position": round((price - low) / (high - low) * 100, 2) if high > low else 50
        }
    
    def _identify_bullish_signals_advanced(self, market_data: Dict, rsi: float, trend: str, kline_data: Dict = None) -> float:
        """改进的做多信号识别（集成K线数据）"""
        signals = []
        weight = 0
        
        change = market_data.get('change_24h', 0)
        volume = market_data.get('volume_24h', 0)
        
        # K线数据增强信号
        if kline_data:
            # 使用K线趋势分析
            trend_analysis = kline_data.get('trend_analysis', {})
            if trend_analysis.get('primary_trend') == 'uptrend':
                confidence = trend_analysis.get('confidence', 0) / 100
                signals.append(0.4 * confidence)
                weight += 1
            
            # 使用K线动量
            momentum = kline_data.get('price_action', {}).get('momentum', {})
            if momentum.get('trend') == 'up':
                signals.append(0.3)
                weight += 1
            
            # 使用K线移动平均线
            ma_features = kline_data.get('technical_features', {}).get('moving_averages', {})
            if ma_features.get('trend') == 'bullish':
                signals.append(0.35)
                weight += 1
            
            # 使用K线突破信号
            breakout = kline_data.get('price_action', {}).get('breakout_signals', {})
            if breakout.get('breakout_up'):
                signals.append(0.25)
                weight += 1
        
        # 1. 上升趋势确认
        if trend == "uptrend":
            signals.append(0.3)
            weight += 1
        
        # 2. RSI超卖反弹
        if rsi < 30:
            signals.append(0.25)
            weight += 1
        elif rsi >= 30 and rsi < 50:
            signals.append(0.1)
            weight += 1
        
        # 3. 价格上涨动能
        if change > 3:
            signals.append(0.2)
            weight += 1
        
        # 4. 成交量确认
        if volume > 1000000:  # 高成交量
            signals.append(0.15)
            weight += 1
        
        # 5. 动量指标看多
        if self._positive_momentum(market_data):
            signals.append(0.1)
            weight += 1
        
        return sum(signals) / weight if weight > 0 else 0
    
    def _identify_bearish_signals_advanced(self, market_data: Dict, rsi: float, trend: str, kline_data: Dict = None) -> float:
        """改进的做空信号识别（集成K线数据）"""
        signals = []
        weight = 0
        
        change = market_data.get('change_24h', 0)
        volume = market_data.get('volume_24h', 0)
        
        # K线数据增强信号
        if kline_data:
            # 使用K线趋势分析
            trend_analysis = kline_data.get('trend_analysis', {})
            if trend_analysis.get('primary_trend') == 'downtrend':
                confidence = trend_analysis.get('confidence', 0) / 100
                signals.append(0.4 * confidence)
                weight += 1
            
            # 使用K线动量
            momentum = kline_data.get('price_action', {}).get('momentum', {})
            if momentum.get('trend') == 'down':
                signals.append(0.3)
                weight += 1
            
            # 使用K线移动平均线
            ma_features = kline_data.get('technical_features', {}).get('moving_averages', {})
            if ma_features.get('trend') == 'bearish':
                signals.append(0.35)
                weight += 1
            
            # 使用K线突破信号
            breakout = kline_data.get('price_action', {}).get('breakout_signals', {})
            if breakout.get('breakout_down'):
                signals.append(0.25)
                weight += 1
        
        # 1. 下降趋势确认
        if trend == "downtrend":
            signals.append(0.3)
            weight += 1
        
        # 2. RSI超买回调
        if rsi > 70:
            signals.append(0.25)
            weight += 1
        elif rsi <= 70 and rsi > 50:
            signals.append(0.1)
            weight += 1
        
        # 3. 价格下跌动能
        if change < -3:
            signals.append(0.2)
            weight += 1
        
        # 4. 放量下跌
        if volume > 1000000 and change < -2:
            signals.append(0.15)
            weight += 1
        
        # 5. 动量指标看空
        if self._negative_momentum(market_data):
            signals.append(0.1)
            weight += 1
        
        return sum(signals) / weight if weight > 0 else 0
    
    def _calculate_momentum(self, market_data: Dict) -> str:
        """计算动量"""
        change = market_data.get('change_24h', 0)
        
        if change > 3:
            return "强势上涨"
        elif change > 0:
            return "温和上涨"
        elif change > -3:
            return "温和下跌"
        else:
            return "强势下跌"
    
    def _positive_momentum(self, market_data: Dict) -> bool:
        """判断是否有正向动量"""
        change = market_data.get('change_24h', 0)
        return change > 2
    
    def _negative_momentum(self, market_data: Dict) -> bool:
        """判断是否有负向动量"""
        change = market_data.get('change_24h', 0)
        return change < -2
    
    def _analyze_volume_trend(self, market_data: Dict) -> str:
        """分析成交量趋势"""
        volume = market_data.get('volume_24h', 0)
        
        if volume > 5000000:
            return "极高"
        elif volume > 1000000:
            return "高"
        elif volume > 100000:
            return "中"
        else:
            return "低"
    
    def _calculate_key_levels(self, market_data: Dict) -> Dict:
        """计算关键支撑阻力位"""
        price = market_data.get('price', 0)
        high_24h = market_data.get('high_24h', price)
        low_24h = market_data.get('low_24h', price)
        
        # 近期支撑位
        support_1 = low_24h
        support_2 = price * 0.98  # 2%下方
        support_3 = price * 0.95  # 5%下方
        
        # 近期阻力位
        resistance_1 = high_24h
        resistance_2 = price * 1.02  # 2%上方
        resistance_3 = price * 1.05  # 5%上方
        
        return {
            "support_levels": [
                round(support_1, 4),
                round(support_2, 4),
                round(support_3, 4)
            ],
            "resistance_levels": [
                round(resistance_1, 4),
                round(resistance_2, 4),
                round(resistance_3, 4)
            ],
            "major_support": round(low_24h, 4),
            "major_resistance": round(high_24h, 4)
        }
    
    def _suggest_stop_levels(self, price: float, volatility: float, key_levels: Dict) -> Dict:
        """基于技术指标建议止盈止损位"""
        # 简单技术止损建议
        return {
            "technical_stop_loss_long": round(price * 0.98, 4),  # 2%止损
            "technical_take_profit_long": round(price * 1.04, 4),  # 4%止盈
            "technical_stop_loss_short": round(price * 1.02, 4),  # 2%止损
            "technical_take_profit_short": round(price * 0.96, 4),  # 4%止盈
            "support_stop": key_levels.get('major_support', price * 0.97),  # 主要支撑位下方
            "resistance_stop": key_levels.get('major_resistance', price * 1.03)  # 主要阻力位上方
        }
    
    def _parse_response(self, content: str) -> Dict:
        """解析AI响应"""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {}

