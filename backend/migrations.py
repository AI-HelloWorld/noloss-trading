"""
数据库迁移脚本
"""
from sqlalchemy import text, inspect
from loguru import logger
from backend.database import engine


async def check_column_exists(table_name: str, column_name: str) -> bool:
    """
    检查表中是否存在指定列
    
    Args:
        table_name: 表名
        column_name: 列名
        
    Returns:
        bool: 存在返回True，否则返回False
    """
    try:
        async with engine.begin() as conn:
            # 使用inspect检查列是否存在
            result = await conn.execute(text(
                f"PRAGMA table_info({table_name})"
            ))
            columns = result.fetchall()
            column_names = [col[1] for col in columns]
            return column_name in column_names
    except Exception as e:
        logger.error(f"检查列是否存在时出错: {e}")
        return False


async def add_column_if_not_exists(table_name: str, column_name: str, column_type: str) -> bool:
    """
    如果列不存在则添加列
    
    Args:
        table_name: 表名
        column_name: 列名
        column_type: 列类型（如: DATETIME, VARCHAR(50), INTEGER等）
        
    Returns:
        bool: 成功返回True，否则返回False
    """
    try:
        # 先检查列是否已存在
        exists = await check_column_exists(table_name, column_name)
        
        if exists:
            logger.info(f"✅ 列 {table_name}.{column_name} 已存在，跳过添加")
            return True
        
        # 列不存在，添加列
        async with engine.begin() as conn:
            await conn.execute(text(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            ))
            logger.info(f"✅ 成功添加列: {table_name}.{column_name} ({column_type})")
            return True
            
    except Exception as e:
        logger.error(f"❌ 添加列失败 {table_name}.{column_name}: {e}")
        return False


async def migrate_add_executed_at():
    """
    迁移: 为trades表添加executed_at字段
    """
    logger.info("🔄 开始执行数据库迁移: 添加executed_at字段...")
    
    success = await add_column_if_not_exists(
        table_name="trades",
        column_name="executed_at",
        column_type="DATETIME"
    )
    
    if success:
        logger.info("✅ 迁移完成: trades.executed_at 字段已就绪")
    else:
        logger.warning("⚠️  迁移可能失败，请检查日志")
    
    return success


async def migrate_add_profit_fields():
    """
    迁移: 为trades表添加盈利相关字段
    """
    logger.info("🔄 开始执行数据库迁移: 添加盈利相关字段...")
    
    # 添加 is_profitable 字段
    success1 = await add_column_if_not_exists(
        table_name="trades",
        column_name="is_profitable",
        column_type="BOOLEAN"
    )
    
    # 添加 entry_price 字段
    success2 = await add_column_if_not_exists(
        table_name="trades",
        column_name="entry_price",
        column_type="FLOAT"
    )
    
    if success1 and success2:
        logger.info("✅ 迁移完成: trades.is_profitable 和 trades.entry_price 字段已就绪")
    else:
        logger.warning("⚠️  部分迁移可能失败，请检查日志")
    
    return success1 and success2


async def migrate_add_stop_loss_take_profit():
    """
    迁移: 为trades和positions表添加止盈止损字段
    """
    logger.info("🔄 开始执行数据库迁移: 添加止盈止损字段...")
    
    # 为 trades 表添加字段
    success1 = await add_column_if_not_exists(
        table_name="trades",
        column_name="stop_loss",
        column_type="REAL"
    )
    
    success2 = await add_column_if_not_exists(
        table_name="trades",
        column_name="take_profit",
        column_type="REAL"
    )
    
    success3 = await add_column_if_not_exists(
        table_name="trades",
        column_name="stop_loss_strategy",
        column_type="VARCHAR(50)"
    )
    
    success4 = await add_column_if_not_exists(
        table_name="trades",
        column_name="take_profit_strategy",
        column_type="VARCHAR(50)"
    )
    
    # 为 positions 表添加字段
    success5 = await add_column_if_not_exists(
        table_name="positions",
        column_name="stop_loss",
        column_type="REAL"
    )
    
    success6 = await add_column_if_not_exists(
        table_name="positions",
        column_name="take_profit",
        column_type="REAL"
    )
    
    success7 = await add_column_if_not_exists(
        table_name="positions",
        column_name="stop_loss_strategy",
        column_type="VARCHAR(50)"
    )
    
    success8 = await add_column_if_not_exists(
        table_name="positions",
        column_name="take_profit_strategy",
        column_type="VARCHAR(50)"
    )
    
    success9 = await add_column_if_not_exists(
        table_name="positions",
        column_name="executed_at",
        column_type="DATETIME"
    )
    
    all_success = all([success1, success2, success3, success4, success5, 
                       success6, success7, success8, success9])
    
    if all_success:
        logger.info("✅ 迁移完成: 止盈止损字段已就绪")
        logger.info("   - trades表: stop_loss, take_profit, stop_loss_strategy, take_profit_strategy")
        logger.info("   - positions表: stop_loss, take_profit, stop_loss_strategy, take_profit_strategy, executed_at")
    else:
        logger.warning("⚠️  部分迁移可能失败，请检查日志")
    
    return all_success


async def migrate_add_positions_entry_price():
    """
    迁移: 为positions表添加entry_price字段
    """
    logger.info("🔄 开始执行数据库迁移: 为positions表添加entry_price字段...")
    
    success = await add_column_if_not_exists(
        table_name="positions",
        column_name="entry_price",
        column_type="REAL"
    )
    
    if success:
        logger.info("✅ 迁移完成: positions.entry_price 字段已就绪")
        # 如果字段是新添加的，用average_price初始化entry_price
        try:
            async with engine.begin() as conn:
                await conn.execute(text(
                    "UPDATE positions SET entry_price = average_price WHERE entry_price IS NULL"
                ))
                logger.info("✅ 已用average_price初始化现有持仓的entry_price")
        except Exception as e:
            logger.warning(f"⚠️  初始化entry_price失败: {e}")
    else:
        logger.warning("⚠️  迁移可能失败，请检查日志")
    
    return success


async def run_all_migrations():
    """
    运行所有数据库迁移
    
    这个函数会在系统启动时自动执行，
    每个迁移函数会自动检查是否需要执行，避免重复迁移
    """
    logger.info("=" * 60)
    logger.info("🔧 开始执行数据库迁移...")
    logger.info("=" * 60)
    
    try:
        # 迁移1: 添加executed_at字段
        await migrate_add_executed_at()
        
        # 迁移2: 添加盈利相关字段
        await migrate_add_profit_fields()
        
        # 迁移3: 添加止盈止损字段
        await migrate_add_stop_loss_take_profit()
        
        # 迁移4: 为positions表添加entry_price字段
        await migrate_add_positions_entry_price()
        
        # 未来的迁移可以在这里添加
        # await migrate_xxx()
        
        logger.info("=" * 60)
        logger.info("✅ 所有数据库迁移已完成")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ 数据库迁移失败: {e}")
        logger.error("=" * 60)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    """
    手动执行迁移的入口
    使用方法: python -m backend.migrations
    """
    import asyncio
    asyncio.run(run_all_migrations())

