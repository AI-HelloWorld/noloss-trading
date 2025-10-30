# AsterDEX 官方SDK集成说明

## 📦 集成概述

本系统已升级为使用 AsterDEX 官方 Python SDK (`aster-connector-python`)，替代之前的自定义实现。

### 官方仓库
- GitHub: https://github.com/asterdex/aster-connector-python
- PyPI: `aster-connector-python`

## 🔧 安装依赖

官方SDK已添加到 `requirements.txt`：

```bash
pip install -r requirements.txt
```

或单独安装：

```bash
pip install aster-connector-python
```

## 🔑 API配置

### 配置参数说明

根据官方SDK文档，需要配置以下参数：

```env
# AsterDEX API配置（官方SDK）
ASTER_DEX_API_KEY=你的API_Key
ASTER_DEX_API_SECRET=你的API_Secret
WALLET_ADDRESS=你的钱包地址（可选）
```

### 配置说明

1. **ASTER_DEX_API_KEY**: API密钥（对应官方SDK的 `key` 参数）
2. **ASTER_DEX_API_SECRET**: API秘密（对应官方SDK的 `secret` 参数）
3. **WALLET_ADDRESS**: 钱包地址（可选，用于显示）

## 📝 主要功能实现

### 1. 账户余额查询

使用官方SDK的 `account()` 方法：

```python
# 官方SDK调用
client = Client(key=api_key, secret=api_secret)
result = client.account()
```

返回格式：
```json
{
  "balances": [
    {"asset": "USDT", "free": "1000.00", "locked": "0.00"},
    {"asset": "BTC", "free": "0.001", "locked": "0.00"}
  ],
  "canTrade": true,
  "canDeposit": true,
  "canWithdraw": true
}
```

### 2. 下单交易

使用官方SDK的 `new_order()` 方法：

```python
# 市价单
params = {
    'symbol': 'BTCUSDT',
    'side': 'BUY',
    'type': 'MARKET',
    'quantity': 0.001
}
response = client.new_order(**params)

# 限价单
params = {
    'symbol': 'BTCUSDT',
    'side': 'SELL',
    'type': 'LIMIT',
    'timeInForce': 'GTC',
    'quantity': 0.002,
    'price': 59808
}
response = client.new_order(**params)
```

返回格式：
```json
{
  "orderId": "12345",
  "symbol": "BTCUSDT",
  "status": "NEW",
  "side": "BUY",
  "type": "MARKET",
  "quantity": "0.001"
}
```

### 3. 查询持仓

使用官方SDK的 `get_position_risk()` 方法：

```python
result = client.get_position_risk()
```

返回格式：
```json
[
  {
    "symbol": "BTCUSDT",
    "positionAmt": "0.001",
    "entryPrice": "60000.00",
    "markPrice": "61000.00",
    "unRealizedProfit": "1.00"
  }
]
```

### 4. 查询行情

使用公开接口（无需认证）：

```python
# 查询单个交易对行情
client = Client()
result = client.ticker_24hr_price_change('BTCUSDT')

# 查询所有交易对行情
result = client.ticker_24hr_price_change()
```

## 🔄 异步适配

由于官方SDK是同步的，而我们的系统是异步的，使用 `asyncio.to_thread()` 进行适配：

```python
async def get_account_balance(self):
    def get_balance():
        return self.client.account()
    
    result = await asyncio.to_thread(get_balance)
    return result
```

## ⚠️ 错误处理

官方SDK提供两种错误类型：

```python
from aster.error import ClientError, ServerError

try:
    result = client.account()
except ClientError as e:
    # 客户端错误（4XX）
    print(f"错误码: {e.error_code}")
    print(f"错误信息: {e.error_message}")
except ServerError as e:
    # 服务器错误（5XX）
    print(f"服务器错误: {e}")
```

## 🔗 Base URL

默认使用 Futures API：

```python
base_url = "https://fapi.asterdex.com"
```

## 📊 支持的接口

### 公开接口（无需认证）
- ✅ `time()` - 服务器时间
- ✅ `exchange_info()` - 交易所信息
- ✅ `ticker_24hr()` - 24小时行情

### 认证接口（需要API密钥）
- ✅ `account()` - 账户信息
- ✅ `balance()` - 账户余额
- ✅ `new_order()` - 创建订单
- ✅ `query_order()` - 查询订单
- ✅ `get_position_risk()` - 持仓风险
- ✅ `get_open_orders()` - 当前委托
- ✅ `cancel_order()` - 取消订单

## 🔍 调试信息

系统启动时会显示SDK配置信息：

```
✅ AsterDEX官方SDK客户端初始化成功
🔗 Base URL: https://fapi.asterdex.com
🔑 API Key: 0x1234...5678
🔐 API Secret: ********************
💳 钱包地址: 0xabcd...ef01
```

## 📚 更多信息

- 官方文档: https://github.com/asterdex/aster-connector-python
- API文档: https://fapi.asterdex.com/docs
- 支持: contact@asterdex.com

## 🎯 升级优势

相比之前的自定义实现：

1. ✅ **官方支持**: 使用官方维护的SDK，更稳定可靠
2. ✅ **自动签名**: SDK自动处理API签名，无需手动实现
3. ✅ **错误处理**: 统一的错误处理机制
4. ✅ **类型安全**: 标准化的参数和返回格式
5. ✅ **易于维护**: SDK更新会自动包含最新API变更

## 🚀 快速测试

安装依赖后，运行测试脚本：

```bash
# 测试API连接
python test_api_auth.py

# 测试交易功能
python test_trading.py

# 测试持仓查询
python test_api_positions.py
```

