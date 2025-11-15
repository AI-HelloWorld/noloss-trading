# 🚀 快速设置指南

## 步骤1：配置环境变量

### 创建 `.env` 文件

```bash
# 复制示例文件
cp .env.example .env

# 编辑配置文件
# Windows: notepad .env
# Mac/Linux: nano .env
```

### 必需配置项

#### 1. Aster DEX API密钥（必需）

```bash
ASTER_DEX_API_KEY=你的API密钥
ASTER_DEX_API_SECRET=你的API密钥
```

**获取方式**：
1. 访问 [Aster DEX官网](https://asterdex.com)
2. 注册账号并完成KYC
3. 进入API管理页面
4. 创建新的API密钥
5. 复制密钥并粘贴到`.env`文件

#### 2. AI模型API密钥（至少配置一个）

**选项A：OpenAI GPT-4**（推荐）
```bash
OPENAI_API_KEY=sk-...
```
- 获取地址：https://platform.openai.com/api-keys
- 费用：按使用量计费
- 用途：技术分析、基本面分析、风险管理、投资组合管理

**选项B：DeepSeek**
```bash
DEEPSEEK_API_KEY=...
```
- 获取地址：https://platform.deepseek.com
- 用途：情绪分析

**选项C：Grok**
```bash
GROK_API_KEY=...
```
- 获取地址：https://x.ai
- 用途：新闻分析

> 💡 **提示**：建议配置所有AI模型以获得最佳效果，但只配置OpenAI也可以正常运行。

### 交易配置

```bash
# 初始资金（建议先用小额测试）
INITIAL_BALANCE=1000.0

# 启用自动交易（建议先设置为False观察）
ENABLE_AUTO_TRADING=False
```

## 步骤2：安装依赖

### 后端依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 前端依赖

```bash
cd frontend
npm install
cd ..
```

## 步骤3：启动应用

### 方式一：使用启动脚本（推荐）

**Windows:**
```bash
start.bat
```

**Mac/Linux:**
```bash
chmod +x start.sh
./start.sh
```

### 方式二：手动启动

**启动后端：**
```bash
python run.py
```

**启动前端（新开终端）：**
```bash
cd frontend
npm run dev
```

### 方式三：Docker部署

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 启动成功标志

看到以下信息表示启动成功：
```
🚀 启动AI交易平台...
📊 市场数据更新任务已启动
🤖 后台交易任务已启动
📡 数据广播任务已启动
INFO: Uvicorn running on http://127.0.0.1:8000
```

## 步骤4：访问应用

- **前端界面**：http://localhost:3000
- **后端API**：http://localhost:8000
- **API文档**：http://localhost:8000/docs

### 主要功能模块

访问前端后，你可以看到以下功能：

1. **投资组合概览** - 总资产、盈亏、现金余额
2. **市场行情** - 实时交易对价格、涨跌幅、成交量
3. **AI决策面板** - AI团队分析和决策过程
4. **当前持仓** - 所有持仓实时盈亏
5. **交易历史** - 完整的历史交易记录

## 步骤5：测试系统

### 观察模式（推荐首次使用）

1. 设置 `ENABLE_AUTO_TRADING=False`
2. 启动应用
3. 观察AI团队的分析和决策
4. 检查日志中的决策理由
5. 确认无误后再启用自动交易

### 启用自动交易

1. 确认API密钥正确配置
2. 设置 `ENABLE_AUTO_TRADING=True`
3. 重启应用
4. 实时监控交易执行

## 常见问题

### Q1: API密钥无效

**问题**：启动时提示API密钥错误

**解决**：
1. 检查`.env`文件中的密钥是否正确
2. 确认没有多余的空格或引号
3. 验证API密钥是否过期
4. 检查API服务是否正常

### Q2: 无法连接到Aster DEX

**问题**：交易执行失败

**解决**：
1. 检查网络连接
2. 验证API密钥权限
3. 查看Aster DEX API文档确认端点
4. 检查API调用频率限制

### Q3: AI模型响应超时

**问题**：AI分析失败或超时

**解决**：
1. 检查API密钥额度
2. 增加超时时间
3. 减少并发请求
4. 检查网络状况

### Q4: 数据库错误

**问题**：无法保存交易记录

**解决**：
```bash
# 删除数据库文件重新初始化
rm trading_platform.db
# 重启应用会自动创建新数据库
```

### Q5: 前端无法连接后端

**问题**：前端页面无法加载数据

**解决**：
1. 确认后端已启动（端口8000）
2. 检查CORS配置
3. 查看浏览器控制台错误
4. 确认防火墙未阻止连接

## 安全建议

### ✅ 应该做的

- ✅ 使用`.env`文件存储敏感信息
- ✅ 定期轮换API密钥
- ✅ 先用小额资金测试
- ✅ 启用HTTPS（生产环境）
- ✅ 定期备份数据库
- ✅ 监控交易日志

### ❌ 不应该做的

- ❌ 将`.env`文件提交到Git
- ❌ 在公共场合分享API密钥
- ❌ 不测试就投入大额资金
- ❌ 忽视风险警告
- ❌ 在不安全的网络使用

## 性能优化

### 提高响应速度

```bash
# .env 配置
DATA_UPDATE_INTERVAL=30  # 减少数据更新间隔
TRADE_CHECK_INTERVAL=180  # 减少交易检查间隔（但不要太频繁）
```

### 减少API调用成本

```bash
# .env 配置
TRADE_CHECK_INTERVAL=600  # 增加交易检查间隔
CONFIDENCE_THRESHOLD=0.7  # 提高置信度阈值，减少交易次数
```

## 下一步

配置完成后，建议阅读：

1. 📚 [多智能体系统文档](MULTI_AGENT_SYSTEM.md) - 了解AI团队如何工作
2. 📖 [API文档](API_DOCUMENTATION.md) - 了解API接口
3. 🚀 [部署指南](DEPLOYMENT.md) - 部署到生产环境
4. 🤝 [贡献指南](CONTRIBUTING.md) - 参与项目开发

## 获取帮助

- 📖 查看文档：[README.md](README.md)
- 🐛 报告问题：[GitHub Issues](https://github.com/AI-HelloWorld/-Ai-Trading/issues)
- 💬 在线交流：提交Issue或讨论

---

**祝交易顺利！🚀**

