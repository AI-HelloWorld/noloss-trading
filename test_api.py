#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试API接口
"""
import requests
import json
import time

def test_api():
    """测试API接口"""
    base_url = "http://localhost:8000"
    
    print("测试API接口...")
    
    # 测试根路径
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"根路径: {response.status_code}")
        print(f"   响应: {response.json()}")
    except Exception as e:
        print(f"根路径失败: {e}")
    
    # 测试状态接口
    try:
        response = requests.get(f"{base_url}/api/status", timeout=5)
        print(f"状态接口: {response.status_code}")
        print(f"   响应: {response.json()}")
    except Exception as e:
        print(f"状态接口失败: {e}")
    
    # 测试投资组合接口
    try:
        response = requests.get(f"{base_url}/api/portfolio", timeout=5)
        print(f"投资组合接口: {response.status_code}")
        data = response.json()
        print(f"   总资产: ${data.get('total_balance', 0):.2f}")
        print(f"   持仓数量: {len(data.get('positions', []))}")
    except Exception as e:
        print(f"投资组合接口失败: {e}")
    
    # 测试账户净值接口
    try:
        response = requests.get(f"{base_url}/api/account_value", timeout=5)
        print(f"账户净值接口: {response.status_code}")
        data = response.json()
        print(f"   数据点数量: {len(data)}")
    except Exception as e:
        print(f"账户净值接口失败: {e}")
    
    # 测试持仓接口
    try:
        response = requests.get(f"{base_url}/api/positions", timeout=5)
        print(f"持仓接口: {response.status_code}")
        data = response.json()
        print(f"   持仓数量: {len(data)}")
    except Exception as e:
        print(f"持仓接口失败: {e}")
    
    # 测试交易记录接口
    try:
        response = requests.get(f"{base_url}/api/trades", timeout=5)
        print(f"交易记录接口: {response.status_code}")
        data = response.json()
        print(f"   交易记录数量: {len(data)}")
    except Exception as e:
        print(f"交易记录接口失败: {e}")
    
    # 测试策略接口
    try:
        response = requests.get(f"{base_url}/api/strategies", timeout=5)
        print(f"策略接口: {response.status_code}")
        data = response.json()
        print(f"   策略数量: {len(data)}")
    except Exception as e:
        print(f"策略接口失败: {e}")

if __name__ == "__main__":
    print("等待服务启动...")
    time.sleep(3)
    test_api()
