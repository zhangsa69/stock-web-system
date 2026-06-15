# AI 股票财报分析平台 - VPS 部署指南

## 架构说明

```
Docker Compose 编排 6 个服务：

┌──────────────────────────────────────────────────────┐
│  Nginx (80/443)  ← 反向代理 + 静态资源               │
│    ├── /api/* → FastAPI:8000                         │
│    └── /* → Vue 3 静态文件                            │
├──────────────────────────────────────────────────────┤
│  FastAPI:8000   ← Web API 主服务                      │
│    ├── POST /api/analysis/start                       │
│    ├── GET  /api/analysis/{id}/status                 │
│    └── GET  /api/analysis/history                     │
├──────────────────────────────────────────────────────┤
│  Celery Worker ×2  ← 异步任务（调用 Hermes CLI）      │
├──────────────────────────────────────────────────────┤
│  PostgreSQL:5432  ← 分析任务记录                       │
│  Redis:6379       ← 任务队列 + 缓存                   │
└──────────────────────────────────────────────────────┘
```

## 前置要求

- VPS 已安装 Docker + Docker Compose
- VPS 已安装 Hermes Agent（`hermes` 命令可用）
- Hermes 的 2 个股票分析 skill 已配置在 `~/.hermes/skills/`

## 部署步骤

### 1. 上传项目

```bash
# 将本地项目上传到 VPS
scp -r ./* user@your-vps-ip:/opt/stock-analysis/
```

### 2. 配置环境变量

```bash
cd /opt/stock-analysis
cp .env.example .env
vi .env
```

关键配置项：
```
POSTGRES_PASSWORD=强密码
SECRET_KEY=随机64字符字符串
HERMES_BIN=hermes
HERMES_HOME=/root/.hermes
HERMES_TIMEOUT=600
```

### 3. 构建并启动

```bash
# 构建镜像
docker compose build

# 启动所有服务
docker compose up -d

# 查看日志
docker compose logs -f

# 查看服务状态
docker compose ps
```

### 4. 数据库初始化

```bash
# 进入 backend 容器运行迁移
docker compose exec backend alembic upgrade head

# 或直接通过 FastAPI 自动建表（开发模式）
# FastAPI 启动时会自动创建表
```

### 5. 验证

```bash
# 健康检查
curl http://localhost:8000/health

# 提交分析任务
curl -X POST http://localhost/api/analysis/start \
  -H "Content-Type: application/json" \
  -d '{"stock_code": "600519"}'

# 浏览器访问
http://your-vps-ip
```

## 日常运维

### 查看日志
```bash
docker compose logs backend -f         # API 日志
docker compose logs celery-worker -f   # 任务日志
docker compose logs nginx -f           # 访问日志
```

### 重启服务
```bash
docker compose restart backend
docker compose restart celery-worker
```

### 扩容 Worker
```bash
docker compose up -d --scale celery-worker=4
```

### 数据备份
```bash
# PostgreSQL
docker compose exec postgres pg_dump -U stock_user stock_analysis > backup.sql

# Redis（自动持久化到 docker-data/redis/）
```

## 注意事项

1. **Hermes CLI 路径**：确保 VPS 上 `hermes` 命令在 PATH 中，或在 `docker-compose.yml` 中挂载正确路径
2. **SSL 证书**：生产环境请放置 SSL 证书到 `nginx/ssl/` 目录，并修改 nginx.conf 启用 HTTPS
3. **防火墙**：开放 80/443 端口
4. **内存**：Celery Worker 每个约消耗 500MB（含 Hermes 子进程），请按 VPS 内存调整 Worker 数量

## 生产环境增强（后续）

- [ ] 添加 SSL 证书（Let's Encrypt）
- [ ] Cloudflare CDN 加速（可选）
- [ ] 接入微信/支付宝支付
- [ ] 添加用户注册登录系统
- [ ] 添加管理后台
