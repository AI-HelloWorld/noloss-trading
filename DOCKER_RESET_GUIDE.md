# Docker容器内重置盈亏计算指南

**更新时间**: 2025-10-24  
**功能**: 在Docker容器内重置和验证盈亏计算

---

## 🚀 快速开始

### 方法1: 使用便捷脚本 (推荐)

#### Windows用户
```bash
# 运行带重置功能的启动脚本
start_with_reset.bat
```

#### Linux用户
```bash
# 运行带重置功能的启动脚本
./start_with_reset.sh
```

### 方法2: 使用Docker Compose命令

#### 仅重置盈亏数据
```bash
# 运行重置服务
docker-compose --profile reset up reset-pnl
```

#### 验证计算结果
```bash
# 在容器内运行验证脚本
docker-compose run --rm backend python test_pnl_fix.py
```

#### 进入容器手动操作
```bash
# 进入后端容器
docker-compose exec backend bash

# 在容器内运行重置脚本
python reset_pnl_calculation.py

# 在容器内运行验证脚本
python test_pnl_fix.py
```

---

## 📁 文件结构

### 新增文件
```
├── docker_reset_pnl.sh          # Linux重置脚本
├── docker_reset_pnl.bat         # Windows重置脚本
├── start_with_reset.sh          # Linux启动脚本
├── start_with_reset.bat         # Windows启动脚本
└── DOCKER_RESET_GUIDE.md        # 本指南
```

### 修改文件
```
├── backend/Dockerfile            # 添加重置脚本
├── docker-compose.yml           # 添加重置服务
└── reset_pnl_calculation.py     # 重置脚本
```

---

## 🔧 Docker配置详情

### Dockerfile更新
```dockerfile
# 复制重置脚本
COPY reset_pnl_calculation.py ./
COPY test_pnl_fix.py ./

# 设置重置脚本为可执行
RUN chmod +x reset_pnl_calculation.py test_pnl_fix.py
```

### Docker Compose服务
```yaml
# 重置盈亏计算服务（一次性运行）
reset-pnl:
  build:
    context: .
    dockerfile: backend/Dockerfile
  container_name: ai-trading-reset-pnl
  volumes:
    - ./data:/app/data
    - ./.env:/app/.env
  environment:
    - PYTHONUNBUFFERED=1
  command: ["python", "reset_pnl_calculation.py"]
  networks:
    - ai-trading-network
  profiles:
    - reset
```

---

## 📋 使用场景

### 1. 首次部署
```bash
# 重置数据并启动服务
start_with_reset.bat
# 选择选项 2: 重置盈亏后启动
```

### 2. 数据异常时
```bash
# 仅重置数据
docker-compose --profile reset up reset-pnl
```

### 3. 验证计算
```bash
# 验证计算结果
docker-compose run --rm backend python test_pnl_fix.py
```

### 4. 开发调试
```bash
# 进入容器调试
docker-compose exec backend bash
python reset_pnl_calculation.py
python test_pnl_fix.py
```

---

## 🔍 验证结果

### 成功输出示例
```
📊 当前投资组合状态:
  总余额: $100.00
  现金余额: $100.00
  持仓价值: $0.00
  总盈亏: $0.00
  盈亏百分比: +0.00%
  初始余额: $100.00
  总交易次数: 0
  胜率: 0.0%

🔍 验证结果:
  总余额计算: ✅ 正确
  现金余额计算: ✅ 正确
  盈亏百分比计算: ✅ 正确
🎉 所有计算都正确！
```

---

## ⚠️ 注意事项

### 1. 数据备份
- 重置前建议备份数据库文件
- 数据库文件位置: `./data/trading_platform.db`

### 2. 服务状态
- 重置过程中后端服务会停止
- 重置完成后需要重启服务
- 使用 `docker-compose restart backend` 重启

### 3. 权限问题
- 确保 `./data` 目录有写权限
- 确保 `.env` 文件存在且可读

### 4. 网络问题
- 确保Docker网络正常
- 确保数据库连接正常

---

## 🐛 故障排除

### 问题1: 重置脚本找不到
```bash
# 检查文件是否存在
docker-compose exec backend ls -la /app/reset_pnl_calculation.py

# 重新构建镜像
docker-compose build backend
```

### 问题2: 数据库连接失败
```bash
# 检查数据库文件权限
ls -la ./data/

# 检查环境变量
docker-compose exec backend env | grep DATABASE
```

### 问题3: 重置后数据异常
```bash
# 重新运行验证脚本
docker-compose run --rm backend python test_pnl_fix.py

# 检查日志
docker-compose logs backend
```

---

## 📞 技术支持

如果遇到问题，请检查：

1. **Docker状态**: `docker-compose ps`
2. **容器日志**: `docker-compose logs backend`
3. **数据库文件**: `ls -la ./data/`
4. **环境变量**: `cat .env`

---

**创建时间**: 2025-10-24  
**版本**: v1.0  
**状态**: ✅ 已测试
