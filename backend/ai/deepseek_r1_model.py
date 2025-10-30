"""
DeepSeek-R1推理模型实现
"""
import json
from typing import Dict, List
import aiohttp
from loguru import logger
from backend.ai.base_model import BaseAIModel, AIDecisionResult
from backend.config import settings


class DeepSeekR1Model(BaseAIModel):
    """DeepSeek-R1推理增强交易模型"""
    
    def __init__(self):
        super().__init__("DeepSeek-R1", settings.deepseek_api_key)
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        # DeepSeek-R1推理模型
        self.model_name = "deepseek-reasoner"
    
    async def analyze_market(
        self, 
        symbol: str, 
        market_data: Dict,
        current_positions: List[Dict],
        portfolio_value: float
    ) -> AIDecisionResult:
        """使用DeepSeek-R1推理模型分析市场"""
        try:
            prompt = self._create_market_prompt(symbol, market_data, current_positions)
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.model_name,
                    "messages": [
                        {
                            "role": "system", 
                            "content": "你是一个专业的加密货币交易分析师，具备深度推理能力。请进行系统性的分析和推理。"
                        },
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.6,  # R1模型推荐使用较低温度
                    "max_tokens": 2000  # R1模型需要更多token进行推理
                }
                
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    data = await response.json()
                    
                    # DeepSeek-R1返回包含推理过程的响应
                    if 'choices' not in data or not data['choices']:
                        logger.error(f"DeepSeek-R1 API响应格式错误: {data}")
                        raise ValueError("API响应格式错误")
                    
                    message = data['choices'][0]['message']
                    content = message.get('content', '')
                    
                    # R1模型可能会返回reasoning_content字段，包含推理过程
                    reasoning_content = message.get('reasoning_content', '')
                    
                    if reasoning_content:
                        logger.info(f"DeepSeek-R1推理过程: {reasoning_content[:500]}...")
            
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
            
            # 如果有推理过程，将其添加到reasoning中
            reasoning = result.get('reasoning', 'DeepSeek-R1分析结果')
            if reasoning_content:
                reasoning = f"[R1推理] {reasoning}\n\n推理过程: {reasoning_content[:300]}..."
            
            return AIDecisionResult(
                decision=result.get('decision', 'hold'),
                confidence=float(result.get('confidence', 0.5)),
                reasoning=reasoning,
                suggested_amount=float(result.get('position_size', 0.1)),
                stop_loss=float(result.get('stop_loss', 0)),
                take_profit=float(result.get('take_profit', 0))
            )
            
        except Exception as e:
            logger.error(f"DeepSeek-R1分析失败: {e}")
            return AIDecisionResult(
                decision="hold",
                confidence=0.0,
                reasoning=f"分析失败: {str(e)}",
                suggested_amount=0.0
            )
    
    async def analyze_with_reasoning(
        self,
        prompt: str,
        system_prompt: str = None
    ) -> Dict:
        """
        使用DeepSeek-R1进行深度推理分析
        
        Returns:
            {
                "content": "最终回答",
                "reasoning_content": "推理过程",
                "raw_response": "原始响应"
            }
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                payload = {
                    "model": self.model_name,
                    "messages": messages,
                    "temperature": 0.6,
                    "max_tokens": 2000
                }
                
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    data = await response.json()
                    
                    if 'choices' not in data or not data['choices']:
                        raise ValueError("API响应格式错误")
                    
                    message = data['choices'][0]['message']
                    
                    return {
                        "content": message.get('content', ''),
                        "reasoning_content": message.get('reasoning_content', ''),
                        "raw_response": data
                    }
        
        except Exception as e:
            logger.error(f"DeepSeek-R1推理失败: {e}")
            return {
                "content": "",
                "reasoning_content": "",
                "error": str(e)
            }
    
    async def get_model_status(self) -> Dict:
        """获取模型状态"""
        return {
            "name": self.name,
            "model": self.model_name,
            "status": "active" if self.api_key else "inactive",
            "api_key_configured": bool(self.api_key),
            "capabilities": ["reasoning", "deep_analysis", "trading_strategy"]
        }


# 全局实例
deepseek_r1_model = DeepSeekR1Model()

