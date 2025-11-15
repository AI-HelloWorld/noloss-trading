import requests
import json

def debug_api_structure():
    """调试API返回结构"""
    base_url = "http://localhost:8000/api"
    
    print("=" * 60)
    print("调试FastAPI返回结构")
    print("=" * 60)
    
    # 1. 检查账户净值接口
    print("\n1. 账户净值接口 (/api/account_value)")
    print("-" * 40)
    try:
        response = requests.get(f"{base_url}/account_value?days=30", timeout=5)
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"数据量: {len(data)}")
        if data:
            print("第一个数据项结构:")
            print(json.dumps(data[0], indent=2, ensure_ascii=False))
            print("\n最后一个数据项结构:")
            print(json.dumps(data[-1], indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"错误: {e}")
    
    # 2. 检查持仓接口
    print("\n2. 持仓接口 (/api/positions)")
    print("-" * 40)
    try:
        response = requests.get(f"{base_url}/positions", timeout=5)
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"数据量: {len(data)}")
        if data:
            print("第一个数据项结构:")
            print(json.dumps(data[0], indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"错误: {e}")
    
    # 3. 检查交易记录接口
    print("\n3. 交易记录接口 (/api/trades)")
    print("-" * 40)
    try:
        response = requests.get(f"{base_url}/trades", timeout=5)
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"数据量: {len(data)}")
        if data:
            print("第一个数据项结构:")
            print(json.dumps(data[0], indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"错误: {e}")
    
    # 4. 检查策略接口
    print("\n4. 策略接口 (/api/strategies)")
    print("-" * 40)
    try:
        response = requests.get(f"{base_url}/strategies", timeout=5)
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"数据量: {len(data)}")
        if data:
            print("第一个数据项结构:")
            print(json.dumps(data[0], indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"错误: {e}")
    
    print("\n" + "=" * 60)
    print("API结构调试完成")

if __name__ == "__main__":
    debug_api_structure()
