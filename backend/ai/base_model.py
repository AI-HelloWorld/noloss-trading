"""
AI模型基础类
"""
from abc import ABC, abstractmethod
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class AIDecisionResult:
    """AI决策结果"""
    decision: str  # buy, sell, hold, short, cover
    confidence: float  # 0-1之间的置信度
    reasoning: str  # 决策理由
    suggested_amount: float  # 建议交易数量（占总资金比例）
    stop_loss: float = 0.0  # 止损价格
    take_profit: float = 0.0  # 止盈价格


class BaseAIModel(ABC):
    """AI模型基础类"""
    
    def __init__(self, name: str, api_key: str):
        self.name = name
        self.api_key = api_key
    
    @abstractmethod
    async def analyze_market(
        self, 
        symbol: str, 
        market_data: Dict,
        current_positions: List[Dict],
        portfolio_value: float
    ) -> AIDecisionResult:
        """
        分析市场并做出交易决策
        
        Args:
            symbol: 交易对符号
            market_data: 市场数据
            current_positions: 当前持仓
            portfolio_value: 投资组合总价值
        
        Returns:
            AIDecisionResult: AI决策结果
        """
        pass
    
    @abstractmethod
    async def get_model_status(self) -> Dict:
        """获取模型状态"""
        pass
    
    def _create_market_prompt(self, symbol: str, market_data: Dict, current_positions: List[Dict]) -> str:
        """创建市场分析提示词"""
        prompt = f"""你是一个专业的加密货币交易AI。请分析以下市场数据并给出交易建议。

交易对: {symbol}
当前价格: ${market_data.get('price', 0):.2f}
24小时涨跌: {market_data.get('change_24h', 0):.2f}%
24小时最高: ${market_data.get('high_24h', 0):.2f}
24小时最低: ${market_data.get('low_24h', 0):.2f}
24小时成交量: ${market_data.get('volume_24h', 0):,.2f}

当前持仓:
{self._format_positions(current_positions)}

请根据以上信息，给出你的交易建议：
1. 决策类型（buy/sell/hold/short/cover）
2. 置信度（0-1之间的数字）
3. 详细的决策理由
4. 建议的仓位大小（占总资金的比例，0-1之间）
5. 止损价格建议
6. 止盈价格建议

请以JSON格式回复：
{{
    "decision": "buy/sell/hold/short/cover",
    "confidence": 0.0-1.0,
    "reasoning": "详细理由",
    "position_size": 0.0-1.0,
    "stop_loss": 价格,
    "take_profit": 价格
}}
"""
        return prompt
    
    def _format_positions(self, positions: List[Dict]) -> str:
        """格式化持仓信息"""
        if not positions:
            return "无持仓"
        
        result = []
        for pos in positions:
            result.append(
                f"- {pos.get('symbol')}: {pos.get('amount')} 个, "
                f"均价 ${pos.get('average_price', 0):.2f}, "
                f"当前价 ${pos.get('current_price', 0):.2f}, "
                f"盈亏: {pos.get('unrealized_pnl', 0):.2f}%"
            )
        return "\n".join(result)

