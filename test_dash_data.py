import requests
import json

def test_dash_data_fetch():
    """测试Dash前端数据获取"""
    base_url = "http://localhost:8000/api"
    
    print("测试Dash前端数据获取...")
    print("=" * 50)
    
    # 测试账户净值数据
    try:
        response = requests.get(f"{base_url}/account_value?days=30", timeout=5)
        print(f"账户净值接口: {response.status_code}")
        data = response.json()
        print(f"   数据点数量: {len(data)}")
        if data:
            print(f"   最新净值: ${data[-1]['equity_usd']:.2f}")
            print(f"   数据示例: {data[0]}")
    except Exception as e:
        print(f"账户净值接口失败: {e}")
    
    # 测试持仓数据
    try:
        response = requests.get(f"{base_url}/positions", timeout=5)
        print(f"持仓接口: {response.status_code}")
        data = response.json()
        print(f"   持仓数量: {len(data)}")
        if data:
            print(f"   持仓示例: {data[0]}")
    except Exception as e:
        print(f"持仓接口失败: {e}")
    
    # 测试交易记录
    try:
        response = requests.get(f"{base_url}/trades", timeout=5)
        print(f"交易记录接口: {response.status_code}")
        data = response.json()
        print(f"   交易记录数量: {len(data)}")
        if data:
            print(f"   交易示例: {data[0]}")
    except Exception as e:
        print(f"交易记录接口失败: {e}")
    
    # 测试策略数据
    try:
        response = requests.get(f"{base_url}/strategies", timeout=5)
        print(f"策略接口: {response.status_code}")
        data = response.json()
        print(f"   策略数量: {len(data)}")
        if data:
            print(f"   策略示例: {data[0]}")
    except Exception as e:
        print(f"策略接口失败: {e}")
    
    print("\n" + "=" * 50)
    print("如果所有接口都返回200状态码且有数据，说明API正常。")
    print("问题可能在于Dash前端的回调函数或数据处理。")

if __name__ == "__main__":
    test_dash_data_fetch()
