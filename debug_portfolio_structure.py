import asyncio
import json
from backend.database import get_db
from backend.trading.trading_engine import trading_engine

async def debug_portfolio_structure():
    """调试投资组合结构"""
    print("调试投资组合结构...")
    print("=" * 50)
    
    async for db in get_db():
        portfolio = await trading_engine.get_portfolio_summary(db)
        
        print("投资组合原始数据:")
        print(json.dumps(portfolio, indent=2, ensure_ascii=False, default=str))
        
        print("\n" + "=" * 50)
        print("分析positions字段:")
        positions = portfolio.get('positions', {})
        print(f"positions类型: {type(positions)}")
        print(f"positions内容: {positions}")
        
        if isinstance(positions, dict):
            print(f"positions是字典，键: {list(positions.keys())}")
            if positions:
                print("第一个持仓:")
                first_key = list(positions.keys())[0]
                print(f"键: {first_key}")
                print(f"值: {positions[first_key]}")
        elif isinstance(positions, list):
            print(f"positions是列表，长度: {len(positions)}")
            if positions:
                print("第一个持仓:")
                print(positions[0])
        
        break

if __name__ == "__main__":
    asyncio.run(debug_portfolio_structure())

