# 贡献指南

感谢您对AI加密货币交易平台的关注！我们欢迎所有形式的贡献。

## 如何贡献

### 报告Bug

在提交Bug报告前，请先搜索已有的Issues，避免重复。

提交Bug时，请包含：
1. **详细描述**：问题的完整描述
2. **复现步骤**：如何重现这个问题
3. **期望行为**：应该发生什么
4. **实际行为**：实际发生了什么
5. **环境信息**：
   - 操作系统
   - Python版本
   - Node.js版本
   - 其他相关信息

### 提出新功能

我们欢迎新功能建议！请创建Issue并说明：
1. 功能描述
2. 使用场景
3. 预期效果
4. 可能的实现方案

### 提交代码

#### 开发流程

1. **Fork项目**
```bash
# 在GitHub上Fork项目
# 克隆你的Fork
git clone https://github.com/your-username/ai-trading-platform.git
cd ai-trading-platform
```

2. **创建分支**
```bash
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/your-bug-fix
```

3. **开发和测试**
```bash
# 安装依赖
pip install -r requirements.txt
cd frontend && npm install

# 运行测试
pytest
npm test

# 代码格式化
black backend/
prettier --write frontend/src/
```

4. **提交代码**
```bash
git add .
git commit -m "feat: 添加新功能"
# 或
git commit -m "fix: 修复某个bug"
```

5. **推送并创建PR**
```bash
git push origin feature/your-feature-name
# 在GitHub上创建Pull Request
```

#### 提交信息规范

我们遵循[Conventional Commits](https://www.conventionalcommits.org/)规范：

- `feat:` 新功能
- `fix:` Bug修复
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建/工具链更新

示例：
```
feat: 添加新的AI模型集成
fix: 修复交易执行时的价格计算错误
docs: 更新API文档
```

#### 代码规范

**Python代码**
- 遵循[PEP 8](https://pep8.org/)规范
- 使用`black`格式化代码
- 使用`pylint`检查代码质量
- 添加类型注解（Type Hints）
- 编写文档字符串（Docstrings）

```python
def calculate_position_size(
    balance: float, 
    risk_percentage: float,
    stop_loss: float
) -> float:
    """
    计算仓位大小
    
    Args:
        balance: 账户余额
        risk_percentage: 风险比例
        stop_loss: 止损价格
    
    Returns:
        建议的仓位大小
    """
    # 实现代码
    pass
```

**JavaScript/React代码**
- 使用ES6+语法
- 使用`prettier`格式化代码
- 遵循React最佳实践
- 使用函数式组件和Hooks
- 添加PropTypes或TypeScript类型

```javascript
/**
 * 投资组合卡片组件
 * @param {Object} props - 组件属性
 * @param {Object} props.portfolioData - 投资组合数据
 */
const PortfolioCard = ({ portfolioData }) => {
  // 组件实现
}
```

#### 测试

**后端测试**
```python
# tests/test_trading_engine.py
import pytest
from backend.trading.trading_engine import TradingEngine

def test_position_calculation():
    engine = TradingEngine()
    result = engine.calculate_position_size(10000, 0.02, 0.05)
    assert result > 0
```

**前端测试**
```javascript
// frontend/src/components/__tests__/PortfolioCard.test.jsx
import { render, screen } from '@testing-library/react'
import PortfolioCard from '../PortfolioCard'

test('renders portfolio balance', () => {
  render(<PortfolioCard portfolioData={mockData} />)
  expect(screen.getByText(/总资产/i)).toBeInTheDocument()
})
```

### 文档贡献

文档同样重要！你可以：
- 改进现有文档
- 翻译文档
- 添加教程和示例
- 修正拼写/语法错误

## 项目结构

```
ai-trading-platform/
├── backend/              # 后端代码
│   ├── ai/              # AI模型
│   ├── exchanges/       # 交易所接口
│   ├── trading/         # 交易引擎
│   ├── config.py        # 配置
│   ├── database.py      # 数据库
│   └── main.py          # 主应用
├── frontend/            # 前端代码
│   └── src/
│       ├── components/  # React组件
│       └── services/    # API服务
├── tests/               # 测试代码
├── docs/                # 文档
└── requirements.txt     # Python依赖
```

## 开发环境设置

### 后端开发

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖

# 配置环境变量
cp .env.example .env
# 编辑.env

# 启动开发服务器
python -m uvicorn backend.main:app --reload
```

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 发布流程

1. 更新版本号（`backend/__init__.py`, `frontend/package.json`）
2. 更新CHANGELOG.md
3. 创建Git标签
4. 发布到GitHub Releases
5. 更新文档

## 行为准则

### 我们的承诺

为了营造开放和友好的环境，我们承诺：
- 使用友好和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

### 不可接受的行为

- 使用性化的语言或图像
- 挑衅、侮辱或贬损的评论
- 公开或私下的骚扰
- 未经许可发布他人的私人信息
- 其他不道德或不专业的行为

## 获取帮助

- 查看[README.md](README.md)
- 阅读[API文档](API_DOCUMENTATION.md)
- 查看[部署指南](DEPLOYMENT.md)
- 在Issues中提问
- 发送邮件：your-email@example.com

## 许可证

通过贡献，您同意您的贡献将按照MIT许可证授权。

## 致谢

感谢所有贡献者！

- 查看[贡献者列表](https://github.com/your-repo/graphs/contributors)

