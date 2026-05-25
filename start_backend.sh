#!/bin/bash

# 快速启动后端服务脚本 (Linux/Mac)
# 使用方法: chmod +x start_backend.sh && ./start_backend.sh

echo "========================================"
echo "  智能房屋租赁系统 - 后端启动脚本"
echo "========================================"
echo ""

# 检查虚拟环境是否存在
if [ ! -d ".venv" ]; then
    echo "错误: 虚拟环境不存在!"
    echo "请先运行: python -m venv .venv"
    exit 1
fi

# 激活虚拟环境
echo "正在激活虚拟环境..."
source .venv/bin/activate

# 检查是否激活成功
if [ $? -ne 0 ]; then
    echo "错误: 虚拟环境激活失败!"
    exit 1
fi

echo "虚拟环境激活成功!"
echo ""

# 从 .env 文件读取端口配置（默认为 8000）
ENV_FILE=".env"
PORT=8000

if [ -f "$ENV_FILE" ]; then
    PORT_LINE=$(grep "^BACKEND_PORT=" "$ENV_FILE")
    if [ -n "$PORT_LINE" ]; then
        PORT=${PORT_LINE#*=}
    fi
fi

echo "后端服务配置:"
echo "  - 主机: 0.0.0.0"
echo "  - 端口: $PORT"
echo "  - 重载模式: 启用"
echo ""

# 启动 uvicorn
echo "正在启动后端服务..."
echo "按 Ctrl+C 停止服务"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port $PORT --reload
