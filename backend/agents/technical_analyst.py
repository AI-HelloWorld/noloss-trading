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
from backend.agents.prompts import TECHNICAL_ANALYST_PROMPT, get_technical_analyst_context


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
            if kline_data and kline_data.get('formatted_summary'):
                kline_summary = kline_data.get('formatted_summary')
            
            analysis_context = f"""当前交易对：{symbol}
{get_technical_analyst_context()}
市场数据：{json.dumps(market_data, ensure_ascii=False, indent=2)}

K线数据总结：{kline_summary}

技术指标：
{json.dumps(technical_indicators, ensure_ascii=False, indent=2)}

===== 分析要求 =====
请基于以上核心数据，进行短线技术分析并输出交易建议。

重点考量：
1. 趋势与反转信号平衡 - RSI超卖vs整体下跌趋势
2. 关键价位博弈 - 当前接近支撑位的反应
3. 风险调整 - 严格按风控规则计算仓位
4. 时间框架匹配 - 1小时图表的短线机会

注意：避免过度依赖单一指标，需综合判断。
"""
            
            prompt = analysis_context
            logger.info(f"技术分析师提示词: {TECHNICAL_ANALYST_PROMPT}\n {prompt}")
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
                    "temperature": 0.3,
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
                priority=5  # 技术分析对短期交易最重要
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
        """技术指标整合分析 - 生成统一的技术指标报告"""
        price = market_data.get('price', 0)
        high = market_data.get('high_24h', price)
        low = market_data.get('low_24h', price)
        change = market_data.get('change_24h', 0)
        volume = market_data.get('volume_24h', 0)
        
        # ============ 1. 趋势分析 ============
        trend_info = self._analyze_trend_integrated(market_data, kline_data)
        
        # ============ 2. 震荡指标（RSI） ============
        rsi_info = self._analyze_rsi_integrated(market_data, kline_data)
        
        # ============ 3. 关键价位 ============
        key_levels_info = self._analyze_key_levels_integrated(market_data, kline_data)
        
        # ============ 4. 成交量分析 ============
        volume_info = self._analyze_volume_integrated(market_data, kline_data)
        
        # ============ 5. 波动率分析（ATR） ============
        volatility_info = self._analyze_volatility_integrated(market_data, kline_data)
        
        # 生成整合的技术指标报告
        integrated_indicators = {
            "趋势分析": trend_info,
            "震荡指标": rsi_info,
            "关键价位": key_levels_info,
            "成交量分析": volume_info,
            "波动率": volatility_info,
            
            # 保留原始数据供其他模块使用
            "_raw": {
                "price": price,
                "kline_based": bool(kline_data),
                "bullish_signals": self._identify_bullish_signals_advanced(market_data, rsi_info["RSI"], trend_info["方向"], kline_data),
                "bearish_signals": self._identify_bearish_signals_advanced(market_data, rsi_info["RSI"], trend_info["方向"], kline_data),
            }
        }
        
        return integrated_indicators
    
    def _analyze_trend_integrated(self, market_data: Dict, kline_data: Dict = None) -> Dict:
        """整合的趋势分析"""
        change = market_data.get('change_24h', 0)
        
        # 优先使用K线数据的趋势分析
        if kline_data and kline_data.get('trend_analysis'):
            trend_analysis = kline_data['trend_analysis']
            primary_trend = trend_analysis.get('primary_trend', 'sideways')
            confidence = trend_analysis.get('confidence', 50)
            
            # 转换趋势方向为中文
            if primary_trend == 'uptrend':
                direction = "上涨趋势"
            elif primary_trend == 'downtrend':
                direction = "下跌趋势"
            else:
                direction = "横盘震荡"
            
            # 趋势强度（基于置信度）
            strength = round(confidence / 10, 1)  # 转换为1-10的强度
        else:
            # 没有K线数据，使用简化计算
            if change > 2:
                direction = "上涨趋势"
                strength = min(10, abs(change) / 2)
            elif change < -2:
                direction = "下跌趋势"
                strength = min(10, abs(change) / 2)
            else:
                direction = "横盘震荡"
                strength = 1.0
        
        # 动量描述
        momentum = self._calculate_momentum(market_data)
        
        return {
            "方向": direction,
            "强度": round(strength, 1),
            "动量": momentum
        }
    
    def _analyze_rsi_integrated(self, market_data: Dict, kline_data: Dict = None) -> Dict:
        """整合的RSI分析"""
        change = market_data.get('change_24h', 0)
        
        # 优先使用K线数据的RSI
        if kline_data and kline_data.get('technical_features', {}).get('rsi'):
            rsi_data = kline_data['technical_features']['rsi']
            rsi = rsi_data.get('rsi', 50)
            rsi_signal = rsi_data.get('signal', '中性')
        else:
            # 使用简化的RSI计算
            rsi = self._calculate_rsi(market_data.get('price', 0), change)
            if rsi > 70:
                rsi_signal = "超买"
            elif rsi < 30:
                rsi_signal = "超卖"
            else:
                rsi_signal = "中性"
        
        # RSI状态和信号
        if rsi < 30:
            status = "超卖区域"
            signal = "潜在反弹"
        elif rsi > 70:
            status = "超买区域"
            signal = "潜在回调"
        elif rsi < 50:
            status = "弱势区域"
            signal = "谨慎观望"
        else:
            status = "强势区域"
            signal = "持续关注"
        
        return {
            "RSI": round(rsi, 2),
            "状态": status,
            "信号": signal
        }
    
    def _analyze_key_levels_integrated(self, market_data: Dict, kline_data: Dict = None) -> Dict:
        """整合的关键价位分析"""
        price = market_data.get('price', 0)
        
        # 优先使用K线数据的关键价位
        if kline_data and kline_data.get('key_levels'):
            key_levels = kline_data['key_levels']
            support_levels = key_levels.get('support_levels', [])
            resistance_levels = key_levels.get('resistance_levels', [])
            price_position = key_levels.get('price_position', 50)
        else:
            # 使用简化的计算
            high = market_data.get('high_24h', price)
            low = market_data.get('low_24h', price)
            
            support_levels = [
                round(low, 2),
                round(price * 0.98, 2),
                round(price * 0.95, 2)
            ]
            
            resistance_levels = [
                round(high, 2),
                round(price * 1.02, 2),
                round(price * 1.05, 2)
            ]
            
            price_position = round((price - low) / (high - low) * 100, 2) if high > low else 50
        
        # 判断当前位置描述
        if price_position < 20:
            position_desc = "接近第一支撑"
        elif price_position < 40:
            position_desc = "支撑区域附近"
        elif price_position < 60:
            position_desc = "中性位置"
        elif price_position < 80:
            position_desc = "阻力区域附近"
        else:
            position_desc = "接近或者破阻力位"
        return {
            "支撑位": [int(s) if s > 100 else round(s, 4) for s in support_levels[:3]],
            "阻力位": [int(r) if r > 100 else round(r, 4) for r in resistance_levels[:3]],
            "当前位置": position_desc
        }
    
    def _analyze_volume_integrated(self, market_data: Dict, kline_data: Dict = None) -> Dict:
        """整合的成交量分析"""
        
        # 优先使用K线数据的成交量分析
        if kline_data and kline_data.get('volume_analysis'):
            vol_analysis = kline_data['volume_analysis']
            
            # 获取成交量比率
            volume_ratio = vol_analysis.get('volume_ratio', 1.0)
            current_volume = vol_analysis.get('current_volume', 0)
            avg_volume = vol_analysis.get('avg_volume', 0)
            volume_trend = vol_analysis.get('volume_trend', 'unknown')
            
            # 格式化当前成交量描述
            if volume_ratio < 0.5:
                current_desc = f"萎缩({int(volume_ratio * 100)}%平均)"
            elif volume_ratio > 1.5:
                current_desc = f"放大({int(volume_ratio * 100)}%平均)"
            else:
                current_desc = f"正常({int(volume_ratio * 100)}%平均)"
            
            # 成交量趋势
            if volume_trend == 'increasing':
                trend_desc = "上升"
            elif volume_trend == 'decreasing':
                trend_desc = "下降"
            else:
                trend_desc = "稳定"
            
            # 价格相关性
            price_correlation = vol_analysis.get('volume_price_correlation', 'neutral')
            if price_correlation == 'positive':
                correlation_desc = "正相关"
            elif price_correlation == 'negative':
                correlation_desc = "负相关"
            else:
                correlation_desc = "无明显相关"
        else:
            # 使用简化的成交量分析
            volume = market_data.get('volume_24h', 0)
            change = market_data.get('change_24h', 0)
            
            current_desc = "正常水平"
            trend_desc = "稳定"
            
            # 简化的价格相关性判断
            if volume > 1000000 and change > 2:
                correlation_desc = "正相关"
            elif volume > 1000000 and change < -2:
                correlation_desc = "负相关"
            else:
                correlation_desc = "无明显相关"
        
        return {
            "当前成交量": current_desc,
            "趋势": trend_desc,
            "价格相关性": correlation_desc
        }
    
    def _analyze_volatility_integrated(self, market_data: Dict, kline_data: Dict = None) -> Dict:
        """整合的波动率分析（ATR）"""
        price = market_data.get('price', 0)
        
        # 优先使用K线数据的波动率指标
        if kline_data and kline_data.get('technical_features', {}).get('volatility_indicators'):
            vol_indicators = kline_data['technical_features']['volatility_indicators']
            atr = vol_indicators.get('atr', 0)
            atr_pct = vol_indicators.get('atr_pct', 0)
            volatility_level = vol_indicators.get('volatility_level', 'medium')
            
            # 转换波动率水平为中文
            if volatility_level == 'high':
                level_desc = "高波动"
            elif volatility_level == 'low':
                level_desc = "低波动"
            else:
                level_desc = "中等波动"
        else:
            # 使用简化的波动率计算
            high = market_data.get('high_24h', price)
            low = market_data.get('low_24h', price)
            
            atr = high - low
            atr_pct = (atr / price * 100) if price > 0 else 0
            
            if atr_pct > 5:
                level_desc = "高波动"
            elif atr_pct < 2:
                level_desc = "低波动"
            else:
                level_desc = "中等波动"
        
        return {
            "ATR": round(atr, 2),
            "ATR百分比": f"{round(atr_pct, 2)}%",
            "水平": level_desc
        }
    
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

