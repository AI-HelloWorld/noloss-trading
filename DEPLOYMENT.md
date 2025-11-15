# 部署指南

## 生产环境部署步骤

### 1. 服务器准备

#### 推荐配置
- **操作系统**: Ubuntu 20.04+ / CentOS 8+
- **内存**: 最少2GB，推荐4GB+
- **CPU**: 2核心+
- **硬盘**: 20GB+
- **网络**: 稳定的互联网连接

#### 安装Docker和Docker Compose

```bash
# Ubuntu
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker

# 将当前用户添加到docker组
sudo usermod -aG docker $USER
```

### 2. 部署步骤

#### 步骤1: 克隆代码

```bash
git clone <your-repository-url>
cd ai-trading-platform
```

#### 步骤2: 配置环境变量

```bash
cp .env.example .env
nano .env
```

必须配置的项目：
```bash
# Aster DEX API（必需）
ASTER_DEX_API_KEY=your_actual_key_here
ASTER_DEX_API_SECRET=your_actual_secret_here

# 至少配置一个AI模型API（推荐配置所有）
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=...
GROK_API_KEY=...

# 交易配置
INITIAL_BALANCE=10000.0
ENABLE_AUTO_TRADING=True
```

#### 步骤3: 构建和启动

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

#### 步骤4: 验证部署

```bash
# 检查服务状态
docker-compose ps

# 测试API
curl http://localhost:8000/api/status

# 检查健康状态
docker-compose ps | grep healthy
```

### 3. 配置域名和HTTPS

#### 获取SSL证书（Let's Encrypt）

```bash
# 安装certbot
sudo apt-get install certbot

# 获取证书
sudo certbot certonly --standalone -d your-domain.com

# 证书位置
# /etc/letsencrypt/live/your-domain.com/fullchain.pem
# /etc/letsencrypt/live/your-domain.com/privkey.pem
```

#### 配置SSL

```bash
# 创建ssl目录
mkdir ssl

# 复制证书
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/key.pem
sudo chown $USER:$USER ssl/*

# 编辑nginx.conf
nano nginx.conf
# 取消注释HTTPS配置部分
# 修改server_name为你的域名

# 重启nginx
docker-compose restart nginx
```

### 4. 设置自动续期证书

```bash
# 创建续期脚本
cat > renew-cert.sh << 'EOF'
#!/bin/bash
certbot renew --quiet
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/key.pem
docker-compose restart nginx
EOF

chmod +x renew-cert.sh

# 添加到crontab（每月1号执行）
(crontab -l 2>/dev/null; echo "0 0 1 * * /path/to/renew-cert.sh") | crontab -
```

### 5. 监控和日志

#### 查看日志

```bash
# 实时查看所有日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f trading-platform

# 查看最近100行
docker-compose logs --tail=100 trading-platform
```

#### 监控磁盘空间

```bash
# 清理旧日志
cd logs
find . -name "*.log" -mtime +30 -delete

# 清理Docker未使用的资源
docker system prune -a
```

### 6. 备份策略

#### 自动备份脚本

```bash
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/ai-trading"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
docker exec ai-trading-platform sqlite3 /app/data/trading_platform.db ".backup /app/data/backup_$DATE.db"
docker cp ai-trading-platform:/app/data/backup_$DATE.db $BACKUP_DIR/

# 备份日志
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz logs/

# 删除30天前的备份
find $BACKUP_DIR -mtime +30 -delete

echo "Backup completed: $DATE"
EOF

chmod +x backup.sh

# 添加到crontab（每天凌晨2点）
(crontab -l 2>/dev/null; echo "0 2 * * * /path/to/backup.sh") | crontab -
```

### 7. 性能优化

#### 优化Docker资源

编辑 `docker-compose.yml`:

```yaml
services:
  trading-platform:
    # ... 其他配置
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

#### 数据库优化

对于大量数据，考虑切换到PostgreSQL：

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: trading
      POSTGRES_USER: trader
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### 8. 安全加固

#### 防火墙配置

```bash
# Ubuntu (UFW)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

#### 限制SSH访问

```bash
# 修改SSH配置
sudo nano /etc/ssh/sshd_config

# 建议设置：
# PermitRootLogin no
# PasswordAuthentication no
# Port 2222  # 更改默认端口

sudo systemctl restart sshd
```

#### 定期更新

```bash
# 系统更新
sudo apt-get update && sudo apt-get upgrade -y

# Docker镜像更新
docker-compose pull
docker-compose up -d
```

### 9. 故障排查

#### 服务无法启动

```bash
# 检查日志
docker-compose logs trading-platform

# 检查端口占用
sudo netstat -tulpn | grep 8000

# 重建容器
docker-compose down
docker-compose up -d --build
```

#### API连接失败

```bash
# 测试API连接
curl -v http://localhost:8000/api/status

# 检查环境变量
docker-compose config

# 进入容器检查
docker exec -it ai-trading-platform bash
```

#### 数据库问题

```bash
# 备份当前数据库
docker cp ai-trading-platform:/app/data/trading_platform.db ./backup.db

# 重新初始化（会丢失数据！）
docker-compose down -v
docker-compose up -d
```

### 10. 扩展部署

#### 多实例负载均衡

```yaml
# docker-compose.yml
services:
  trading-platform-1:
    # ... 配置
  
  trading-platform-2:
    # ... 配置
  
  nginx:
    # ... 负载均衡配置
```

#### 使用云服务

- **AWS**: 使用ECS/EKS部署
- **阿里云**: 使用ACK（容器服务）
- **腾讯云**: 使用TKE（容器服务）
- **Vercel/Netlify**: 部署前端静态页面

### 11. 监控告警

#### Prometheus + Grafana

```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
```

#### 钉钉/企业微信告警

在代码中添加告警webhook，当发生重要事件时推送通知。

### 12. 生产检查清单

部署前确认：

- [ ] 所有API密钥已正确配置
- [ ] 已设置合理的交易参数
- [ ] 数据库备份策略已配置
- [ ] 日志轮转已配置
- [ ] 防火墙规则已设置
- [ ] SSL证书已配置
- [ ] 监控和告警已设置
- [ ] 已在测试环境验证
- [ ] 已进行小额资金测试
- [ ] 应急回滚方案已准备

## 常见问题

### Q: 如何更改交易参数？
A: 修改 `.env` 文件中的交易配置参数，然后重启服务：`docker-compose restart`

### Q: 如何暂停自动交易？
A: 设置 `ENABLE_AUTO_TRADING=False`，重启服务

### Q: 如何备份数据？
A: 使用上面提供的备份脚本，或手动复制 `data/` 目录

### Q: 如何升级到新版本？
```bash
git pull
docker-compose down
docker-compose up -d --build
```

### Q: 如何查看实时交易情况？
A: 访问 `https://your-domain.com` 查看可视化界面

## 技术支持

遇到问题？
1. 查看日志：`docker-compose logs -f`
2. 查看文档：README.md
3. 提交Issue：GitHub Issues
4. 联系支持：your-email@example.com

