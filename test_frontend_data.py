import requests
import json

def test_frontend_data():
    """测试前端数据获取"""
    base_url = "http://localhost:8000/api"
    
    print("测试前端数据接口...")
    print("=" * 50)
    
    # 测试账户净值数据
    try:
        response = requests.get(f"{base_url}/account_value", timeout=5)
        print(f"账户净值接口: {response.status_code}")
        data = response.json()
        print(f"   数据点数量: {len(data)}")
        if data:
            print(f"   最新净值: ${data[-1]['equity_usd']:.2f}")
    except Exception as e:
        print(f"账户净值接口失败: {e}")
    
    # 测试持仓数据
    try:
        response = requests.get(f"{base_url}/positions", timeout=5)
        print(f"持仓接口: {response.status_code}")
        data = response.json()
        print(f"   持仓数量: {len(data)}")
        if data:
            for pos in data:
                print(f"   {pos['symbol']}: {pos['size_pct']:.2f}%")
    except Exception as e:
        print(f"持仓接口失败: {e}")
    
    # 测试交易记录
    try:
        response = requests.get(f"{base_url}/trades", timeout=5)
        print(f"交易记录接口: {response.status_code}")
        data = response.json()
        print(f"   交易记录数量: {len(data)}")
        if data:
            print(f"   最新交易: {data[0]['symbol']} {data[0]['side']} {data[0]['size_pct']:.2f}%")
    except Exception as e:
        print(f"交易记录接口失败: {e}")
    
    # 测试策略数据
    try:
        response = requests.get(f"{base_url}/strategies", timeout=5)
        print(f"策略接口: {response.status_code}")
        data = response.json()
        print(f"   策略数量: {len(data)}")
        if data:
            print(f"   最新策略: {data[0]['model_name']} - {data[0]['decision']}")
    except Exception as e:
        print(f"策略接口失败: {e}")
    
    print("\n" + "=" * 50)
    print("前端数据测试完成！")
    print("如果所有接口都返回200状态码，说明前端可以正常获取数据。")
    print("请访问 http://localhost:3000 查看仪表盘。")

if __name__ == "__main__":
    test_frontend_data()
