"""
基本面分析师智能体
"""
import json
import re
from typing import Dict, Optional
from loguru import logger
import openai
import aiohttp

from backend.agents.base_agent import BaseAgent, AgentRole, AgentAnalysis
from backend.agents.prompts import FUNDAMENTAL_ANALYST_PROMPT, get_risk_control_context


class FundamentalAnalyst(BaseAgent):
    """基本面分析师 - 分析代币的内在价值和潜在风险"""
    
    def __init__(self, ai_model: str, api_key: str):
        super().__init__(AgentRole.FUNDAMENTAL_ANALYST, ai_model, api_key)
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
        """分析代币基本面"""
        try:
            # 获取链上数据和项目信息（这里可以集成真实的链上API）
            onchain_data = additional_data.get('onchain', {}) if additional_data else {}
            project_info = additional_data.get('project', {}) if additional_data else {}
            
            # 新增：基本面评分系统
            fundamental_score = self._calculate_fundamental_score(project_info, onchain_data)
            
            # 新增：估值评估
            valuation_assessment = self._assess_valuation(project_info, market_data)
            
            # 构建分析上下文（注入风控配置）
            analysis_context = f"""
{get_risk_control_context()}

当前交易对：{symbol}
市场数据：{json.dumps(market_data, ensure_ascii=False, indent=2)}

链上数据：
{json.dumps(onchain_data, ensure_ascii=False, indent=2)}

项目信息：
{json.dumps(project_info, ensure_ascii=False, indent=2)}

基本面综合评分: {fundamental_score}/100
估值评估: {valuation_assessment}

做空信号触发条件：
- 基本面评分 < 40分
- 项目估值明显高估
- 关键指标持续恶化
- 团队或生态出现重大问题

请基于以上数据进行基本面分析，评估代币的长期价值和成长潜力。如果项目高估或基本面恶化，请考虑做空建议。
注意：建议必须符合系统风控规则！
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
                        {"role": "system", "content": FUNDAMENTAL_ANALYST_PROMPT},
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
                reasoning=result.get('reasoning', '基本面分析'),
                key_metrics=result.get('key_metrics', {}),
                risk_score=float(result.get('risk_score', 0.5)),
                priority=3  # 基本面分析优先级中等
            )
            
        except Exception as e:
            logger.error(f"基本面分析失败: {e}")
            return AgentAnalysis(
                agent_role=self.role,
                recommendation="hold",
                confidence=0.0,
                reasoning=f"分析失败: {str(e)}",
                key_metrics={},
                risk_score=0.5,
                priority=3
            )
    
    def _calculate_fundamental_score(self, project_info: Dict, onchain_data: Dict) -> float:
        """计算项目基本面评分(0-100)"""
        score = 50  # 基础分
        
        # 1. 团队实力 (默认中等)
        team_strength = project_info.get('team_strength', 0.5)
        score += (team_strength - 0.5) * 20
        
        # 2. 生态发展
        ecosystem_health = onchain_data.get('ecosystem_health', 0.5)
        score += (ecosystem_health - 0.5) * 15
        
        # 3. 代币经济
        tokenomics_score = project_info.get('tokenomics_score', 0.5)
        score += (tokenomics_score - 0.5) * 15
        
        # 4. 竞争优势
        competitive_advantage = project_info.get('competitive_advantage', 0.5)
        score += (competitive_advantage - 0.5) * 10
        
        # 5. 链上活跃度
        active_users = onchain_data.get('active_users', 0)
        if active_users > 10000:
            score += 10
        elif active_users > 1000:
            score += 5
        
        # 6. 风险因素（负分）
        risk_factors = project_info.get('risk_factors', [])
        score -= len(risk_factors) * 5
        
        # 7. 技术创新
        tech_innovation = project_info.get('tech_innovation', 0.5)
        score += (tech_innovation - 0.5) * 10
        
        return max(0, min(100, round(score, 2)))
    
    def _assess_valuation(self, project_info: Dict, market_data: Dict) -> str:
        """评估估值水平"""
        market_cap = market_data.get('market_cap', 0)
        price = market_data.get('price', 0)
        
        # 获取项目收入或TVL
        revenue = project_info.get('annual_revenue', 0)
        tvl = project_info.get('tvl', 0)
        
        # 基于市值/收入比评估
        if revenue > 0:
            ps_ratio = market_cap / revenue
            if ps_ratio > 50:
                return "严重高估"
            elif ps_ratio > 20:
                return "高估"
            elif ps_ratio > 5:
                return "合理"
            else:
                return "低估"
        
        # 基于市值/TVL比评估
        elif tvl > 0:
            mcap_tvl_ratio = market_cap / tvl
            if mcap_tvl_ratio > 5:
                return "高估"
            elif mcap_tvl_ratio > 1:
                return "合理"
            else:
                return "低估"
        
        # 基于价格变化评估
        change_24h = market_data.get('change_24h', 0)
        change_7d = market_data.get('change_7d', 0)
        
        if change_24h > 20 or change_7d > 50:
            return "可能高估（短期涨幅过大）"
        elif change_24h < -20 or change_7d < -50:
            return "可能低估（短期跌幅过大）"
        
        return "未知（缺乏基本面数据）"
    
    def _parse_response(self, content: str) -> Dict:
        """解析AI响应"""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {}

