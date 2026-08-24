# 元基鉴股

> 让每一份财报，都变成看得懂、用得上的投资洞察。

[![Deploy](https://img.shields.io/badge/deploy-Docker%20Compose-blue)](https://github.com/zhangsa69/stock-web-system)
[![Backend](https://img.shields.io/badge/backend-FastAPI%20%2B%20Celery-teal)](#技术栈)
[![Database](https://img.shields.io/badge/database-PostgreSQL%2015-blue)](#技术栈)

## 项目简介

元基鉴股是一套面向 A 股与港股的 AI 财报研究平台。它把繁琐的财报获取、资料整理和深度阅读交给自动化分析流程，让用户只需输入股票代码，就能快速获得一份结构清晰、信息完整的研究报告。

平台通过 Hermes Agent 串联巨潮资讯网与 NotebookLM，自动获取企业年报、半年报和季报，从成长性、盈利能力、偿债能力、运营效率、现金流质量等多个维度梳理企业基本面，并将关键结论沉淀为可持续查看的分析记录。

## 核心能力

- 邮箱注册、验证码验证、登录和 JWT 鉴权
- 点券余额和充值卡密核销
- A 股 / 港股股票代码校验
- 财报分析任务异步提交和状态查询
- Celery Worker 执行耗时分析任务
- Hermes Agent HTTP Bridge 调用 `cninfo-financial-analysis`
- NotebookLM 财报深度分析
- 分析失败自动退还点券
- 分析历史记录和 Markdown 报告下载
- 首页示例报告（独立示例数据库）
- 首页 A 股指数和全球市场行情展示
- 市场研究驾驶舱 `/mrd/`
- 管理后台：管理员登录、卡密管理、用户管理、仪表盘统计
- 首页 SEO 元数据、JSON-LD、robots.txt、sitemap.xml 和示例报告页

## 系统架构

```text
浏览器
  │
  ▼
Nginx :80/:443
  ├── 主站 SPA：/          → frontend/dist
  ├── 市场驾驶舱：/mrd/     → mrd-dist
  └── 业务 API：/api/*      → FastAPI :8000
                                  │
                    PostgreSQL 15 + Redis 7
                                  │
                         Celery Worker
                                  │
                         Hermes Bridge
                                  │ HTTP POST
                                  ▼
                        hermes-agent:9888
                                  │
                                  ▼
                 cninfo-financial-analysis
                                  │
                                  ▼
                              NotebookLM
```

### Docker 服务

| 容器 | 镜像 | 用途 |
|---|---|---|
| `stock-nginx` | `nginx:alpine` | 反向代理、主站和市场驾驶舱静态文件、WebSocket 分流 |
| `stock-backend` | `backend/Dockerfile` | FastAPI API 服务 |
| `stock-celery-worker` | `backend/Dockerfile` | Celery 异步分析任务 |
| `stock-postgres` | `postgres:15-alpine` | 用户、点券、分析任务等业务数据 |
| `stock-redis` | `redis:7-alpine` | 缓存、验证码、Celery broker/result |

Hermes Agent 不是本项目 Compose 文件中的服务，而是通过 `hermes_api_url` 连接到外部已运行的 `hermes-agent` 容器。

## 技术栈

| 层 | 实际使用 |
|---|---|
| 前端 | 已构建的 HTML / CSS / JavaScript 静态 SPA，部署文件为 `frontend/dist/index.html` |
| 前端工程文件 | `frontend/` 下保留 package 配置和 `src-original-backup/` |
| 后端 | Python 3.11、FastAPI、SQLAlchemy Async、Pydantic Settings |
| 异步任务 | Celery |
| 数据库 | PostgreSQL 15，异步访问使用 asyncpg，Worker 使用同步 psycopg2 |
| 缓存与队列 | Redis 7 |
| 分析执行 | Hermes Agent HTTP Bridge |
| 财报分析 | `cninfo-financial-analysis` + NotebookLM |
| 反向代理 | Nginx |
| 部署 | Docker Compose |

## 关键流程

### 分析流程

1. 前端向 `POST /api/analysis/start` 提交股票代码。
2. 后端校验股票代码、用户登录状态和点券余额。
3. 后端扣除 2 点券并创建分析任务。
4. Celery Worker 调用 Hermes Bridge。
5. Hermes Bridge 向 `hermes-agent:9888/exec` 发起命令请求。
6. Hermes 执行 `cninfo-financial-analysis`，并要求将完整报告写入临时 Markdown 文件。
7. 后端读取报告、保存任务结果并更新状态。
8. 如果任务最终失败，系统退还 2 点券。

当前代码中邮件任务仍存在，但成功分析后的邮件触发调用已注释禁用。

### 市场数据

首页的 A 股指数和全球市场行情由前端静态页面直接请求数据源并展示。后端另有用户驾驶舱数据 API，用于保存和读取登录用户的：

- `watchlist`：自选股
- `chains`：产业链数据

对应 API 为：

```text
GET    /api/market/{watchlist|chains}
PUT    /api/market/{watchlist|chains}
DELETE /api/market/{watchlist|chains}
```

## API 概览

### 认证

```text
POST /api/register
POST /api/verify-email
POST /api/login
GET  /api/me
```

### 分析

```text
POST /api/analysis/start
GET  /api/analysis/{task_id}/status
GET  /api/analysis/history
GET  /api/analysis/{task_id}/download
GET  /api/samples/{stock_code}
GET  /api/health
```

### 点券

```text
POST /api/redeem
GET  /api/balance
```

### 管理后台

```text
POST /api/admin/send-code
POST /api/admin/login
GET  /api/admin/dashboard
GET  /api/admin/codes
POST /api/admin/codes/import
GET  /api/admin/users
POST /api/admin/users/{user_id}/tickets
```

## 项目结构

```text
stock-web-system/
├── backend/
│   ├── app/
│   │   ├── api/                    # auth、analysis、recharge、admin、market
│   │   ├── models/                 # user、analysis、recharge、dashboard
│   │   ├── schemas/                # 请求和响应数据模型
│   │   ├── services/               # Hermes、邮件、报告 HTML/PDF 服务
│   │   ├── tasks/                  # Celery 分析和邮件任务
│   │   ├── config.py               # 环境变量和服务配置
│   │   ├── database.py             # 数据库连接和初始化
│   │   └── main.py                 # FastAPI 入口
│   ├── alembic/                    # 数据库迁移目录
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── dist/index.html             # 当前部署的主站 SPA
│   ├── src-original-backup/        # 原前端工程文件备份
│   └── package.json
├── mrd-dist/                       # 市场研究驾驶舱静态文件
├── nginx/
│   ├── nginx.conf                  # 主站、API、MRD 和 WebSocket 配置
│   └── mrd.conf                    # MRD 配置片段
├── scripts/                        # 数据库、数据和部署诊断脚本
├── docker-compose.yml
├── deploy.sh
├── hermes-cmd-server.py            # Hermes 命令执行 HTTP 服务
├── .env.example
└── README.md
```

## 快速开始

### 环境要求

- Docker Engine
- Docker Compose
- 可访问 PostgreSQL 和 Redis 的运行环境
- 一个已运行并接入项目网络的 `hermes-agent` 容器
- Hermes Agent 中已安装并可调用 `cninfo-financial-analysis`
- NotebookLM 所需的登录状态和配置

### 部署

```bash
git clone https://github.com/zhangsa69/stock-web-system.git
cd stock-web-system

cp .env.example .env
# 编辑 .env，填写数据库、JWT、SMTP（如需邮件任务）和 Hermes 配置

docker compose up -d --build

# 如 hermes-agent 尚未接入项目网络，按实际网络名称连接
docker network connect stock-web-system_stock-network hermes-agent

# 验证服务
docker compose ps
docker exec stock-nginx nginx -t
```

生产代码目录：

```text
/opt/data/stock-web-system
```

## 常用运维命令

```bash
# 查看服务
docker compose ps

# 查看后端日志
docker logs stock-backend --tail 100

# 查看 Worker 日志
docker logs stock-celery-worker --tail 100

# 检查并重载 Nginx
docker exec stock-nginx nginx -t
docker exec stock-nginx nginx -s reload

# 重启后端和 Worker
docker compose restart backend celery-worker

# 备份 PostgreSQL
docker exec stock-postgres pg_dump -U stock_user stock_analysis > backup.sql
```

## 生产修改流程

当前仓库统一使用 `main` 作为生产代码分支：

```bash
cd /opt/data/stock-web-system
git switch main
git pull --ff-only origin main

# 修改并检查
git diff --check

# 提交和推送
git add <files>
git commit -m "type: describe the production change"
git push origin main
```

修改范围对应的服务操作：

- 只改 `frontend/dist/`：检查文件后执行 Nginx reload。
- 改 `nginx/`：先执行 `nginx -t`，再 reload；涉及 Compose 挂载变化时重建 Nginx。
- 改 `backend/`：重建或重启 `backend` 和 `celery-worker`。
- 改数据库模型或迁移：先备份数据库，再执行对应迁移并检查服务日志。

## 配置和安全注意事项

1. 不要把 `.env`、数据库密码、JWT 密钥、SMTP 密码或 NotebookLM 登录状态提交到 Git。
2. 不要删除 `docker-data/`，其中包含 PostgreSQL、Redis、PDF 缓存和示例数据库数据。
3. `frontend/dist/` 是当前实际部署的静态文件，修改前先确认工作区和生产版本一致。
4. 修改 Docker 或 Nginx 配置后，必须执行配置检查和服务健康检查。
5. 分析任务最长执行时间由 `hermes_timeout` 控制，默认值为 900 秒；Celery 任务最多重试 6 次。
6. 生产环境不要使用默认的 `secret_key`、JWT 密钥和数据库密码。
7. 项目只支持当前代码中实现的 A 股 / 港股财报分析；美股功能尚未实现。

## 许可证

MIT License

## 相关链接

- [CNinfo2Notebookllm](https://github.com/jarodise/CNinfo2Notebookllm)
- [Hermes Agent](https://hermes-agent.nousresearch.com)
- [VPS 部署指南](./VPS部署指南.md)
- [编码规则](./编码规则.md)
