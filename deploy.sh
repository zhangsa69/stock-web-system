#!/bin/bash
set -e

echo "========================================"
echo "  股票分析平台 - VPS 一键部署"
echo "========================================"
echo ""

cd "$(dirname "$0")"

# 1. 检查 Hermes 是否已安装
echo "[1/4] 检查 Hermes Agent..."
if [ ! -f "/usr/local/bin/hermes" ]; then
    echo "  ⚠ 未找到 /usr/local/bin/hermes，请先安装 Hermes Agent"
    echo "  参考: pip install hermes-agent"
    exit 1
fi
echo "  ✅ Hermes CLI 已就绪"

# 2. 构建前端
echo "[2/4] 构建前端..."
cd frontend
npm install --registry=https://registry.npmmirror.com
npm run build
cd ..
echo "  ✅ 前端构建完成 -> frontend/dist/"

# 3. 创建 Docker 数据目录
echo "[3/4] 准备数据目录..."
mkdir -p docker-data/postgres docker-data/redis docker-data/pdf_cache docker-data/hermes_sessions
echo "  ✅ 数据目录已就绪"

# 4. 启动所有服务
echo "[4/4] 启动 Docker 服务..."
docker compose up -d --build

echo ""
echo "========================================"
echo "  🎉 部署完成！"
echo "  访问: http://<VPS_IP>"
echo "  API 文档: http://<VPS_IP>/docs"
echo "========================================"
