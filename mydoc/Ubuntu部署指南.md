# NoteAgents Ubuntu 服务器部署指南

## 目录

- [环境要求](#环境要求)
- [服务器配置](#服务器配置)
- [安装步骤](#安装步骤)
- [配置说明](#配置说明)
- [运行方式](#运行方式)
- [系统服务配置](#系统服务配置)
- [反向代理配置](#反向代理配置)
- [安全设置](#安全设置)
- [常见问题](#常见问题)

---

## 环境要求

### 硬件要求

| 配置 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 1核 | 2核+ |
| 内存 | 1GB | 2GB+ |
| 磁盘 | 10GB | 20GB+ |
| 带宽 | 1Mbps | 5Mbps+ |

### 软件要求

- **操作系统**: Ubuntu 20.04 LTS / 22.04 LTS / 24.04 LTS
- **Python**: 3.12+
- **包管理器**: uv (推荐) 或 pip
- **内存**: 建议 2GB 以上

---

## 服务器配置

### 1. 系统更新

```bash
# 更新系统软件包
sudo apt update && sudo apt upgrade -y

# 安装基础工具
sudo apt install -y curl wget git vim unzip zip
```

### 2. 创建部署用户

```bash
# 创建专用用户（推荐）
sudo adduser noteagents

# 添加到 sudo 组（如果需要）
sudo usermod -aG sudo noteagents

# 切换到部署用户
sudo su - noteagents
```

### 3. 安装 Python 环境

Ubuntu 22.04+ 自带 Python 3.12，可以直接使用：

```bash
# 检查 Python 版本
python3 --version

# 安装 pip（如果没有）
curl -sS https://bootstrap.pypa.io/get-pip.py | sudo python3

# 安装 uv 包管理器（推荐）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 激活 uv 环境
source $HOME/.cargo/env
```

或者使用 pip 安装 uv：

```bash
pip3 install uv
```

---

## 安装步骤

### 1. 上传项目文件

**方式一：使用 Git 克隆**

```bash
cd /home/noteagents
git clone https://your-repo-url/NoteAgents.git
cd NoteAgents
```

**方式二：使用 SCP 上传**

```bash
# 在本地执行
scp -r ./NoteAgents noteagents@your-server-ip:/home/noteagents/
```

### 2. 创建虚拟环境

```bash
cd /home/noteagents/NoteAgents

# 使用 uv 创建虚拟环境（推荐）
uv venv .venv

# 激活虚拟环境
source .venv/bin/activate
```

### 3. 安装依赖

```bash
# 使用 uv 安装依赖（推荐，速度快）
uv pip install -r requirements.txt

# 或者使用 pip 安装
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
vim .env
```

---

## 配置说明

### 基础配置 (.env)

```ini
# Telegram Bot 配置（必需）
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# LLM API 配置（至少配置一个）
# OpenAI
OPENAI_API_KEY=your_openai_api_key

# 通义千问（阿里云）
DASHSCOPE_API_KEY=your_dashscope_api_key

# Anthropic Claude
ANTHROPIC_API_KEY=your_anthropic_api_key

# Google Gemini
GOOGLE_API_KEY=your_google_api_key

# DeepSeek
DEEPSEEK_API_KEY=your_deepseek_api_key

# LLM 模型配置
DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-3.5-turbo

# 用户白名单（逗号分隔的 Telegram 用户 ID）
WHITELIST_USERS=123456789,987654321

# Obsidian 笔记存储路径
OBSIDIAN_VAULT_PATH=/home/noteagents/obsidian-vault

# GitHub 同步配置（可选）
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_REPO=your_username/your-repo

# 日志级别
LOG_LEVEL=INFO
```

### Telegram Bot 创建步骤

1. 在 Telegram 中搜索 `@BotFather`
2. 发送 `/newbot` 创建新机器人
3. 按提示输入机器人名称和用户名
4. 复制获得的 Bot Token 并填入 `.env` 文件
5. 添加机器人管理员：`/setprivacy` 选择 `Disable`

### LLM API 获取

**OpenAI API Key**
- 访问 https://platform.openai.com/api-keys
- 创建新的 API Key

**通义千问 API Key（阿里云百炼）**
- 访问 https://bailian.console.aliyun.com/
- 申请开通模型服务并获取 API Key

**Anthropic Claude API Key**
- 访问 https://console.anthropic.com/
- 创建 API Key

**Google Gemini API Key**
- 访问 https://aistudio.google.com/apikey
- 创建 API Key

**DeepSeek API Key**
- 访问 https://platform.deepseek.com/
- 创建 API Key

---

## 运行方式

### 方式一：直接运行（开发环境）

```bash
cd /home/noteagents/NoteAgents
source .venv/bin/activate
python main.py
```

### 方式二：使用 Screen（推荐用于后台运行）

```bash
# 安装 screen
sudo apt install -y screen

# 创建新的 screen 会话
screen -S noteagents

# 在 screen 中运行
cd /home/noteagents/NoteAgents
source .venv/bin/activate
python main.py

# 分离 screen 会话：按 Ctrl+A，然后按 D
# 重新连接：screen -r noteagents
```

### 方式三：使用 tmux（替代方案）

```bash
# 安装 tmux
sudo apt install -y tmux

# 创建 tmux 会话
tmux new -s noteagents

# 在 tmux 中运行
cd /home/noteagents/NoteAgents
source .venv/bin/activate
python main.py

# 分离 tmux 会话：按 Ctrl+B，然后按 D
# 重新连接：tmux attach -t noteagents
```

---

## 系统服务配置

### 创建 Systemd 服务

创建服务文件：

```bash
sudo vim /etc/systemd/system/noteagents.service
```

添加以下内容：

```ini
[Unit]
Description=NoteAgents - Telegram AI Note Collection System
After=network.target

[Service]
Type=simple
User=noteagents
WorkingDirectory=/home/noteagents/NoteAgents
Environment=PATH=/home/noteagents/NoteAgents/.venv/bin
ExecStart=/home/noteagents/NoteAgents/.venv/bin/python main.py
Restart=always
RestartSec=10

# 日志配置
StandardOutput=journal
StandardError=journal
SyslogIdentifier=noteagents

[Install]
WantedBy=multi-user.target
```

设置权限并启用服务：

```bash
# 重新加载 systemd 配置
sudo systemctl daemon-reload

# 设置开机自启
sudo systemctl enable noteagents

# 启动服务
sudo systemctl start noteagents

# 查看服务状态
sudo systemctl status noteagents

# 查看日志
sudo journalctl -u noteagents -f
```

### 服务管理命令

```bash
# 启动服务
sudo systemctl start noteagents

# 停止服务
sudo systemctl stop noteagents

# 重启服务
sudo systemctl restart noteagents

# 查看状态
sudo systemctl status noteagents

# 查看实时日志
sudo journalctl -u noteagents -f

# 禁用开机自启
sudo systemctl disable noteagents
```

---

## 反向代理配置

### 安装 Nginx

```bash
sudo apt install -y nginx
```

### 配置 Nginx

创建配置文件：

```bash
sudo vim /etc/nginx/sites-available/noteagents
```

添加以下内容（如果需要 Webhook 回调）：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用站点：

```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/noteagents /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx
```

### 配置 SSL（Let's Encrypt）

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取 SSL 证书
sudo certbot --nginx -d your-domain.com

# 自动续期测试
sudo certbot renew --dry-run
```

---

## 安全设置

### 1. 防火墙配置

```bash
# 安装 ufw
sudo apt install -y ufw

# 配置规则
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 启用防火墙
sudo ufw enable
```

### 2. 设置 Fail2Ban（防暴力破解）

```bash
# 安装
sudo apt install -y fail2ban

# 启动
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3. 文件权限设置

```bash
# 设置目录权限
chmod 700 /home/noteagents/NoteAgents/.env
chmod 700 /home/noteagents/NoteAgents/.venv

# 设置所有者
sudo chown -R noteagents:noteagents /home/noteagents/NoteAgents
```

### 4. 定期备份

创建备份脚本 `/home/noteagents/backup.sh`：

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/home/noteagents/backups
NOTEAGENTS_DIR=/home/noteagents/NoteAgents

mkdir -p $BACKUP_DIR

# 备份笔记
tar -czf $BACKUP_DIR/notes_$DATE.tar.gz $NOTEAGENTS_DIR/storage/

# 保留最近 30 天的备份
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

添加定时任务：

```bash
# 编辑 crontab
crontab -e

# 添加每日凌晨 3 点执行备份
0 3 * * * /home/noteagents/backup.sh >> /home/noteagents/backup.log 2>&1
```

---

## 常见问题

### 1. 依赖安装失败

**问题**: `uv` 或 `pip` 安装依赖时出现错误

**解决**:
```bash
# 更新 pip
pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. 权限错误

**问题**: `Permission denied` 错误

**解决**:
```bash
# 检查文件所有者
ls -la /home/noteagents/NoteAgents

# 修改所有者
sudo chown -R noteagents:noteagents /home/noteagents/NoteAgents
```

### 3. 机器人无响应

**解决**:
```bash
# 检查服务状态
sudo systemctl status noteagents

# 查看日志
sudo journalctl -u noteagents -n 100

# 重启服务
sudo systemctl restart noteagents
```

### 4. LLM API 调用失败

**解决**:
```bash
# 检查 API Key 配置
cat /home/noteagents/NoteAgents/.env | grep API_KEY

# 测试 API 连接
curl -H "Authorization: Bearer YOUR_API_KEY" https://api.openai.com/v1/models
```

### 5. 内存不足

**解决**:
```bash
# 创建交换文件
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 6. 更新代码后重启服务

```bash
cd /home/noteagents/NoteAgents
git pull

# 重新安装依赖（如果 requirements.txt 有变化）
source .venv/bin/activate
uv pip install -r requirements.txt

# 重启服务
sudo systemctl restart noteagents
```

---

## 快速命令参考

```bash
# 启动服务
sudo systemctl start noteagents

# 停止服务
sudo systemctl stop noteagents

# 重启服务
sudo systemctl restart noteagents

# 查看状态
sudo systemctl status noteagents

# 查看日志
sudo journalctl -u noteagents -f

# 进入项目目录
cd /home/noteagents/NoteAgents

# 激活环境
source .venv/bin/activate

# 手动运行（调试用）
python main.py
```

---

## 技术支持

如有问题，请检查：
1. 日志文件：`sudo journalctl -u noteagents -n 200`
2. `.env` 配置文件是否正确
3. API Key 是否有效
4. 网络连接是否正常
