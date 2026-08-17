# 元基财报分析引擎

> 基于企业财报深挖核心基本面的超级 AI 分析平台 访问https://miaoousc.xyz

[![Deploy](https://img.shields.io/badge/deploy-Docker%20Compose-blue)](https://github.com/zhangsa69/stock-web-system)
[![Frontend](https://img.shields.io/badge/frontend-纯HTML%20SPA-green)](#)
[![Backend](https://img.shields.io/badge/backend-FastAPI%20%2B%20Celery-teal)](#)

---

## 🚀 项目简介

基于 [CNinfo2Notebookllm](https://github.com/jarodise/CNinfo2Notebookllm) 二次开发，在其财报获取与 NotebookLM 集成能力之上，构建了完整的 Web 平台：用户注册登录、点券充值、异步分析、邮件报告、管理后台等生产级功能。

输入 A 股/港股代码，自动拉取近五年财报，通过 NotebookLM 大模型深度分析，生成结构化投资报告并发送至邮箱。全程自动化，从代码到报告只需十余分钟。

首页同时集成 **大盘指数**（上证/深证成指/创业板指/沪深300）与 **全球市场**（道指/标普500/纳指/恒指/恒生科技）实时行情，方便用户开盘前快速把握市场全貌；并内置 **市场研究驾驶舱**（`/mrd/`）一屏式实时行情大屏。
<img width="1619" height="1065" alt="image" src="https://github.com/user-attachments/assets/6217c7e5-a658-40d4-ba79-b3175f756270" />

### 核心能力

- **全自动财报采集** — 对接巨潮资讯网，自动拉取年报/半年报/季报，结构化提取上百项财务指标
- **深度 AI 分析** — 财报上传 Google NotebookLM，大模型进行多维度解读：成长性、盈利能力、偿债能力、运营效率、现金流质量
- **结构化报告** — 自动生成包含执行摘要、财务全景、估值分析、风险提示、投资建议等章节的专业报告
- **邮件直达** — 报告直接发送至注册邮箱，支持历史回溯与下载
- **市场速览** — 首页实时展示 A 股大盘指数 + 全球主要市场行情（纯前端，5 分钟缓存）

---

## 🏗️ 系统架构

```
用户 → nginx(:80) → FastAPI(backend:8000) → PostgreSQL + Redis
                                ↕
                     Celery Worker → HTTP POST → hermes-agent:9888
                                                  (hermes-cmd-server.py)
                                                  ThreadingHTTPServer + Semaphore(5)
                                     ↕
                          hermes chat → cninfo-financial-analysis（A股/港股）
                                     → UZI-Skill deep-analysis（美股）
                                     → NotebookLM
```

### 容器清单

| 容器 | 镜像 | 用途 |
|------|------|------|
| `stock-nginx` | nginx:alpine | 反向代理 + 前端静态文件 + WebSocket 分流（/v2-secret → Xray） |
| `stock-backend` | 自建 | FastAPI 主服务 |
| `stock-celery-worker` | 自建 | Celery 异步分析任务 |
| `stock-postgres` | postgres:15-alpine | 数据库 |
| `stock-redis` | redis:7-alpine | Celery broker/result + 限流 |

---

## 🎨 技术栈

| 层 | 技术 |
|---|------|
| 前端 | 纯 HTML/CSS/JS 单文件 SPA（Apple 白色简约风格，零框架零构建，含管理后台） |
| 后端 | Python FastAPI + SQLAlchemy Async + Celery |
| 数据库 | PostgreSQL 15 |
| 缓存/队列 | Redis 7 |
| AI 引擎 | Hermes Agent + NotebookLM（A股/港股）；UZI-Skill（美股） |
| 行情数据 | 腾讯财经 gtimg（A股指数）+ 东方财富 push2delay（全球指数），浏览器直连；驾驶舱由 mrd-server（Node :3000）提供 |
| 部署 | Docker Compose |
| 分析管道 | cninfo-financial-analysis（巨潮资讯 → NotebookLM） |

---

## 📦 快速开始

### 环境要求

- Docker & Docker Compose
- 4GB+ 内存（推荐 8GB）
- Hermes Agent 容器（含 CNinfo2Notebookllm 管道）

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
│   │   ├── api/                # 路由：analysis, auth, recharge, admin, market
│   │   ├── models/             # ORM：analysis, user, recharge, dashboard
│   │   ├── schemas/            # Pydantic 校验
│   │   ├── services/           # hermes_bridge, email_service, analysis_service
│   │   ├── tasks/              # Celery 任务 + 配置
│   │   ├── utils/              # JWT 鉴权、限流
│   │   ├── config.py           # 配置（全部可由 .env 覆盖）
│   │   ├── database.py         # 数据库初始化
│   │   └── main.py             # FastAPI 入口
│   └── Dockerfile
├── frontend/
│   └── dist/
│       └── index.html          # Apple 风格 SPA（单文件，含客户首页 + 管理后台）
├── mrd-dist/                   # 市场研究驾驶舱前端构建产物（React SPA，/mrd/ 路径）
├── nginx/
│   └── nginx.conf              # Nginx 配置（SPA 回退 + WebSocket 分流 + MRD API 分流）
├── scripts/                    # 运维诊断脚本（数据库查询、枚举修复等）
├── hermes-cmd-server.py        # Hermes Agent HTTP → CLI 桥接
├── docker-compose.yml
└── README.md
```

---

## 🔐 功能特性

### 用户系统

- 邮箱注册 + 验证码验证（Redis 管理，10 分钟过期）
- JWT 鉴权（未验证用户不占数据库）
- 点券余额管理
- 未登录门控：所有分析操作需先登录
- 忘记密码：两步验证码重置

### 点券充值

- 4 档翻转充值卡片（2/30/50/100 点券，每次分析消耗 2 点券）
- 兑换码核销（唯一性校验，防重复使用）
- 管理后台批量 CSV 导入/导出
<img width="1424" height="1195" alt="image" src="https://github.com/user-attachments/assets/cc7442b5-9924-498b-b9d8-a1362cf2fe77" />

### 市场速览（首页）

- **大盘指数**：上证指数 / 深证成指 / 创业板指 / 沪深300（腾讯财经，实时）
- **全球市场**：道琼斯 / 标普500 / 纳斯达克 / 恒生指数 / 恒生科技（东方财富）
- 纯前端实现，零后端依赖；5 分钟 localStorage 缓存 + 手动刷新
- 桌面 4+5 列 / 移动端 2 列自适应
- 8 秒 fetch 超时保护：数据源挂起自动中止，避免页面无限转圈

### 市场研究驾驶舱（`/mrd/`）

- 一屏式实时行情大屏：全球关键指数、板块热点、资金流向、7×24 快讯、个股榜单、大宗商品、美债曲线、产业链全景
- 沪深港美指数 + 大宗商品 + 美债收益率 + 板块资金流多维度同屏
- 自选股（代码/名称/拼音检索）、产业链上下游（大模型/具身智能/半导体/新能源/创新药等）自定义图谱
- 独立前端构建（React 单页应用）由 `mrd-server`（Node, :3000）提供数据 API
- 深色大屏主题，支持区域放大、轮播、全屏展示；首屏骨架屏动画提示首次加载约 1 分钟

### 分析管道

- 股票代码校验（A 股 6 位 / 港股 1-5 位，前端三层防注入）
- 并发上限 5（Semaphore 控制）+ Bridge 503 自动重试 + Celery 线性退避（最长 21 分钟）
- 分析失败自动退点券（含 Celery 崩溃兜底）
- 余额不足客户端拦截（阈值 = 扣除量 2）
- 7 天 per-user 结果缓存（命中不重复扣费）

### 报告体验

- 报告直达邮箱 + 历史回溯下载（.md 格式）
- 内嵌 Markdown 阅读器（`/md-reader.html`，暗色主题，支持目录/搜索/字号）
- 首页快捷查看 4 支示例报告（独立 SQLite 库，不扣点券）
<img width="1829" height="1195" alt="image" src="https://github.com/user-attachments/assets/f8ba30a0-7a98-4b7e-a5d9-a19f2ab65b19" />
<img width="1675" height="1205" alt="image" src="https://github.com/user-attachments/assets/db310e50-5e33-428f-83b5-48c324faba2f" />
<img width="1544" height="1221" alt="image" src="https://github.com/user-attachments/assets/b81119d9-6fcf-4cea-8bbc-f5a76b239226" />

### 管理后台

- 管理员验证码登录（Redis 存储，60 秒限流）
- 兑换码批量生成 / CSV 导入 / 面值筛选 / 批量删除
- 使用统计面板（用户/卡密/分析/点券四卡片）
- 用户管理（删除）

### SEO

- meta / OG / Twitter 标签 + JSON-LD 结构化数据
- robots.txt + sitemap.xml
- 4 支示例股票静态 SEO 报告页（预渲染完整报告正文）

---

## 🛠️ 常用运维命令

```bash
# 前端部署（纯 HTML，零构建）
scp index.html root@SERVER:/opt/data/stock-web-system/frontend/dist/
docker exec stock-nginx nginx -s reload

# 后端部署（docker cp 热更新）
scp backend/app/xxx.py root@SERVER:/opt/data/stock-web-system/backend/app/
docker cp /opt/data/stock-web-system/backend/app/xxx.py stock-backend:/app/app/xxx.py
docker cp /opt/data/stock-web-system/backend/app/xxx.py stock-celery-worker:/app/app/xxx.py
docker compose restart backend celery-worker
docker exec stock-nginx nginx -s reload  # 清除 DNS 缓存

# 查看日志
docker logs stock-backend --tail 50
docker logs stock-celery-worker --tail 50

# 重启 hermes-cmd-server（看门狗也会自动拉起）
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
2. 后端重建后必须 `docker exec stock-nginx nginx -s reload`，否则 API 全部 502（nginx DNS 缓存旧 IP）
3. hermes-agent 重启后需手动重连网络 + 重启 cmd-server（宿主机 cron 看门狗每 30 秒自动检测）
4. Redis 内存上限 256MB + Celery result 1h 过期，防 OOM
5. 修改前端前必须先 scp 拉取服务器最新版，防止旧快照覆盖

---

## 🧪 系统优势（vs 人工分析 & 免费大模型）

| 对比维度 | 人工分析 | 免费大模型 | 元基财报分析引擎 |
|---------|---------|-----------|----------------|
| 数据获取 | 手动查找近五年财报，数十万至百万字 | 不支持超长文本上传 | 自动拉取全文，百万字深度阅读 |
| 分析深度 | 浅显，依赖个人经验 | 数十秒出摘要，无交叉验证 | 十余分钟深度挖掘，22 维指标 |
| 报告输出 | 零散，格式不统一 | 简单文本摘要 | 结构化专业报告 |
| 时效性 | 难以追踪更新 | 无法自动追踪 | 实时对接数据源 |
| 成本 | 单只股票数小时 | 免费但无法支撑决策 | 单次 2 点券（¥2），机构级分析 |

---

## 📄 许可证

MIT License

---

## 🔗 相关链接

- [CNinfo2Notebookllm](https://github.com/jarodise/CNinfo2Notebookllm) — 本项目的数据采集与分析管道基础
- [Hermes Agent](https://hermes-agent.nousresearch.com)
- [编码规则](./编码规则.md)

---

## 🙏 致谢

本项目基于 [jarodise/CNinfo2Notebookllm](https://github.com/jarodise/CNinfo2Notebookllm) 二次开发，感谢原作者提供的巨潮资讯网财报爬取与 NotebookLM 集成方案，为本项目奠定了数据采集与 AI 分析的核心能力。
