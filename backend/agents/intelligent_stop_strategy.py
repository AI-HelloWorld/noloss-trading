"""
智能止盈止损策略
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from loguru import logger
from enum import Enum


class StopStrategyType(Enum):
    FIXED = "fixed"  # 固定比例
    VOLATILITY_BASED = "volatility"  # 波动率基准
    TRAILING = "trailing"  # 移动止损
    TIME_BASED = "time"  # 时间基准
    SUPPORT_RESISTANCE = "support_resistance"  # 支撑阻力位


class IntelligentStopStrategy:
    """智能止盈止损策略"""
    
    def __init__(self):
        self.base_stop_loss_pct = 0.02  # 基础止损比例 2%
        self.base_take_profit_pct = 0.04  # 基础止盈比例 4%
        self.volatility_multiplier = 2.0  # 波动率乘数
        self.trailing_activation_pct = 0.03  # 移动止损激活阈值 3%
        self.trailing_stop_pct = 0.015  # 移动止损比例 1.5%
    
    def calculate_stop_levels(
        self,
        action: str,
        entry_price: float,
        market_data: Dict,
        position_size: float,
        confidence: float,
        volatility: float,
        additional_factors: Optional[Dict] = None
    ) -> Dict:
        """
        计算智能止盈止损水平
        
        Args:
            action: 交易方向 (buy/short)
            entry_price: 入场价格
            market_data: 市场数据
            position_size: 仓位大小
            confidence: 信号置信度
            volatility: 波动率
            additional_factors: 额外因素
        
        Returns:
            止盈止损配置
        """
        if additional_factors is None:
            additional_factors = {}
        
        # 根据置信度调整止损幅度
        confidence_adjustment = self._calculate_confidence_adjustment(confidence)
        
        # 根据波动率调整
        volatility_adjustment = self._calculate_volatility_adjustment(volatility)
        
        # 根据仓位大小调整
        position_adjustment = self._calculate_position_adjustment(position_size)
        
        # 综合调整因子
        adjustment_factor = confidence_adjustment * volatility_adjustment * position_adjustment
        
        if action == "buy":
            return self._calculate_long_stops(entry_price, adjustment_factor, market_data, additional_factors)
        elif action == "short":
            return self._calculate_short_stops(entry_price, adjustment_factor, market_data, additional_factors)
        else:
            return {"stop_loss": 0, "take_profit": 0, "strategy_type": "none"}
    
    def _calculate_long_stops(
        self,
        entry_price: float,
        adjustment_factor: float,
        market_data: Dict,
        additional_factors: Dict
    ) -> Dict:
        """计算做多止盈止损"""
        # 基础止损止盈
        base_stop_loss = entry_price * (1 - self.base_stop_loss_pct * adjustment_factor)
        base_take_profit = entry_price * (1 + self.base_take_profit_pct * adjustment_factor)
        
        # 支撑阻力位分析
        support_level = self._find_support_level(market_data, additional_factors)
        resistance_level = self._find_resistance_level(market_data, additional_factors)
        
        # 使用更优的止损位（基础止损或支撑位下方）
        if support_level and support_level > base_stop_loss:
            stop_loss = support_level * 0.99  # 在支撑位下方1%
            strategy_type = StopStrategyType.SUPPORT_RESISTANCE
        else:
            stop_loss = base_stop_loss
            strategy_type = StopStrategyType.VOLATILITY_BASED
        
        # 使用更优的止盈位（基础止盈或阻力位）
        if resistance_level and resistance_level < base_take_profit:
            take_profit = resistance_level * 0.99  # 在阻力位下方1%
        else:
            take_profit = base_take_profit
        
        # 计算风险回报比
        risk = entry_price - stop_loss
        reward = take_profit - entry_price
        risk_reward_ratio = reward / risk if risk > 0 else 0
        
        # 如果风险回报比不理想，调整止盈
        if risk_reward_ratio < 1.5:
            take_profit = entry_price + (risk * 2)  # 至少1:2的风险回报比
            risk_reward_ratio = 2.0
        
        return {
            "stop_loss": round(stop_loss, 4),
            "take_profit": round(take_profit, 4),
            "strategy_type": strategy_type.value,
            "risk_reward_ratio": round(risk_reward_ratio, 2),
            "risk_pct": round((entry_price - stop_loss) / entry_price * 100, 2),
            "reward_pct": round((take_profit - entry_price) / entry_price * 100, 2)
        }
    
    def _calculate_short_stops(
        self,
        entry_price: float,
        adjustment_factor: float,
        market_data: Dict,
        additional_factors: Dict
    ) -> Dict:
        """计算做空止盈止损"""
        # 基础止损止盈（做空方向相反）
        base_stop_loss = entry_price * (1 + self.base_stop_loss_pct * adjustment_factor)
        base_take_profit = entry_price * (1 - self.base_take_profit_pct * adjustment_factor)
        
        # 支撑阻力位分析
        support_level = self._find_support_level(market_data, additional_factors)
        resistance_level = self._find_resistance_level(market_data, additional_factors)
        
        # 使用更优的止损位（基础止损或阻力位上方）
        if resistance_level and resistance_level < base_stop_loss:
            stop_loss = resistance_level * 1.01  # 在阻力位上方1%
            strategy_type = StopStrategyType.SUPPORT_RESISTANCE
        else:
            stop_loss = base_stop_loss
            strategy_type = StopStrategyType.VOLATILITY_BASED
        
        # 使用更优的止盈位（基础止盈或支撑位）
        if support_level and support_level > base_take_profit:
            take_profit = support_level * 1.01  # 在支撑位上方1%
        else:
            take_profit = base_take_profit
        
        # 计算风险回报比
        risk = stop_loss - entry_price
        reward = entry_price - take_profit
        risk_reward_ratio = reward / risk if risk > 0 else 0
        
        # 如果风险回报比不理想，调整止盈
        if risk_reward_ratio < 1.5:
            take_profit = entry_price - (risk * 2)  # 至少1:2的风险回报比
            risk_reward_ratio = 2.0
        
        return {
            "stop_loss": round(stop_loss, 4),
            "take_profit": round(take_profit, 4),
            "strategy_type": strategy_type.value,
            "risk_reward_ratio": round(risk_reward_ratio, 2),
            "risk_pct": round((stop_loss - entry_price) / entry_price * 100, 2),
            "reward_pct": round((entry_price - take_profit) / entry_price * 100, 2)
        }
    
    def _calculate_confidence_adjustment(self, confidence: float) -> float:
        """根据置信度调整止损幅度"""
        if confidence > 0.8:
            return 0.7  # 高置信度，使用更紧止损
        elif confidence > 0.6:
            return 1.0  # 中等置信度，标准止损
        else:
            return 1.3  # 低置信度，使用更宽止损
    
    def _calculate_volatility_adjustment(self, volatility: float) -> float:
        """根据波动率调整止损幅度"""
        if volatility > 10:  # 高波动率
            return 1.5
        elif volatility > 5:  # 中等波动率
            return 1.2
        else:  # 低波动率
            return 0.8
    
    def _calculate_position_adjustment(self, position_size: float) -> float:
        """根据仓位大小调整止损幅度"""
        if position_size > 0.2:  # 大仓位
            return 0.8  # 使用更紧止损
        elif position_size > 0.1:  # 中等仓位
            return 1.0
        else:  # 小仓位
            return 1.2  # 可以使用更宽止损
    
    def _find_support_level(self, market_data: Dict, additional_factors: Dict) -> Optional[float]:
        """寻找支撑位"""
        # 从技术指标中获取支撑位
        key_levels = additional_factors.get('key_levels', {})
        support_levels = key_levels.get('support_levels', [])
        
        if support_levels:
            # 返回最接近当前价格的支撑位
            current_price = market_data.get('price', 0)
            valid_supports = [s for s in support_levels if s < current_price]
            if valid_supports:
                return max(valid_supports)
        
        # 使用近期低点作为支撑
        low_24h = market_data.get('low_24h')
        
        if low_24h:
            return low_24h
        
        return None
    
    def _find_resistance_level(self, market_data: Dict, additional_factors: Dict) -> Optional[float]:
        """寻找阻力位"""
        # 从技术指标中获取阻力位
        key_levels = additional_factors.get('key_levels', {})
        resistance_levels = key_levels.get('resistance_levels', [])
        
        if resistance_levels:
            # 返回最接近当前价格的阻力位
            current_price = market_data.get('price', 0)
            valid_resistances = [r for r in resistance_levels if r > current_price]
            if valid_resistances:
                return min(valid_resistances)
        
        # 使用近期高点作为阻力
        high_24h = market_data.get('high_24h')
        
        if high_24h:
            return high_24h
        
        return None
    
    def calculate_trailing_stop(
        self,
        action: str,
        entry_price: float,
        current_price: float,
        highest_price: float,
        lowest_price: float
    ) -> float:
        """计算移动止损位"""
        if action == "buy":
            # 做多移动止损：从最高点回撤一定比例
            if current_price >= entry_price * (1 + self.trailing_activation_pct):
                trailing_stop = highest_price * (1 - self.trailing_stop_pct)
                return max(trailing_stop, entry_price * (1 - self.base_stop_loss_pct))
            else:
                return entry_price * (1 - self.base_stop_loss_pct)
        
        elif action == "short":
            # 做空移动止损：从最低点回撤一定比例
            if current_price <= entry_price * (1 - self.trailing_activation_pct):
                trailing_stop = lowest_price * (1 + self.trailing_stop_pct)
                return min(trailing_stop, entry_price * (1 + self.base_stop_loss_pct))
            else:
                return entry_price * (1 + self.base_stop_loss_pct)
        
        return 0


# 全局止盈止损策略实例
intelligent_stop_strategy = IntelligentStopStrategy()

