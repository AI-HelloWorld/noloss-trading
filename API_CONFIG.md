# API配置说明

## 必需的API配置

### 1. DEEPSEEK API
- 访问: https://platform.deepseek.com/
- 获取API密钥
- 在.env文件中设置: `DEEPSEEK_API_KEY=your_key_here`

### 2. ASTER DEX API
- 访问: https://asterdex.com/
- 获取API密钥和密钥
- 在.env文件中设置:
  ```
  ASTER_DEX_API_KEY=your_api_key_here
  ASTER_DEX_API_SECRET=your_api_secret_here
  ```

## 配置步骤

1. 复制 `.env.example` 到 `.env`
2. 填入你的API密钥
3. 运行测试脚本: `python config_api.py`

## 测试API连接

```bash
# 测试所有API
python config_api.py

# 只测试DEEPSEEK
python -c "import asyncio; from config_api import test_deepseek_api; asyncio.run(test_deepseek_api())"

# 只测试ASTER
python -c "import asyncio; from config_api import test_aster_api; asyncio.run(test_aster_api())"
```

## 注意事项

- 确保API密钥有效且有足够权限
- ASTER DEX目前使用模拟数据模式
- 所有交易都是模拟的，不会产生真实资金损失
