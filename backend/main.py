"""
FastAPI主应用
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from typing import List, Optional
import asyncio
import json
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import init_db, get_db, Trade, PortfolioSnapshot, AIDecision, MarketData
from backend.trading.trading_engine import trading_engine
from backend.agents.agent_team import agent_team
from backend.exchanges.aster_dex import aster_client
from backend.locales.manager import get_message, get_supported_languages
from backend.migrations import run_all_migrations

# ==================== 🚨 重构模式：停止所有交易逻辑 ====================
REFACTORING_MODE = False  # 设置为True时，停止所有交易和后台任务
# ========================================================================

# 配置日志
logger.add("logs/trading_{time}.log", rotation="1 day", retention="30 days")


# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


manager = ConnectionManager()


# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    if REFACTORING_MODE:
        logger.warning("⚠️  重构模式已启用 - 所有交易逻辑已停止")
        logger.info("📊 启动静态展示模式 - 仅提供数据查询功能")
    else:
        logger.info("🚀 启动AI交易平台...")
    
    # 初始化数据库
    await init_db()
    
    # 执行数据库迁移
    await run_all_migrations()
    
    async for db in get_db():
        await trading_engine.initialize(db)
        break
    
    # 启动后台任务（重构模式下跳过）
    if not REFACTORING_MODE:
        asyncio.create_task(update_market_data_task())  # 市场数据更新任务
        asyncio.create_task(background_trading_task_only_buy())  # 交易任务
        asyncio.create_task(background_trading_task())  # 交易任务
        asyncio.create_task(broadcast_updates_task())   # 广播任务
        logger.info("✅ 所有后台任务已启动")
    else:
        logger.warning("⚠️  后台任务已禁用（重构模式）")
    
    yield
    
    # 关闭时执行
    if REFACTORING_MODE:
        logger.info("🛑 关闭静态展示模式...")
    else:
        logger.info("🛑 关闭AI交易平台...")
    await aster_client.close()


app = FastAPI(title="AI加密货币交易平台", version="1.0.0", lifespan=lifespan)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== API路由 ====================

@app.get("/")
async def root():
    """根路由"""
    return {
        "message": "AI加密货币交易平台API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/api/status")
async def get_status(language: str = Query("zh", description="Language code (zh/en)")):
    """获取系统状态"""
    team_status = agent_team.get_team_status()
    
    # 重构模式下显示特殊状态
    if REFACTORING_MODE:
        trading_status = False
        system_status = "refactoring"
    else:
        trading_status = settings.enable_auto_trading
        system_status = "online"
    
    return {
        "system": system_status,
        "trading_enabled": trading_status,
        "refactoring_mode": REFACTORING_MODE,
        "agent_team": team_status,
        "timestamp": datetime.now().isoformat(),
        "messages": {
            "system_online": get_message("system.online", language),
            "system_offline": get_message("system.offline", language),
            "trading_enabled": get_message("system.trading_enabled", language),
            "trading_disabled": get_message("system.trading_disabled", language)
        }
    }


@app.get("/api/team")
async def get_team_status():
    """获取AI分析师团队状态"""
    return agent_team.get_team_status()


@app.get("/api/languages")
async def get_languages():
    """获取支持的语言列表"""
    return {
        "supported_languages": get_supported_languages(),
        "default_language": "zh"
    }


@app.get("/api/portfolio")
async def get_portfolio(db: AsyncSession = Depends(get_db)):
    """获取投资组合信息 - 实时钱包余额"""
    # 确保获取最新钱包余额
    summary = await trading_engine.get_portfolio_summary(db)
    logger.debug(f"📊 API返回投资组合: 总资产=${summary.get('total_balance', 0):.2f}")
    return summary


@app.get("/api/trades")
async def get_trades(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """获取交易历史"""
    try:
        # 刷新数据库会话，确保获取最新数据
        await db.commit()
        
        # 查询交易记录
        result = await db.execute(
            select(Trade).order_by(desc(Trade.timestamp)).limit(limit)
        )
        trades = result.scalars().all()
        
        logger.debug(f"📊 查询到 {len(trades)} 条交易记录")
        
        # 构建返回数据
        trade_list = []
        for t in trades:
            try:
                trade_data = {
                    "id": t.id,
                    "timestamp": t.timestamp.isoformat() if t.timestamp else datetime.now().isoformat(),
                    "symbol": t.symbol or "",
                    "side": t.side or "",
                    "price": float(t.price) if t.price else 0.0,
                    "amount": float(t.amount) if t.amount else 0.0,
                    "total_value": float(t.total_value) if t.total_value else 0.0,
                    "ai_model": t.ai_model or "",
                    "ai_reasoning": t.ai_reasoning or "",
                    "success": bool(t.success) if hasattr(t, 'success') else True,
                    "profit_loss": float(t.profit_loss) if t.profit_loss is not None else None,
                    "profit_loss_percentage": float(t.profit_loss_percentage) if hasattr(t, 'profit_loss_percentage') and t.profit_loss_percentage is not None else None,
                    "order_id": t.order_id if hasattr(t, 'order_id') else ""
                }
                trade_list.append(trade_data)
            except Exception as e:
                logger.error(f"处理交易记录 {t.id} 时出错: {e}")
                continue
        
        return trade_list
        
    except Exception as e:
        logger.error(f"❌ 获取交易历史失败: {e}")
        return []


@app.get("/api/portfolio-history")
async def get_portfolio_history(days: int = 30, db: AsyncSession = Depends(get_db)):
    """获取投资组合历史"""
    cutoff_date = datetime.now() - timedelta(days=days)
    result = await db.execute(
        select(PortfolioSnapshot)
        .where(PortfolioSnapshot.timestamp >= cutoff_date)
        .order_by(PortfolioSnapshot.timestamp)
    )
    snapshots = result.scalars().all()
    
    return [
        {
            "timestamp": s.timestamp.isoformat(),
            "total_balance": s.total_balance,
            "cash_balance": s.cash_balance,
            "positions_value": s.positions_value,
            "total_profit_loss": s.total_profit_loss,
            "total_pnl_percentage": s.total_pnl_percentage if hasattr(s, 'total_pnl_percentage') else None,
            "daily_profit_loss": s.daily_profit_loss,
            "win_rate": s.win_rate,
            "total_trades": s.total_trades
        }
        for s in snapshots
    ]


@app.get("/api/ai-decisions")
async def get_ai_decisions(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """获取AI决策历史"""
    result = await db.execute(
        select(AIDecision).order_by(desc(AIDecision.timestamp)).limit(limit)
    )
    decisions = result.scalars().all()
    
    return [
        {
            "id": d.id,
            "timestamp": d.timestamp.isoformat(),
            "ai_model": d.ai_model,
            "symbol": d.symbol,
            "decision": d.decision,
            "confidence": d.confidence,
            "reasoning": d.reasoning,
            "executed": d.executed
        }
        for d in decisions
    ]


@app.get("/api/market-data")
async def get_market_data(db: AsyncSession = Depends(get_db)):
    """获取最新市场数据"""
    # 获取每个交易对的最新数据
    result = await db.execute(
        select(MarketData).order_by(desc(MarketData.timestamp)).limit(100)
    )
    market_data = result.scalars().all()
    
    return [
        {
            "symbol": m.symbol,
            "price": m.price,
            "volume_24h": m.volume_24h,
            "change_24h": m.change_24h,
            "high_24h": m.high_24h,
            "low_24h": m.low_24h,
            "timestamp": m.timestamp.isoformat()
        }
        for m in market_data
    ]


@app.post("/api/market-data/refresh")
async def refresh_market_data(
    db: AsyncSession = Depends(get_db),
    language: str = Query("zh", description="Language code (zh/en)")
):
    """手动刷新市场数据"""
    try:
        await trading_engine.update_market_data(db)
        return {
            "success": True, 
            "message": get_message("market.data_refreshed", language)
        }
    except Exception as e:
        logger.error(f"刷新市场数据失败: {e}")
        return {
            "success": False, 
            "message": get_message("market.error", language)
        }


# ==================== 新增的仪表盘数据接口 ====================

@app.get("/api/account_value")
async def get_account_value(days: int = 30, db: AsyncSession = Depends(get_db)):
    """获取账户净值趋势数据 - 包含实时钱包余额"""
    cutoff_date = datetime.now() - timedelta(days=days)
    result = await db.execute(
        select(PortfolioSnapshot)
        .where(PortfolioSnapshot.timestamp >= cutoff_date)
        .order_by(PortfolioSnapshot.timestamp)
    )
    snapshots = result.scalars().all()
    
    # 获取当前实时钱包余额作为最新数据点
    current_portfolio = await trading_engine.get_portfolio_summary(db)
    
    history = [
        {
            "timestamp": s.timestamp.isoformat(),
            "equity_usd": s.total_balance,
            "cash_balance": s.cash_balance,
            "positions_value": s.positions_value,
            "total_pnl": s.total_profit_loss,
            "total_pnl_percentage": s.total_pnl_percentage if hasattr(s, 'total_pnl_percentage') else None,
            "daily_pnl": s.daily_profit_loss
        }
        for s in snapshots
    ]
    
    # 添加当前实时余额作为最新数据点
    history.append({
        "timestamp": datetime.now().isoformat(),
        "equity_usd": current_portfolio['total_balance'],
        "cash_balance": current_portfolio['cash_balance'],
        "positions_value": current_portfolio['positions_value'],
        "total_pnl": current_portfolio['total_pnl'],
        "total_pnl_percentage": current_portfolio['total_pnl_percentage'],
        "daily_pnl": 0.0,
        "real_time": True  # 标记为实时数据
    })
    
    return history


@app.get("/api/positions")
async def get_positions(db: AsyncSession = Depends(get_db)):
    """获取当前持仓分布数据 - 基于实时钱包余额"""
    # 直接调用get_portfolio获取实际持仓数据（内部会查询钱包）
    portfolio = await get_portfolio(db)
    
    # 检查positions字段
    positions_data = portfolio.get('positions', [])
    
    # 如果positions是空列表或None，返回空数组
    if not positions_data:
        logger.debug("📊 当前无持仓")
        return []
    
    total_value = portfolio['total_balance']  # 来自实时钱包余额
    positions = []
    
    # 处理positions可能是列表或字典的情况
    if isinstance(positions_data, list):
        for pos in positions_data:
            position_value = pos['amount'] * pos['current_price']
            size_pct = (position_value / total_value) * 100 if total_value > 0 else 0
            
            positions.append({
                "symbol": pos['symbol'],
                "size_pct": round(size_pct, 2),
                "amount": pos['amount'],
                "current_price": pos['current_price'],
                "average_price": pos['average_price'],
                "entry_price": pos.get('entry_price', pos['average_price']),  # 添加入场价格
                "unrealized_pnl": pos['unrealized_pnl'],
                "value_usd": position_value,
                "stop_loss": pos.get('stop_loss', 0),
                "take_profit": pos.get('take_profit', 0),
                "executed_at": pos.get('executed_at', datetime.now()),
                "position_type": pos.get('position_type', 'long'),
                "stop_loss_strategy": pos.get('stop_loss_strategy', 'default'),
                "take_profit_strategy": pos.get('take_profit_strategy', 'default'),
                "stop_loss_strategy": pos.get('stop_loss_strategy', 'default'),
            })
    
    logger.debug(f"📊 返回{len(positions)}个持仓，总价值=${sum(p['value_usd'] for p in positions):.2f}")
    return positions


@app.get("/api/strategies")
async def get_strategies(limit: int = 10, db: AsyncSession = Depends(get_db)):
    """获取策略解释数据"""
    result = await db.execute(
        select(AIDecision)
        .where(AIDecision.reasoning.isnot(None))
        .order_by(desc(AIDecision.timestamp))
        .limit(limit)
    )
    decisions = result.scalars().all()
    
    strategies = []
    for decision in decisions:
        strategies.append({
            "model_name": decision.ai_model,
            "symbol": decision.symbol,
            "strategy_text": decision.reasoning,
            "decision": decision.decision,
            "confidence": decision.confidence,
            "timestamp": decision.timestamp.isoformat()
        })
    
    return strategies


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket连接 - 实时数据推送"""
    await manager.connect(websocket)
    try:
        while True:
            # 保持连接
            data = await websocket.receive_text()
            # 可以处理客户端发来的消息
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ==================== 后台任务 ====================

async def update_market_data_task():
    """市场数据更新任务（高频更新）"""
    # 重构模式：停止市场数据更新
    if REFACTORING_MODE:
        logger.info("⚠️  市场数据更新任务已跳过（重构模式）")
        return
    
    logger.info("📊 市场数据更新任务已启动（实时模式）")
    
    while True:
        try:
            async for db in get_db():
                await trading_engine.update_market_data(db)
                break
            
            # 使用配置的更新间隔（默认10秒，更实时）
            await asyncio.sleep(settings.data_update_interval)
            
        except Exception as e:
            logger.error(f"市场数据更新任务错误: {e}")
            await asyncio.sleep(60)


async def background_trading_task():
    """后台交易任务（快速响应）"""
    # 重构模式：停止所有交易
    if REFACTORING_MODE:
        logger.info("⚠️  后台交易任务已跳过（重构模式）")
        return
    
    logger.info("🤖 后台交易任务已启动（快速模式）")
    
    def _next_aligned_time(reference: datetime) -> datetime:
        aligned = reference.replace(second=0, microsecond=0)
        remainder = aligned.minute % 30
        if remainder == 0 and reference.second == 0 and reference.microsecond == 0:
            return aligned
        increment = 30 - remainder if remainder != 0 else 30
        return aligned + timedelta(minutes=increment)

    next_run = _next_aligned_time(datetime.now())
    logger.info(f"⏰ 后台交易任务将于 {next_run.strftime('%Y-%m-%d %H:%M:%S')} 首次执行，并按整十分钟对齐运行")

    while True:
        try:
            now = datetime.now()
            wait_seconds = (next_run - now).total_seconds()
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)
            else:
                logger.debug("已错过计划执行时间，立即执行补偿任务")

            cycle_start = datetime.now()
            
            if settings.enable_auto_trading:
                async for db in get_db():
                    await trading_engine.execute_trading_cycle(db)
                    break
            else:
                logger.debug("自动交易已禁用，跳过本轮执行")

            finished_at = datetime.now()
            duration = finished_at - cycle_start
            next_run = _next_aligned_time(finished_at + timedelta(seconds=1))
            logger.debug(
                f"本轮任务耗时 {duration.total_seconds():.2f} 秒，下一次后台交易任务将在 {next_run.strftime('%Y-%m-%d %H:%M:%S')} 执行"
            )
            
        except Exception as e:
            logger.error(f"后台交易任务错误: {e}")
            next_run = _next_aligned_time(datetime.now())
            await asyncio.sleep(300)

async def background_trading_task_only_buy():
    """后台交易任务（快速响应）"""
    # 重构模式：停止所有交易
    if REFACTORING_MODE:
        logger.info("⚠️  后台交易任务已跳过（重构模式）")
        return
    
    logger.info("🤖 后台交易任务已启动（快速模式）")
    
    while True:
        try:
            if settings.enable_auto_trading:
                async for db in get_db():
                    await trading_engine.execute_trading_cycle(db=db,only_buy=True)
                    break
            
            # 使用配置的交易检查间隔（默认60秒，更频繁）
            await asyncio.sleep(120)
            
        except Exception as e:
            logger.error(f"后台交易任务错误: {e}")
            await asyncio.sleep(300)
async def broadcast_updates_task():
    """广播更新任务（实时SDK钱包余额）"""
    # 重构模式：停止WebSocket广播（前端仍可通过API查询）
    if REFACTORING_MODE:
        logger.info("⚠️  WebSocket广播任务已跳过（重构模式）")
        return
    
    logger.info("📡 数据广播任务已启动（实时SDK钱包余额推送模式）")
    
    while True:
        try:
            async for db in get_db():
                # 刷新数据库会话，确保获取最新数据
                await db.commit()
                
                # 获取最新数据（内部会实时查询SDK钱包余额）
                portfolio = await trading_engine.get_portfolio_summary(db)
                
                # 获取最近的交易
                result = await db.execute(
                    select(Trade).order_by(desc(Trade.timestamp)).limit(5)
                )
                recent_trades = result.scalars().all()
                
                # 构建交易列表
                trades_list = []
                for t in recent_trades:
                    try:
                        trades_list.append({
                            "id": t.id,
                            "symbol": t.symbol or "",
                            "side": t.side or "",
                            "price": float(t.price) if t.price else 0.0,
                            "amount": float(t.amount) if t.amount else 0.0,
                            "total_value": float(t.total_value) if t.total_value else 0.0,
                            "profit_loss": float(t.profit_loss) if t.profit_loss is not None else None,
                            "profit_loss_percentage": float(t.profit_loss_percentage) if hasattr(t, 'profit_loss_percentage') and t.profit_loss_percentage is not None else None,
                            "timestamp": t.timestamp.isoformat() if t.timestamp else datetime.now().isoformat()
                        })
                    except Exception as e:
                        logger.error(f"处理交易记录 {t.id} 广播时出错: {e}")
                        continue
                
                # 广播数据（包含实时SDK钱包余额）
                await manager.broadcast({
                    "type": "portfolio_update",
                    "data": portfolio,
                    "recent_trades": trades_list,
                    "timestamp": datetime.now().isoformat(),
                    "wallet_synced": True,  # 标记数据来自SDK钱包实时查询
                    "balance_source": "SDK"  # 明确标记余额来源
                })
                
                # logger.info(f"💰 广播SDK钱包余额: 总资产=${portfolio.get('total_balance', 0):.2f}, 钱包=${portfolio.get('cash_balance', 0):.2f}, 交易记录数={len(trades_list)}")
                break
            
            await asyncio.sleep(settings.broadcast_interval)
            
        except Exception as e:
            logger.error(f"广播任务错误: {e}")
            await asyncio.sleep(30)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug_mode
    )

