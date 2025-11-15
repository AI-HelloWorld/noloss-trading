"""
配置管理模块
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """应用配置"""
    
    # AsterDEX专业API配置
    aster_dex_api_key: str = os.getenv("ASTER_DEX_API_KEY", "")
    aster_dex_api_secret: str = os.getenv("ASTER_DEX_API_SECRET", "")  # 保留兼容性，专业API可能不需要
    wallet_address: str = os.getenv("WALLET_ADDRESS", "")  # API授权的钱包地址（专业API必需）
    
    # AI模型密钥
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    grok_api_key: str = os.getenv("GROK_API_KEY", "")
    qwen_api_key: str = os.getenv("QWEN_API_KEY", "")
    
    # 数据库
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///app/data/trading_platform.db")
    
    # 应用配置
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    debug_mode: bool = os.getenv("DEBUG_MODE", "False").lower() == "true"
    sql_echo: bool = os.getenv("SQL_ECHO", "True").lower() == "true"  # 是否打印SQL语句
    
    # 交易配置
    initial_balance: float = float(os.getenv("INITIAL_BALANCE", "100"))
    max_position_size: float = float(os.getenv("MAX_POSITION_SIZE", "0.2"))
    risk_per_trade: float = float(os.getenv("RISK_PER_TRADE", "0.02"))
    enable_auto_trading: bool = os.getenv("ENABLE_AUTO_TRADING", "True").lower() == "true"
    
    # 风控配置 - 防止爆仓
    max_wallet_usage: float = float(os.getenv("MAX_WALLET_USAGE", "0.5"))  # 单笔最多用50%钱包余额
    margin_reserve_ratio: float = float(os.getenv("MARGIN_RESERVE_RATIO", "0.3"))  # 合约交易保证金预留比例
    
    # 交易对筛选配置
    min_volume_threshold: float = float(os.getenv("MIN_VOLUME_THRESHOLD", "20000000"))  # 最小24H交易量（美元），默认2000万
    max_trading_symbols: int = int(os.getenv("MAX_TRADING_SYMBOLS", "50"))  # 最多选择多少个交易对进行分析，默认50个
    
    # 更新频率（秒）- 超实时模式
    data_update_interval: int = int(os.getenv("DATA_UPDATE_INTERVAL", "60"))  # 市场数据每3秒更新（超实时）
    trade_check_interval: int = int(os.getenv("TRADE_CHECK_INTERVAL", "600"))  # 交易检查每5分钟
    broadcast_interval: int = int(os.getenv("BROADCAST_INTERVAL", "2"))  # WebSocket推送每2秒
    
    # 新闻API配置
    news_api_url: str = os.getenv("NEWS_API_URL", "")
    
    # 高级配置
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    max_concurrent_trades: int = int(os.getenv("MAX_CONCURRENT_TRADES", "3"))
    risk_threshold: float = float(os.getenv("RISK_THRESHOLD", "0.7"))
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.6"))
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # 忽略额外字段而不是报错


settings = Settings()

