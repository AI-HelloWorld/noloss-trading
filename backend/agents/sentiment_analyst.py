"""
情绪分析师智能体
"""
import json
import re
from typing import Dict, Optional
from loguru import logger
import aiohttp

from backend.agents.base_agent import BaseAgent, AgentRole, AgentAnalysis
from backend.agents.prompts import SENTIMENT_ANALYST_PROMPT, get_risk_control_context


class SentimentAnalyst(BaseAgent):
    """情绪分析师 - 分析社交媒体和公众情绪"""
    
    def __init__(self, ai_model: str, api_key: str):
        super().__init__(AgentRole.SENTIMENT_ANALYST, ai_model, api_key)
        
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
        """分析市场情绪"""
        try:
            # 获取情绪数据（这里可以集成真实的社交媒体API）
            sentiment_data = additional_data.get('sentiment', {}) if additional_data else {}
            
            # 新增：计算恐惧贪婪指数
            fear_greed_index = self._calculate_fear_greed_index(sentiment_data, market_data)
            
            # 新增：检测情绪极端化
            sentiment_extremity = self._assess_sentiment_extremity(sentiment_data, fear_greed_index)
            
            # 构建分析上下文（注入风控配置）
            analysis_context = f"""
{get_risk_control_context()}

当前交易对：{symbol}
市场数据：{json.dumps(market_data, ensure_ascii=False, indent=2)}

情绪数据：
{json.dumps(sentiment_data, ensure_ascii=False, indent=2)}

情绪极端程度: {sentiment_extremity}
恐惧贪婪指数: {fear_greed_index} (0-100, <20极度恐惧, >80极度贪婪)

新增分析维度：
- 当情绪极度贪婪时(FGI > 80)，考虑反转做空
- 当情绪极度恐惧时(FGI < 20)，考虑反转做多
- 情绪与价格背离时，预示趋势反转

请基于以上数据进行情绪分析，评估市场参与者的情绪倾向和变化趋势。
注意：建议必须符合系统风控规则！
"""
            
            prompt = analysis_context
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": SENTIMENT_ANALYST_PROMPT},
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
                reasoning=result.get('reasoning', '情绪分析'),
                key_metrics=result.get('key_metrics', {}),
                risk_score=float(result.get('risk_score', 0.5)),
                priority=2  # 情绪分析对短期交易优先级较高
            )
            
        except Exception as e:
            logger.error(f"情绪分析失败: {e}")
            return AgentAnalysis(
                agent_role=self.role,
                recommendation="hold",
                confidence=0.0,
                reasoning=f"分析失败: {str(e)}",
                key_metrics={},
                risk_score=0.5,
                priority=2
            )
    
    def _calculate_fear_greed_index(self, sentiment_data: Dict, market_data: Dict) -> int:
        """计算恐惧贪婪指数(0-100)"""
        factors = []
        
        # 1. 社交媒体情绪
        social_sentiment = sentiment_data.get('social_sentiment', 0.5)
        factors.append(social_sentiment)
        
        # 2. 市场波动率（高波动通常伴随恐惧）
        price = market_data.get('price', 0)
        high = market_data.get('high_24h', price)
        low = market_data.get('low_24h', price)
        volatility = ((high - low) / price * 100) if price > 0 else 0
        
        if volatility > 10:  # 高波动 -> 恐惧
            factors.append(0.3)
        elif volatility < 2:   # 低波动 -> 贪婪
            factors.append(0.8)
        else:
            factors.append(0.5)
        
        # 3. 价格动量
        price_change = market_data.get('change_24h', 0)
        if price_change > 5:   # 大涨 -> 贪婪
            factors.append(0.9)
        elif price_change < -5: # 大跌 -> 恐惧
            factors.append(0.2)
        else:
            factors.append(0.5 + (price_change / 10))  # 线性映射
        
        # 4. 成交量（异常成交量可能表示情绪极端）
        volume = market_data.get('volume_24h', 0)
        if volume > 5000000:  # 极高成交量
            factors.append(0.7)  # 偏向贪婪
        elif volume < 100000:  # 低成交量
            factors.append(0.4)  # 偏向恐惧
        else:
            factors.append(0.5)
        
        avg_factor = sum(factors) / len(factors) if factors else 0.5
        return int(avg_factor * 100)
    
    def _assess_sentiment_extremity(self, sentiment_data: Dict, fear_greed_index: int) -> str:
        """评估情绪极端程度"""
        sentiment_score = sentiment_data.get('sentiment_score', 0.5)
        
        # 综合情绪分数和恐惧贪婪指数
        if fear_greed_index > 80 or fear_greed_index < 20:
            return "extreme"
        elif fear_greed_index > 70 or fear_greed_index < 30:
            return "high"
        elif sentiment_score > 0.8 or sentiment_score < 0.2:
            return "high"
        elif sentiment_score > 0.7 or sentiment_score < 0.3:
            return "moderate"
        else:
            return "low"
    
    def _parse_response(self, content: str) -> Dict:
        """解析AI响应"""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {}

