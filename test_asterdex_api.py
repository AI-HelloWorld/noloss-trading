"""测试AsterDEX API"""
import requests
import hmac
import hashlib
import time

API_KEY = "55f5fb754474d786bd4d4567927dbb1b08d0532b0cfa8adcad64ab983fdd75a9"
API_SECRET = "18b6ab62259b44676143434f4081f3d6c2246a0fa7fc65c49d2eb9cb50a9a065"
BASE_URL = "https://fapi.asterdex.com"

def test_ping():
    """测试Ping端点"""
    print("\n=== Testing Ping ===")
    try:
        response = requests.get(f"{BASE_URL}/fapi/v1/ping", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

def test_time():
    """测试Time端点"""
    print("\n=== Testing Time ===")
    try:
        response = requests.get(f"{BASE_URL}/fapi/v1/time", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

def test_symbols():
    """测试获取交易对"""
    print("\n=== Testing Symbols (No Auth) ===")
    try:
        response = requests.get(f"{BASE_URL}/fapi/v1/exchangeInfo", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

def test_authenticated():
    """测试需要认证的API"""
    print("\n=== Testing Authenticated API ===")
    timestamp = int(time.time() * 1000)
    
    # 尝试不同的参数顺序和格式
    params = {
        'timestamp': timestamp,
        'recvWindow': 5000
    }
    
    query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
    signature = hmac.new(
        API_SECRET.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    params['signature'] = signature
    
    headers = {
        'X-MBX-APIKEY': API_KEY
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/fapi/v1/account",
            params=params,
            headers=headers,
            timeout=5
        )
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Response: {response.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ping()
    test_time()
    test_symbols()
    test_authenticated()

