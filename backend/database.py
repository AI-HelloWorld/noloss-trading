"""
数据库模型和连接管理
"""
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, Text, create_engine, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import shutil
from pathlib import Path
from loguru import logger
from backend.config import settings


def get_local_time():
    """获取本地时间"""
    return datetime.now()


def ensure_db_path():
    """
    确保数据库路径正确，处理Linux下Docker挂载导致的目录问题
    """
    # 从database_url中提取实际的文件路径
    db_url = settings.database_url
    if "sqlite" in db_url:
        # 提取文件路径 (例如: sqlite+aiosqlite:///app/data/trading_platform.db -> /app/data/trading_platform.db)
        db_path_str = db_url.split("///")[-1] if ":///" in db_url else db_url.split("//")[-1]
        db_path = Path(db_path_str)
        
        logger.info(f"检查数据库路径: {db_path}")
        
        # 确保父目录存在
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 如果数据库路径是目录（Docker挂载错误导致），删除它
        if db_path.exists() and db_path.is_dir():
            logger.warning(f"检测到数据库路径是目录而不是文件: {db_path}")
            logger.warning("正在删除错误的目录并创建正确的数据库文件...")
            try:
                shutil.rmtree(db_path)
                logger.info(f"已删除错误的目录: {db_path}")
            except Exception as e:
                logger.error(f"删除目录失败: {e}")
                raise
        
        # 如果数据库文件不存在，创建一个空文件
        if not db_path.exists():
            logger.info(f"创建数据库文件: {db_path}")
            db_path.touch()
            logger.info(f"数据库文件创建成功: {db_path}")
        
        logger.info(f"数据库路径验证完成: {db_path}")
    
    return True

Base = declarative_base()


class Trade(Base):
    """交易记录"""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=get_local_time)
    symbol = Column(String(50), index=True)
    side = Column(String(10))  # buy, sell, short, cover
    price = Column(Float)
    amount = Column(Float)
    total_value = Column(Float)
    ai_model = Column(String(50))
    ai_reasoning = Column(Text)
    success = Column(Boolean, default=True)
    order_id = Column(String(100))
    profit_loss = Column(Float, nullable=True)
    profit_loss_percentage = Column(Float, nullable=True)  # 盈亏百分比
    executed_at = Column(DateTime, nullable=True)  # 交易执行时间
    is_profitable = Column(Boolean, nullable=True)  # 是否盈利（仅平仓操作有效）
    entry_price = Column(Float, nullable=True)  # 入场价格（仅平仓操作记录）
    stop_loss = Column(Float, nullable=True)  # 止损价格
    take_profit = Column(Float, nullable=True)  # 止盈价格
    stop_loss_strategy = Column(String(50), nullable=True)  # 止损策略类型
    take_profit_strategy = Column(String(50), nullable=True)  # 止盈策略类型


class PortfolioSnapshot(Base):
    """投资组合快照"""
    __tablename__ = "portfolio_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=get_local_time)
    total_balance = Column(Float)
    cash_balance = Column(Float)
    positions_value = Column(Float)
    total_profit_loss = Column(Float)
    total_pnl_percentage = Column(Float, nullable=True)  # 盈亏百分比
    daily_profit_loss = Column(Float, nullable=True)
    win_rate = Column(Float, nullable=True)
    total_trades = Column(Integer, default=0)


class Position(Base):
    """当前持仓"""
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), unique=True, index=True)
    amount = Column(Float)
    average_price = Column(Float)
    current_price = Column(Float)
    unrealized_pnl = Column(Float)
    position_type = Column(String(10))  # long, short
    last_updated = Column(DateTime, default=get_local_time)
    entry_price = Column(Float, nullable=True)  # 入场价格（记录开仓时的价格）
    stop_loss = Column(Float, nullable=True)  # 止损价格
    take_profit = Column(Float, nullable=True)  # 止盈价格
    stop_loss_strategy = Column(String(50), nullable=True)  # 止损策略类型
    take_profit_strategy = Column(String(50), nullable=True)  # 止盈策略类型
    executed_at = Column(DateTime, nullable=True)  # 持仓创建时间


class AIDecision(Base):
    """AI决策记录"""
    __tablename__ = "ai_decisions"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=get_local_time)
    ai_model = Column(String(50))
    symbol = Column(String(50))
    decision = Column(String(20))  # buy, sell, hold, short, cover
    confidence = Column(Float)
    reasoning = Column(Text)
    market_analysis = Column(Text)
    executed = Column(Boolean, default=False)


class MarketData(Base):
    """市场数据"""
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=get_local_time)
    symbol = Column(String(50), index=True)
    price = Column(Float)
    volume_24h = Column(Float)
    change_24h = Column(Float)
    high_24h = Column(Float)
    low_24h = Column(Float)
    market_cap = Column(Float, nullable=True)


class News(Base):
    """新闻数据"""
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    summary = Column(Text)  # AI生成的摘要
    sentiment = Column(String(20))  # positive, negative, neutral
    sentiment_score = Column(Float)  # 情绪评分 0-1
    mentioned_coins = Column(JSON)  # 提及的币种列表 ["BTC", "SOL"]
    source_url = Column(String(500))  # 新闻来源URL
    received_at = Column(DateTime, default=get_local_time, index=True)  # 接收时间
    is_major = Column(Boolean, default=False)  # 是否为重大新闻
    original_content = Column(Text, nullable=True)  # 原文内容（仅重大新闻）



# 创建异步引擎
engine = create_async_engine(
    settings.database_url,
    echo=settings.sql_echo,  # 使用专门的SQL日志配置
    pool_pre_ping=True,  # 连接池健康检查
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db():
    """初始化数据库"""
    # 确保数据库路径正确（处理Linux下Docker挂载问题）
    ensure_db_path()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        yield session

