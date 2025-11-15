"""
风险管理经理智能体
"""
import json
import re
from typing import Dict, List, Optional
from loguru import logger
import openai
import aiohttp

from backend.agents.base_agent import BaseAgent, AgentRole, AgentAnalysis
from backend.agents.prompts import RISK_MANAGER_PROMPT, get_risk_control_context
from backend.agents.intelligent_stop_strategy import intelligent_stop_strategy


class RiskManager(BaseAgent):
    """风险管理经理 - 评估市场波动性、流动性和其他风险因素"""
    
    def __init__(self, ai_model: str, api_key: str):
        super().__init__(AgentRole.RISK_MANAGER, ai_model, api_key)
        if "GPT" in ai_model.upper():
            openai.api_key = self.api_key
        
        # 根据不同的AI模型设置API URL
        if "DeepSeek" in ai_model:
            self.api_url = "https://api.deepseek.com/v1/chat/completions"
            self.model_name = "deepseek-chat"
        elif "Grok" in ai_model:
            self.api_url = "https://api.x.ai/v1/chat/completions"
            self.model_name = "grok-beta"
        elif "Qwen" in ai_model or "千问" in ai_model:
            self.api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
            self.model_name = "qwen-plus"
        else:
            self.api_url = "https://api.deepseek.com/v1/chat/completions"
            self.model_name = "deepseek-chat"
    
    async def analyze(
        self,
        symbol: str,
        market_data: Dict,
        additional_data: Optional[Dict] = None
    ) -> AgentAnalysis:
        """评估风险并提供风险管理建议"""
        try:
            portfolio = additional_data.get('portfolio', {}) if additional_data else {}
            positions = additional_data.get('positions', []) if additional_data else []
            
            # 获取K线数据（如果有）
            kline_data = additional_data.get('kline_compressed', {}) if additional_data else {}
            
            # 计算风险指标（集成K线数据）
            risk_metrics = self._calculate_risk_metrics(market_data, portfolio, positions, kline_data)
            
            # 评估止盈止损风险
            stop_risk_assessment = self._assess_stop_risk(
                symbol, market_data, portfolio, additional_data
            )
            risk_metrics.update(stop_risk_assessment)
            
            # 获取团队分析结果（如果有的话）
            team_analyses = additional_data.get('team_analyses', []) if additional_data else []
            muti_agent_analysis_context = ""
            for analysis in team_analyses:
                # 拼接分析结果到字符串
                muti_agent_analysis_context += f"""角色 {self._get_target_role_name(analysis.agent_role)} 建议: {analysis.recommendation} 置信度: {analysis.confidence}\n"""
                muti_agent_analysis_context += f"""理由：{analysis.reasoning}\n"""
                muti_agent_analysis_context += f"""技术指标：{analysis.key_metrics}\n"""
                muti_agent_analysis_context += f"""风险评分: {analysis.risk_score}\n"""
                muti_agent_analysis_context += f"""优先级: {analysis.priority}\n"""
                muti_agent_analysis_context += f"""置信度: {analysis.confidence}\n"""
            # for position in positions:
            #     if position.get('symbol') == symbol:
            #         position_info = position
            #         break
            # 构建分析上下文（注入风控配置）
            analysis_context = f"""
{get_risk_control_context()}

当前交易对：{symbol}
市场数据：{json.dumps(market_data, ensure_ascii=False, indent=2)}

持仓数据：
{json.dumps(positions, ensure_ascii=False, indent=2) if positions else "无持仓数据"}

风险评估指标：
{json.dumps(risk_metrics, ensure_ascii=False, indent=2)}

账号投资组合状态：
- 总资产: ${portfolio.get('total_balance', 0):,.2f}
- 现金余额: ${portfolio.get('cash_balance', 0):,.2f}
- 持仓价值: ${portfolio.get('positions_value', 0):,.2f}
- 总盈亏: ${portfolio.get('total_pnl', 0):,.2f}

团队分析建议：
{muti_agent_analysis_context}

请基于以上数据进行全面风险评估，判断是否批准当前交易建议。
特别注意：严格检查是否违反系统风控规则！
"""
            
            prompt = analysis_context
            logger.info(f"风险管理分析提示词:{RISK_MANAGER_PROMPT}\n {prompt}")
            # 使用DeepSeek API
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": RISK_MANAGER_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
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
                reasoning=result.get('reasoning', '风险管理分析'),
                key_metrics=result.get('key_metrics', risk_metrics),
                risk_score=float(result.get('risk_score', 0.5)),
                priority=5  # 风险管理最重要，具有否决权
            )
            
        except Exception as e:
            logger.error(f"风险管理分析失败: {e}")
            return AgentAnalysis(
                agent_role=self.role,
                recommendation="hold",
                confidence=0.0,
                reasoning=f"分析失败: {str(e)}",
                key_metrics={},
                risk_score=0.8,  # 分析失败时风险评分偏高
                priority=5
            )
    
    def _calculate_risk_metrics(
        self, 
        market_data: Dict, 
        portfolio: Dict, 
        positions: List[Dict],
        kline_data: Dict = None
    ) -> Dict:
        """改进的风险指标计算 - 包含做空风险溢价，集成K线数据"""
        price = market_data.get('price', 0)
        high = market_data.get('high_24h', price)
        low = market_data.get('low_24h', price)
        volume = market_data.get('volume_24h', 0)
        change = market_data.get('change_24h', 0)
        
        total_balance = portfolio.get('total_balance', 10000)
        positions_value = portfolio.get('positions_value', 0)
        
        # 计算波动率 - 优先使用K线数据的真实波动率
        if kline_data and kline_data.get('technical_features'):
            volatility_indicators = kline_data['technical_features'].get('volatility_indicators', {})
            if volatility_indicators.get('atr_pct'):
                volatility = volatility_indicators['atr_pct']
                volatility_source = "K线ATR"
            else:
                volatility = ((high - low) / ((high - low)/2)) * 100 if price > 0 else 0
                volatility_source = "24小时"
        else:
            volatility = ((high - low) /  ((high - low)/2)) * 100 if price > 0 else 0
            volatility_source = "24小时"
        
        # 计算持仓比例
        position_size = (positions_value / total_balance * 100) if total_balance > 0 else 0
        
        # 流动性评估
        liquidity_score = "高" if volume > 1000000 else "中" if volume > 100000 else "低"
        
        # 新增：多空风险差异 - 计算做空风险溢价
        short_risk_premium = self._calculate_short_risk_premium(market_data)
        
        # 新增：市场环境风险评估
        market_regime_risk = self._assess_market_regime_risk(market_data)
        
        # 新增：清算风险
        liquidation_risk = self._calculate_liquidation_risk(positions, market_data)
        
        # 新增：相关性风险
        correlation_risk = self._assess_correlation_risk(portfolio, positions)
        
        metrics = {
            "volatility": round(volatility, 2),
            "volatility_source": volatility_source,
            "position_size": round(position_size, 2),
            "liquidity": liquidity_score,
            "volume_24h": volume,
            "risk_level": "高" if volatility > 10 or position_size > 50 else "中" if volatility > 5 or position_size > 30 else "低",
            "max_drawdown": round(portfolio.get('total_pnl', 0) / total_balance * 100, 2) if total_balance > 0 else 0,
            "cash_ratio": round((portfolio.get('cash_balance', 0) / total_balance * 100), 2) if total_balance > 0 else 100,
            "short_risk_premium": short_risk_premium,
            "market_regime": market_regime_risk,
            "liquidation_risk": liquidation_risk,
            "correlation_risk": correlation_risk
        }
        
        # 如果有K线数据，添加K线风险分析
        if kline_data:
            # 趋势风险
            trend_analysis = kline_data.get('trend_analysis', {})
            trend_risk = "低" if trend_analysis.get('confidence', 0) > 70 else "中" if trend_analysis.get('confidence', 0) > 40 else "高"
            
            # 成交量风险
            volume_analysis = kline_data.get('volume_analysis', {})
            volume_anomaly = volume_analysis.get('volume_anomaly', 'normal')
            volume_risk = "高" if volume_anomaly == 'low' else "低" if volume_anomaly == 'high' else "中"
            
            metrics["kline_risk_analysis"] = {
                "trend_risk": trend_risk,
                "trend_confidence": trend_analysis.get('confidence', 0),
                "volume_risk": volume_risk,
                "volume_anomaly": volume_anomaly,
                "price_action_risk": self._assess_price_action_risk(kline_data)
            }
        
        return metrics
    
    def _calculate_short_risk_premium(self, market_data: Dict) -> float:
        """计算做空风险溢价（做空比做多需要更高风险补偿）"""
        change = market_data.get('change_24h', 0)
        volatility = ((market_data.get('high_24h', 0) - market_data.get('low_24h', 0)) / 
                     market_data.get('price', 1)) * 100
        
        # 计算趋势强度
        if change > 5:  # 强势上涨
            trend_strength = min(change / 10, 1.0)
        elif change < -5:  # 强势下跌
            trend_strength = max(change / 10, -1.0)
        else:
            trend_strength = change / 10
        
        # 在强势上涨趋势中做空风险更高
        if trend_strength > 0.7:  # 强势上涨
            return 0.3
        elif trend_strength < -0.7:  # 强势下跌
            return 0.1  # 做空风险相对较低
        else:
            return 0.2  # 中性市场
    
    def _assess_market_regime_risk(self, market_data: Dict) -> str:
        """改进的市场环境识别"""
        change = market_data.get('change_24h', 0)
        high = market_data.get('high_24h', 0)
        low = market_data.get('low_24h', 0)
        avg_price = (high + low) / 2
        
        # 改进的波动率计算
        volatility = ((high - low) / avg_price) * 100 if avg_price > 0 else 0
        
        # 波动率分类
        if volatility > 20:
            vol_regime = "极端波动"
        elif volatility > 12:
            vol_regime = "高波动"
        elif volatility > 5:
            vol_regime = "中等波动"
        else:
            vol_regime = "低波动"
        
        # 趋势分类
        if change > 15:
            trend_regime = "强势上涨"
        elif change > 5:
            trend_regime = "温和上涨"
        elif change < -15:
            trend_regime = "强势下跌"
        elif change < -5:
            trend_regime = "温和下跌"
        elif abs(change) < 2:
            trend_regime = "横盘"
        else:
            trend_regime = "小幅震荡"
        
        return f"{vol_regime}-{trend_regime}"
    
    def _calculate_liquidation_risk(self, positions: List[Dict], market_data: Dict) -> str:
        """计算清算风险"""
        if not positions:
            return "无"
        
        # 简化计算：基于持仓数量和市场波动
        total_positions = len(positions)
        volatility = ((market_data.get('high_24h', 0) - market_data.get('low_24h', 0)) / 
                     market_data.get('price', 1)) * 100
        
        if total_positions > 5 and volatility > 10:
            return "高"
        elif total_positions > 3 or volatility > 5:
            return "中"
        else:
            return "低"
    
    def _assess_correlation_risk(self, portfolio: Dict, positions: List[Dict]) -> str:
        """评估相关性风险"""
        if not positions:
            return "无"
        
        # 简化评估：基于持仓集中度
        total_value = portfolio.get('positions_value', 0)
        if total_value == 0:
            return "无"
        
        # 检查是否过度集中
        position_count = len(positions)
        if position_count == 1:
            return "高（单一持仓）"
        elif position_count <= 3:
            return "中（持仓较少）"
        else:
            return "低（分散持仓）"
    
    def _assess_price_action_risk(self, kline_data: Dict) -> str:
        """评估价格行为风险（基于K线数据）"""
        price_action = kline_data.get('price_action', {})
        
        # 检查突破信号
        breakout = price_action.get('breakout_signals', {})
        if breakout.get('breakout_up') or breakout.get('breakout_down'):
            return "高（突破阶段，波动加剧）"
        
        # 检查K线形态
        patterns = price_action.get('recent_patterns', [])
        if patterns and len(patterns) > 0:
            # 如果有重要反转形态，风险较高
            reversal_patterns = ['hammer', 'shooting_star', 'bullish_engulfing', 'bearish_engulfing']
            for pattern in patterns:
                if pattern in reversal_patterns:
                    return "中（反转形态出现）"
        
        # 检查动量
        momentum = price_action.get('momentum', {})
        if momentum.get('strength', 0) > 5:
            return "中（动量强劲）"
        
        return "低（价格行为正常）"
    
    def _assess_stop_risk(
        self,
        symbol: str,
        market_data: Dict,
        portfolio: Dict,
        additional_data: Dict
    ) -> Dict:
        """评估止盈止损风险"""
        risk_assessment = {}
        
        # 检查团队分析结果中的建议
        team_analyses = additional_data.get('team_analyses', []) if additional_data else []
        
        proposed_action = None
        proposed_confidence = 0.5
        
        # 寻找交易建议
        for analysis in team_analyses:
            if analysis.recommendation in ['buy', 'short']:
                proposed_action = analysis.recommendation
                proposed_confidence = analysis.confidence
                break
        
        if proposed_action:
            # 模拟计算止盈止损
            entry_price = market_data.get('price', 0)
            
            # 计算波动率
            volatility = ((market_data.get('high_24h', entry_price) - 
                          market_data.get('low_24h', entry_price)) / entry_price * 100)
            
            # 获取技术分析的支撑阻力位
            technical_factors = {}
            for analysis in team_analyses:
                if analysis.agent_role == AgentRole.TECHNICAL_ANALYST:
                    technical_factors = analysis.key_metrics
                    break
            
            stop_levels = intelligent_stop_strategy.calculate_stop_levels(
                action=proposed_action,
                entry_price=entry_price,
                market_data=market_data,
                position_size=0.1,  # 假设标准仓位
                confidence=proposed_confidence,
                volatility=volatility,
                additional_factors=technical_factors
            )
            
            proposed_stop_loss = stop_levels.get('stop_loss')
            proposed_take_profit = stop_levels.get('take_profit')
            risk_reward_ratio = stop_levels.get('risk_reward_ratio', 0)
            risk_pct = stop_levels.get('risk_pct', 0)
            reward_pct = stop_levels.get('reward_pct', 0)
            strategy_type = stop_levels.get('strategy_type', 'unknown')
            
            # 风险评估
            if risk_reward_ratio < 1:
                risk_assessment['stop_risk'] = "⚠️ 高风险 - 风险回报比不理想"
                risk_assessment['stop_risk_level'] = "high"
            elif risk_reward_ratio < 1.5:
                risk_assessment['stop_risk'] = "⚡ 中等风险 - 风险回报比较低"
                risk_assessment['stop_risk_level'] = "medium"
            elif risk_reward_ratio > 3:
                risk_assessment['stop_risk'] = "✅ 低风险 - 风险回报比极佳"
                risk_assessment['stop_risk_level'] = "low"
            else:
                risk_assessment['stop_risk'] = "✓ 合理风险 - 风险回报比适中"
                risk_assessment['stop_risk_level'] = "acceptable"
            
            # 止损风险评估
            if abs(risk_pct) > 5:
                risk_assessment['stop_loss_warning'] = "⚠️ 止损距离较大，可能遭受较大损失"
            elif abs(risk_pct) < 1:
                risk_assessment['stop_loss_warning'] = "⚠️ 止损距离过小，可能被正常波动触发"
            
            # 波动率风险
            if volatility > 10 and abs(risk_pct) < 3:
                risk_assessment['volatility_warning'] = "⚠️ 高波动市场，建议扩大止损幅度"
            
            risk_assessment['calculated_rr_ratio'] = risk_reward_ratio
            risk_assessment['suggested_stop_loss'] = proposed_stop_loss
            risk_assessment['suggested_take_profit'] = proposed_take_profit
            risk_assessment['risk_percentage'] = risk_pct
            risk_assessment['reward_percentage'] = reward_pct
            risk_assessment['stop_strategy_type'] = strategy_type
            
            logger.info(f"📊 止盈止损风险评估:")
            logger.info(f"   风险回报比: 1:{risk_reward_ratio:.2f}")
            logger.info(f"   风险百分比: {risk_pct:+.2f}%")
            logger.info(f"   收益百分比: {reward_pct:+.2f}%")
            logger.info(f"   风险等级: {risk_assessment.get('stop_risk_level', 'unknown')}")
        
        return risk_assessment
    
    def _parse_response(self, content: str) -> Dict:
        """解析AI响应"""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {}

