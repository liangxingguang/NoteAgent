# NoteAgents - Telegram AI Note Auto Collection System

基于自定义AI Agent的Telegram AI笔记自动收集系统。

## 功能特性

- 📝 **文本/链接处理** - 直接发送文本或链接，自动生成Obsidian笔记
- 🌐 **网页内容下载** - 支持下载微博、微信公众号等网页内容并转换为Markdown
- 📄 **文件支持** - 支持PDF、Word、TXT文件，自动提取内容并总结
- 🤖 **AI总结** - 集成第三方AI（通义千问、OpenAI、Claude、Gemini、DeepSeek等），智能生成笔记
- 💾 **Obsidian集成** - 笔记自动保存到本地Obsidian知识库
- 🔀 **GitHub同步** - 支持将笔记推送备份到GitHub仓库
- 🔒 **权限控制** - 白名单用户访问，防止滥用
- 🛡️ **异常处理** - 完善的错误处理和自动恢复机制
- 📊 **日志记录** - 详细的操作日志，便于排查问题
- 🌊 **流式输出** - 支持AI响应流式输出
- 🔧 **多LLM支持** - 统一适配OpenAI、Anthropic、Gemini、DeepSeek等多种模型

## 支持的内容类型

| 类型 | 支持格式 | 说明 |
|------|----------|------|
| 文本 | 直接发送 | 自动总结 |
| 链接 | 微博、微信公众号、博客等 | 自动下载内容并总结 |
| 文件 | PDF、DOCX、TXT | 自动提取文本并总结 |

## 支持的AI模型

| 提供商 | 模型 | 说明 |
|--------|------|------|
| OpenAI | gpt-3.5-turbo, gpt-4, gpt-4-turbo, o1, o1-mini | OpenAI官方模型 |
| 通义千问 | qwen-turbo, qwen-plus, qwen-max | 阿里云百炼模型 |
| Anthropic | claude-3-haiku, claude-3-sonnet, claude-3-opus | Claude系列模型 |
| Google | gemini-pro, gemini-1.5-pro | Google Gemini模型 |
| DeepSeek | deepseek-chat, deepseek-coder, deepseek-reasoner | DeepSeek系列模型 |

## 技术架构

项目采用**混合架构**，结合传统模块化设计和自定义AI Agent模式：

```
NoteAgents/
├── agent/              # AI Agent核心层
│   ├── perception.py   # 感知模块 - 消息接收、解析
│   ├── decision.py     # 决策模块 - 意图识别、工具选择
│   ├── task_scheduler.py # 任务调度 - 任务拆解、执行
│   └── exception_handler.py # 异常处理 - 自愈、反馈
├── tools/              # 业务工具层
│   ├── tg_tool.py      # Telegram消息工具
│   ├── file_tool.py    # 文件处理工具
│   ├── ai_summary_tool.py # AI总结工具
│   ├── obsidian_tool.py # Obsidian入库工具
│   ├── temp_clean_tool.py # 临时文件清理
│   ├── web_tool.py    # 网页内容下载工具
│   ├── github_tool.py  # GitHub推送工具
│   ├── model_adapter.py # 多LLM适配器
│   ├── llm.py          # LLM响应类型定义
│   └── llm_adapters.py # LLM适配器实现
├── storage/            # 存储层
│   ├── temp_files/     # 临时文件
│   ├── logs/           # 日志文件
│   ├── temp_manager.py
│   ├── log_manager.py
│   └── context_cache.py
├── config/             # 配置层
│   └── config.py       # 配置管理
├── utils/              # 工具函数
├── test/               # 测试套件
│   ├── conftest.py     # pytest配置
│   ├── test_config.py  # 配置模块测试
│   ├── test_utils.py   # 工具模块测试
│   ├── test_llm_adapters.py # LLM适配器测试
│   ├── test_web_tool.py # 网页工具测试
│   └── test_github_tool.py # GitHub工具测试
├── main.py             # 入口文件
├── requirements.txt    # 依赖列表
├── pyproject.toml     # 项目配置
├── setup.bat          # Windows初始化脚本 (uv)
├── setup.sh           # Linux/macOS初始化脚本 (uv)
└── .python-version    # Python版本
```

## 快速开始

### 1. 环境要求

- Python 3.12+
- 能够访问Telegram的网络环境
- 第三方AI API Key（通义千问、OpenAI、Claude等）

### 2. 安装依赖（使用 uv）

[uv](https://github.com/astral-sh/uv) 是一个用Rust编写的超快速Python包安装器，比传统pip快10-100倍。

```bash
# Windows (使用PowerShell或CMD)
.\setup.bat

# Linux/macOS
chmod +x setup.sh
./setup.sh
```

或者手动使用uv：

```bash
# 安装uv (如果未安装)
pip install uv

# 创建虚拟环境
uv venv .venv

# 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
# 或: .venv\Scripts\activate  # Windows

# 安装依赖
uv pip install -r requirements.txt
```

### 3. 配置

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
# 填入你的配置：
# - TG_BOT_TOKEN
# - ALLOWED_USER_IDS
# - AI_API_KEY
# - AI_MODEL
# - AI_BASE_URL (可选)
# - OBSIDIAN_VAULT_PATH
```

### 4. 获取配置

#### 获取Telegram Bot Token

1. 访问 [@BotFather](https://t.me/BotFather)
2. 发送 `/newbot`
3. 按照提示创建机器人
4. 复制获取到的Token

#### 获取用户ID

1. 访问 [@userinfobot](https://t.me/userinfobot)
2. 发送任意消息
3. 复制获取到的ID

#### 获取AI API Key

**通义千问（推荐）**：
- 访问 [阿里云百炼](https://bailian.console.aliyun.com/)
- 创建API Key
- 模型选择：`qwen-turbo`, `qwen-plus`, `qwen-max`

**OpenAI**：
- 访问 [OpenAI API](https://platform.openai.com/api-keys)
- 创建API Key

**Anthropic Claude**：
- 访问 [Anthropic Console](https://console.anthropic.com/)
- 创建API Key

**Google Gemini**：
- 访问 [Google AI Studio](https://aistudio.google.com/)
- 创建API Key

**DeepSeek**：
- 访问 [DeepSeek API](https://platform.deepseek.com/)
- 创建API Key

### 5. 运行

```bash
# 开发模式
python main.py

# 生产模式（后台运行，使用systemd）
# 参考下文"部署"章节
```

### 6. 使用

1. 在Telegram中找到你的机器人
2. 发送 `/start` 开始使用
3. 发送以下类型的内容：
   - **文本**：直接输入文字
   - **链接**：发送微博、微信公众号、博客等链接
   - **文件**：上传PDF、DOCX、TXT文件
4. 等待AI处理，笔记自动保存到Obsidian
5. 可选：发送 `/push` 将最新笔记推送到GitHub
6. 可选：发送 `/pull` 从GitHub拉取笔记到本地

## 测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest test/test_config.py

# 运行特定测试类
pytest test/test_llm_adapters.py::TestModelPresets

# 带覆盖率报告
pytest --cov=tools --cov-report=html

# 显示详细输出
pytest -v
```

## 配置说明

| 配置项 | 说明 | 示例 |
|--------|------|------|
| TG_BOT_TOKEN | Telegram Bot Token | `123456:ABCdef` |
| ALLOWED_USER_IDS | 允许的用户ID（逗号分隔） | `123456,789012` |
| AI_API_KEY | AI API Key | `sk-xxx...` |
| AI_MODEL | AI模型 | `qwen-turbo` |
| AI_BASE_URL | AI API Base URL（可选） | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| AI_TEMPERATURE | 采样温度（默认0.7） | `0.7` |
| AI_MAX_TOKENS | 最大Token数（默认2000） | `2000` |
| OBSIDIAN_VAULT_PATH | Obsidian目录路径 | `/home/user/Obsidian/Notes` |
| GITHUB_ENABLED | 启用GitHub推送（默认false） | `true` |
| GITHUB_TOKEN | GitHub Personal Access Token | `ghp_xxx...` |
| GITHUB_OWNER | GitHub用户名或组织名 | `username` |
| GITHUB_REPO | GitHub仓库名 | `notes` |
| GITHUB_BRANCH | Git分支（默认main） | `main` |
| LOG_LEVEL | 日志级别 | `INFO` |

### GitHub配置说明

要启用GitHub同步功能，需要：

1. **创建GitHub Personal Access Token**：
   - 访问 [GitHub Settings > Personal Access Tokens](https://github.com/settings/tokens)
   - 点击 "Generate new token (classic)"
   - 勾选 `repo` 权限（完全控制私有仓库）

2. **创建备份仓库**（可选）：
   - 创建一个新的私有仓库用于存储笔记
   - 或使用现有仓库

3. **配置环境变量**：
   ```env
   GITHUB_ENABLED=true
   GITHUB_TOKEN=ghp_xxxxxxxxxxxx
   GITHUB_OWNER=your_username
   GITHUB_REPO=notes-backup
   GITHUB_BRANCH=main
   ```

4. **使用**：
   - 发送 `/push` 将Obsidian中的最新笔记推送到GitHub
   - 发送 `/pull` 从GitHub拉取最新笔记到本地Obsidian目录
   - 发送 `/github` 同样可以触发推送

## 部署（Linux Systemd）

1. 创建服务文件 `/etc/systemd/system/noteagents.service`：

```ini
[Unit]
Description=NoteAgents - Telegram AI Note Auto Collection System
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/NoteAgents
Environment="PATH=/path/to/NoteAgents/.venv/bin"
ExecStart=/path/to/NoteAgents/.venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. 启用并启动服务：

```bash
# 重新加载systemd配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start noteagents

# 设置开机自启
sudo systemctl enable noteagents

# 查看状态
sudo systemctl status noteagents

# 查看日志
sudo journalctl -u noteagents -f
```

## 项目结构说明

### Agent模块

**Perception（感知模块）**
- 接收和解析Telegram消息
- 用户权限验证
- 消息类型识别

**Decision（决策模块）**
- 用户意图识别（文本/链接/文件/GitHub推送）
- 工具选择和流程决策
- 优先级判定

**Task Scheduler（任务调度）**
- 任务拆解
- 工具执行调度
- 重试机制

**Exception Handler（异常处理）**
- 异常分类
- 自动重试
- 用户友好反馈

### Tools模块

- `tg_tool.py` - Telegram消息收发、文件下载
- `file_tool.py` - 文件验证、文本提取
- `ai_summary_tool.py` - AI API调用、笔记生成（支持流式）
- `obsidian_tool.py` - 文件写入、目录管理
- `temp_clean_tool.py` - 临时文件清理
- `web_tool.py` - 网页内容下载、HTML转Markdown
- `github_tool.py` - GitHub笔记推送
- `model_adapter.py` - 多LLM适配器（统一接口）
- `llm_adapters.py` - 各类LLM适配器实现

## 开发计划

- [ ] 图片OCR识别
- [ ] 多用户权限管理
- [ ] 多渠道异常告警
- [ ] 视频字幕提取
- [ ] 笔记模板自定义

## 常见问题

### Q: 机器人收不到消息？
A: 检查网络连接、Token是否正确，确保机器人没有被屏蔽

### Q: AI调用失败？
A: 检查API Key是否正确、是否有额度，网络是否能访问API

### Q: Obsidian笔记没有生成？
A: 检查配置的路径是否正确、是否有写入权限

### Q: 如何切换不同的AI模型？
A: 在`.env`文件中修改`AI_MODEL`配置项，支持的模型请参考上文的"支持的AI模型"列表

### Q: 如何使用代理/自定义API地址？
A: 在`.env`文件中配置`AI_BASE_URL`为你的API代理地址

### Q: 支持微博和微信公众号链接吗？
A: 支持。发送链接后，系统会自动下载网页内容，提取文本，然后进行AI总结。注意：部分需要登录的页面可能无法完整获取内容。

### Q: 如何将笔记备份到GitHub？
A: 配置好GitHub相关环境变量后，发送 `/push` 或 `/github` 命令即可将Obsidian中的最新笔记推送到GitHub仓库。

### Q: 如何从GitHub拉取笔记？
A: 配置好GitHub相关环境变量后，发送 `/pull` 命令即可从GitHub仓库拉取最新笔记到本地Obsidian目录。

### Q: GitHub推送失败？
A: 检查以下几点：
   1. `GITHUB_TOKEN` 是否有效且具有 `repo` 权限
   2. `GITHUB_OWNER` 和 `GITHUB_REPO` 是否正确
   3. 仓库是否存在且你有推送权限

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

- Issues: [GitHub Issues](https://github.com/your-repo/issues)
