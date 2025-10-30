"""
Grok模型实现
"""
import json
from typing import Dict, List
import aiohttp
from loguru import logger
from backend.ai.base_model import BaseAIModel, AIDecisionResult
from backend.config import settings


class GrokModel(BaseAIModel):
    """Grok交易模型"""
    
    def __init__(self):
        super().__init__("Grok", settings.grok_api_key)
        self.api_url = "https://api.x.ai/v1/chat/completions"
    
    async def analyze_market(
        self, 
        symbol: str, 
        market_data: Dict,
        current_positions: List[Dict],
        portfolio_value: float
    ) -> AIDecisionResult:
        """使用Grok分析市场"""
        try:
            prompt = self._create_market_prompt(symbol, market_data, current_positions)
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": "grok-beta",
                    "messages": [
                        {"role": "system", "content": "你是一个专业的加密货币交易分析师。"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
                
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    data = await response.json()
                    content = data['choices'][0]['message']['content']
            
            # 解析JSON响应
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    raise ValueError("无法解析AI响应")
            
            return AIDecisionResult(
                decision=result.get('decision', 'hold'),
                confidence=float(result.get('confidence', 0.5)),
                reasoning=result.get('reasoning', 'Grok分析结果'),
                suggested_amount=float(result.get('position_size', 0.1)),
                stop_loss=float(result.get('stop_loss', 0)),
                take_profit=float(result.get('take_profit', 0))
            )
            
        except Exception as e:
            logger.error(f"Grok分析失败: {e}")
            return AIDecisionResult(
                decision="hold",
                confidence=0.0,
                reasoning=f"分析失败: {str(e)}",
                suggested_amount=0.0
            )
    
    async def get_model_status(self) -> Dict:
        """获取模型状态"""
        return {
            "name": self.name,
            "status": "active" if self.api_key else "inactive",
            "api_key_configured": bool(self.api_key)
        }

