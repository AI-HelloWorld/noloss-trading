import requests
import json

response = requests.get("http://localhost:8000/api/positions", timeout=5)
print(f"状态码: {response.status_code}")
print(f"响应类型: {type(response.json())}")
data = response.json()
print(f"数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
if isinstance(data, list):
    print(f"数据量: {len(data)}")
elif isinstance(data, dict):
    print(f"数据键: {list(data.keys())}")

