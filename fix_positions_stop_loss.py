"""
修复脚本：为现有持仓补充止损止盈数据

规则：
- 多仓（long/buy）：止损 = 入场价 * 0.98 (-2%), 止盈 = 入场价 * 1.04 (+4%)
- 空仓（short）：止损 = 入场价 * 1.02 (+2%), 止盈 = 入场价 * 0.96 (-4%)
"""
import asyncio
from loguru import logger
from sqlalchemy import select, update
from backend.database import Position, AsyncSessionLocal, init_db


async def fix_positions_stop_loss():
    """为现有持仓补充止损止盈数据"""
    logger.info("=" * 60)
    logger.info("🔧 开始修复持仓止损止盈数据...")
    logger.info("=" * 60)
    
    try:
        # 初始化数据库
        await init_db()
        
        async with AsyncSessionLocal() as session:
            # 查询所有持仓
            result = await session.execute(select(Position))
            positions = result.scalars().all()
            
            if not positions:
                logger.info("📊 没有找到持仓记录")
                return
            
            logger.info(f"📊 找到 {len(positions)} 个持仓记录")
            
            fixed_count = 0
            skipped_count = 0
            
            for position in positions:
                # 检查是否需要修复
                needs_fix = False
                
                if position.stop_loss is None or position.stop_loss == 0:
                    needs_fix = True
                    reason = "缺少止损"
                elif position.take_profit is None or position.take_profit == 0:
                    needs_fix = True
                    reason = "缺少止盈"
                
                if not needs_fix:
                    logger.debug(f"⏭️  跳过 {position.symbol}: 已有完整止损止盈数据")
                    skipped_count += 1
                    continue
                
                # 获取入场价格
                entry_price = position.entry_price if position.entry_price else position.average_price
                
                if not entry_price or entry_price == 0:
                    logger.warning(f"⚠️  跳过 {position.symbol}: 入场价格无效")
                    skipped_count += 1
                    continue
                
                # 根据持仓类型计算止损止盈
                position_type = position.position_type or 'long'
                
                if position_type in ['long', 'buy']:
                    # 多仓：止损-2%, 止盈+4%
                    stop_loss = entry_price * 0.98
                    take_profit = entry_price * 1.04
                    type_name = "多仓"
                else:
                    # 空仓：止损+2%, 止盈-4%
                    stop_loss = entry_price * 1.02
                    take_profit = entry_price * 0.96
                    type_name = "空仓"
                
                # 更新持仓
                position.stop_loss = stop_loss
                position.take_profit = take_profit
                position.stop_loss_strategy = 'fixed_percentage'
                position.take_profit_strategy = 'fixed_percentage'
                
                fixed_count += 1
                
                logger.info(
                    f"✅ 修复 {position.symbol} ({type_name}):\n"
                    f"   入场价: ${entry_price:.4f}\n"
                    f"   止损: ${stop_loss:.4f} ({((stop_loss - entry_price) / entry_price * 100):+.2f}%)\n"
                    f"   止盈: ${take_profit:.4f} ({((take_profit - entry_price) / entry_price * 100):+.2f}%)\n"
                    f"   原因: {reason}"
                )
            
            # 提交更改
            await session.commit()
            
            logger.info("=" * 60)
            logger.info(f"✅ 修复完成:")
            logger.info(f"   - 已修复: {fixed_count} 个持仓")
            logger.info(f"   - 已跳过: {skipped_count} 个持仓（已有数据）")
            logger.info(f"   - 总计: {len(positions)} 个持仓")
            logger.info("=" * 60)
            
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ 修复失败: {e}")
        logger.error("=" * 60)
        import traceback
        traceback.print_exc()


async def preview_fix():
    """预览将要修复的持仓（不实际修改数据库）"""
    logger.info("=" * 60)
    logger.info("👀 预览持仓止损止盈数据修复...")
    logger.info("=" * 60)
    
    try:
        # 初始化数据库
        await init_db()
        
        async with AsyncSessionLocal() as session:
            # 查询所有持仓
            result = await session.execute(select(Position))
            positions = result.scalars().all()
            
            if not positions:
                logger.info("📊 没有找到持仓记录")
                return
            
            logger.info(f"📊 找到 {len(positions)} 个持仓记录\n")
            
            will_fix_count = 0
            
            for position in positions:
                # 检查是否需要修复
                needs_fix = False
                reason_parts = []
                
                if position.stop_loss is None or position.stop_loss == 0:
                    needs_fix = True
                    reason_parts.append("缺少止损")
                
                if position.take_profit is None or position.take_profit == 0:
                    needs_fix = True
                    reason_parts.append("缺少止盈")
                
                if not needs_fix:
                    logger.debug(f"⏭️  跳过 {position.symbol}: 已有完整数据")
                    continue
                
                # 获取入场价格
                entry_price = position.entry_price if position.entry_price else position.average_price
                
                if not entry_price or entry_price == 0:
                    logger.warning(f"⚠️  无法修复 {position.symbol}: 入场价格无效")
                    continue
                
                # 计算新的止损止盈
                position_type = position.position_type or 'long'
                
                if position_type in ['long', 'buy']:
                    new_stop_loss = entry_price * 0.98
                    new_take_profit = entry_price * 1.04
                    type_name = "多仓"
                else:
                    new_stop_loss = entry_price * 1.02
                    new_take_profit = entry_price * 0.96
                    type_name = "空仓"
                
                will_fix_count += 1
                
                logger.info(
                    f"🔍 将修复 {position.symbol} ({type_name}):\n"
                    f"   入场价: ${entry_price:.4f}\n"
                    f"   当前止损: ${position.stop_loss or 0:.4f} → 新止损: ${new_stop_loss:.4f}\n"
                    f"   当前止盈: ${position.take_profit or 0:.4f} → 新止盈: ${new_take_profit:.4f}\n"
                    f"   原因: {', '.join(reason_parts)}\n"
                )
            
            logger.info("=" * 60)
            logger.info(f"📊 预览结果:")
            logger.info(f"   - 将修复: {will_fix_count} 个持仓")
            logger.info(f"   - 将跳过: {len(positions) - will_fix_count} 个持仓")
            logger.info(f"   - 总计: {len(positions)} 个持仓")
            logger.info("=" * 60)
            
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ 预览失败: {e}")
        logger.error("=" * 60)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--preview":
        # 预览模式
        logger.info("运行预览模式（不会修改数据库）")
        asyncio.run(preview_fix())
    else:
        # 执行模式
        logger.info("运行执行模式（将修改数据库）")
        logger.info("如果只想预览，请使用: python fix_positions_stop_loss.py --preview")
        
        # 询问确认
        confirm = input("\n确定要执行修复吗？(yes/no): ")
        if confirm.lower() in ['yes', 'y']:
            asyncio.run(fix_positions_stop_loss())
        else:
            logger.info("已取消修复操作")

