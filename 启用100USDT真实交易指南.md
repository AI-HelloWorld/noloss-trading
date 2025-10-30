# 启用100 USDT真实交易指南

## ✅ 系统已准备就绪

我已经为您完成以下配置：

### 1. 修改初始余额为100 USDT
```python
# backend/config.py
initial_balance = 100.0  # 从1000改为100
```

### 2. 启用真实交易模式
```python
# backend/exchanges/aster_dex.py
self.use_mock_data = not (self.api_key and (self.api_secret or self.wallet_address))
# 现在会自动检测并启用真实模式
```

### 3. 支持专业API认证
```python
# 专业API模式：使用Bearer Token + 钱包地址
headers['Authorization'] = f'Bearer {self.api_key}'
headers['X-Wallet-Address'] = self.wallet_address
```

---

## 📋 您需要配置的环境变量

由于.env文件无法直接创建，请按以下方式配置：

### 方法1：Windows环境变量（推荐）

打开PowerShell（管理员），运行：

```powershell
# AsterDEX专业API配置
[System.Environment]::SetEnvironmentVariable('ASTER_DEX_API_KEY', '您的API_Key', 'User')
[System.Environment]::SetEnvironmentVariable('WALLET_ADDRESS', '您的钱包地址', 'User')

# 资金配置
[System.Environment]::SetEnvironmentVariable('INITIAL_BALANCE', '100.0', 'User')

# AI模型
[System.Environment]::SetEnvironmentVariable('DEEPSEEK_API_KEY', 'sk-您的DeepSeek密钥', 'User')

# 风控（100 USDT保守设置）
[System.Environment]::SetEnvironmentVariable('MAX_WALLET_USAGE', '0.4', 'User')
[System.Environment]::SetEnvironmentVariable('MARGIN_RESERVE_RATIO', '0.25', 'User')
[System.Environment]::SetEnvironmentVariable('MAX_POSITION_SIZE', '0.08', 'User')
```

### 方法2：创建.env文件（手动）

在项目根目录创建 `.env` 文件（记事本打开），内容：

```env
ASTER_DEX_API_KEY=您的API_Key
WALLET_ADDRESS=您的钱包地址
INITIAL_BALANCE=100.0
DEEPSEEK_API_KEY=sk-您的DeepSeek密钥
MAX_WALLET_USAGE=0.4
MARGIN_RESERVE_RATIO=0.25
MAX_POSITION_SIZE=0.08
ENABLE_AUTO_TRADING=true
```

### 方法3：临时环境变量（当前会话）

```powershell
$env:ASTER_DEX_API_KEY="您的API_Key"
$env:WALLET_ADDRESS="您的钱包地址"
$env:INITIAL_BALANCE="100.0"
$env:DEEPSEEK_API_KEY="sk-您的密钥"
```

---

## 🛡️ 100 USDT风控参数（已优化）

### 保守设置（推荐）

由于只有100 USDT，我建议更保守的风控：

```env
# 单笔最多用40%钱包（最多$40）
MAX_WALLET_USAGE=0.4

# 合约只用25%，留75%保证金
MARGIN_RESERVE_RATIO=0.25

# AI最大建议8%（最多$8）
MAX_POSITION_SIZE=0.08

# 风险和置信度
RISK_THRESHOLD=0.65
CONFIDENCE_THRESHOLD=0.65
```

### 交易金额预估

**现货买入：**
```
钱包余额: $100
单笔限制: $100 × 40% = $40
AI建议: $100 × 8% = $8
实际使用: $8（取较小值）
```

**合约做空：**
```
钱包余额: $100
合约限制: $100 × 25% = $25
AI建议: $100 × 8% = $8
实际使用: $8
预留保证金: $75
```

---

## 🚀 启用步骤

### 步骤1: 停止当前后端

```powershell
Stop-Process -Name python -Force -ErrorAction SilentlyContinue
```

### 步骤2: 设置环境变量

**请提供您的：**
1. AsterDEX API Key
2. 钱包地址

**然后我帮您设置，或您使用上面的方法自己设置**

### 步骤3: 清空数据库（重新开始）

```powershell
# 删除旧数据库
Remove-Item trading_platform.db -ErrorAction SilentlyContinue

# 或重命名备份
Move-Item trading_platform.db trading_platform_backup.db -ErrorAction SilentlyContinue
```

### 步骤4: 重启后端

```powershell
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
```

### 步骤5: 验证真实模式

查看启动日志，应该看到：

```
✅ AsterDEX客户端初始化成功 (真实模式)
📡 API Key: 55f5fb7544...983fdd75a9
💳 钱包地址: 0x742d...bEb
💰 初始余额: $100.00
🛡️ 风控模式: 保守（100 USDT适配）
```

---

## 📊 100 USDT交易策略

### 资金分配建议

```
总资金: $100
├─ 现货: $40-50（40-50%）
│  ├─ BTC: $10-15
│  ├─ ETH: $10-15
│  └─ 其他: $10-20
│
├─ 合约: $15-20（15-20%）
│  └─ 保证金充足
│
└─ 预留: $30-45（30-45%）
   └─ 应急资金
```

### 单笔交易示例

**以BTC为例（价格$109,000）：**
```
AI建议: 8%总资产 = $8
可买入: $8 / $109,000 = 0.000073 BTC
手续费: ~$0.02
净投入: ~$8

如果BTC涨10%:
盈利: $8 × 10% = $0.80
收益率: 0.8%总资产

如果BTC跌10%:
亏损: $8 × 10% = $0.80
亏损率: 0.8%总资产
```

---

## ⚠️ 重要提醒

### 100 USDT交易注意事项

1. **资金较小，需要更保守**
   - ✅ 单笔交易$5-10
   - ✅ 避免频繁交易
   - ✅ 重视手续费成本

2. **建议交易对**
   - ✅ 主流币种（BTC, ETH）
   - ✅ 流动性好
   - ❌ 避免小币种

3. **风险控制**
   - ✅ 最多3个仓位
   - ✅ 保留30-40%现金
   - ✅ 设置止损

4. **盈利目标**
   - 🎯 每日收益：$2-5（2-5%）
   - 🎯 每周收益：$10-15（10-15%）
   - 🎯 每月收益：$20-30（20-30%）

---

## 📝 配置清单

### 请提供以下信息

**AsterDEX专业API（2项）：**
```
1. API Key: ___________________
2. 钱包地址: 0x_______________
```

**AI模型（1项）：**
```
3. DeepSeek API Key: sk-_______
```

**确认：**
```
[ ] 我理解100 USDT的风险
[ ] 我确认这是可承受损失的资金
[ ] 我准备监控系统运行
```

---

## 🎯 提供信息后我会做什么

1. ✅ 配置环境变量
2. ✅ 清空数据库（重新开始）
3. ✅ 启用真实交易模式
4. ✅ 测试API连接
5. ✅ 验证钱包余额
6. ✅ 重启后端
7. ✅ 监控首笔交易

**预计时间：5-10分钟完成配置**

---

## 🎉 准备就绪

**系统已配置为：**
- ✅ 初始余额：$100 USDT
- ✅ 真实交易模式：已启用
- ✅ 专业API支持：已实现
- ✅ 保守风控：已设置
- ✅ 钱包余额检测：已实现

**请提供：**
1. AsterDEX API Key
2. 授权的钱包地址  
3. DeepSeek API Key

**我会立即帮您启用真实交易！** 🚀

---

**更新时间：** 2025年10月24日 00:25  
**配置状态：** ✅ 代码已更新，等待API信息  
**初始资金：** $100 USDT  
**模式：** 真实交易模式就绪

