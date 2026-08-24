#!/usr/bin/env bash
# ============================================================
# 美国持仓监控 · 宿主机一键部署脚本
# 在宿主机(66.63.162.26)上以 root 运行:
#   bash /opt/data/stock-web-system/scripts/deploy_congress.sh
#
# 作用:
#   1. 重建 nginx 容器(挂载 congress-dist 目录)   [必需]
#   2. 安装 crontab(每 2 小时自动更新特朗普数据)  [必需]
#   3. 立即跑一次数据更新                          [可选/推荐]
# ============================================================
set -euo pipefail

PROJ=/opt/data/stock-web-system
SCRIPT=$PROJ/scripts/update_trump_data.py
CRON_LINE="0 */2 * * * /usr/bin/python3 $SCRIPT >> $PROJ/scripts/update_trump_data.log 2>&1"

echo "========== 1/3 重建 nginx 容器(挂载 congress-dist) =========="
cd "$PROJ"
# 校验 nginx.conf 语法(仅检查,不启动)
docker compose config -q && echo "compose 配置合法 ✓"
# 重建 nginx 容器(重新挂载新卷 + 新 nginx.conf)
docker compose up -d --no-deps nginx
echo "nginx 容器已重建 ✓"

echo "========== 2/3 配置 crontab(每2小时更新) =========="
# 备份现有 crontab
if [ -f /tmp/cron.backup ]; then :; else crontab -l > /tmp/cron.backup 2>/dev/null || true; fi
# 移除旧的行(若重复),再追加新的,避免重复条目
( crontab -l 2>/dev/null | grep -v "update_trump_data.py" || true ) \
  | { cat; echo "$CRON_LINE"; } | crontab -
echo "crontab 已安装:"
crontab -l | grep update_trump_data.py

echo "========== 3/3 立即执行一次数据更新 =========="
chmod +x "$SCRIPT"
python3 "$SCRIPT"

echo ""
echo "============================================================"
echo "✅ 部署完成！"
echo "   访问地址: https://miaoousc.xyz/congress/"
echo "   前端导航已含「美国持仓监控」按钮"
echo "   crontab: 每2小时自动更新(0 */2 * * *)"
echo "   日志: $PROJ/scripts/update_trump_data.log"
echo "============================================================"
