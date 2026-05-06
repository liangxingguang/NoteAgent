# Telegram Webhook 模式使用指南

## 📋 目录

1. [Webhook 模式简介](#webhook-模式简介)
2. [与轮询模式对比](#与轮询模式对比)
3. [快速开始](#快速开始)
4. [详细配置步骤](#详细配置步骤)
5. [内网穿透方案](#内网穿透方案)
6. [部署建议](#部署建议)
7. [常见问题](#常见问题)
8. [安全建议](#安全建议)

---

## Webhook 模式简介

Webhook 模式是 Telegram Bot 的推荐接收方式，相比轮询模式，具有以下优势：

- ✅ **实时性高**：消息即时推送，无延迟
- ✅ **资源占用低**：不需要持续轮询请求
- ✅ **API 调用少**：减少 API 调用次数，避免限流
- ✅ **官方推荐**：Telegram 官方推荐的方式

---

## 与轮询模式对比

| 特性 | Webhook 模式 | 轮询模式 |
|------|--------------|----------|
| 实时性 | ⚡ 实时 | 🐌 有延迟（取决于轮询间隔）|
| 资源占用 | 低 | 较高 |
| API 调用 | 仅事件推送 | 持续轮询 |
| HTTPS 证书 | ✅ 需要（除 localhost） | ❌ 不需要 |
| 复杂度 | 中等 | 简单 |
| 推荐度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## 快速开始

### 1. 环境要求

- 公网可访问的服务器/主机（或使用内网穿透工具）
- 有效的 HTTPS 证书（可选 localhost 开发时）
- NoteAgents v0.2+

### 2. 配置 .env 文件

```env
# === Telegram 配置 ===
# 机器人 Token（从 @BotFather 获取）
TG_BOT_TOKEN=your_bot_token_here

# Webhook 模式启用
TG_USE_WEBHOOK=true

# Webhook URL（外网可访问的 HTTPS 地址）
TG_WEBHOOK_URL=https://your-domain.com/telegram/webhook

# Webhook 服务器监听地址和端口
TG_WEBHOOK_HOST=0.0.0.0
TG_WEBHOOK_PORT=8443  # Telegram 支持的端口：443, 80, 88, 8443

# Webhook 密钥（可选但推荐，用于验证请求来源）
TG_WEBHOOK_SECRET=your_secret_key_here

# 轮询配置（当 webhook 禁用时使用）
TG_POLL_INTERVAL=1.0
TG_POLL_TIMEOUT=20
```

### 3. 启动程序

```bash
# Windows
.venv\Scripts\python.exe main_multi.py

# Linux/Mac
source .venv/bin/activate
python main_multi.py
```

### 4. 检查 webhook 设置

查看日志确认 webhook 设置成功：

```
INFO:Telegram适配器初始化成功
INFO:Telegram适配器启动Webhook模式
INFO:Telegram Webhook设置成功: https://your-domain.com/telegram/webhook
```

---

## 详细配置步骤

### 第一步：创建 Telegram Bot

1. 在 Telegram 中搜索 `@BotFather`
2. 发送 `/newbot` 命令
3. 按照提示设置：
   - 机器人名称（显示名称）
   - 机器人用户名（必须以 `bot` 结尾）
4. BotFather 会给出一个 Token，这就是 `TG_BOT_TOKEN`
5. 建议发送 `/setcommands` 设置命令列表

### 第二步：获取 HTTPS 证书

Telegram Webhook 要求必须使用 HTTPS（开发时可以使用 localhost）。

**选项 A：使用自签名证书（不推荐生产）**

```bash
# 生成自签名证书
openssl req -newkey rsa:2048 -sha256 -nodes -keyout private.key -x509 -days 365 -out cert.pem -subj "/CN=your-domain.com"
```

**选项 B：使用 Let's Encrypt（推荐生产）**

使用 Certbot 自动获取免费证书。

**选项 C：使用内网穿透工具（开发测试）**

使用 ngrok 等工具，它们会自动提供 HTTPS 证书。

### 第三步：配置 Webhook URL

确保你的 Webhook URL：
- 使用 HTTPS（开发时可以是 http://localhost:port）
- 响应 `/telegram/webhook` 路径
- 端口必须是 443, 80, 88, 或 8443
- 使用有效的证书（自签名需要上传到 Telegram）

### 第四步：配置安全设置（可选但推荐）

1. 设置 `TG_WEBHOOK_SECRET` 用于验证请求
2. 在 Nginx/Caddy 等反向代理中配置证书

---

## 内网穿透方案

如果你没有公网服务器，可以使用内网穿透工具。

### 方案一：使用 ngrok（推荐）

1. 下载 [ngrok](https://ngrok.com/)
2. 运行命令：

```bash
ngrok http 8443
```

3. ngrok 会提供一个 HTTPS 地址，例如：
   `https://abc123.ngrok-free.app`

4. 将地址配置到 `.env`：

```env
TG_WEBHOOK_URL=https://abc123.ngrok-free.app/telegram/webhook
TG_WEBHOOK_PORT=8443
```

注意：ngrok 免费版域名会定期变化，适合开发测试。

### 方案二：使用 Cloudflare Tunnel（推荐稳定）

1. 注册 Cloudflare 账号
2. 配置 Cloudflare Tunnel

```bash
# 安装 cloudflared
# Windows: 下载安装包
# Linux: 参照官方文档

# 配置隧道
cloudflared tunnel --url localhost:8443
```

Cloudflare Tunnel 提供稳定的 HTTPS 连接。

---

## 部署建议

### 使用 Nginx 反向代理

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/private.key;

    location /telegram/webhook {
        proxy_pass http://127.0.0.1:8443;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 使用 Caddy（自动 HTTPS）

```caddyfile
your-domain.com {
    reverse_proxy /telegram/webhook localhost:8443
}
```

Caddy 会自动配置和更新 Let's Encrypt 证书。

### 使用 systemd 管理服务（Linux）

创建 `/etc/systemd/system/noteagents.service`：

```ini
[Unit]
Description=NoteAgents AI Note Bot
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/NoteAgents
ExecStart=/path/to/NoteAgents/.venv/bin/python main_multi.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable noteagents
sudo systemctl start noteagents
sudo systemctl status noteagents
```

---

## 常见问题

### Q1：Telegram 验证连接失败怎么办？

**A：** 检查以下几点：
1. 确保服务已启动并正常运行
2. 检查 HTTPS 证书是否有效
3. 检查防火墙和安全组设置
4. 确认端口是 443, 80, 88, 或 8443
5. 查看日志中的错误信息

### Q2：可以同时使用 Webhook 和轮询吗？

**A：** 不可以。同一时间只能使用一种模式，配置 `TG_USE_WEBHOOK=true/false` 切换。切换时系统会自动清理旧的 webhook 设置。

### Q3：Webhook 模式需要 HTTPS 吗？

**A：** 是的，生产环境必须使用 HTTPS。开发测试时可以使用 `localhost` 地址。

### Q4：如何查看当前 Webhook 设置？

**A：** 使用 Bot API 查看：

```bash
curl "https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
```

或者查看 NoteAgents 的启动日志。

### Q5：如何清除 Webhook 设置？

**A：** 有两种方式：
1. 将 `TG_USE_WEBHOOK` 设为 `false`，系统会自动清除
2. 手动调用 API：

```bash
curl "https://api.telegram.org/bot{TOKEN}/deleteWebhook"
```

### Q6：自签名证书如何上传？

**A：** 可以使用 API 上传：

```bash
curl -F "certificate=@cert.pem" "https://api.telegram.org/bot{TOKEN}/setWebhook?url=https://your-domain.com/telegram/webhook"
```

或者使用 python-telegram-bot 内置功能（我们的系统会自动处理）。

---

## 安全建议

### 1. 使用 Webhook Secret

配置 `TG_WEBHOOK_SECRET` 来验证请求确实来自 Telegram。

### 2. 使用 HTTPS

生产环境务必使用受信任的 HTTPS 证书，不要使用自签名证书。

### 3. 配置防火墙

限制只有 Telegram IP 可以访问 Webhook 端口（可选但推荐）。

### 4. 最小权限原则

只给机器人必要的权限（通过 @BotFather 设置）。

### 5. 定期更新

定期更新依赖库，特别是安全相关更新。

---

## 附录：环境变量完整列表

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `TG_BOT_TOKEN` | (必填) | Telegram Bot Token |
| `TG_USE_WEBHOOK` | `false` | 是否启用 Webhook 模式 |
| `TG_WEBHOOK_URL` | - | Webhook 回调 URL |
| `TG_WEBHOOK_HOST` | `0.0.0.0` | Webhook 服务器监听地址 |
| `TG_WEBHOOK_PORT` | `8443` | Webhook 服务器监听端口 |
| `TG_WEBHOOK_SECRET` | - | Webhook 验证密钥 |
| `TG_POLL_INTERVAL` | `1.0` | 轮询模式下的轮询间隔 |
| `TG_POLL_TIMEOUT` | `20` | 轮询模式下的超时时间 |

---

## 获取帮助

如有问题，请：
1. 查看日志文件
2. 检查本文档的常见问题部分
3. 参考 [python-telegram-bot 官方文档](https://python-telegram-bot.readthedocs.io/)
4. 参考 [Telegram Bot API 文档](https://core.telegram.org/bots/api)

---

**文档版本：** 1.0  
**最后更新：** 2026-05-03
