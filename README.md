# 元基鉴股

> 面向 A 股、港股和美股研究的 AI 财报分析与市场信息平台。

[![Deploy](https://img.shields.io/badge/deploy-Docker%20Compose-blue)](https://github.com/zhangsa69/stock-web-system)
[![Frontend](https://img.shields.io/badge/frontend-纯HTML%20SPA-green)](#技术栈)
[![Backend](https://img.shields.io/badge/backend-FastAPI%20%2B%20Celery-teal)](#技术栈)

## 项目简介

元基鉴股基于 [CNinfo2Notebookllm](https://github.com/jarodise/CNinfo2Notebookllm) 的财报获取与 NotebookLM 集成能力，提供用户注册、点券充值、异步分析、邮件报告、历史记录和管理后台等完整 Web 功能。

用户输入股票代码后，系统自动获取财报资料并调用对应分析管道，生成结构化投资研究报告并发送到邮箱。首页同时提供 A 股大盘、全球市场行情和市场研究驾驶舱；另有独立的美国持仓监控页面。

## 核心功能

- **A 股 / 港股财报分析**：从巨潮资讯网获取年报、半年报和季报，交由 NotebookLM 深度分析。
- **美股深度分析**：使用 UZI-Skill deep-analysis 管道完成研究分析。
- **结构化报告**：包含执行摘要、财务全景、估值分析、风险提示和投资建议等内容。
- **用户与点券系统**：邮箱注册、验证码、JWT 鉴权、点券余额、充值卡密和失败退券。
- **异步任务处理**：Celery 执行分析任务，包含并发控制、失败重试和结果缓存。
- **市场行情**：首页展示上证、深证、创业板、沪深 300，以及道指、标普 500、纳指、恒指和恒生科技。
- **市场研究驾驶舱**：访问 `/mrd/`，提供市场数据和研究信息展示。
- **美国持仓监控**：访问 `/congress/`，展示美国政治人物交易披露、持仓排行、买卖趋势和资产分类。
- **管理后台**：卡密管理、用户管理、分析统计和系统数据维护。
- **报告阅读**：支持历史报告下载和内嵌 Markdown 阅读器。

## 系统架构

```text
用户
  │
  ▼
Nginx :80/:443
  ├── 主站 SPA：/                 → frontend/dist
  ├── 市场驾驶舱：/mrd/            → mrd-dist
  ├── 美国持仓监控：/congress/     → congress-dist
  ├── 业务 API：/api/*             → FastAPI :8000
  └── WebSocket：/v2-secret        → Xray

FastAPI backend :8000
  ├── PostgreSQL 15
  ├── Redis 7
  └── Celery Worker
        └── hermes-agent :9888
              └── cninfo-financial-analysis / UZI-Skill
                    └── NotebookLM
```

### Docker 服务

| 容器 | 镜像 | 用途 |
|---|---|---|
| `stock-nginx` | `nginx:alpine` | 反向代理、静态文件、WebSocket 分流 |
| `stock-backend` | 本地构建 | FastAPI 主服务 |
| `stock-celery-worker` | 本地构建 | 异步分析任务 |
| `stock-postgres` | `postgres:15-alpine` | 业务数据库 |
| `stock-redis` | `redis:7-alpine` | 缓存、队列和限流 |

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | 纯 HTML / CSS / JavaScript 单文件 SPA，Apple 白色简约风格 |
| 后端 | Python FastAPI、SQLAlchemy Async、Celery |
| 数据库 | PostgreSQL 15 |
| 缓存与队列 | Redis 7 |
| AI 引擎 | Hermes Agent、NotebookLM、UZI-Skill |
| 财报数据 | 巨潮资讯网（CNinfo） |
| 市场行情 | 腾讯财经 gtimg、东方财富 push2delay |
| 部署 | Docker Compose + Nginx |
| 美国持仓数据 | Kadoa Congress Trading Monitor 数据源 |

## 快速开始

### 环境要求

- Docker 和 Docker Compose
- 至少 4 GB 内存，推荐 8 GB
- 可访问 NotebookLM 和相关数据源的 Hermes Agent 环境

### 部署

```bash
git clone https://github.com/zhangsa69/stock-web-system.git
cd stock-web-system

# 首次部署时创建并填写环境变量
cp .env.example .env
# 编辑 .env，填写数据库、JWT、SMTP 等配置

# 启动服务
docker compose up -d

# 将 hermes-agent 接入项目网络（如尚未接入）
docker network connect stock-web-system_stock-network hermes-agent

# 启动 Hermes 命令桥接服务（按实际容器路径调整）
docker exec -d hermes-agent bash -c \
  'nohup /opt/hermes/.venv/bin/python3 /opt/hermes/hermes-cmd-server.py > /tmp/cmd-server.log 2>&1 &'

# 检查 Nginx 配置
docker exec stock-nginx nginx -t

# 访问主站
# http://localhost
```

生产环境项目目录为：

```text
/opt/data/stock-web-system
```

## 项目结构

```text
stock-web-system/
├── backend/
│   ├── app/
│   │   ├── api/                    # analysis、auth、recharge、admin、market
│   │   ├── models/                 # 用户、分析、充值、市场数据模型
│   │   ├── schemas/                # Pydantic 数据校验
│   │   ├── services/               # 分析、鉴权、邮件和 Hermes 桥接服务
│   │   ├── tasks/                  # Celery 任务和配置
│   │   ├── utils/                  # JWT、限流等工具
│   │   ├── database.py
│   │   └── main.py
│   └── Dockerfile
├── frontend/
│   └── dist/index.html             # 主站 SPA 和管理后台
├── mrd-dist/                       # 市场研究驾驶舱静态文件
├── congress-dist/                  # 美国持仓监控静态文件和数据
├── nginx/
│   ├── nginx.conf                  # 主 Nginx 配置
│   └── mrd.conf                    # MRD 相关配置
├── scripts/
│   ├── check_*.py                  # 运维诊断脚本
│   └── update_trump_data.py        # 持仓数据更新脚本
├── hermes-cmd-server.py            # Hermes HTTP → CLI 桥接
├── docker-compose.yml
└── README.md
```

## 业务说明

### 用户、鉴权和点券

- 邮箱注册和验证码验证，验证码由 Redis 管理并自动过期。
- JWT 鉴权，分析操作需要登录。
- 充值卡密支持唯一性校验，防止重复核销。
- 当前分析单次消耗 2 点券；分析失败时自动退还点券。
- 支持忘记密码和验证码重置。

### 分析任务

- 支持 A 股、港股和美股代码校验。
- Celery Worker 执行耗时分析，避免阻塞 Web 请求。
- Hermes 桥接服务控制分析任务并限制并发。
- 支持失败重试、结果缓存和历史记录。
- 报告完成后发送到用户注册邮箱。

### 市场与持仓页面

- 首页市场行情由浏览器请求数据源，使用本地缓存降低重复请求。
- `/mrd/` 为市场研究驾驶舱，静态文件独立部署。
- `/congress/` 为美国持仓监控页面，数据文件位于 `congress-dist/data/`。
- 更新美国持仓数据：

```bash
python3 scripts/update_trump_data.py
```

该脚本会重新生成 `trump_raw.json`、`trump.json` 和 `trump.js`。如需重建 Nginx 挂载并安装定时更新任务，可执行：

```bash
bash scripts/deploy_congress.sh
```

## 常用运维命令

```bash
# 查看服务状态
docker compose ps

# 查看后端日志
docker logs stock-backend --tail 100

# 查看 Celery 日志
docker logs stock-celery-worker --tail 100

# 检查并重载 Nginx
docker exec stock-nginx nginx -t
docker exec stock-nginx nginx -s reload

# 重启后端和 Worker
docker compose restart backend celery-worker

# 查看 Hermes 命令桥接服务日志
docker exec hermes-agent tail -100 /tmp/cmd-server.log

# 数据库备份
docker exec stock-postgres pg_dump -U stock_user stock_analysis > backup.sql
```

## 直接修改生产代码

当前仓库统一使用 `main` 分支作为生产代码分支。修改流程：

```bash
cd /opt/data/stock-web-system
git switch main
# 修改并验证代码
git diff --check
git add <files>
git commit -m "type: describe the production change"
git push origin main
```

生产环境修改前应先确认工作区状态，避免覆盖尚未提交的改动。前端静态文件修改后需要执行 Nginx reload；后端代码修改后通常需要重启 `backend` 和 `celery-worker`。

## 重要注意事项

1. 不要在没有备份的情况下删除 `docker-data/`，其中包含数据库、Redis 和 PDF 缓存数据。
2. 前端是已构建的静态产物，修改前应确认当前 `frontend/dist/` 是生产版本。
3. 修改后端并重建容器时，需检查 Nginx 是否仍能解析新的 backend 容器地址。
4. `nginx/ssl/` 是 Docker 挂载目录；即使当前采用 Cloudflare Flexible SSL，也不要随意删除其中的生产证书文件。
5. 环境变量和密钥只放在 `.env`，不要提交到 GitHub。
6. 美国持仓原始数据可能较大，更新脚本会覆盖 `congress-dist/data/` 下的生成文件。
7. 修改生产代码前先执行 `git status --short --branch`，确认没有误留的工作区改动。

## 许可证

MIT License

## 相关链接

- [CNinfo2Notebookllm](https://github.com/jarodise/CNinfo2NotebookLLM) — 财报采集与 NotebookLM 集成基础
- [Hermes Agent](https://hermes-agent.nousresearch.com)
- [编码规则](./编码规则.md)
- [VPS 部署指南](./VPS部署指南.md)
