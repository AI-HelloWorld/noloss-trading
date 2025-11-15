#!/bin/bash
set -e

echo "? 检查数据库路径..."

# 确保数据目录存在
mkdir -p /app/data

# 检查数据库路径是否被错误创建为目录
if [ -d "/app/data/trading_platform.db" ]; then
    echo "??  检测到数据库路径是目录，正在修复..."
    rm -rf /app/data/trading_platform.db
    echo "? 已删除错误的目录"
fi

echo "? 数据库路径检查完成"

# 执行传入的命令
echo "? 启动应用..."
exec "$@"