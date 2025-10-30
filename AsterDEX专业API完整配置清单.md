# AsterDEX专业API完整配置清单

## 📋 完整配置项列表

### AsterDEX专业API需要的所有配置

我已经为您准备了完整的配置模板，包含以下AsterDEX专业API配置项：

---

## 🔑 1. API认证配置（必需）

### ASTER_DEX_API_KEY
```env
ASTER_DEX_API_KEY=您的API_Key
```
- **用途：** API身份验证
- **获取位置：** https://www.asterdex.com/zh-CN/api-management
- **格式：** 64位字符串
- **权限要求：** 读取账户、交易（不含提现）

### ASTER_DEX_API_SECRET
```env
ASTER_DEX_API_SECRET=您的API_Secret
```
- **用途：** API请求签名
- **获取位置：** 创建API Key时一起生成
- **格式：** 64位字符串
- **⚠️ 注意：** 只显示一次，必须立即保存

### ASTER_DEX_BASE_URL
```env
ASTER_DEX_BASE_URL=https://fapi.asterdex.com
```
- **用途：** API端点URL
- **默认值：** https://fapi.asterdex.com（期货API）
- **可选值：**
  - `https://fapi.asterdex.com` - 期货API（支持做空）
  - `https://api.asterdex.com` - 现货API（只做多）

---

## 💳 2. 钱包配置（必需）

### WALLET_ADDRESS
```env
WALLET_ADDRESS=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
```
- **用途：** API授权的钱包地址
- **获取位置：** https://www.asterdex.com/zh-CN/api-wallet
- **格式：** 0x开头的以太坊地址格式
- **⚠️ 重要步骤：**
  1. 在API钱包页面创建/选择钱包
  2. 点击"授权"按钮
  3. 确认授权后复制地址
  4. 未授权的地址无法通过API交易

### INITIAL_BALANCE
```env
INITIAL_BALANCE=500.0
```
- **用途：** 系统使用的初始交易资金
- **建议：** 不超过钱包实际USDT余额
- **首次测试：** $100-$500
- **正式交易：** $1,000+

---

## 🛡️ 3. 风控配置（强烈建议）

### MAX_WALLET_USAGE
```env
MAX_WALLET_USAGE=0.5
```
- **用途：** 单笔交易最多使用钱包余额的比例
- **默认：** 0.5（50%）
- **保守：** 0.3（30%）
- **激进：** 0.7（70%）

### MARGIN_RESERVE_RATIO
```env
MARGIN_RESERVE_RATIO=0.3
```
- **用途：** 合约交易保证金预留比例
- **默认：** 0.3（用30%，留70%保证金）
- **保守：** 0.2（用20%，留80%保证金）
- **激进：** 0.5（用50%，留50%保证金）

### MAX_POSITION_SIZE
```env
MAX_POSITION_SIZE=0.1
```
- **用途：** AI建议的最大单笔仓位
- **默认：** 0.1（10%总资产）
- **保守：** 0.05（5%）
- **激进：** 0.15（15%）

---

## 🤖 4. AI模型配置（必需）

### DEEPSEEK_API_KEY
```env
DEEPSEEK_API_KEY=sk-your-deepseek-key
```
- **用途：** AI分析师团队（7个分析师）
- **获取：** https://platform.deepseek.com/api_keys
- **必需：** 系统运行必需

---

## 📝 完整配置示例

### 真实交易完整配置

```env
# ====================================================
# AsterDEX专业API配置
# ====================================================
ASTER_DEX_BASE_URL=https://fapi.asterdex.com
ASTER_DEX_API_KEY=55f5fb7544a1b2c3d4e5f6789abc123def
ASTER_DEX_API_SECRET=abc123def456ghi789jkl012mno345pqr
WALLET_ADDRESS=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
INITIAL_BALANCE=500.0

# ====================================================
# AI模型
# ====================================================
DEEPSEEK_API_KEY=sk-your-actual-deepseek-key

# ====================================================
# 风控（保守设置，首次推荐）
# ====================================================
MAX_WALLET_USAGE=0.3
MARGIN_RESERVE_RATIO=0.2
MAX_POSITION_SIZE=0.05
RISK_THRESHOLD=0.6
CONFIDENCE_THRESHOLD=0.7

# ====================================================
# 交易
# ====================================================
ENABLE_AUTO_TRADING=true
TRADE_CHECK_INTERVAL=300
DATA_UPDATE_INTERVAL=60
```

---

## ✅ 配置完整性检查

### 必需配置项（5项）

| 配置项 | 状态 | 说明 |
|--------|------|------|
| ASTER_DEX_BASE_URL | ✅ 已添加 | API端点URL |
| ASTER_DEX_API_KEY | ⚠️ 需填写 | 从AsterDEX获取 |
| ASTER_DEX_API_SECRET | ⚠️ 需填写 | 从AsterDEX获取 |
| WALLET_ADDRESS | ⚠️ 需填写 | 必须先授权 |
| DEEPSEEK_API_KEY | ⚠️ 需填写 | AI模型必需 |

### 推荐配置项（风控）

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| MAX_WALLET_USAGE | 0.5 | ✅ 已设置 |
| MARGIN_RESERVE_RATIO | 0.3 | ✅ 已设置 |
| MAX_POSITION_SIZE | 0.1 | ✅ 已设置 |
| RISK_THRESHOLD | 0.7 | ✅ 已设置 |

---

## 🔍 配置验证命令

### 验证配置完整性

```bash
# 运行测试脚本
python test_wallet_connection.py
```

**检查输出：**
```
✅ API Key: 55f5fb7544...983fdd75a9
✅ API Secret: ********************
✅ Base URL: https://fapi.asterdex.com  ← 新增
✅ 钱包地址: 0x742d...bEb              ← 新增
✅ 模式: 真实模式
```

---

## 📊 当前配置状态

### 已完成

✅ **配置模板创建**
- 真实交易配置模板.env
- 包含所有必需项
- 详细注释说明

✅ **配置项完善**
- ASTER_DEX_BASE_URL（API端点）
- ASTER_DEX_API_KEY（身份验证）
- ASTER_DEX_API_SECRET（签名）
- WALLET_ADDRESS（授权钱包）

✅ **代码支持**
- config.py支持所有配置
- aster_dex.py读取配置
- 钱包地址验证

✅ **测试脚本**
- test_wallet_connection.py
- 完整验证流程

### 待完成

⚠️ **需要您提供：**
1. AsterDEX API Key
2. AsterDEX API Secret
3. 授权的钱包地址
4. DeepSeek API Key（如果还没配置）

---

## 🎯 AsterDEX专业API配置总结

### 当前已包含的配置

```
✅ ASTER_DEX_BASE_URL      - API端点URL（新增）
✅ ASTER_DEX_API_KEY       - API密钥
✅ ASTER_DEX_API_SECRET    - API签名密钥
✅ WALLET_ADDRESS          - API授权钱包地址（新增）
✅ 风控参数                - 完整的风控配置
✅ AI配置                  - DeepSeek等AI模型
✅ 交易配置                - 自动交易、频率等
```

### 配置文件位置

**主配置模板：** `真实交易配置模板.env`

**包含：**
- 🔑 完整的AsterDEX专业API配置
- 💳 钱包地址配置
- 🛡️ 风控参数
- 🤖 AI模型配置
- ⚙️ 交易参数

---

## 🎉 配置已完善

**AsterDEX专业API配置项：**

✅ **API端点URL** - 已添加（ASTER_DEX_BASE_URL）  
✅ **API Key** - 已准备（需填写）  
✅ **API Secret** - 已准备（需填写）  
✅ **钱包地址** - 已准备（需授权后填写）  
✅ **风控参数** - 已设置  
✅ **测试脚本** - 已创建  

**现在配置已经完整，等待您填写API信息！** 🚀

---

**填写步骤：**
1. 打开：`真实交易配置模板.env`
2. 填写必需的4项配置
3. 保存为：`.env`
4. 运行测试：`python test_wallet_connection.py`
5. 告诉我结果

我随时准备帮您启用真实交易！
