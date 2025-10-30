# 🤖 AI加密货币自主交易平台

这是一个完全自主的AI驱动加密货币交易平台，集成多个先进AI模型（GPT、DeepSeek、Grok）进行智能交易决策，实时展示交易过程、盈亏和AI分析。

## ✨ 功能特性

### 核心功能
- 🤖 **多智能体协同系统**：模拟专业投资团队，6位AI专家协同决策
- 🎯 **分工明确的分析师团队**：
  - 📊 **技术分析师**：利用MACD、RSI等技术指标分析价格走势
  - 💭 **情绪分析师**：分析社交媒体和市场情绪
  - 📰 **新闻分析师**：监控全球新闻和宏观经济
  - 🏛️ **基本面分析师**：评估代币内在价值
  - 🛡️ **风险管理经理**：评估风险并设置风控参数
  - 👔 **投资组合经理**：综合决策，批准/拒绝交易
- 📊 **实时可视化**：实时展示投资组合、交易历史和团队分析过程
- 💹 **全方位交易**：支持买入、卖出、做空、平仓等全部交易类型
- ⚡ **自动化交易**：7x24小时自动运行，无需人工干预
- 📈 **数据分析**：完整的历史数据记录和可视化图表
- 🔄 **实时更新**：WebSocket实时推送交易数据

### 交易能力
- ✅ 支持所有Aster DEX上的交易对
- ✅ 支持做多和做空交易
- ✅ 智能仓位管理
- ✅ 风险控制机制
- ✅ 止损止盈策略

### 可视化展示
- 💰 总资产、盈亏、现金余额实时展示
- 📉 投资组合历史趋势图表
- 📋 完整的交易历史记录
- 🧩 AI决策分析面板
- 📊 当前持仓一览表

## 🏗️ 技术架构

### 后端技术栈
- **FastAPI**: 高性能异步API框架
- **SQLAlchemy**: ORM数据库管理
- **APScheduler**: 定时任务调度
- **WebSocket**: 实时数据推送
- **Loguru**: 日志管理

### 前端技术栈
- **React 18**: 现代化UI框架
- **Recharts**: 数据可视化图表
- **Tailwind CSS**: 现代化样式设计
- **Axios**: HTTP客户端
- **Lucide React**: 图标库

### AI集成
- **OpenAI GPT-4**: 先进的语言模型
- **DeepSeek**: 中国领先AI模型
- **Grok**: X.AI的先进模型

### 交易所集成
- **Aster DEX**: 去中心化交易所API

## 📦 快速开始

### 前置要求
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose（可选）

### 方式一：Docker部署（推荐）

1. **克隆项目**
```bash
git clone <repository-url>
cd ai-trading-platform
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑.env文件，填入你的API密钥
```

3. **启动服务**
```bash
docker-compose up -d
```

4. **访问平台**
```
http://localhost:8000
```

### 方式二：本地开发部署

#### 后端启动

1. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
cp .env.example .env
# 编辑.env文件
```

4. **启动后端**
```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端启动

1. **安装依赖**
```bash
cd frontend
npm install
```

2. **启动开发服务器**
```bash
npm run dev
```

3. **访问应用**
```
http://localhost:3000
```

## ⚙️ 配置说明

### 必需配置

在`.env`文件中配置以下必需项：

```bash
# Aster DEX API
ASTER_DEX_API_KEY=your_api_key
ASTER_DEX_API_SECRET=your_api_secret

# AI模型API密钥（至少配置一个）
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=your_key
GROK_API_KEY=your_key
```

### 可选配置

```bash
# 交易配置
INITIAL_BALANCE=10000.0        # 初始资金
MAX_POSITION_SIZE=0.1           # 最大单笔仓位（10%）
RISK_PER_TRADE=0.02             # 单笔风险比例（2%）
ENABLE_AUTO_TRADING=True        # 启用自动交易

# 更新频率
DATA_UPDATE_INTERVAL=60         # 数据更新间隔（秒）
TRADE_CHECK_INTERVAL=300        # 交易检查间隔（秒）
```

## 🚀 生产部署

### 1. 服务器部署

```bash
# 1. 拉取代码
git clone <repository-url>
cd ai-trading-platform

# 2. 配置环境变量
cp .env.example .env
nano .env  # 编辑配置

# 3. 使用Docker Compose部署
docker-compose up -d

# 4. 查看日志
docker-compose logs -f
```

### 2. 配置域名和HTTPS

1. 修改`nginx.conf`中的`server_name`
2. 获取SSL证书（Let's Encrypt推荐）
3. 将证书放置在`ssl/`目录
4. 取消注释nginx.conf中的HTTPS配置
5. 重启服务：`docker-compose restart nginx`

### 3. 监控和维护

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f trading-platform

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 更新部署
git pull
docker-compose up -d --build
```

## 📊 使用指南

### 主要功能模块

1. **投资组合概览**
   - 总资产、盈亏、现金余额实时显示
   - 交易统计和胜率展示

2. **投资组合图表**
   - 历史总资产和盈亏趋势
   - 支持30天数据回溯

3. **AI决策面板**
   - 实时展示AI分析结果
   - 显示决策类型、置信度和理由
   - 标记已执行的决策

4. **当前持仓**
   - 展示所有当前持仓
   - 实时盈亏计算
   - 区分做多/做空仓位

5. **交易历史**
   - 完整的历史交易记录
   - 交易详情和AI决策依据

## 🔒 安全建议

1. **API密钥管理**
   - 不要将`.env`文件提交到Git
   - 使用环境变量或密钥管理服务
   - 定期轮换API密钥

2. **访问控制**
   - 建议配置防火墙规则
   - 使用HTTPS加密传输
   - 考虑添加身份认证（如需要）

3. **资金安全**
   - 初期使用小额资金测试
   - 设置合理的风险参数
   - 定期检查交易记录

4. **监控告警**
   - 设置服务健康监控
   - 配置异常交易告警
   - 记录审计日志

## 🛠️ 开发指南

### 项目结构

```
ai-trading-platform/
├── backend/                 # 后端代码
│   ├── ai/                 # AI模型模块
│   │   ├── base_model.py   # AI模型基类
│   │   ├── gpt_model.py    # GPT模型实现
│   │   ├── deepseek_model.py
│   │   ├── grok_model.py
│   │   └── ai_manager.py   # AI管理器
│   ├── exchanges/          # 交易所接口
│   │   └── aster_dex.py    # Aster DEX客户端
│   ├── trading/            # 交易引擎
│   │   └── trading_engine.py
│   ├── config.py           # 配置管理
│   ├── database.py         # 数据库模型
│   └── main.py             # FastAPI应用
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── components/     # React组件
│   │   ├── services/       # API服务
│   │   ├── App.jsx         # 主应用
│   │   └── main.jsx        # 入口文件
│   ├── package.json
│   └── vite.config.js
├── requirements.txt        # Python依赖
├── Dockerfile             # Docker配置
├── docker-compose.yml     # Docker Compose配置
├── nginx.conf             # Nginx配置
└── README.md              # 项目文档
```

### 添加新的AI模型

1. 在`backend/ai/`创建新模型文件
2. 继承`BaseAIModel`类
3. 实现`analyze_market`方法
4. 在`ai_manager.py`中注册模型

### 添加新的交易所

1. 在`backend/exchanges/`创建新客户端
2. 实现标准交易接口
3. 在`trading_engine.py`中集成

## 📝 API文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要API端点

- `GET /api/status` - 系统状态
- `GET /api/portfolio` - 投资组合信息
- `GET /api/trades` - 交易历史
- `GET /api/portfolio-history` - 投资组合历史
- `GET /api/ai-decisions` - AI决策记录
- `GET /api/market-data` - 市场数据
- `WS /ws` - WebSocket实时推送

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## ⚠️ 免责声明

本平台仅供学习和研究使用。加密货币交易存在高风险，可能导致资金损失。使用本平台进行实际交易需自行承担风险。开发者不对任何交易损失负责。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- GitHub Issues
- Email: eternalaie3a@gmail.com
- X:https://x.com/Qubyt_E3A

## 🙏 致谢

- OpenAI、DeepSeek、X.AI提供的优秀AI模型
- Aster DEX提供的交易API
- 所有开源项目贡献者

---

**祝交易顺利！🚀**

