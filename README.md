# 元基财报分析引擎

> 基于企业财报深挖核心基本面的超级 AI 分析平台

[![Deploy](https://img.shields.io/badge/deploy-Docker%20Compose-blue)](https://github.com/zhangsa69/stock-web-system)
[![Frontend](https://img.shields.io/badge/frontend-纯HTML%20SPA-green)](#)
[![Backend](https://img.shields.io/badge/backend-FastAPI%20%2B%20Celery-teal)](#)

---

## 🚀 项目简介

输入 A 股/港股代码，自动拉取近五年财报，通过 NotebookLM 大模型深度分析，生成结构化投资报告并发送至邮箱。全程自动化，从代码到报告只需十余分钟。

### 核心能力

- **全自动财报采集** — 对接巨潮资讯网，自动拉取年报/半年报/季报，结构化提取上百项财务指标
- **深度 AI 分析** — 财报上传 Google NotebookLM，大模型进行多维度解读：成长性、盈利能力、偿债能力、运营效率、现金流质量
- **结构化报告** — 自动生成包含执行摘要、财务全景、估值分析、风险提示、投资建议等章节的专业报告
- **邮件直达** — 报告直接发送至注册邮箱，支持历史回溯与下载

---

## 🏗️ 系统架构

```
用户 → nginx(:80) → FastAPI(backend:8000) → PostgreSQL + Redis
                                ↕
                     Celery Worker → HTTP POST → hermes-agent:9888
                                                  (hermes-cmd-server.py)
                                                  ThreadingHTTPServer + Semaphore(3)
                                     ↕
                          hermes chat → cninfo-financial-analysis
                                     → NotebookLM
```

### 容器清单

| 容器 | 镜像 | 用途 |
|------|------|------|
| `stock-nginx` | nginx:alpine | 反向代理 + 前端静态文件 |
| `stock-backend` | 自建 | FastAPI 主服务 |
| `stock-celery-worker` | 自建 | Celery 异步分析任务 |
| `stock-postgres` | postgres:15-alpine | 数据库 |
| `stock-redis` | redis:7-alpine | Celery broker/result + 限流 |

---

## 🎨 技术栈

| 层 | 技术 |
|---|------|
| 前端 | 纯 HTML/CSS/JS 单文件 SPA（Apple 白色简约风格，零框架零构建） |
| 后端 | Python FastAPI + SQLAlchemy Async + Celery |
| 数据库 | PostgreSQL 15 |
| 缓存/队列 | Redis 7 |
| AI 引擎 | Hermes Agent + NotebookLM（A股/港股）；UZI-Skill（美股） |
| 部署 | Docker Compose |
| 分析管道 | cninfo-financial-analysis（巨潮资讯 → NotebookLM） |

---

## 📦 快速开始

### 环境要求

- Docker & Docker Compose
- 4GB+ 内存（推荐 8GB）
- Hermes Agent 容器

### 部署步骤

```bash
# 1. 克隆仓库
git clone https://github.com/zhangsa69/stock-web-system.git
cd stock-web-system

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填写 JWT_SECRET、SMTP 等配置

# 3. 启动所有服务
docker compose up -d

# 4. 连接 hermes-agent 到 stock 网络
docker network connect stock-web-system_stock-network hermes-agent

# 5. 在 hermes-agent 容器内启动 cmd-server
docker exec -d hermes-agent bash -c \
  'nohup /opt/hermes/.venv/bin/python3 /opt/hermes/hermes-cmd-server.py > /tmp/cmd-server.log 2>&1 &'

# 6. 重载 nginx（清除 DNS 缓存）
docker exec stock-nginx nginx -s reload

# 7. 访问
open http://localhost
```

---

## 📂 项目结构

```
stock-web-system/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/                # 路由：analysis, auth, recharge, admin
│   │   ├── models/             # ORM：analysis, user, recharge
│   │   ├── schemas/            # Pydantic 校验
│   │   ├── services/           # hermes_bridge, email_service, analysis_service
│   │   ├── tasks/              # Celery 任务 + 配置
│   │   ├── utils/              # JWT 鉴权、限流
│   │   ├── config.py           # 配置
│   │   ├── database.py         # 数据库初始化
│   │   └── main.py             # FastAPI 入口
│   └── Dockerfile
├── frontend/
│   └── dist/
│       └── index.html          # 苹果风格 SPA（单文件，80KB）
├── nginx/
│   └── nginx.conf              # Nginx 配置
├── hermes-cmd-server.py        # Hermes Agent HTTP → CLI 桥接
├── docker-compose.yml
└── README.md
```

---

## 🔐 功能特性

### 用户系统

- 邮箱注册 + 验证码验证
- JWT 鉴权
- 点券余额管理
- 未登录门控：所有分析操作需先登录

### 点券充值

- 4 档 3D 翻转充值卡片（1/20/50/100 点券）
- 兑换码核销（16 位随机码）
- 管理后台批量生成/导入/导出兑换码

### 分析管道

- 股票代码校验（A 股 6 位 / 港股 1-5 位）
- 并发上限 3（Semaphore 控制）
- 分析失败自动退点券
- 余额不足客户端拦截

### 管理后台

- 管理员验证码登录
- 兑换码批量生成/CSV 导入/导出
- 使用统计面板
- 用户管理

---

## 🛠️ 常用运维命令

```bash
# 前端部署（纯 HTML，零构建）
scp index.html root@SERVER:/opt/data/stock-web-system/frontend/dist/
docker exec stock-nginx nginx -s reload

# 后端部署
scp -r backend/app root@SERVER:/opt/data/stock-web-system/backend/
docker compose up -d --build backend celery-worker
docker exec stock-nginx nginx -s reload  # 清除 DNS 缓存

# 查看日志
docker logs stock-backend --tail 50
docker logs stock-celery-worker --tail 50

# 重启 hermes-cmd-server
docker exec hermes-agent pkill -f hermes-cmd-server
docker network connect stock-web-system_stock-network hermes-agent
docker exec -d hermes-agent bash -c \
  'nohup /opt/hermes/.venv/bin/python3 /opt/hermes/hermes-cmd-server.py > /tmp/cmd-server.log 2>&1 &'

# 数据库备份
docker exec stock-postgres pg_dump -U stock_user stock_analysis > backup.sql
```

---

## ⚠️ 重要注意事项

1. **不要 `docker compose up -d --build nginx`** — 会覆盖前端 SPA
2. 后端重建后必须 `docker exec stock-nginx nginx -s reload`，否则 API 全部 502
3. hermes-agent 重启后需手动重连网络 + 重启 cmd-server
4. 本项目遵循 `编码规则.md` 中的增量开发协议

---

## 🧪 系统优势（vs 人工分析 & 免费大模型）

| 对比维度 | 人工分析 | 免费大模型 | 元基财报分析引擎 |
|---------|---------|-----------|----------------|
| 数据获取 | 手动查找近五年财报，数十万至百万字 | 不支持超长文本上传 | 自动拉取全文，百万字深度阅读 |
| 分析深度 | 浅显，依赖个人经验 | 数十秒出摘要，无交叉验证 | 十余分钟深度挖掘，22 维指标 |
| 报告输出 | 零散，格式不统一 | 简单文本摘要 | 结构化专业报告 |
| 时效性 | 难以追踪更新 | 无法自动追踪 | 实时对接数据源 |
| 成本 | 单只股票数小时 | 免费但无法支撑决策 | 单次 ¥1，机构级分析 |

---

## 📄 许可证

MIT License

---

## 🔗 相关链接

- [Hermes Agent](https://hermes-agent.nousresearch.com)
- [编码规则](./编码规则.md)
