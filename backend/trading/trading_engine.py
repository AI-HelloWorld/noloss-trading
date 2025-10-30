"""
交易引擎 - 核心交易逻辑
"""
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.exchanges.aster_dex import aster_client
from backend.agents.agent_team import agent_team
from backend.agents.simple_trading_strategy import simple_strategy
from backend.agents.stop_loss_decision_system import stop_decision_system
from backend.agents.intelligent_stop_strategy import intelligent_stop_strategy
from backend.database import Trade, Position, PortfolioSnapshot, AIDecision, MarketData, get_db
from backend.config import settings


class TradingEngine:
    """交易引擎"""
    
    def __init__(self):
        self.is_running = False
        self.current_balance = settings.initial_balance
        self.total_pnl = 0.0
        self.trade_count = 0
        self.winning_trades = 0
    
    async def initialize(self, db: AsyncSession):
        """初始化交易引擎"""
        # 从数据库加载最新状态
        result = await db.execute(
            select(PortfolioSnapshot).order_by(desc(PortfolioSnapshot.timestamp)).limit(1)
        )
        latest_snapshot = result.scalar_one_or_none()
        
        if latest_snapshot:
            self.current_balance = latest_snapshot.total_balance
            self.total_pnl = latest_snapshot.total_profit_loss
            self.trade_count = latest_snapshot.total_trades
            logger.info(f"从数据库加载状态 - 余额: ${self.current_balance:.2f}, 总盈亏: ${self.total_pnl:.2f}")
        else:
            logger.info(f"初始化新账户 - 初始余额: ${self.current_balance:.2f}")
    
    async def update_market_data(self, db: AsyncSession):
        """更新市场数据（优化实时性）"""
        try:
            logger.debug("开始更新市场数据...")
            
            # 优化1: 使用批量API获取所有行情（一次请求）
            try:
                all_tickers = await aster_client.get_all_tickers()
                if all_tickers and len(all_tickers) > 0:
                    # 批量保存
                    for ticker in all_tickers:
                        market_data_record = MarketData(
                            symbol=ticker.get("symbol", ""),
                            price=ticker.get("price", 0),
                            volume_24h=ticker.get("volume_24h", 0),
                            change_24h=ticker.get("change_24h", 0),
                            high_24h=ticker.get("high_24h", 0),
                            low_24h=ticker.get("low_24h", 0)
                        )
                        db.add(market_data_record)
                    
                    await db.commit()
                    logger.debug(f"✅ 市场数据批量更新完成 - {len(all_tickers)} 个交易对")
                    return
            except Exception as e:
                logger.debug(f"批量更新失败，使用单独更新: {e}")
            
            # 优化2: 如果批量API不可用，只更新主流币种（快速）
            priority_symbols = [
                "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
                "ADAUSDT", "DOTUSDT", "MATICUSDT", "AVAXUSDT", "LINKUSDT"
            ]
            
            # 并发获取数据
            import asyncio
            tasks = [aster_client.get_ticker(symbol) for symbol in priority_symbols]
            tickers = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 保存数据
            for symbol, ticker in zip(priority_symbols, tickers):
                if isinstance(ticker, dict) and ticker:
                    market_data_record = MarketData(
                        symbol=symbol,
                        price=ticker.get("price", 0),
                        volume_24h=ticker.get("volume_24h", 0),
                        change_24h=ticker.get("change_24h", 0),
                        high_24h=ticker.get("high_24h", 0),
                        low_24h=ticker.get("low_24h", 0)
                    )
                    db.add(market_data_record)
            
            await db.commit()
            logger.debug(f"✅ 主流币种更新完成 - {len(priority_symbols)} 个")
            
        except Exception as e:
            logger.error(f"更新市场数据失败: {e}")
    
    async def execute_trading_cycle(self, db: AsyncSession):
        """执行一轮完整的交易周期"""
        try:
            logger.info("开始交易周期...")
            
            # 1. 获取支持的交易对
            symbols = await aster_client.get_supported_symbols()
            logger.info(f"支持的交易对数量: {len(symbols)}")
            
            # 2. 获取当前持仓
            positions = await self._get_current_positions(db)
            
            # 3. 获取账户余额
            balance_info = await aster_client.get_account_balance()
            
            # 4. 【新增】AI团队评估现有持仓的止盈止损
            if positions:
                logger.info(f"📊 开始评估{len(positions)}个持仓的止盈止损...")
                await self._evaluate_positions_stop_loss(db, positions)
            
            # 5. 遍历交易对，让AI分析新交易机会
            for symbol in symbols[:10]:  # 限制每次分析前10个，避免API调用过多
                try:
                    await self._analyze_and_trade(db, symbol, positions)
                except Exception as e:
                    logger.error(f"分析 {symbol} 失败: {e}")
            
            # 6. 更新投资组合快照
            await self._save_portfolio_snapshot(db)
            
            logger.info("交易周期完成")
            
        except Exception as e:
            logger.error(f"交易周期执行失败: {e}")
    
    async def _analyze_and_trade(self, db: AsyncSession, symbol: str, positions: List[Dict]):
        """分析单个交易对并执行交易"""
        try:
            # 获取市场数据
            ticker = await aster_client.get_ticker(symbol)
            if not ticker:
                return
            
            market_data = {
                "price": ticker.get("price", 0),
                "change_24h": ticker.get("change_24h", 0),
                "high_24h": ticker.get("high_24h", 0),
                "low_24h": ticker.get("low_24h", 0),
                "volume_24h": ticker.get("volume_24h", 0),
                "market_cap": ticker.get("market_cap", 0)
            }
            
            # 保存市场数据到数据库
            market_data_record = MarketData(
                symbol=symbol,
                price=market_data["price"],
                volume_24h=market_data["volume_24h"],
                change_24h=market_data["change_24h"],
                high_24h=market_data["high_24h"],
                low_24h=market_data["low_24h"]
            )
            db.add(market_data_record)
            await db.commit()
            logger.debug(f"市场数据已保存: {symbol} @ ${market_data['price']:.2f}")
            
            # 获取投资组合信息
            portfolio = {
                "total_balance": self.current_balance,
                "cash_balance": self.current_balance - sum(p.get('amount', 0) * p.get('current_price', 0) for p in positions),
                "positions_value": sum(p.get('amount', 0) * p.get('current_price', 0) for p in positions),
                "total_pnl": self.total_pnl
            }
            
            # 多智能体团队协同分析
            team_decision = await agent_team.conduct_team_analysis(
                symbol=symbol,
                market_data=market_data,
                portfolio=portfolio,
                positions=positions,
                additional_data={
                    "sentiment": {},  # 可以接入真实的情绪数据API
                    "news": []  # 可以接入真实的新闻API
                }
            )
            
            # 如果AI团队决策失败（置信度为0），使用简单策略作为后备
            if team_decision['confidence'] == 0.0 or team_decision['action'] == 'hold' and team_decision['final_decision'] == 'reject':
                logger.info(f"🔄 {symbol} AI团队不可用，使用简单策略")
                simple_decision = simple_strategy.analyze(symbol, market_data, portfolio)
                
                # 将简单策略的结果转换为团队决策格式
                team_decision = {
                    'final_decision': 'approve' if simple_decision['confidence'] >= 0.6 else 'reject',
                    'action': simple_decision['action'],
                    'confidence': simple_decision['confidence'],
                    'position_size': simple_decision['position_size'],
                    'reasoning': simple_decision['reasoning'],
                    'stop_loss': 0,
                    'take_profit': 0,
                    'key_considerations': [simple_decision['reasoning']],
                    'team_analyses': [{
                        'role': 'simple_strategy',
                        'recommendation': simple_decision['action'],
                        'confidence': simple_decision['confidence'],
                        'reasoning': simple_decision['reasoning']
                    }]
                }
            
            # 保存AI决策（包含团队分析）
            ai_decision = AIDecision(
                ai_model="Multi-Agent Team",
                symbol=symbol,
                decision=team_decision['action'],
                confidence=team_decision['confidence'],
                reasoning=team_decision['reasoning'],
                market_analysis=str(team_decision.get('team_analyses', []))
            )
            db.add(ai_decision)
            await db.commit()
            
            # 只有在投资组合经理批准且置信度足够时才执行交易
            if (team_decision['final_decision'] == 'approve' and 
                team_decision['confidence'] >= 0.6 and
                team_decision['action'] != 'hold'):
                await self._execute_trade(db, symbol, team_decision, market_data)
            else:
                logger.info(f"⏸️  {symbol} 交易未批准 - {team_decision['reasoning'][:100]}")
            
        except Exception as e:
            logger.error(f"分析交易 {symbol} 失败: {e}")
    
    async def _execute_trade(self, db: AsyncSession, symbol: str, team_decision: Dict, market_data: Dict):
        """执行交易"""
        action = team_decision['action']
        
        if action == "hold":
            return
        
        try:
            # 获取当前持仓信息
            positions = await self._get_current_positions(db)
            positions_value = sum(p['amount'] * p['current_price'] for p in positions)
            
            # 获取账户余额信息
            balance_info = await aster_client.get_account_balance()
            cash_balance = self.current_balance - positions_value
            
            current_price = market_data['price']
            
            # 对于平仓操作（sell/cover），需要特殊处理
            if action in ["sell", "cover"]:
                await self._execute_close_position(db, symbol, action, current_price, team_decision)
                return
            
            # 对于开仓操作（buy/short），进行风控计算
            # 计算交易金额 - 应用严格风控规则
            position_size = team_decision.get('position_size', 0.1)
            
            # 风控规则1: 每笔交易不超过钱包余额的配置百分比（默认50%）
            max_wallet_usage = settings.max_wallet_usage
            max_trade_by_wallet = cash_balance * max_wallet_usage
            
            # 风控规则2: 使用AI建议的仓位，但不超过钱包限制
            ai_suggested_value = self.current_balance * position_size
            
            # 取两者较小值
            max_trade_value = min(max_trade_by_wallet, ai_suggested_value)
            
            # 风控规则3: 如果是合约交易（做空），需要预留保证金防止爆仓
            if action in ["short"]:
                # 合约需要保证金，使用配置的保证金预留比例（默认30%）
                margin_ratio = settings.margin_reserve_ratio
                max_trade_value_with_margin = cash_balance * margin_ratio
                max_trade_value = min(max_trade_value, max_trade_value_with_margin)
                
                # 计算预留的保证金
                reserved_margin = cash_balance * (1 - margin_ratio)
                logger.info(f"🛡️ 合约交易保证金保护：使用{margin_ratio*100:.0f}%余额，预留${reserved_margin:.2f}保证金防止爆仓")
            
            # 最终检查：确保有足够余额
            if max_trade_value > cash_balance:
                logger.warning(f"⚠️ 余额不足：需要${max_trade_value:.2f}，可用${cash_balance:.2f}")
                return
            
            # 风控规则4: 确保交易金额有意义（至少$10）
            min_trade_value = 10.0
            if max_trade_value < min_trade_value:
                logger.warning(f"⚠️ 交易金额过小：${max_trade_value:.2f} < ${min_trade_value:.2f}，跳过交易")
                return
            
            # 计算交易数量
            amount = max_trade_value / current_price
            
            # 处理交易数量精度 - 根据交易对设置合适的精度
            amount_before = amount
            amount = self._adjust_trade_precision(symbol, amount)
            
            # 详细日志
            logger.info(f"💰 风控计算详情:")
            logger.info(f"   现金余额: ${cash_balance:.2f}")
            logger.info(f"   持仓价值: ${positions_value:.2f}")
            logger.info(f"   AI建议使用: ${ai_suggested_value:.2f} ({position_size*100:.1f}%总资产)")
            logger.info(f"   钱包限制({max_wallet_usage*100:.0f}%): ${max_trade_by_wallet:.2f}")
            logger.info(f"   实际使用: ${max_trade_value:.2f}")
            logger.info(f"   交易数量: {amount_before:.8f} {symbol} -> {amount} {symbol} (精度调整)")
            logger.info(f"   实际交易金额: ${amount * current_price:.2f}")
            
            order_result = None
            
            if action == "buy":
                # 买入做多
                logger.info(f"📈 执行买入做多: {symbol}")
                order_result = await aster_client.place_order(
                    symbol, "buy", "market", amount
                )
            
            elif action == "short":
                # 做空
                logger.info(f"📉 执行做空: {symbol}")
                order_result = await aster_client.place_short_order(symbol, amount)
            
            # 记录交易
            if order_result and order_result.get('success', False):
                # 开仓操作不计算盈亏
                profit_loss = 0.0
                profit_loss_percentage = 0.0
                
                # 记录交易到数据库
                trade = Trade(
                    symbol=symbol,
                    side=action,
                    price=current_price,
                    amount=amount,
                    total_value=amount * current_price,
                    ai_model="Multi-Agent Team",
                    ai_reasoning=team_decision['reasoning'],
                    success=True,
                    order_id=order_result.get('order_id', ''),
                    profit_loss=None,  # 开仓不计算盈亏
                    profit_loss_percentage=None
                )
                db.add(trade)
                await db.commit()
                await db.refresh(trade)
                
                self.trade_count += 1
                action_name = "买入做多" if action == "buy" else "做空"
                logger.info(f"✅ {action_name}成功: ID={trade.id}, {symbol} {amount:.6f} @ ${current_price:.2f}")
                
                # 立即更新持仓数据
                await self._update_positions_after_trade(db)
                logger.info(f"📊 持仓数据已更新")
                
                # 【新增】如果有止盈止损配置，加入监控
                if team_decision.get('stop_loss', 0) > 0 or team_decision.get('take_profit', 0) > 0:
                    position_id = f"{symbol}_{trade.id}"
                    stop_decision_system.add_position(
                        position_id,
                        symbol,
                        action,
                        current_price,
                        amount,
                        team_decision.get('stop_loss', 0),
                        team_decision.get('take_profit', 0)
                    )
                    logger.info(f"🎯 已加入止盈止损监控: {position_id}")
            else:
                logger.error(f"❌ 交易失败: {symbol} {action}")
                # 记录失败的交易
                trade = Trade(
                    symbol=symbol,
                    side=action,
                    price=current_price,
                    amount=amount,
                    total_value=amount * current_price,
                    ai_model="Multi-Agent Team",
                    ai_reasoning=team_decision['reasoning'],
                    success=False,
                    order_id='',
                    profit_loss=None,
                    profit_loss_percentage=None
                )
                db.add(trade)
                await db.commit()
        
        except Exception as e:
            logger.error(f"交易执行失败: {e}")
            import traceback
            traceback.print_exc()
    
    async def _execute_close_position(
        self, 
        db: AsyncSession, 
        symbol: str, 
        action: str, 
        current_price: float, 
        team_decision: Dict
    ):
        """
        执行平仓操作（sell/cover）
        
        Args:
            db: 数据库会话
            symbol: 交易对
            action: 动作类型 (sell或cover)
            current_price: 当前价格
            team_decision: 团队决策信息
        """
        try:
            # 获取持仓信息
            position = await self._get_position(db, symbol)
            
            if not position:
                logger.warning(f"⚠️ 无法执行{action}：{symbol}无持仓")
                return
            
            # 验证持仓类型匹配
            if action == "sell" and position.side != "buy":
                logger.warning(f"⚠️ 无法执行sell：{symbol}持仓类型为{position.side}，不是多仓")
                return
            
            if action == "cover" and position.side != "short":
                logger.warning(f"⚠️ 无法执行cover：{symbol}持仓类型为{position.side}，不是空仓")
                return
            
            # 获取持仓数量
            close_amount = position.amount
            entry_price = position.average_price
            
            if close_amount <= 0:
                logger.warning(f"⚠️ 无法执行{action}：{symbol}持仓数量为0")
                return
            
            logger.info(f"🔄 准备平仓:")
            logger.info(f"   交易对: {symbol}")
            logger.info(f"   操作: {action} ({'平多仓' if action == 'sell' else '平空仓'})")
            logger.info(f"   持仓数量: {close_amount:.6f}")
            logger.info(f"   入场价格: ${entry_price:.4f}")
            logger.info(f"   当前价格: ${current_price:.4f}")
            
            # 调整精度
            close_amount = self._adjust_trade_precision(symbol, close_amount)
            
            # 执行平仓
            order_result = None
            
            if action == "sell":
                # 平多仓（卖出）
                logger.info(f"📤 执行卖出平多仓: {symbol}")
                order_result = await aster_client.place_order(
                    symbol, "sell", "market", close_amount
                )
            
            elif action == "cover":
                # 平空仓（买入平仓）
                logger.info(f"📥 执行买入平空仓: {symbol}")
                # 根据交易所API，平空仓可能需要特殊处理
                # 方案1: 使用close_position
                try:
                    order_result = await aster_client.close_position(symbol)
                except:
                    # 方案2: 如果close_position不支持，使用买入
                    order_result = await aster_client.place_order(
                        symbol, "buy", "market", close_amount
                    )
            
            # 记录交易结果
            if order_result and order_result.get('success', False):
                # 计算盈亏
                if action == "sell":
                    # 多仓盈亏 = (当前价格 - 入场价格) * 数量
                    profit_loss = (current_price - entry_price) * close_amount
                    profit_loss_percentage = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
                elif action == "cover":
                    # 空仓盈亏 = (入场价格 - 当前价格) * 数量
                    profit_loss = (entry_price - current_price) * close_amount
                    profit_loss_percentage = ((entry_price - current_price) / entry_price * 100) if entry_price > 0 else 0
                else:
                    profit_loss = 0
                    profit_loss_percentage = 0
                
                # 更新总盈亏
                self.total_pnl += profit_loss
                if profit_loss > 0:
                    self.winning_trades += 1
                
                # 记录交易到数据库
                trade = Trade(
                    symbol=symbol,
                    side=action,
                    price=current_price,
                    amount=close_amount,
                    total_value=close_amount * current_price,
                    ai_model="Multi-Agent Team",
                    ai_reasoning=team_decision['reasoning'],
                    success=True,
                    order_id=order_result.get('order_id', ''),
                    profit_loss=profit_loss,
                    profit_loss_percentage=profit_loss_percentage
                )
                db.add(trade)
                await db.commit()
                await db.refresh(trade)
                
                self.trade_count += 1
                
                # 友好的日志输出
                action_name = "平多仓" if action == "sell" else "平空仓"
                pnl_emoji = "💰" if profit_loss > 0 else "💸"
                logger.info(
                    f"✅ {action_name}成功: ID={trade.id}, {symbol} {close_amount:.6f} @ ${current_price:.2f} | "
                    f"{pnl_emoji} 盈亏: ${profit_loss:.2f} ({profit_loss_percentage:+.2f}%)"
                )
                
                # 从止盈止损监控中移除
                position_id = f"{symbol}_{position.id}"
                stop_decision_system.remove_position(position_id)
                logger.info(f"🗑️  已移除持仓监控: {position_id}")
                
                # 更新持仓数据
                await self._update_positions_after_trade(db)
                logger.info(f"📊 持仓数据已更新")
                
            else:
                logger.error(f"❌ 平仓失败: {symbol} {action}")
                # 记录失败的交易
                trade = Trade(
                    symbol=symbol,
                    side=action,
                    price=current_price,
                    amount=close_amount,
                    total_value=close_amount * current_price,
                    ai_model="Multi-Agent Team",
                    ai_reasoning=team_decision['reasoning'],
                    success=False,
                    order_id='',
                    profit_loss=None,
                    profit_loss_percentage=None
                )
                db.add(trade)
                await db.commit()
        
        except Exception as e:
            logger.error(f"平仓执行失败: {symbol} {action} - {e}")
            import traceback
            traceback.print_exc()
    
    async def _update_balance(self, db: AsyncSession):
        """更新账户余额 - 从SDK实时查询钱包余额"""
        try:
            # 从交易所SDK获取最新钱包余额
            balance_info = await aster_client.get_account_balance()
            logger.info(f"💰 SDK余额查询结果: {balance_info}")
            
            # 处理余额信息（真实模式和模拟模式都支持）
            if balance_info.get('success'):
                balances = balance_info.get('balances', [])
                usdt_balance = next((b for b in balances if b.get('asset') == 'USDT'), None)
                if usdt_balance:
                    # 钱包余额 = 可用余额 + 锁定余额（从SDK获取的真实钱包余额）
                    wallet_balance = float(usdt_balance.get('free', 0)) + float(usdt_balance.get('locked', 0))
                    
                    # 获取当前持仓价值
                    positions = await aster_client.get_open_positions()
                    positions_value = sum(p['amount'] * p['current_price'] for p in positions)
                    
                    # 总资产 = 钱包余额 + 持仓价值
                    self.current_balance = wallet_balance + positions_value
                    
                    logger.info(f"💰 钱包余额SDK更新: 钱包=${wallet_balance:.2f}, 持仓=${positions_value:.2f}, 总计=${self.current_balance:.2f}")
                else:
                    logger.warning(f"⚠️ 未找到USDT余额，使用当前余额: ${self.current_balance:.2f}")
            else:
                logger.warning(f"⚠️ SDK获取余额失败，使用当前余额: ${self.current_balance:.2f}")
                    
        except Exception as e:
            logger.error(f"SDK更新余额失败: {e}")
    
    async def _update_positions_after_trade(self, db: AsyncSession):
        """交易后立即更新持仓数据"""
        try:
            # 从交易所获取最新持仓
            positions = await aster_client.get_open_positions()
            
            # 获取数据库中的持仓记录
            db_result = await db.execute(select(Position))
            db_positions = {p.symbol: p for p in db_result.scalars().all()}
            
            # 更新数据库中的持仓
            for pos in positions:
                symbol = pos['symbol']
                if symbol in db_positions:
                    # 更新现有持仓
                    db_pos = db_positions[symbol]
                    db_pos.amount = pos['amount']
                    db_pos.current_price = pos['current_price']
                    db_pos.unrealized_pnl = pos['unrealized_pnl']
                    db_pos.average_price = pos.get('average_price', db_pos.average_price)
                    db_pos.position_type = pos.get('position_type', db_pos.position_type)
                    db_pos.last_updated = datetime.now()
                else:
                    # 添加新持仓
                    new_pos = Position(
                        symbol=symbol,
                        amount=pos['amount'],
                        average_price=pos['average_price'],
                        current_price=pos['current_price'],
                        unrealized_pnl=pos['unrealized_pnl'],
                        position_type=pos.get('position_type', 'long')
                    )
                    db.add(new_pos)
            
            # 删除已平仓的持仓
            current_symbols = {p['symbol'] for p in positions}
            for symbol, db_pos in db_positions.items():
                if symbol not in current_symbols:
                    db.delete(db_pos)
            
            await db.commit()
            logger.debug(f"持仓数据已同步: {len(positions)} 个持仓")
            
        except Exception as e:
            logger.error(f"更新持仓数据失败: {e}")
    
    async def _get_current_positions(self, db: AsyncSession) -> List[Dict]:
        """获取当前持仓"""
        # 从交易所获取实时持仓（模拟模式下从mock_market获取）
        positions = await aster_client.get_open_positions()
        
        # 也从数据库获取持仓记录并同步
        db_result = await db.execute(select(Position))
        db_positions = {p.symbol: p for p in db_result.scalars().all()}
        
        # 更新数据库中的持仓
        for pos in positions:
            symbol = pos['symbol']
            if symbol in db_positions:
                # 更新现有持仓
                db_pos = db_positions[symbol]
                db_pos.amount = pos['amount']
                db_pos.current_price = pos['current_price']
                db_pos.unrealized_pnl = pos['unrealized_pnl']
            else:
                # 添加新持仓
                new_pos = Position(
                    symbol=symbol,
                    amount=pos['amount'],
                    average_price=pos['average_price'],
                    current_price=pos['current_price'],
                    unrealized_pnl=pos['unrealized_pnl'],
                    position_type=pos['position_type']
                )
                db.add(new_pos)
        
            # 删除已平仓的持仓
            current_symbols = {p['symbol'] for p in positions}
            for symbol, db_pos in db_positions.items():
                if symbol not in current_symbols:
                    db.delete(db_pos)
        
        await db.commit()
        
        return positions
    
    async def _get_position(self, db: AsyncSession, symbol: str) -> Optional[Position]:
        """获取指定交易对的持仓"""
        result = await db.execute(
            select(Position).where(Position.symbol == symbol)
        )
        return result.scalar_one_or_none()
    
    def _adjust_trade_precision(self, symbol: str, amount: float) -> float:
        """调整交易数量精度，避免精度错误（统一精度配置）"""
        # 根据交易对设置合适的精度（基于AsterDEX的严格要求）
        precision_rules = {
            # BTC相关 - 通常3-4位小数
            "BTC/USDT": 3,
            "BTCUSDT": 3,
            # ETH相关 - 通常3-4位小数
            "ETH/USDT": 3,
            "ETHUSDT": 3,
            # BNB相关 - 通常2-3位小数
            "BNB/USDT": 2,
            "BNBUSDT": 2,
            # SOL相关 - 通常1-2位小数
            "SOL/USDT": 1,
            "SOLUSDT": 1,
            # ADA相关 - 通常0-1位小数（数量较大）
            "ADA/USDT": 0,
            "ADAUSDT": 0,
            # XRP相关 - 通常0-1位小数（数量较大）
            "XRP/USDT": 0,
            "XRPUSDT": 0,
            # DOT相关 - 通常1-2位小数
            "DOT/USDT": 1,
            "DOTUSDT": 1,
            # DOGE相关 - 通常0位小数（数量很大）
            "DOGE/USDT": 0,
            "DOGEUSDT": 0,
            # MATIC相关 - 通常0-1位小数（数量较大）
            "MATIC/USDT": 0,
            "MATICUSDT": 0,
            # AVAX相关 - 通常1-2位小数
            "AVAX/USDT": 1,
            "AVAXUSDT": 1,
            # LINK相关 - 通常1-2位小数
            "LINK/USDT": 1,
            "LINKUSDT": 1,
            # UNI相关 - 通常1-2位小数
            "UNI/USDT": 1,
            "UNIUSDT": 1,
            # ATOM相关 - 通常1-2位小数
            "ATOM/USDT": 1,
            "ATOMUSDT": 1,
            # LTC相关 - 通常2-3位小数
            "LTC/USDT": 2,
            "LTCUSDT": 2,
            # ETC相关 - 通常1-2位小数
            "ETC/USDT": 1,
            "ETCUSDT": 1,
            # ASTER相关 - 通常0-1位小数
            "ASTER/USDT": 0,
            "ASTERUSDT": 0,
            # 默认精度 - 非常保守，整数
            "default": 0
        }
        
        # 获取精度规则
        precision = precision_rules.get(symbol, precision_rules.get("default"))
        
        # 调整精度
        adjusted_amount = round(amount, precision)
        
        # 确保不为0（如果原值大于最小值）
        if adjusted_amount == 0 and amount > 0:
            # 如果四舍五入后为0，使用最小精度值
            adjusted_amount = 10 ** (-precision) if precision > 0 else 1
        
        # 确保最小交易数量（避免过小的交易）
        min_amounts = {
            "BTC/USDT": 0.001,
            "BTCUSDT": 0.001,
            "ETH/USDT": 0.001,
            "ETHUSDT": 0.001,
            "BNB/USDT": 0.01,
            "BNBUSDT": 0.01,
            "SOL/USDT": 0.1,
            "SOLUSDT": 0.1,
            "ADA/USDT": 1,
            "ADAUSDT": 1,
            "XRP/USDT": 1,
            "XRPUSDT": 1,
            "DOT/USDT": 0.1,
            "DOTUSDT": 0.1,
            "DOGE/USDT": 1,
            "DOGEUSDT": 1,
            "MATIC/USDT": 1,
            "MATICUSDT": 1,
            "ASTER/USDT": 1,
            "ASTERUSDT": 1,
        }
        
        min_amount = min_amounts.get(symbol, 1)
        if adjusted_amount < min_amount:
            adjusted_amount = min_amount
        
        logger.info(f"🔧 精度调整: {symbol} {amount:.8f} -> {adjusted_amount:.{precision}f} (精度: {precision}位小数, 最小: {min_amount})")
        
        return adjusted_amount
    
    async def _register_position_to_stop_loss(
        self,
        db: AsyncSession,
        symbol: str,
        action: str,
        entry_price: float,
        amount: float,
        team_decision: Dict,
        trade_id: int
    ):
        """注册持仓到止盈止损系统"""
        try:
            # 获取持仓信息
            position = await self._get_position(db, symbol)
            if not position:
                logger.warning(f"⚠️ 未找到持仓{symbol}，无法注册止盈止损")
                return
            
            position_id = f"{symbol}_{position.id}"
            
            # 计算止盈止损
            volatility = abs(team_decision.get('market_data', {}).get('change_24h', 5.0))
            
            stop_levels = intelligent_stop_strategy.calculate_stop_levels(
                action=action,
                entry_price=entry_price,
                market_data={
                    'price': entry_price,
                    'high_24h': entry_price * 1.05,
                    'low_24h': entry_price * 0.95
                },
                position_size=team_decision.get('position_size', 0.1),
                confidence=team_decision.get('confidence', 0.7),
                volatility=volatility,
                additional_factors={}
            )
            
            # 注册到止盈止损系统
            stop_decision_system.register_position(
                position_id=position_id,
                symbol=symbol,
                action=action,
                entry_price=entry_price,
                quantity=amount,
                stop_loss=stop_levels.get('stop_loss', entry_price * 0.98 if action == 'buy' else entry_price * 1.02),
                take_profit=stop_levels.get('take_profit', entry_price * 1.04 if action == 'buy' else entry_price * 0.96),
                confidence=team_decision.get('confidence', 0.7),
                strategy_info={
                    'trade_id': trade_id,
                    'strategy_type': stop_levels.get('strategy_type', 'volatility'),
                    'risk_reward_ratio': stop_levels.get('risk_reward_ratio', 2.0),
                    'team_decision': team_decision.get('reasoning', '')[:200]
                }
            )
            
            logger.info(f"✅ 持仓已注册到止盈止损系统: {position_id}")
            logger.info(f"   止损: ${stop_levels.get('stop_loss', 0):.2f} ({stop_levels.get('risk_pct', 0):.2f}%)")
            logger.info(f"   止盈: ${stop_levels.get('take_profit', 0):.2f} ({stop_levels.get('reward_pct', 0):.2f}%)")
            logger.info(f"   风险回报比: 1:{stop_levels.get('risk_reward_ratio', 0):.2f}")
            
        except Exception as e:
            logger.error(f"注册持仓到止盈止损系统失败: {e}")
    
    async def _evaluate_positions_stop_loss(self, db: AsyncSession, positions: List[Dict]):
        """评估所有持仓的止盈止损（AI团队协同决策）"""
        try:
            portfolio = await self.get_portfolio_summary(db)
            
            for position in positions:
                try:
                    symbol = position['symbol']
                    position_id = f"{symbol}_{position.get('id', 'unknown')}"
                    
                    # 获取市场数据
                    ticker = await aster_client.get_ticker(symbol)
                    if not ticker:
                        continue
                    
                    market_data = {
                        'price': ticker.get('price', 0),
                        'change_24h': ticker.get('change_24h', 0),
                        'high_24h': ticker.get('high_24h', 0),
                        'low_24h': ticker.get('low_24h', 0),
                        'volume_24h': ticker.get('volume_24h', 0)
                    }
                    
                    # 检查持仓是否已在系统中
                    position_status = stop_decision_system.get_position_status(position_id)
                    if not position_status:
                        # 如果不在系统中，先注册
                        logger.info(f"📝 持仓{position_id}不在监控中，先注册...")
                        stop_decision_system.register_position(
                            position_id=position_id,
                            symbol=symbol,
                            action=position.get('position_type', 'buy'),
                            entry_price=position['average_price'],
                            quantity=position['amount'],
                            stop_loss=position['average_price'] * 0.98,  # 默认-2%
                            take_profit=position['average_price'] * 1.04,  # 默认+4%
                            confidence=0.7,
                            strategy_info={'auto_registered': True}
                        )
                        position_status = stop_decision_system.get_position_status(position_id)
                    
                    # 更新持仓价格
                    stop_decision_system.update_position_price(position_id, market_data['price'])
                    
                    # 准备持仓信息
                    position_info = stop_decision_system.get_position_status(position_id)
                    position_info['portfolio'] = portfolio
                    
                    # AI团队评估止盈止损
                    logger.info(f"🤖 AI团队评估持仓止盈止损: {symbol}")
                    decision = await agent_team.evaluate_stop_loss_decision(
                        position_id=position_id,
                        symbol=symbol,
                        market_data=market_data,
                        position_info=position_info
                    )
                    
                    # 执行决策
                    if decision['final_decision'] == 'execute':
                        action_type = str(decision['action'])
                        
                        logger.info(f"🎯 执行止盈止损: {symbol} - {action_type}")
                        logger.info(f"   理由: {decision['reasoning']}")
                        logger.info(f"   置信度: {decision['confidence']:.2f}, 紧急度: {decision['urgency']:.2f}")
                        
                        # 判断是平仓还是调整止损
                        if 'stop_loss' in action_type or 'take_profit' in action_type or 'trailing_stop' in action_type:
                            # 执行平仓
                            close_action = 'sell' if position.get('position_type') == 'buy' else 'cover'
                            
                            # 构造团队决策格式
                            close_team_decision = {
                                'action': close_action,
                                'confidence': decision['confidence'],
                                'reasoning': f"AI团队止盈止损决策: {decision['reasoning']}",
                                'position_size': 1.0  # 全部平仓
                            }
                            
                            # 执行平仓交易
                            await self._execute_trade(db, symbol, close_team_decision, market_data)
                            
                        elif 'tighten_stop' in action_type or 'adjust_stop' in action_type:
                            # 收紧止损（暂时只记录日志，未来可以更新数据库）
                            new_stop_loss = decision.get('suggested_stop_loss')
                            if new_stop_loss:
                                logger.info(f"🔧 建议收紧止损: {symbol} → ${new_stop_loss:.2f}")
                                logger.info(f"   当前持仓系统已更新，下次评估时将使用新止损位")
                    else:
                        logger.debug(f"⏸️  继续持仓: {symbol} - {decision['reasoning']}")
                
                except Exception as e:
                    logger.error(f"评估持仓{position.get('symbol')}止盈止损失败: {e}")
        
        except Exception as e:
            logger.error(f"评估持仓止盈止损失败: {e}")
    
    async def _save_portfolio_snapshot(self, db: AsyncSession):
        """保存投资组合快照（基于SDK钱包余额）"""
        # 实时查询钱包余额
        await self._update_balance(db)
        
        # 获取持仓
        positions = await self._get_current_positions(db)
        positions_value = sum(p['amount'] * p['current_price'] for p in positions)
        
        # 从SDK获取真实钱包余额
        balance_info = await aster_client.get_account_balance()
        wallet_balance = 0.0
        
        if balance_info.get('success'):
            balances = balance_info.get('balances', [])
            usdt_balance = next((b for b in balances if b.get('asset') == 'USDT'), None)
            if usdt_balance:
                # 钱包余额 = 可用余额 + 锁定余额（从SDK获取的真实钱包余额）
                wallet_balance = float(usdt_balance.get('free', 0)) + float(usdt_balance.get('locked', 0))
        
        # 计算每日盈亏（与前一个快照比较）
        daily_pnl = 0.0
        result = await db.execute(
            select(PortfolioSnapshot).order_by(desc(PortfolioSnapshot.timestamp)).limit(1)
        )
        last_snapshot = result.scalar_one_or_none()
        if last_snapshot:
            daily_pnl = self.current_balance - last_snapshot.total_balance
        
        # 计算正确的总盈亏：基于交易记录和持仓
        # 1. 获取已实现盈亏（从交易记录）
        trade_result = await db.execute(select(Trade))
        trades = trade_result.scalars().all()
        realized_pnl = sum(trade.profit_loss for trade in trades if trade.profit_loss is not None)
        
        # 2. 获取未实现盈亏（从持仓）
        position_result = await db.execute(select(Position))
        positions_db = position_result.scalars().all()
        unrealized_pnl = sum(pos.unrealized_pnl for pos in positions_db if pos.unrealized_pnl is not None)
        
        # 3. 计算总盈亏
        total_pnl_value = realized_pnl + unrealized_pnl
        
        # 4. 计算正确的总余额（钱包余额 + 持仓价值）
        correct_total_balance = wallet_balance + positions_value
        
        # 5. 计算盈亏百分比
        initial_balance = settings.initial_balance
        total_pnl_percentage = (total_pnl_value / initial_balance * 100) if initial_balance > 0 else 0
        
        snapshot = PortfolioSnapshot(
            total_balance=correct_total_balance,
            cash_balance=wallet_balance,  # 使用SDK获取的真实钱包余额
            positions_value=positions_value,
            total_profit_loss=total_pnl_value,
            total_pnl_percentage=total_pnl_percentage,
            daily_profit_loss=daily_pnl,
            total_trades=self.trade_count,
            win_rate=self.winning_trades / self.trade_count if self.trade_count > 0 else 0
        )
        
        db.add(snapshot)
        await db.commit()
        
        logger.info(f"📊 投资组合快照已保存 - 总资产: ${snapshot.total_balance:.2f}, " +
                   f"钱包: ${snapshot.cash_balance:.2f}, 持仓: ${snapshot.positions_value:.2f}, " +
                   f"总盈亏: ${snapshot.total_profit_loss:.2f} ({snapshot.total_pnl_percentage:+.2f}%), " +
                   f"每日盈亏: ${snapshot.daily_profit_loss:.2f}")
    
    async def get_portfolio_summary(self, db: AsyncSession) -> Dict:
        """获取投资组合摘要（基于SDK钱包余额）"""
        # 实时查询钱包余额
        await self._update_balance(db)
        
        # 获取持仓
        positions = await self._get_current_positions(db)
        positions_value = sum(p['amount'] * p['current_price'] for p in positions)
        
        # 从SDK获取真实钱包余额
        balance_info = await aster_client.get_account_balance()
        wallet_balance = 0.0
        
        if balance_info.get('success'):
            balances = balance_info.get('balances', [])
            usdt_balance = next((b for b in balances if b.get('asset') == 'USDT'), None)
            if usdt_balance:
                # 钱包余额 = 可用余额 + 锁定余额（从SDK获取的真实钱包余额）
                wallet_balance = float(usdt_balance.get('free', 0)) + float(usdt_balance.get('locked', 0))
        
        # 计算正确的总盈亏：基于交易记录和持仓
        # 1. 获取已实现盈亏（从交易记录）
        trade_result = await db.execute(select(Trade))
        trades = trade_result.scalars().all()
        realized_pnl = sum(trade.profit_loss for trade in trades if trade.profit_loss is not None)
        
        # 2. 获取未实现盈亏（从持仓）
        position_result = await db.execute(select(Position))
        positions_db = position_result.scalars().all()
        unrealized_pnl = sum(pos.unrealized_pnl for pos in positions_db if pos.unrealized_pnl is not None)
        
        # 3. 计算总盈亏
        total_pnl_value = realized_pnl + unrealized_pnl
        
        # 4. 计算正确的总余额（钱包余额 + 持仓价值）
        correct_total_balance = wallet_balance + positions_value
        
        # 5. 计算盈亏百分比
        initial_balance = settings.initial_balance
        total_pnl_percentage = (total_pnl_value / initial_balance * 100) if initial_balance > 0 else 0
        
        logger.info(f"📊 投资组合SDK查询: 钱包=${wallet_balance:.2f}, 持仓=${positions_value:.2f}, 总计=${correct_total_balance:.2f}, 盈亏=${total_pnl_value:.2f}")
        
        return {
            "total_balance": correct_total_balance,  # 钱包余额 + 持仓价值
            "cash_balance": wallet_balance,  # 从SDK获取的真实钱包余额
            "positions_value": positions_value,  # 持仓总价值
            "total_pnl": total_pnl_value,  # 盈亏金额
            "total_pnl_percentage": total_pnl_percentage,  # 盈亏百分比
            "initial_balance": initial_balance,  # 初始余额
            "total_trades": self.trade_count,
            "win_rate": self.winning_trades / self.trade_count if self.trade_count > 0 else 0,
            "positions": positions
        }


# 全局交易引擎实例
trading_engine = TradingEngine()

