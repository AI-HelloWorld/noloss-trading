"""
基础智能体类
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class AgentRole(Enum):
    """智能体角色"""
    FUNDAMENTAL_ANALYST = "fundamental_analyst"
    SENTIMENT_ANALYST = "sentiment_analyst"
    NEWS_ANALYST = "news_analyst"
    TECHNICAL_ANALYST = "technical_analyst"
    RISK_MANAGER = "risk_manager"
    PORTFOLIO_MANAGER = "portfolio_manager"


@dataclass
class AgentAnalysis:
    """智能体分析结果"""
    agent_role: AgentRole
    recommendation: str  # buy, sell, hold, short, cover
    confidence: float  # 0-1之间的置信度
    reasoning: str
    key_metrics: Dict  # 关键指标
    risk_score: float = 0.5  # 0-1之间，风险评分
    priority: int = 1  # 优先级，1-5


class BaseAgent(ABC):
    """智能体基类"""
    
    def __init__(self, role: AgentRole, ai_model: str, api_key: str):
        self.role = role
        self.ai_model = ai_model
        self.api_key = api_key
        self.name = self._get_role_name()
    
    def _get_role_name(self) -> str:
        """获取角色名称"""
        role_names = {
            AgentRole.FUNDAMENTAL_ANALYST: "基本面分析师",
            AgentRole.SENTIMENT_ANALYST: "情绪分析师",
            AgentRole.NEWS_ANALYST: "新闻分析师",
            AgentRole.TECHNICAL_ANALYST: "技术分析师",
            AgentRole.RISK_MANAGER: "风险管理经理",
            AgentRole.PORTFOLIO_MANAGER: "投资组合经理"
        }
        return role_names.get(self.role, "未知角色")
    
    @abstractmethod
    async def analyze(
        self,
        symbol: str,
        market_data: Dict,
        additional_data: Optional[Dict] = None
    ) -> AgentAnalysis:
        """
        分析市场并给出建议
        
        Args:
            symbol: 交易对
            market_data: 市场数据
            additional_data: 额外数据（如新闻、社交媒体等）
        
        Returns:
            AgentAnalysis: 分析结果
        """
        pass
    
    def _create_prompt(self, symbol: str, market_data: Dict, role_specific_context: str) -> str:
        """创建AI提示词"""
        base_prompt = f"""你是一个专业的{self.name}。

交易对: {symbol}
当前价格: ${market_data.get('price', 0):.2f}
24小时涨跌: {market_data.get('change_24h', 0):.2f}%
24小时最高: ${market_data.get('high_24h', 0):.2f}
24小时最低: ${market_data.get('low_24h', 0):.2f}
24小时成交量: ${market_data.get('volume_24h', 0):,.2f}

{role_specific_context}

请从{self.name}的专业角度进行分析，并以JSON格式回复：
{{
    "recommendation": "buy/sell/hold/short/cover",
    "confidence": 0.0-1.0,
    "reasoning": "详细的分析理由",
    "key_metrics": {{"指标名": 值}},
    "risk_score": 0.0-1.0
}}
"""
        return base_prompt

