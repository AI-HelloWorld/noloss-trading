# 更新日志

所有重要的项目变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布]

### 计划添加
- 更多AI模型集成（Claude、Gemini等）
- 回测功能
- 策略编辑器
- 多用户支持
- 移动端应用
- 接入真实的情绪API和新闻API

## [1.1.0] - 2024-10-22

### 🎉 重大升级：多智能体协同决策系统

#### 新增
- 🤖 **6位AI专家团队协同决策**
  - 技术分析师：分析技术指标和图表形态
  - 情绪分析师：监测社交媒体和市场情绪
  - 新闻分析师：追踪全球新闻和宏观经济
  - 基本面分析师：评估代币内在价值
  - 风险管理经理：评估风险并拥有否决权
  - 投资组合经理：综合决策并批准/拒绝交易

- 📊 **前端新增团队面板**
  - 实时展示各分析师状态
  - 显示决策流程和协同机制

- 📚 **新增文档**
  - MULTI_AGENT_SYSTEM.md：详细介绍多智能体系统架构

#### 改进
- ⚡ **更专业的决策流程**：从简单投票升级到分层决策
- 🛡️ **增强风险控制**：专门的风险管理经理监控风险
- 📈 **更好的可解释性**：每个决策可追溯到具体分析师
- 🎯 **专业化分工**：每个智能体专注自己的领域

#### 技术改进
- 新增 `backend/agents/` 模块
- 重构交易引擎以使用多智能体团队
- 更新API端点支持团队状态查询
- 前端增加团队可视化组件

### 优势对比
**之前**：3个AI模型简单投票  
**现在**：6位专家分工协作，层次化决策

## [1.0.0] - 2024-10-22

### 新增
- 🎉 首次发布
- 🧠 集成多个AI模型（GPT-4、DeepSeek、Grok）
- 📊 实时可视化仪表板
- 💹 完整的交易功能（买入、卖出、做空、平仓）
- 🤖 AI共识决策系统
- 📈 投资组合历史追踪
- 🔄 WebSocket实时数据推送
- 📋 交易历史记录
- 🎯 AI决策分析面板
- 🐳 Docker部署支持
- 📚 完整的文档和部署指南

### 技术栈
- 后端：FastAPI + SQLAlchemy + APScheduler
- 前端：React 18 + Tailwind CSS + Recharts
- AI：OpenAI GPT-4 + DeepSeek + Grok
- 部署：Docker + Docker Compose + Nginx

### API端点
- GET `/api/status` - 系统状态
- GET `/api/portfolio` - 投资组合
- GET `/api/trades` - 交易历史
- GET `/api/portfolio-history` - 历史数据
- GET `/api/ai-decisions` - AI决策记录
- GET `/api/market-data` - 市场数据
- WS `/ws` - WebSocket实时推送

## 版本说明

### 主版本 (Major)
当进行不兼容的API更改时

### 次版本 (Minor)
当以向后兼容的方式添加功能时

### 修订版本 (Patch)
当进行向后兼容的错误修复时

