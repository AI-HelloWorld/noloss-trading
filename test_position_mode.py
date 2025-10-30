"""测试并修复持仓模式设置"""
import asyncio
from backend.exchanges.aster_dex import aster_client
from loguru import logger

async def test_position_mode():
    """测试持仓模式设置"""
    
    # 1. 检查当前持仓模式
    logger.info("=" * 60)
    logger.info("步骤 1: 查询当前持仓模式")
    logger.info("=" * 60)
    
    try:
        def get_mode():
            return aster_client.client.get_position_mode()
        
        mode_result = await asyncio.to_thread(get_mode)
        logger.info(f"当前持仓模式: {mode_result}")
        
        if isinstance(mode_result, dict):
            dual_side = mode_result.get('dualSidePosition', False)
            logger.info(f"dualSidePosition = {dual_side}")
            
            if not dual_side or dual_side == "false":
                logger.warning("⚠️  当前为单向持仓模式，需要切换为双向持仓模式")
            else:
                logger.info("✅ 当前已是双向持仓模式")
    except Exception as e:
        logger.error(f"查询持仓模式失败: {e}")
    
    # 2. 尝试设置为双向持仓模式
    logger.info("\n" + "=" * 60)
    logger.info("步骤 2: 设置为双向持仓模式")
    logger.info("=" * 60)
    
    try:
        def change_mode():
            # 注意：参数值应该是字符串 "true" 而不是布尔值 True
            return aster_client.client.change_position_mode(dualSidePosition="true")
        
        change_result = await asyncio.to_thread(change_mode)
        logger.info(f"设置结果: {change_result}")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"设置持仓模式时出现错误: {error_msg}")
        
        # 检查是否是"已经是双向模式"的错误
        if 'No need to change' in error_msg or 'already' in error_msg.lower():
            logger.info("✅ 账户已经是双向持仓模式，无需更改")
        else:
            logger.error("❌ 设置失败，需要手动在交易所设置")
    
    # 3. 再次检查持仓模式
    logger.info("\n" + "=" * 60)
    logger.info("步骤 3: 再次查询持仓模式（验证）")
    logger.info("=" * 60)
    
    try:
        def get_mode_again():
            return aster_client.client.get_position_mode()
        
        mode_result = await asyncio.to_thread(get_mode_again)
        logger.info(f"最终持仓模式: {mode_result}")
        
        if isinstance(mode_result, dict):
            dual_side = mode_result.get('dualSidePosition', False)
            if dual_side and dual_side != "false":
                logger.info("✅ 验证成功：双向持仓模式已启用")
            else:
                logger.warning("⚠️  验证失败：仍为单向持仓模式")
    except Exception as e:
        logger.error(f"再次查询失败: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("测试完成")
    logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_position_mode())

