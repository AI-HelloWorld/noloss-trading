"""
动态止盈止损监控器
"""
from typing import Dict
from loguru import logger
from backend.agents.intelligent_stop_strategy import intelligent_stop_strategy


class DynamicStopMonitor:
    """动态止盈止损监控器"""
    
    def __init__(self):
        self.active_positions = {}
        self.stop_strategy = intelligent_stop_strategy
    
    def update_position(
        self,
        position_id: str,
        symbol: str,
        action: str,
        entry_price: float,
        current_price: float,
        quantity: float,
        stop_loss: float,
        take_profit: float
    ):
        """更新持仓信息"""
        self.active_positions[position_id] = {
            'symbol': symbol,
            'action': action,
            'entry_price': entry_price,
            'current_price': current_price,
            'quantity': quantity,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'highest_price': max(entry_price, current_price),
            'lowest_price': min(entry_price, current_price),
            'pnl': (current_price - entry_price) * quantity if action == 'buy' else (entry_price - current_price) * quantity
        }
        
        logger.info(f"📝 更新持仓监控: {position_id} - {symbol} {action} @ ${entry_price:.2f}")
        logger.info(f"   止损: ${stop_loss:.2f}, 止盈: ${take_profit:.2f}")
    
    def check_stop_conditions(self, position_id: str, current_price: float) -> Dict:
        """检查止盈止损条件"""
        if position_id not in self.active_positions:
            return {'action': 'hold', 'reason': '仓位不存在'}
        
        position = self.active_positions[position_id]
        position['current_price'] = current_price
        
        # 更新最高价/最低价
        if position['action'] == 'buy':
            position['highest_price'] = max(position['highest_price'], current_price)
        else:  # short
            position['lowest_price'] = min(position['lowest_price'], current_price)
        
        # 检查固定止盈止损
        if position['action'] == 'buy':
            if current_price <= position['stop_loss']:
                logger.warning(f"⚠️ 止损触发: {position_id} - 价格${current_price:.2f} <= 止损${position['stop_loss']:.2f}")
                return {'action': 'sell', 'reason': '止损触发', 'price': current_price}
            elif current_price >= position['take_profit']:
                logger.info(f"✅ 止盈触发: {position_id} - 价格${current_price:.2f} >= 止盈${position['take_profit']:.2f}")
                return {'action': 'sell', 'reason': '止盈触发', 'price': current_price}
        else:  # short
            if current_price >= position['stop_loss']:
                logger.warning(f"⚠️ 止损触发: {position_id} - 价格${current_price:.2f} >= 止损${position['stop_loss']:.2f}")
                return {'action': 'cover', 'reason': '止损触发', 'price': current_price}
            elif current_price <= position['take_profit']:
                logger.info(f"✅ 止盈触发: {position_id} - 价格${current_price:.2f} <= 止盈${position['take_profit']:.2f}")
                return {'action': 'cover', 'reason': '止盈触发', 'price': current_price}
        
        # 检查移动止损
        trailing_stop = self.stop_strategy.calculate_trailing_stop(
            position['action'],
            position['entry_price'],
            current_price,
            position['highest_price'],
            position['lowest_price']
        )
        
        if position['action'] == 'buy' and current_price <= trailing_stop:
            logger.info(f"📍 移动止损触发: {position_id} - 价格${current_price:.2f} <= 移动止损${trailing_stop:.2f}")
            return {'action': 'sell', 'reason': '移动止损触发', 'price': current_price}
        elif position['action'] == 'short' and current_price >= trailing_stop:
            logger.info(f"📍 移动止损触发: {position_id} - 价格${current_price:.2f} >= 移动止损${trailing_stop:.2f}")
            return {'action': 'cover', 'reason': '移动止损触发', 'price': current_price}
        
        return {'action': 'hold', 'reason': '继续持仓'}
    
    def get_position_health(self, position_id: str) -> Dict:
        """获取持仓健康状态"""
        if position_id not in self.active_positions:
            return {'status': 'unknown'}
        
        position = self.active_positions[position_id]
        current_price = position['current_price']
        
        if position['action'] == 'buy':
            stop_distance_pct = (current_price - position['stop_loss']) / current_price * 100
            profit_pct = (current_price - position['entry_price']) / position['entry_price'] * 100
        else:  # short
            stop_distance_pct = (position['stop_loss'] - current_price) / current_price * 100
            profit_pct = (position['entry_price'] - current_price) / position['entry_price'] * 100
        
        # 计算移动止损
        trailing_stop = self.stop_strategy.calculate_trailing_stop(
            position['action'],
            position['entry_price'],
            current_price,
            position['highest_price'],
            position['lowest_price']
        )
        
        # 健康状态判断
        if stop_distance_pct > 2:
            status = 'healthy'
            status_emoji = '🟢'
        elif stop_distance_pct > 1:
            status = 'warning'
            status_emoji = '🟡'
        else:
            status = 'critical'
            status_emoji = '🔴'
        
        return {
            'status': status,
            'status_emoji': status_emoji,
            'stop_distance_pct': round(stop_distance_pct, 2),
            'profit_pct': round(profit_pct, 2),
            'current_stop_loss': position['stop_loss'],
            'suggested_trailing_stop': trailing_stop,
            'pnl': round(position['pnl'], 2),
            'entry_price': position['entry_price'],
            'current_price': current_price
        }
    
    def remove_position(self, position_id: str):
        """移除持仓监控"""
        if position_id in self.active_positions:
            logger.info(f"🗑️ 移除持仓监控: {position_id}")
            del self.active_positions[position_id]
    
    def get_all_positions_health(self) -> Dict:
        """获取所有持仓的健康状态"""
        health_report = {
            'total_positions': len(self.active_positions),
            'healthy': 0,
            'warning': 0,
            'critical': 0,
            'positions': []
        }
        
        for position_id, position in self.active_positions.items():
            health = self.get_position_health(position_id)
            health_report['positions'].append({
                'position_id': position_id,
                'symbol': position['symbol'],
                'action': position['action'],
                **health
            })
            
            if health['status'] == 'healthy':
                health_report['healthy'] += 1
            elif health['status'] == 'warning':
                health_report['warning'] += 1
            elif health['status'] == 'critical':
                health_report['critical'] += 1
        
        return health_report


# 全局动态监控器实例
dynamic_stop_monitor = DynamicStopMonitor()

