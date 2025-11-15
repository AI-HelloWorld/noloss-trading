# API文档

## 基础信息

- **Base URL**: `http://localhost:8000`
- **协议**: HTTP/HTTPS
- **数据格式**: JSON
- **WebSocket**: `ws://localhost:8000/ws`

## 认证

当前版本为展示平台，不需要认证。如需添加认证，请参考FastAPI的安全文档。

## API端点

### 1. 系统状态

#### GET `/api/status`

获取系统运行状态和AI模型状态。

**请求示例：**
```bash
curl http://localhost:8000/api/status
```

**响应示例：**
```json
{
  "system": "online",
  "trading_enabled": true,
  "ai_models": [
    {
      "name": "GPT-4",
      "status": "active",
      "api_key_configured": true
    },
    {
      "name": "DeepSeek",
      "status": "active",
      "api_key_configured": true
    }
  ],
  "timestamp": "2024-01-01T12:00:00"
}
```

### 2. 投资组合

#### GET `/api/portfolio`

获取当前投资组合信息。

**响应示例：**
```json
{
  "total_balance": 10500.50,
  "cash_balance": 5000.00,
  "positions_value": 5500.50,
  "total_pnl": 500.50,
  "total_trades": 25,
  "win_rate": 0.68,
  "positions": [
    {
      "symbol": "BTC/USDT",
      "amount": 0.15,
      "average_price": 45000.00,
      "current_price": 46000.00,
      "unrealized_pnl": 150.00,
      "position_type": "long"
    }
  ]
}
```

### 3. 交易历史

#### GET `/api/trades?limit={limit}`

获取交易历史记录。

**参数：**
- `limit` (可选): 返回记录数量，默认50

**请求示例：**
```bash
curl http://localhost:8000/api/trades?limit=10
```

**响应示例：**
```json
[
  {
    "id": 1,
    "timestamp": "2024-01-01T12:00:00",
    "symbol": "BTC/USDT",
    "side": "buy",
    "price": 45000.00,
    "amount": 0.1,
    "total_value": 4500.00,
    "ai_model": "Consensus",
    "ai_reasoning": "市场趋势向上...",
    "success": true,
    "profit_loss": null
  }
]
```

### 4. 投资组合历史

#### GET `/api/portfolio-history?days={days}`

获取投资组合历史数据。

**参数：**
- `days` (可选): 历史天数，默认30

**响应示例：**
```json
[
  {
    "timestamp": "2024-01-01T00:00:00",
    "total_balance": 10500.50,
    "cash_balance": 5000.00,
    "positions_value": 5500.50,
    "total_profit_loss": 500.50,
    "daily_profit_loss": 50.25,
    "win_rate": 0.68,
    "total_trades": 25
  }
]
```

### 5. AI决策记录

#### GET `/api/ai-decisions?limit={limit}`

获取AI决策历史。

**参数：**
- `limit` (可选): 返回记录数量，默认20

**响应示例：**
```json
[
  {
    "id": 1,
    "timestamp": "2024-01-01T12:00:00",
    "ai_model": "Consensus",
    "symbol": "BTC/USDT",
    "decision": "buy",
    "confidence": 0.85,
    "reasoning": "多个模型一致看涨，技术指标支持...",
    "executed": true
  }
]
```

### 6. 市场数据

#### GET `/api/market-data`

获取最新市场数据。

**响应示例：**
```json
[
  {
    "symbol": "BTC/USDT",
    "price": 46000.00,
    "volume_24h": 1500000000.00,
    "change_24h": 2.5,
    "high_24h": 46500.00,
    "low_24h": 44800.00,
    "timestamp": "2024-01-01T12:00:00"
  }
]
```

## WebSocket API

### 连接

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('WebSocket连接已建立');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('收到更新:', data);
};
```

### 消息格式

#### 投资组合更新

```json
{
  "type": "portfolio_update",
  "data": {
    "total_balance": 10500.50,
    "cash_balance": 5000.00,
    "positions_value": 5500.50,
    "total_pnl": 500.50,
    "total_trades": 25,
    "win_rate": 0.68,
    "positions": [...]
  },
  "recent_trades": [
    {
      "symbol": "BTC/USDT",
      "side": "buy",
      "price": 46000.00,
      "timestamp": "2024-01-01T12:00:00"
    }
  ],
  "timestamp": "2024-01-01T12:00:00"
}
```

## 错误处理

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

### 常见错误码

- `400` Bad Request - 请求参数错误
- `404` Not Found - 资源不存在
- `500` Internal Server Error - 服务器内部错误
- `503` Service Unavailable - 服务暂时不可用

## 数据模型

### Trade（交易）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | integer | 交易ID |
| timestamp | datetime | 交易时间 |
| symbol | string | 交易对 |
| side | string | 交易方向（buy/sell/short/cover） |
| price | float | 成交价格 |
| amount | float | 交易数量 |
| total_value | float | 交易总价值 |
| ai_model | string | AI模型名称 |
| ai_reasoning | string | AI决策理由 |
| success | boolean | 是否成功 |
| profit_loss | float | 盈亏（可选） |

### Position（持仓）

| 字段 | 类型 | 描述 |
|------|------|------|
| symbol | string | 交易对 |
| amount | float | 持仓数量 |
| average_price | float | 平均成本价 |
| current_price | float | 当前价格 |
| unrealized_pnl | float | 未实现盈亏 |
| position_type | string | 持仓类型（long/short） |

### AIDecision（AI决策）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | integer | 决策ID |
| timestamp | datetime | 决策时间 |
| ai_model | string | AI模型名称 |
| symbol | string | 交易对 |
| decision | string | 决策类型（buy/sell/hold/short/cover） |
| confidence | float | 置信度（0-1） |
| reasoning | string | 决策理由 |
| executed | boolean | 是否已执行 |

## 使用示例

### Python

```python
import requests

# 获取系统状态
response = requests.get('http://localhost:8000/api/status')
print(response.json())

# 获取投资组合
response = requests.get('http://localhost:8000/api/portfolio')
portfolio = response.json()
print(f"总资产: ${portfolio['total_balance']}")

# 获取交易历史
response = requests.get('http://localhost:8000/api/trades?limit=10')
trades = response.json()
for trade in trades:
    print(f"{trade['symbol']}: {trade['side']} @ ${trade['price']}")
```

### JavaScript

```javascript
// 获取投资组合
fetch('http://localhost:8000/api/portfolio')
  .then(response => response.json())
  .then(data => {
    console.log('总资产:', data.total_balance);
    console.log('盈亏:', data.total_pnl);
  });

// WebSocket连接
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  if (update.type === 'portfolio_update') {
    console.log('投资组合更新:', update.data);
  }
};
```

### cURL

```bash
# 获取系统状态
curl http://localhost:8000/api/status

# 获取投资组合
curl http://localhost:8000/api/portfolio

# 获取交易历史
curl "http://localhost:8000/api/trades?limit=5"

# 获取AI决策
curl "http://localhost:8000/api/ai-decisions?limit=10"
```

## 频率限制

当前版本没有频率限制。生产环境建议添加：
- API请求：每分钟60次
- WebSocket连接：每个IP 5个连接

## 版本历史

### v1.0.0 (2024-01-01)
- 初始版本发布
- 支持基础交易功能
- 集成多AI模型
- WebSocket实时推送

## 技术支持

- API文档：http://localhost:8000/docs (Swagger UI)
- ReDoc文档：http://localhost:8000/redoc
- GitHub Issues: [项目地址]
- Email: your-email@example.com

