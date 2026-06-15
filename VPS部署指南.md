# 股票分析系统 - VPS 部署指南（小白专用版）

> 📖 **阅读说明**：本文档中，每个代码块里的每一行都是一个独立命令。打完一行按一次回车，等它跑完再打下一行。如果一行很长，请完整复制粘贴，不要拆开。

---

## 第 0 步：连接到 VPS

用你习惯的工具（Xshell、PuTTY、Termius 等）SSH 连接到你的 VPS。

连接成功后，你会看到类似这样的提示符：

```
root@racknerd-xxxxx:~#
```

这表示你已经成功登录 VPS，可以开始操作了。

---

## 第 1 步：安装 Docker

Docker 就像是一个"打包盒子"，能把整个项目需要的所有东西都装进去，不需要你单独装 Python、数据库等。

**一次复制下面这一整行，粘贴到终端，按回车：**

```bash
curl -fsSL https://get.docker.com | bash
```

> 💡 这个命令会从网上下载 Docker 并自动安装，大约需要 1-3 分钟。你会看到很多文字滚动，不用管它，等它跑完。

安装完成后，继续执行以下 4 个命令（一个一个来）：

**命令 1：让 Docker 开机自动启动**
```bash
systemctl enable docker
```
> 预期：没有报错就表示成功。

**命令 2：立即启动 Docker**
```bash
systemctl start docker
```
> 预期：没有报错就表示成功。

**命令 3：检查 Docker 是否安装成功**
```bash
docker --version
```
> 预期输出类似：`Docker version 24.x.x, build xxxxx`
> 如果看到版本号，说明安装成功！

**命令 4：把自己加入 Docker 用户组（避免以后每次都要打 sudo）**
```bash
usermod -aG docker root
```
> 预期：没有报错就表示成功。

---

## 第 2 步：安装 Node.js 18

Node.js 是用来"编译前端页面"的工具。前端代码写完不能直接用浏览器看，需要用 Node.js 把它"打包"成浏览器能读的格式。

**命令 1：添加 Node.js 的下载源**
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
```
> 预计 10-30 秒。

**命令 2：安装 Node.js**
```bash
apt-get install -y nodejs
```
> 预计 30 秒 - 1 分钟。

**命令 3：检查是否安装成功**
```bash
node --version
```
> 预期输出：`v18.x.x`（例如 `v18.20.3`）
> 只要看到 v18 开头就行！

---

## 第 3 步：安装 Hermes Agent

Hermes 是股票分析用的 AI 引擎，后端需要调用它来做分析。

### 情况 A：全新安装（推荐，适用新版 Debian/Ubuntu）

> 📖 新版系统（Debian 12+/Ubuntu 24+）不能用 `pip install` 直接装，需要走 `pipx`。

**命令 1：安装 pipx**
```bash
apt install pipx -y
```

**命令 2：把 pipx 加入 PATH**
```bash
pipx ensurepath
```
> 执行后，关掉当前终端重新连接，或者执行下面这条让 PATH 立即生效：
> ```bash
> export PATH="$PATH:/root/.local/bin"
> ```

**命令 3：用 pipx 安装 Hermes**
```bash
pipx install hermes-agent
```

**命令 4：检查是否安装成功**
```bash
hermes --version
```
> 预期输出：显示 Hermes 的版本号。
> 
> 如果提示 `hermes: command not found`，先执行 `export PATH="$PATH:/root/.local/bin"` 再试。

> 💡 `deploy.sh` 脚本会自动检测 pipx 安装路径并创建软链接，无需手动处理。

---

### 情况 B：你已经在 Docker 里跑着 Hermes

如果你和我一样，之前已经用 Docker 方式部署了 Hermes，并且上面还跑着定时任务，**宿主机上可能没有 `/usr/local/bin/hermes` 这个文件**。

这种情况下，你有两个选择：

**选择 1（简单）：也在宿主机装一份 Hermes CLI**
```bash
apt install pipx -y
pipx ensurepath
pipx install hermes-agent
```
> 这不会影响你 Docker 里的 Hermes，只是多装了一个命令行工具。后端容器通过挂载使用它。

**选择 2：跳过 Hermes 检查，手动调整 docker-compose**
> 第 6 步运行 `deploy.sh` 时，脚本会检测到没有本地 Hermes，会问你是否继续。输入 `y` 继续即可。
> 
> ⚠️ 注意：继续后你需要手动编辑 `docker-compose.yml`，把 backend 和 celery-worker 中挂载 hermes 的行注释掉，否则启动会报错。

---

> 📖 选 A 还是选 B？
> - 新手 → 选 **情况 A**，用 pipx 安装最简单

---

## 第 4 步：下载项目代码

这里是把你 GitHub 上的代码拉到 VPS 上。

> 📖 以下 3 行是 3 个独立命令，打完一行按一次回车，等它跑完再打下一行。

**第 1 个命令：切换到 `/opt` 文件夹**
```bash
cd /opt
```
> 💡 `cd` = **C**hange **D**irectory（切换目录）
> `/opt` 是 Linux 里专门放第三方软件的文件夹。

**第 2 个命令：从 GitHub 下载你的项目**
```bash
git clone https://github.com/zhangsa69/stock-web-system.git
```
> 这个命令跑完后你会看到类似这样的输出：
> ```
> Cloning into 'stock-web-system'...
> remote: Enumerating objects: 80, done.
> ...
> ```
> 出现 "done" 就表示下载完了。

**第 3 个命令：进入下载好的项目文件夹**
```bash
cd stock-web-system
```
> 执行后，你的终端提示符会变成类似：
> ```
> root@racknerd-xxxxx:/opt/stock-web-system#
> ```
> 注意路径末尾变成了 `/opt/stock-web-system`，说明已经进去了。

---

## 第 5 步：配置环境变量

环境变量就是项目的"配置文件"，告诉系统数据库密码是什么、密钥是什么等。

### 5.1 生成随机密钥

先在终端里生成一个 64 位的随机密钥：

```bash
openssl rand -hex 32
```

它会输出类似这样的字符串：
```
a7f3c9e1b2d4f6a8c0e2d4f6a8b0c2e4d6f8a0b2c4e6f8a0c2e4d6f8a0b2c4e6f8
```

**把这串字符复制下来，待会要用！**（鼠标选中 → 右键复制）

### 5.2 创建并编辑配置文件

**命令 1：把配置模板复制一份**
```bash
cp .env.example .env
```
> 💡 `cp` = **c**o**p**y（复制）
> 这行命令的意思是：把 `.env.example`（模板文件）复制一份，新文件叫 `.env`。

**命令 2：打开配置文件进行编辑**
```bash
nano .env
```

这时你会进入一个文本编辑器界面，屏幕上显示类似：
```
POSTGRES_DB=stock_analysis
POSTGRES_USER=stock_user
POSTGRES_PASSWORD=change_me_please
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
...
SECRET_KEY=change_me_to_a_random_string_64_chars
...
```

### 5.3 你需要改的 2 个地方

**修改 1：把数据库密码改掉**

找到这一行：
```
POSTGRES_PASSWORD=change_me_please
```
用方向键移过去，把 `change_me_please` 删掉，输入你自己设的密码。
> ⚠️ 密码最好 8 位以上，包含字母和数字，比如：`WoDeMiMa2024`

**修改 2：把密钥改掉**

找到这一行：
```
SECRET_KEY=change_me_to_a_random_string_64_chars
```
把 `change_me_to_a_random_string_64_chars` 删掉，然后**粘贴**你在 5.1 步生成的那串 64 位字符。

---

### nano 编辑器操作速查

| 你要做什么 | 按什么键 |
|-----------|---------|
| 移动光标 | 键盘的 **↑ ↓ ← →** 方向键 |
| 删除文字 | **Backspace** 键（退格键） |
| 粘贴 | 鼠标右键（Xshell/PuTTY 默认） |
| **保存并退出** | 先按 **Ctrl+O**，然后按**回车**，再按 **Ctrl+X** |
| 放弃修改退出 | 按 **Ctrl+X**，提示保存时按 **N**，再按**回车** |

### 5.4 确认改好了

改完保存后，在终端里执行：

```bash
cat .env
```
> 这行命令会把 `.env` 文件的内容全部打印出来，你确认一下 `POSTGRES_PASSWORD` 和 `SECRET_KEY` 后面确实是你改的值。

---

## 第 6 步：执行部署

这里只有 2 个命令，一个一个执行。

**第 1 个命令：给部署脚本"运行权限"**
```bash
chmod +x deploy.sh
```

| 分解 | 含义 |
|------|------|
| `chmod` | **ch**ange **mod**e，修改文件权限 |
| `+x` | 加上 e**x**ecute（执行）权限 |
| `deploy.sh` | 你的部署脚本文件 |
| 整句话 | **让 `deploy.sh` 这个文件变得可以执行（就像 Windows 里的 .exe 文件）** |

> 预期输出：**没有任何输出**。没有报错就表示成功了。

**第 2 个命令：运行部署脚本**
```bash
./deploy.sh
```

| 分解 | 含义 |
|------|------|
| `./` | 表示"当前文件夹下的" |
| `deploy.sh` | 要运行的文件名 |
| 整句话 | **执行当前文件夹里的 deploy.sh 这个脚本** |

这个脚本会自动帮你做 4 件事：

1. ✅ 检查 Hermes 装好了没
2. ✅ **编译前端**（`npm install` + `npm run build`），这一步需要 **2-5 分钟**，耐心等！
3. ✅ 创建存放数据的文件夹
4. ✅ 启动所有 Docker 服务（数据库、后端、前端等）

你会看到类似这样的输出：

**如果 Hermes 已安装（第 3 步选了 A）：**
```
========================================
  股票分析平台 - VPS 一键部署
========================================

[1/4] 检查 Hermes Agent...
  ✅ Hermes CLI 已就绪
[2/4] 构建前端...
  ✅ 前端构建完成 -> frontend/dist/
[3/4] 准备数据目录...
  ✅ 数据目录已就绪
[4/4] 启动 Docker 服务...
  ✅ 完成

========================================
  🎉 部署完成！
  访问: http://<VPS_IP>
========================================
```

**如果 Hermes 没装（第 3 步选了 B 的选择 2）：**
```
[1/4] 检查 Hermes Agent...
  ⚠ 未在宿主机找到 /usr/local/bin/hermes
  
  如果你已经在 Docker 中运行 Hermes（独立容器），可以跳过此检查。
  ...
  是否继续部署？(y/n)
```
> 此时输入 `y` 按回车即可继续。但后续需要手动调整 docker-compose.yml（脚本会提示具体怎么做）。

> ⚠️ **第 2 步（构建前端）需要从网上下载很多依赖包，大概会跑 3-5 分钟。** 屏幕会一直滚动，请不要关闭终端，耐心等它跑完。

---

## 第 7 步：检查是否运行成功

依次执行以下命令来验证：

**检查 1：看有哪些 Docker 容器在运行**
```bash
docker compose ps
```
> 预期看到 5 个容器，状态都是 `Up`（运行中）：
> - stock-nginx
> - stock-backend
> - stock-celery-worker
> - stock-postgres
> - stock-redis

**检查 2：测试前端能不能访问**
```bash
curl -s http://localhost | head -5
```
> 如果输出一堆 HTML 代码（`<!DOCTYPE html>...`），说明前端正常。

**检查 3：测试后端 API 能不能访问**
```bash
curl -s http://localhost/api/health
```
> 预期输出类似 `{"status":"ok"}`。

---

## 第 8 步：用浏览器访问

打开你的浏览器，在地址栏输入：

```
http://你的VPS的IP地址
```

例如：`http://192.168.1.100` 或 `http://45.xxx.xxx.xxx`

> 💡 你的 VPS IP 地址，可以从 VPS 提供商（RackNerd 等）的后台面板找到。通常是一个类似 `192.x.x.x` 或 `45.x.x.x` 的数字。

---

## 第 9 步：配置防火墙（为了安全！）

只让 22（SSH）、80（网页）、443（HTTPS）端口对外开放：

```bash
ufw allow 22
ufw allow 80
ufw allow 443
ufw enable
```

> 提示 `Command may disrupt existing ssh connections` 时，输入 `y` 按回车。

---

## 服务端口说明

| 服务 | 端口 | 说明 |
|------|------|------|
| Nginx（前端 + API网关） | 80 / 443 | 对外唯一入口 |
| FastAPI | 8000 | 仅内网，Nginx 转发 `/api/` |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 缓存 + 消息队列 |

---

## 日常运维命令速查

### 看日志（出问题时用）
```bash
docker compose logs -f backend           # 看后端日志（实时滚动）
docker compose logs --tail=100           # 看最近 100 行全部日志
```
> 按 `Ctrl+C` 退出日志查看。

### 重启服务
```bash
docker compose restart                   # 重启全部服务
docker compose restart backend           # 只重启后端
docker compose down && docker compose up -d  # 完全重启
```

### 更新代码（以后代码有更新时用）
```bash
cd /opt/stock-web-system
git pull                                 # 拉取最新代码

cd frontend && npm install && npm run build && cd ..   # 重新编译前端

docker compose up -d --build             # 重新构建并启动
```

### 数据库操作
```bash
# 进入 PostgreSQL 数据库
docker exec -it stock-postgres psql -U stock_user -d stock_analysis

# 备份数据库
docker exec stock-postgres pg_dump -U stock_user stock_analysis > backup.sql

# 恢复数据库
cat backup.sql | docker exec -i stock-postgres psql -U stock_user -d stock_analysis
```

### 查看磁盘占用
```bash
docker system df                         # Docker 占了多少空间
du -sh docker-data/*                     # 数据目录各子目录大小
```

---

## 目录结构（了解即可）

```
/opt/stock-web-system/
├── docker-compose.yml      # 服务编排
├── deploy.sh               # 一键部署脚本
├── .env                    # 环境变量（密码等，不要泄露）
├── frontend/dist/          # 编译好的前端页面
├── nginx/nginx.conf        # Nginx 配置
├── backend/                # FastAPI 后端代码
├── docker-data/            # 所有数据存放的地方
│   ├── postgres/           # 数据库文件
│   ├── redis/              # Redis 缓存
│   ├── pdf_cache/          # 分析报告 PDF 缓存
│   └── hermes_sessions/    # Hermes 会话数据
```

---

## 常见问题排查

| 错误提示 | 原因 | 解决办法 |
|---------|------|---------|
| `pip: command not found` | pip 没装 | `apt install python3-pip -y` |
| `externally-managed-environment` | 新版系统禁用了 pip 直接安装 | 改用 `pipx install hermes-agent`，参考第 3 步 |
| `hermes: command not found` | Hermes 没装或 PATH 没更新 | `pipx ensurepath` 或 `export PATH="$PATH:/root/.local/bin"` |
| `未在宿主机找到 /usr/local/bin/hermes` | Hermes 路径不在标准位置 | 创建软链接：`ln -s ~/.local/bin/hermes /usr/local/bin/hermes` |
| `node: command not found` | Node.js 没装 | 回到第 2 步重新安装 |
| `docker: command not found` | Docker 没装 | 回到第 1 步重新安装 |
| `port is already allocated` | 端口被占用 | 执行 `docker compose down` 后再 `docker compose up -d` |
| 浏览器打开是空白页 | 前端没编译好 | 进入 `frontend` 目录，重新 `npm run build` |
| 前端 404 | Nginx 配置有问题 | 执行 `docker compose restart nginx` |
| 数据库连接失败 | 密码不对 | 检查 `.env` 中的 `POSTGRES_PASSWORD` 是否一致 |

---

## 免费 SSL 证书（有域名时用）

如果你有域名，可以申请免费 HTTPS 证书：

```bash
apt install certbot python3-certbot-nginx
certbot --nginx -d 你的域名
```

---

> 🎉 恭喜！按照以上步骤操作，你的股票分析系统就部署完毕了！
>
> 如果在某一步遇到问题，把终端的**完整错误信息**复制发给我，我来帮你排查。
