"""
数据库迁移脚本：添加止盈止损字段
"""
import asyncio
import sqlite3
from pathlib import Path
from loguru import logger


def migrate_database():
    """迁移数据库，添加止盈止损字段"""
    
    db_path = "data/trading_platform.db"
    
    # 确保数据库文件存在
    if not Path(db_path).exists():
        logger.error(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info("开始数据库迁移...")
        
        # 检查 trades 表是否已有 stop_loss 字段
        cursor.execute("PRAGMA table_info(trades)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # 为 trades 表添加新字段
        if 'stop_loss' not in columns:
            logger.info("为 trades 表添加 stop_loss 字段...")
            cursor.execute("ALTER TABLE trades ADD COLUMN stop_loss REAL")
            logger.info("✅ stop_loss 字段已添加")
        else:
            logger.info("trades.stop_loss 字段已存在，跳过")
        
        if 'take_profit' not in columns:
            logger.info("为 trades 表添加 take_profit 字段...")
            cursor.execute("ALTER TABLE trades ADD COLUMN take_profit REAL")
            logger.info("✅ take_profit 字段已添加")
        else:
            logger.info("trades.take_profit 字段已存在，跳过")
        
        if 'stop_loss_strategy' not in columns:
            logger.info("为 trades 表添加 stop_loss_strategy 字段...")
            cursor.execute("ALTER TABLE trades ADD COLUMN stop_loss_strategy VARCHAR(50)")
            logger.info("✅ stop_loss_strategy 字段已添加")
        else:
            logger.info("trades.stop_loss_strategy 字段已存在，跳过")
        
        if 'take_profit_strategy' not in columns:
            logger.info("为 trades 表添加 take_profit_strategy 字段...")
            cursor.execute("ALTER TABLE trades ADD COLUMN take_profit_strategy VARCHAR(50)")
            logger.info("✅ take_profit_strategy 字段已添加")
        else:
            logger.info("trades.take_profit_strategy 字段已存在，跳过")
        
        # 检查 positions 表是否已有 stop_loss 字段
        cursor.execute("PRAGMA table_info(positions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # 为 positions 表添加新字段
        if 'stop_loss' not in columns:
            logger.info("为 positions 表添加 stop_loss 字段...")
            cursor.execute("ALTER TABLE positions ADD COLUMN stop_loss REAL")
            logger.info("✅ stop_loss 字段已添加")
        else:
            logger.info("positions.stop_loss 字段已存在，跳过")
        
        if 'take_profit' not in columns:
            logger.info("为 positions 表添加 take_profit 字段...")
            cursor.execute("ALTER TABLE positions ADD COLUMN take_profit REAL")
            logger.info("✅ take_profit 字段已添加")
        else:
            logger.info("positions.take_profit 字段已存在，跳过")
        
        if 'stop_loss_strategy' not in columns:
            logger.info("为 positions 表添加 stop_loss_strategy 字段...")
            cursor.execute("ALTER TABLE positions ADD COLUMN stop_loss_strategy VARCHAR(50)")
            logger.info("✅ stop_loss_strategy 字段已添加")
        else:
            logger.info("positions.stop_loss_strategy 字段已存在，跳过")
        
        if 'take_profit_strategy' not in columns:
            logger.info("为 positions 表添加 take_profit_strategy 字段...")
            cursor.execute("ALTER TABLE positions ADD COLUMN take_profit_strategy VARCHAR(50)")
            logger.info("✅ take_profit_strategy 字段已添加")
        else:
            logger.info("positions.take_profit_strategy 字段已存在，跳过")
        
        if 'executed_at' not in columns:
            logger.info("为 positions 表添加 executed_at 字段...")
            cursor.execute("ALTER TABLE positions ADD COLUMN executed_at TIMESTAMP")
            logger.info("✅ executed_at 字段已添加")
        else:
            logger.info("positions.executed_at 字段已存在，跳过")
        
        # 提交更改
        conn.commit()
        logger.info("✅ 数据库迁移完成！")
        
        # 验证字段
        logger.info("\n验证 trades 表结构:")
        cursor.execute("PRAGMA table_info(trades)")
        for col in cursor.fetchall():
            logger.info(f"  - {col[1]} ({col[2]})")
        
        logger.info("\n验证 positions 表结构:")
        cursor.execute("PRAGMA table_info(positions)")
        for col in cursor.fetchall():
            logger.info(f"  - {col[1]} ({col[2]})")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.exception(f"数据库迁移失败: {e}")
        return False


if __name__ == "__main__":
    success = migrate_database()
    if success:
        print("\n✅ 数据库迁移成功！现在可以运行测试脚本了。")
    else:
        print("\n❌ 数据库迁移失败，请查看日志。")
