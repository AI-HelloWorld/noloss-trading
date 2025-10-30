"""
止盈止损决策系统 - 由AI团队协同决策
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from backend.agents.intelligent_stop_strategy import intelligent_stop_strategy, StopStrategyType


class StopActionType(Enum):
    """止盈止损操作类型"""
    HOLD = "hold"  # 继续持仓
    STOP_LOSS = "stop_loss"  # 执行止损
    TAKE_PROFIT = "take_profit"  # 执行止盈
    TRAILING_STOP = "trailing_stop"  # 移动止损
    ADJUST_STOP = "adjust_stop"  # 调整止损位
    TIGHTEN_STOP = "tighten_stop"  # 收紧止损


@dataclass
class StopLossOpinion:
    """智能体的止盈止损意见"""
    agent_role: str  # 智能体角色
    agent_name: str  # 智能体名称
    action: StopActionType  # 建议操作
    confidence: float  # 置信度 0-1
    reasoning: str  # 理由
    suggested_stop_loss: Optional[float] = None  # 建议的止损价
    suggested_take_profit: Optional[float] = None  # 建议的止盈价
    urgency: float = 0.5  # 紧急程度 0-1
    risk_assessment: float = 0.5  # 风险评估 0-1


class StopLossDecisionSystem:
    """止盈止损决策系统"""
    
    def __init__(self):
        self.stop_strategy = intelligent_stop_strategy
        self.active_positions = {}  # 存储活跃持仓
    
    def register_position(
        self,
        position_id: str,
        symbol: str,
        action: str,
        entry_price: float,
        quantity: float,
        stop_loss: float,
        take_profit: float,
        confidence: float,
        strategy_info: Dict
    ):
        """注册新持仓"""
        self.active_positions[position_id] = {
            'symbol': symbol,
            'action': action,
            'entry_price': entry_price,
            'quantity': quantity,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'confidence': confidence,
            'strategy_info': strategy_info,
            'highest_price': entry_price,
            'lowest_price': entry_price,
            'pnl': 0.0,
            'pnl_pct': 0.0
        }
        logger.info(f"📝 注册持仓监控: {position_id} - {symbol} {action} @ ${entry_price:.2f}")
    
    def update_position_price(self, position_id: str, current_price: float):
        """更新持仓价格"""
        if position_id not in self.active_positions:
            return
        
        position = self.active_positions[position_id]
        position['current_price'] = current_price
        
        # 更新最高价/最低价
        position['highest_price'] = max(position.get('highest_price', current_price), current_price)
        position['lowest_price'] = min(position.get('lowest_price', current_price), current_price)
        
        # 计算盈亏
        if position['action'] == 'buy':
            position['pnl'] = (current_price - position['entry_price']) * position['quantity']
            position['pnl_pct'] = (current_price - position['entry_price']) / position['entry_price'] * 100
        else:  # short
            position['pnl'] = (position['entry_price'] - current_price) * position['quantity']
            position['pnl_pct'] = (position['entry_price'] - current_price) / position['entry_price'] * 100
    
    def collect_team_opinions(
        self,
        position_id: str,
        team_analyses: List,
        market_data: Dict
    ) -> List[StopLossOpinion]:
        """收集AI团队对止盈止损的意见"""
        if position_id not in self.active_positions:
            logger.warning(f"持仓{position_id}不存在")
            return []
        
        position = self.active_positions[position_id]
        opinions = []
        
        # 遍历所有AI智能体的分析
        for analysis in team_analyses:
            opinion = self._extract_stop_opinion_from_analysis(
                analysis, position, market_data
            )
            if opinion:
                opinions.append(opinion)
        
        logger.info(f"📊 收集到{len(opinions)}个AI智能体的止盈止损意见")
        return opinions
    
    def _extract_stop_opinion_from_analysis(
        self,
        analysis,
        position: Dict,
        market_data: Dict
    ) -> Optional[StopLossOpinion]:
        """从AI分析中提取止盈止损意见"""
        try:
            current_price = market_data.get('price', position['current_price'])
            pnl_pct = position.get('pnl_pct', 0)
            
            # 根据AI智能体的角色和建议判断止盈止损
            agent_role = str(analysis.agent_role.value if hasattr(analysis, 'agent_role') else 'unknown')
            recommendation = analysis.recommendation if hasattr(analysis, 'recommendation') else 'hold'
            confidence = analysis.confidence if hasattr(analysis, 'confidence') else 0.5
            reasoning = analysis.reasoning if hasattr(analysis, 'reasoning') else ''
            risk_score = analysis.risk_score if hasattr(analysis, 'risk_score') else 0.5
            
            # 判断止盈止损操作
            action = StopActionType.HOLD
            urgency = 0.3
            suggested_stop = position['stop_loss']
            suggested_take_profit = position['take_profit']
            
            # 技术分析师 - 关注价格突破和趋势反转
            if 'technical' in agent_role.lower():
                if position['action'] == 'buy':
                    # 如果技术分析建议卖出，可能是趋势反转
                    if recommendation in ['sell', 'cover'] and confidence > 0.6:
                        action = StopActionType.STOP_LOSS if pnl_pct < 0 else StopActionType.TAKE_PROFIT
                        urgency = confidence
                        reasoning_detail = f"技术信号显示趋势反转: {reasoning[:100]}"
                    # 如果持仓盈利且技术分析不建议买入，考虑收紧止损
                    elif pnl_pct > 3 and recommendation == 'hold':
                        action = StopActionType.TIGHTEN_STOP
                        suggested_stop = position['highest_price'] * 0.98  # 在最高价下方2%
                        reasoning_detail = f"盈利{pnl_pct:.2f}%，技术面建议收紧止损保护利润"
                    else:
                        action = StopActionType.HOLD
                        reasoning_detail = f"技术面支持继续持仓: {reasoning[:100]}"
                else:  # short
                    if recommendation in ['buy', 'cover'] and confidence > 0.6:
                        action = StopActionType.STOP_LOSS if pnl_pct < 0 else StopActionType.TAKE_PROFIT
                        urgency = confidence
                        reasoning_detail = f"技术信号显示空头反转: {reasoning[:100]}"
                    elif pnl_pct > 3 and recommendation == 'hold':
                        action = StopActionType.TIGHTEN_STOP
                        suggested_stop = position['lowest_price'] * 1.02
                        reasoning_detail = f"空头盈利{pnl_pct:.2f}%，建议收紧止损"
                    else:
                        action = StopActionType.HOLD
                        reasoning_detail = f"技术面支持继续做空: {reasoning[:100]}"
            
            # 风险管理经理 - 关注风险控制
            elif 'risk' in agent_role.lower():
                if risk_score > 0.7:
                    # 高风险环境，建议止损或收紧止损
                    if pnl_pct < -2:
                        action = StopActionType.STOP_LOSS
                        urgency = 0.9
                        reasoning_detail = f"风险过高({risk_score:.2f})，亏损{pnl_pct:.2f}%，建议止损"
                    elif pnl_pct > 2:
                        action = StopActionType.TIGHTEN_STOP
                        urgency = 0.7
                        reasoning_detail = f"风险升高，建议收紧止损保护{pnl_pct:.2f}%的利润"
                    else:
                        action = StopActionType.HOLD
                        reasoning_detail = f"风险较高但在可控范围，继续监控"
                elif pnl_pct > 5:
                    # 盈利丰厚，建议部分止盈或移动止损
                    action = StopActionType.TRAILING_STOP
                    urgency = 0.6
                    reasoning_detail = f"盈利{pnl_pct:.2f}%，建议启用移动止损锁定利润"
                else:
                    action = StopActionType.HOLD
                    reasoning_detail = f"风险可控({risk_score:.2f})，继续持仓"
            
            # 基本面分析师 - 关注长期价值
            elif 'fundamental' in agent_role.lower():
                if position['action'] == 'buy':
                    if recommendation == 'sell' and confidence > 0.7:
                        action = StopActionType.TAKE_PROFIT
                        urgency = 0.7
                        reasoning_detail = f"基本面恶化，建议止盈离场: {reasoning[:100]}"
                    elif pnl_pct > 10:
                        action = StopActionType.TAKE_PROFIT
                        urgency = 0.6
                        reasoning_detail = f"盈利{pnl_pct:.2f}%，达到基本面目标，建议止盈"
                    else:
                        action = StopActionType.HOLD
                        reasoning_detail = f"基本面良好，继续持有: {reasoning[:100]}"
                else:  # short
                    if recommendation == 'buy' and confidence > 0.7:
                        action = StopActionType.TAKE_PROFIT
                        urgency = 0.7
                        reasoning_detail = f"基本面改善，建议平空: {reasoning[:100]}"
                    else:
                        action = StopActionType.HOLD
                        reasoning_detail = f"基本面支持做空: {reasoning[:100]}"
            
            # 情绪分析师 - 关注市场情绪
            elif 'sentiment' in agent_role.lower():
                # 情绪极端时考虑反向操作
                if position['action'] == 'buy' and recommendation == 'sell' and confidence > 0.7:
                    action = StopActionType.TAKE_PROFIT if pnl_pct > 0 else StopActionType.HOLD
                    urgency = 0.5
                    reasoning_detail = f"市场情绪转负，建议谨慎: {reasoning[:100]}"
                elif position['action'] == 'short' and recommendation == 'buy' and confidence > 0.7:
                    action = StopActionType.TAKE_PROFIT if pnl_pct > 0 else StopActionType.HOLD
                    urgency = 0.5
                    reasoning_detail = f"市场情绪转正，建议平空: {reasoning[:100]}"
                else:
                    action = StopActionType.HOLD
                    reasoning_detail = f"市场情绪稳定: {reasoning[:100]}"
            
            # 新闻分析师 - 关注重大事件
            elif 'news' in agent_role.lower():
                if confidence > 0.8:
                    # 重大新闻可能导致急剧变化
                    if position['action'] == 'buy' and recommendation == 'sell':
                        action = StopActionType.STOP_LOSS if pnl_pct < 0 else StopActionType.TAKE_PROFIT
                        urgency = 0.8
                        reasoning_detail = f"重大利空消息: {reasoning[:100]}"
                    elif position['action'] == 'short' and recommendation == 'buy':
                        action = StopActionType.STOP_LOSS if pnl_pct < 0 else StopActionType.TAKE_PROFIT
                        urgency = 0.8
                        reasoning_detail = f"重大利好消息: {reasoning[:100]}"
                    else:
                        action = StopActionType.HOLD
                        reasoning_detail = f"新闻面无重大影响: {reasoning[:100]}"
                else:
                    action = StopActionType.HOLD
                    reasoning_detail = f"新闻面平稳: {reasoning[:100]}"
            
            # 默认处理
            else:
                action = StopActionType.HOLD
                reasoning_detail = f"{agent_role}建议: {reasoning[:100]}"
            
            return StopLossOpinion(
                agent_role=agent_role,
                agent_name=getattr(analysis, 'name', agent_role),
                action=action,
                confidence=confidence,
                reasoning=reasoning_detail,
                suggested_stop_loss=suggested_stop,
                suggested_take_profit=suggested_take_profit,
                urgency=urgency,
                risk_assessment=risk_score
            )
        
        except Exception as e:
            logger.error(f"提取止盈止损意见失败: {e}")
            return None
    
    def make_stop_decision(
        self,
        position_id: str,
        opinions: List[StopLossOpinion],
        market_data: Dict
    ) -> Dict:
        """
        综合所有AI意见，做出最终止盈止损决策（由投资组合经理决定）
        
        Returns:
            {
                'final_decision': 'execute' or 'hold',
                'action': StopActionType,
                'confidence': float,
                'reasoning': str,
                'suggested_stop_loss': float,
                'suggested_take_profit': float,
                'team_votes': Dict,
                'urgency': float
            }
        """
        if position_id not in self.active_positions:
            return {'final_decision': 'hold', 'action': StopActionType.HOLD}
        
        position = self.active_positions[position_id]
        
        # 统计各种意见
        vote_counts = {action: 0 for action in StopActionType}
        total_confidence = 0
        total_urgency = 0
        risk_manager_opinion = None
        
        for opinion in opinions:
            vote_counts[opinion.action] += 1
            total_confidence += opinion.confidence
            total_urgency += opinion.urgency
            
            # 风险管理经理的意见权重最高
            if 'risk' in opinion.agent_role.lower():
                risk_manager_opinion = opinion
        
        avg_confidence = total_confidence / len(opinions) if opinions else 0
        avg_urgency = total_urgency / len(opinions) if opinions else 0
        
        # 决策逻辑（投资组合经理综合判断）
        final_action = StopActionType.HOLD
        final_decision = 'hold'
        reasoning_parts = []
        
        # 1. 风险管理经理有否决权
        if risk_manager_opinion:
            if risk_manager_opinion.action in [StopActionType.STOP_LOSS, StopActionType.TAKE_PROFIT]:
                if risk_manager_opinion.urgency > 0.7:
                    final_action = risk_manager_opinion.action
                    final_decision = 'execute'
                    reasoning_parts.append(f"🛡️ 风险管理经理强烈建议{final_action.value}: {risk_manager_opinion.reasoning}")
        
        # 2. 如果风险经理没有强制要求，看团队共识
        if final_decision == 'hold':
            # 找出票数最多的操作
            max_votes = max(vote_counts.values())
            consensus_actions = [action for action, votes in vote_counts.items() if votes == max_votes]
            
            # 如果有明确共识（超过50%支持）
            consensus_threshold = len(opinions) * 0.5
            
            for action, votes in vote_counts.items():
                if votes >= consensus_threshold and action != StopActionType.HOLD:
                    final_action = action
                    if avg_confidence > 0.6 and avg_urgency > 0.5:
                        final_decision = 'execute'
                        reasoning_parts.append(
                            f"👥 团队共识({votes}/{len(opinions)}): {action.value}, "
                            f"置信度{avg_confidence:.2f}, 紧急度{avg_urgency:.2f}"
                        )
                    else:
                        reasoning_parts.append(
                            f"⚠️ 团队建议{action.value}但置信度不足({avg_confidence:.2f}), 继续观察"
                        )
                    break
        
        # 3. 自动触发条件（六种止盈止损方式）
        current_price = market_data.get('price', position.get('current_price', 0))
        
        # 检查固定止损止盈
        if position['action'] == 'buy':
            if current_price <= position['stop_loss']:
                final_action = StopActionType.STOP_LOSS
                final_decision = 'execute'
                reasoning_parts.append(f"🚨 固定止损触发: ${current_price:.2f} <= ${position['stop_loss']:.2f}")
            elif current_price >= position['take_profit']:
                final_action = StopActionType.TAKE_PROFIT
                final_decision = 'execute'
                reasoning_parts.append(f"🎯 固定止盈触发: ${current_price:.2f} >= ${position['take_profit']:.2f}")
        else:  # short
            if current_price >= position['stop_loss']:
                final_action = StopActionType.STOP_LOSS
                final_decision = 'execute'
                reasoning_parts.append(f"🚨 固定止损触发: ${current_price:.2f} >= ${position['stop_loss']:.2f}")
            elif current_price <= position['take_profit']:
                final_action = StopActionType.TAKE_PROFIT
                final_decision = 'execute'
                reasoning_parts.append(f"🎯 固定止盈触发: ${current_price:.2f} <= ${position['take_profit']:.2f}")
        
        # 检查移动止损
        trailing_stop = self.stop_strategy.calculate_trailing_stop(
            position['action'],
            position['entry_price'],
            current_price,
            position['highest_price'],
            position['lowest_price']
        )
        
        if position['action'] == 'buy' and current_price <= trailing_stop:
            final_action = StopActionType.TRAILING_STOP
            final_decision = 'execute'
            reasoning_parts.append(f"📍 移动止损触发: ${current_price:.2f} <= ${trailing_stop:.2f}")
        elif position['action'] == 'short' and current_price >= trailing_stop:
            final_action = StopActionType.TRAILING_STOP
            final_decision = 'execute'
            reasoning_parts.append(f"📍 移动止损触发: ${current_price:.2f} >= ${trailing_stop:.2f}")
        
        # 4. 如果决定执行但没有reasoning，添加默认说明
        if not reasoning_parts:
            if final_decision == 'execute':
                reasoning_parts.append(f"执行{final_action.value}操作")
            else:
                reasoning_parts.append(f"继续持仓，团队建议继续观察")
        
        # 构建详细的决策报告
        team_votes_summary = ", ".join([
            f"{action.value}({count}票)" 
            for action, count in vote_counts.items() if count > 0
        ])
        
        reasoning = " | ".join(reasoning_parts) + f" | 团队投票: {team_votes_summary}"
        
        logger.info(f"{'✅ 执行' if final_decision == 'execute' else '⏸️  继续持仓'} "
                   f"{position_id}: {final_action.value}")
        logger.info(f"   决策依据: {reasoning}")
        
        return {
            'final_decision': final_decision,
            'action': final_action,
            'confidence': avg_confidence,
            'reasoning': reasoning,
            'suggested_stop_loss': position['stop_loss'],
            'suggested_take_profit': position['take_profit'],
            'trailing_stop': trailing_stop,
            'team_votes': vote_counts,
            'urgency': avg_urgency,
            'position_pnl': position.get('pnl', 0),
            'position_pnl_pct': position.get('pnl_pct', 0)
        }
    
    def remove_position(self, position_id: str):
        """移除持仓"""
        if position_id in self.active_positions:
            logger.info(f"🗑️ 移除持仓监控: {position_id}")
            del self.active_positions[position_id]
    
    def get_position_status(self, position_id: str) -> Optional[Dict]:
        """获取持仓状态"""
        return self.active_positions.get(position_id)


# 全局止盈止损决策系统实例
stop_decision_system = StopLossDecisionSystem()

