#!/bin/bash
set -e

echo "========================================"
echo "  股票分析平台 - VPS 一键部署"
echo "========================================"
echo ""

cd "$(dirname "$0")"

# 1. 检查 Hermes 是否已安装
echo "[1/4] 检查 Hermes Agent..."

# 查找 hermes 命令（支持 pip/pipx 不同安装路径）
HERMES_CMD=""
for candidate in "/usr/local/bin/hermes" "/root/.local/bin/hermes" "$HOME/.local/bin/hermes"; do
    if [ -f "$candidate" ]; then
        HERMES_CMD="$candidate"
        break
    fi
done

# 也尝试用 which 查找
if [ -z "$HERMES_CMD" ]; then
    HERMES_CMD=$(which hermes 2>/dev/null || echo "")
fi

if [ -n "$HERMES_CMD" ] && [ -f "$HERMES_CMD" ]; then
    echo "  ✅ Hermes CLI 已就绪 ($HERMES_CMD)"

    # 如果不在 /usr/local/bin/（比如 pipx 装在了 ~/.local/bin/），
    # 自动创建软链接，因为 docker-compose.yml 需要这个路径
    if [ "$HERMES_CMD" != "/usr/local/bin/hermes" ] && [ ! -f "/usr/local/bin/hermes" ]; then
        echo "  🔗 创建软链接: $HERMES_CMD -> /usr/local/bin/hermes"
        ln -sf "$HERMES_CMD" /usr/local/bin/hermes
    fi
else
    echo "  ⚠ 未在宿主机找到 hermes 命令"
    echo "  "
    echo "  如果你已经在 Docker 中运行 Hermes（独立容器），可以跳过此检查。"
    echo "  但请注意：docker-compose.yml 会将宿主机的 hermes 挂载到后端容器中，"
    echo "  如果宿主机没有 hermes，后端容器将无法调用它。"
    echo "  "
    echo "  推荐安装方式（Debian 12+/Ubuntu 24+）："
    echo "     sudo apt install pipx -y"
    echo "     pipx ensurepath"
    echo "     pipx install hermes-agent"
    echo "     ln -s ~/.local/bin/hermes /usr/local/bin/hermes"
    echo "  "
    read -p "  是否继续部署？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "  已取消部署。"
        exit 1
    fi
fi

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
