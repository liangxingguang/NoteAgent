# 飞书 Webhook 模式使用指南

## 📋 目录

1. [Webhook 模式简介](#webhook-模式简介)
2. [与轮询模式对比](#与轮询模式对比)
3. [快速开始](#快速开始)
4. [详细配置步骤](#详细配置步骤)
5. [事件订阅配置](#事件订阅配置)
6. [常见问题](#常见问题)
7. [安全建议](#安全建议)

---

## Webhook 模式简介

Webhook 模式是飞书机器人的推荐接收方式，相比轮询模式，具有以下优势：

- ✅ **实时性高**：消息即时推送，无延迟
- ✅ **资源占用低**：不需要持续轮询请求
- ✅ **API 调用少**：减少 API 调用次数，避免限流
- ✅ **官方推荐**：飞书开放平台推荐的方式

---

## 与轮询模式对比

| 特性 | Webhook 模式 | 轮询模式 |
|------|--------------|----------|
| 实时性 | ⚡ 实时 | 🐌 有延迟（取决于轮询间隔）|
| 资源占用 | 低 | 较高 |
| API 调用 | 仅事件推送 | 持续轮询 |
| 公网 IP | ✅ 需要 | ❌ 不需要 |
| 复杂度 | 中等 | 简单 |
| 推荐度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## 快速开始

### 1. 环境要求

- 公网可访问的服务器/主机（或使用内网穿透工具）
- 可选：域名（推荐使用 HTTPS）
- NoteAgents v0.2+

### 2. 配置 .env 文件

```env
# === 飞书 Configuration ===
# 启用飞书
FEISHU_ENABLED=true

# 飞书应用凭证
FEISHU_APP_ID=cli_xxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxx

# Webhook 模式开启
FEISHU_USE_WEBHOOK=true
FEISHU_WEBHOOK_HOST=0.0.0.0
FEISHU_WEBHOOK_PORT=8000

# 验证令牌（从飞书开放平台获取）
FEISHU_VERIFICATION_TOKEN=xxxxxxxxxxxxx

# 授权用户
FEISHU_ALLOWED_USER_IDS=ou_xxxxxxxxxxxxx
```

### 3. 启动程序

```bash
# Windows
.venv\Scripts\python.exe main_multi.py

# Linux/Mac
source .venv/bin/activate
python main_multi.py
```

### 4. 检查服务是否正常

访问 `http://your-server-ip:8000/health` 检查：

```json
{"status": "ok"}
```

---

## 详细配置步骤

### 第一步：创建飞书应用

1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 点击「创建应用」→「创建企业自建应用」
3. 填写应用信息：
   - 应用名称：NoteAgents
   - 应用描述：AI 笔记自动收集助手
   - 应用图标：上传自定义图标

4. 创建后，在「凭证与基础信息」页面获取：
   - App ID（即 `FEISHU_APP_ID`）
   - App Secret（即 `FEISHU_APP_SECRET`）

### 第二步：添加应用能力

1. 在应用详情页，进入「添加应用能力」
2. 添加「机器人」能力
3. 配置机器人信息：
   - 机器人名称：NoteAgents
   - 机器人头像：上传头像
   - 机器人简介：AI 笔记自动收集助手

### 第三步：配置权限

进入「权限管理」页面，添加以下权限：

| 权限名称 | 权限代码 | 用途 |
|----------|----------|------|
| 获取与发送单聊消息 | `im:message` | 发送/接收消息 |
| 获取与上传文件 | `im:resource` | 下载文件 |

选中权限后，点击「批量申请」。

### 第四步：配置事件订阅

这是 Webhook 模式的关键步骤：

1. 进入「事件订阅」页面
2. 点击「开启事件订阅」
3. 配置请求网址 URL：

   ```
   https://your-domain.com/feishu/webhook
   ```

   如果使用 IP 地址（不推荐生产环境）：

   ```
   http://your-server-ip:8000/feishu/webhook
   ```

4. 配置 Encrypt Key（可选但推荐）：
   - 点击「随机生成」
   - 复制后填入 `.env` 的 `FEISHU_ENCRYPT_KEY`

5. 配置 Verification Token：
   - 系统自动生成
   - 复制后填入 `.env` 的 `FEISHU_VERIFICATION_TOKEN`

6. 点击「保存」，飞书会发送验证请求

7. 验证成功后，添加事件：

   | 事件类型 | 事件代码 | 用途 |
   |----------|----------|------|
   | 接收消息 v2 | `im.message.receive_v1` | 接收用户消息 |

8. 点击「添加事件」，选择上述事件后保存

### 第五步：创建版本并发布

1. 进入「版本管理与发布」页面
2. 点击「创建版本」
3. 填写版本信息：
   - 版本号：0.1.0
   - 更新日志：首次发布
4. 点击「保存」→「申请发布」
5. 选择发布范围：
   - 「仅自己」：测试使用，仅自己可用
   - 「全员」或「部分人员」：正式使用

6. 提交审核（企业自建应用通常审核很快）

### 第六步：在飞书中找到机器人

审核通过后：
1. 打开飞书
2. 搜索「NoteAgents」
3. 开始聊天！

---

## 事件订阅配置详解

### 支持的事件

当前版本支持以下飞书事件：

- `im.message.receive_v1` - 接收消息事件

### 事件处理流程

```
飞书服务器
    ↓ POST
Webhook 端点 (/feishu/webhook)
    ↓ 验证请求
消息解析和转换
    ↓
权限检查
    ↓
业务处理（AI 总结、Obsidian 入库）
    ↓
返回响应 {"code": 0, "msg": "success"}
```

### 健康检查端点

除了 Webhook 端点，还提供健康检查：

```
GET /health
```

响应：
```json
{"status": "ok"}
```

---

## 内网穿透方案

如果你没有公网服务器，可以使用内网穿透工具：

### 方案一：使用 ngrok

1. 下载 [ngrok](https://ngrok.com/)
2. 运行命令：

```bash
ngrok http 8000
```

3. 复制类似 `https://abc123.ngrok.io` 的公网地址
4. 填入飞书开放平台的事件订阅 URL：

```
https://abc123.ngrok.io/feishu/webhook
```

注意：ngrok 免费版域名会定期变化，适合开发测试。

### 方案二：使用花生壳/frp

类似地，配置内网穿透到本地的 8000 端口。

---

## 部署建议

### 使用 HTTPS

生产环境强烈建议使用 HTTPS：

1. 使用 Nginx 或 Caddy 反向代理
2. 配置 Let's Encrypt 免费证书

Nginx 配置示例：

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /feishu/webhook {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

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

### Q1: 飞书验证失败怎么办？

**A:** 检查以下几点：

1. 确认服务已启动并正常运行
2. 检查 Verification Token 是否正确
3. 查看 NoteAgents 日志中的错误信息
4. 确认公网访问是否正常（防火墙、安全组）

### Q2: 可以同时使用 Webhook 和轮询吗？

**A:** 不可以。同一时间只能使用一种模式，配置 `FEISHU_USE_WEBHOOK=true/false` 切换。

### Q3: Webhook 模式需要公网 IP 吗？

**A:** 是的，飞书服务器需要能访问到你的 Webhook URL。如果没有公网服务器，可以使用内网穿透。

### Q4: 消息处理失败怎么办？

**A:** 查看日志定位问题：

1. 检查是否有权限错误
2. 检查 AI API 是否正常
3. 检查 Obsidian 路径配置
4. 查看具体错误信息

### Q5: 如何获取用户 open_id？

**A:** 有两种方式：

1. 给机器人发送任意消息，查看日志中的 `user_id`
2. 在 Webhook 事件数据中查看 `sender.sender_id.open_id`

### Q6: Webhook 请求需要多久响应？

**A:** 飞书要求在 3 秒内响应，NoteAgents 采用异步处理，响应非常快。

---

## 安全建议

### 1. 使用 Verification Token

始终配置并验证 `FEISHU_VERIFICATION_TOKEN`，防止伪造请求。

### 2. 使用 Encrypt Key（可选但推荐）

启用消息加密，保护数据传输安全。

### 3. 使用 HTTPS

生产环境务必使用 HTTPS 协议。

### 4. 最小权限原则

只申请必要的权限：
- `im:message`
- `im:resource`

### 5. 控制授权用户列表

在 `FEISHU_ALLOWED_USER_IDS` 中明确列出允许使用的用户，防止滥用。

### 6. 定期轮换密钥

定期更换 App Secret、Verification Token 等密钥。

---

## 附录：Webhook 请求示例

### 飞书发送的请求示例

```json
{
    "header": {
        "event_id": "5e3702a8e85935935d51e6e429f302d1",
        "token": "41a9425ea7df4536a7623ea76a86cd55",
        "create_time": "1609073151380",
        "event_type": "im.message.receive_v1",
        "tenant_key": "2ca1d211f64f6438",
        "app_id": "cli_xxxxxxxxxxxxx"
    },
    "event": {
        "sender": {
            "sender_id": {
                "union_id": "on_xxxxxxxxxxxxx",
                "user_id": "5gxxxxx",
                "open_id": "ou_xxxxxxxxxxxxx"
            },
            "sender_type": "user",
            "tenant_key": "2ca1d211f64f6438"
        },
        "message": {
            "message_id": "om_xxxxxxxxxxxxx",
            "root_id": "",
            "parent_id": "",
            "create_time": "1609073151380",
            "chat_id": "oc_xxxxxxxxxxxxx",
            "chat_type": "p2p",
            "message_type": "text",
            "content": "{\"text\":\"Hello World\"}"
        }
    }
}
```

---

## 获取帮助

如有问题，请：
1. 查看日志文件
2. 检查本文档的常见问题部分
3. 参考飞书开放平台官方文档

---

**文档版本**：1.0
**最后更新**：2026-05-02
