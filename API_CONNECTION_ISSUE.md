# AsterDEX API连接问题

## 当前状态

✅ **配置成功**:
- API密钥已加载: `55f5fb7544...983fdd75a9`
- API密钥已加载: `18b6ab6225...50a9a065`
- 系统已切换到真实模式

❌ **连接失败**:
- 无法连接到: `https://api.asterdex.com:443`
- 错误: `Cannot connect to host api.asterdex.com:443`

## 可能的原因

1. **API端点URL不正确**
   - 当前配置: `https://api.asterdex.com`
   - 可能需要：
     - `https://api.aster-dex.com`
     - `https://asterdex.io/api`
     - `https://trade.asterdex.com`
     - 其他自定义端点

2. **网络问题**
   - DNS解析失败
   - 需要VPN访问
   - 防火墙阻止

3. **API文档**
   - 需要查看官方API文档确认正确的端点

## 需要的信息

请提供以下信息以修复连接问题：

### 1. AsterDEX API端点URL
例如：
```
https://api.aster-dex.com
https://asterdex.io/api/v1
https://trade.asterdex.com/api
```

### 2. API文档链接
如果有官方API文档，请提供链接。

### 3. 测试API连接
您可以尝试在浏览器或Postman中访问：
```
https://api.asterdex.com/api/v1/symbols
https://api.asterdex.com/api/v1/ticker/BTC_USDT
```

## 临时解决方案

在获得正确的API端点之前，系统会在API请求失败时：
1. 记录错误
2. 返回空数据
3. 使用默认的交易对列表

这样可以确保系统继续运行，但不会进行实际交易。

## 修改API端点

找到正确的端点后，修改 `backend/exchanges/aster_dex.py` 第21行：

```python
self.base_url = "https://正确的api端点"
```

然后重启后端服务。

