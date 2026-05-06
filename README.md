# NoteAgents

多平台 AI 笔记自动收集与知识管理系统。

支持 Telegram、飞书（Feishu）等多种平台，自动采集内容 → AI 总结 → 结构化存储到 Obsidian 知识库。

## 核心特性

### 多平台采集
- **飞书（Feishu）** - WebSocket 长连接，支持群聊 @ 机器人
- **Telegram** - 传统 Bot 模式，支持文本/链接/文件

### AI 智能处理
- **多模型支持** - OpenAI、Claude、Gemini、DeepSeek、通义千问、豆包等
- **自动总结** - 智能提取核心观点，生成结构化笔记
- **动态分类** - AI 根据内容自动分类，无需手动打标签

### LLM Wiki 知识管理
- **双轨存储** - `raw/` 原始采集 + `structured/` 结构化笔记
- **按日归档** - 原始文件按日期自动归档
- **分类管理** - 技术类、工作、学习、生活等动态分类
- **知识图谱** - 自动建立笔记间的双向链接

### 开发者生态
- **Skill 模块** - 可扩展的命令系统，类似 Claude Code Skills
- **插件化架构** - 平台适配器、工具模块可插拔
- **零框架依赖** - 自定义 AI Agent，无 LangChain/AutoGPT

## 快速开始

### 环境要求

- Python 3.12+
- Obsidian 知识库（可选）
- 第三方 AI API Key

### 安装

```bash
# Windows
.\setup.bat

# Linux/macOS
chmod +x setup.sh
./setup.sh
```

### 配置

```bash
cp .env.example .env
# 编辑 .env 填入配置
```

### 运行

```bash
python main_multi.py
```

## 支持的 AI 模型

| 提供商 | 模型 | Base URL |
|--------|------|----------|
| 豆包（字节） | doubao-seed-2.0-code, ark-code-latest | ark.cn-beijing.volces.com |
| 通义千问 | qwen-turbo, qwen-plus, qwen-max | dashscope.aliyuncs.com |
| OpenAI | gpt-4, gpt-4-turbo, o1 | api.openai.com |
| Anthropic | claude-3-sonnet, claude-3-opus | anthropic.com |
| DeepSeek | deepseek-chat, deepseek-coder | api.deepseek.com |

## 项目结构

```
NoteAgents/
├── agent/                     # AI Agent 核心
│   ├── perception.py          # 感知模块 - 消息接收、解析
│   ├── decision.py            # 决策模块 - 意图识别、工具选择
│   ├── task_scheduler.py      # 任务调度 - 任务拆解、执行
│   └── exception_handler.py   # 异常处理 - 自愈、反馈
├── platforms/                 # 平台适配层
│   ├── base.py                # 平台基类
│   ├── coordinator.py         # 平台协调器
│   ├── feishu_adapter.py      # 飞书适配器（WebSocket 长连接）
│   ├── feishu_commands.py    # 飞书命令处理
│   ├── feishu_rich_text.py    # 飞书富文本解析
│   ├── telegram_adapter.py    # Telegram 适配器
│   └── tg_commands.py         # Telegram 命令处理
├── tools/                     # 业务工具层
│   ├── ai_summary_tool.py     # AI 总结工具
│   ├── file_tool.py           # 文件处理（PDF/DOCX/TXT）
│   ├── obsidian_tool.py       # Obsidian 写入
│   ├── web_tool.py            # 网页内容下载
│   ├── github_tool.py         # GitHub 同步
│   ├── model_adapter.py       # 多 LLM 适配器
│   ├── llm_adapters.py        # LLM 适配器实现
│   └── wiki_tool.py           # Wiki 工具
├── wiki/                      # LLM Wiki 模块
│   ├── pipeline.py            # 处理管道（结构化）
│   ├── watcher.py             # 文件监控
│   ├── index.py               # 索引管理
│   ├── knowledge.py           # 知识图谱
│   ├── saver.py               # 笔记持久化
│   ├── path_utils.py          # 路径管理
│   ├── category_manager.py    # 分类管理
│   └── command_handler.py     # 命令处理
├── storage/                   # 存储层
│   ├── log_manager.py         # 日志管理
│   ├── temp_manager.py        # 临时文件
│   └── context_cache.py       # 上下文缓存
├── config/                    # 配置层
│   └── config.py              # 配置管理
├── doc/                       # 设计文档
├── test/                      # 测试套件
└── main_multi.py              # 入口文件（多平台）
```

## 目录结构（Obsidian Vault）

```
<vault-root>/
├── raw/                       # 原始采集
│   ├── auto/                  # 自动采集（按日归档）
│   │   └── YYYY/MM/DD/
│   ├── auto_processed/        # 已处理的自动采集
│   └── manual/                # 手动写入
├── structured/                # 结构化笔记（按分类）
│   ├── 技术类/
│   ├── 工作/
│   ├── 学习/
│   └── ...
└── wiki/                      # Wiki 知识组织（扩展）
    ├── sources/               # 源文档摘要
    ├── entities/              # 实体
    ├── concepts/              # 概念
    └── graph/                 # 知识图谱
```

## 配置说明

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `OBSIDIAN_VAULT_PATH` | Obsidian 路径 | `D:/Obsidian/Vault` |
| `FEISHU_APP_ID` | 飞书 App ID | `cli_xxx` |
| `FEISHU_APP_SECRET` | 飞书 App Secret | `xxx` |
| `TG_BOT_TOKEN` | Telegram Token | `123:xxx` |
| `TG_ENABLED` | 启用 Telegram | `true` |
| `AI_API_KEY` | AI API Key | `sk-xxx` |
| `AI_MODEL` | AI 模型 | `ark-code-latest` |
| `AI_BASE_URL` | API Base URL | `https://ark.cn-beijing.volces.com/api/v3` |
| `WIKI_LLM_MODEL` | Wiki 专用模型 | `ark-code-latest` |

## Skill 模块

NoteAgents 支持类似 Claude Code Skills 的命令扩展系统：

| 命令 | 说明 |
|------|------|
| `/wiki process` | 处理单条笔记 |
| `/wiki index` | 更新索引 |
| `/wiki stats` | 统计信息 |
| `/wiki import` | 导入知识 |
| `/wiki query <keyword>` | 查询知识 |
| `/wiki health` | 健康检查 |
| `/push` | 推送到 GitHub |
| `/pull` | 从 GitHub 拉取 |

## 与 llm-wiki-skill 的关系

[llm-wiki-skill](https://github.com/llmrix/llm-wiki-skill) 是运行在 Claude Code 中的 Skill。

NoteAgents 采用**目录结构兼容**策略，可以与 llm-wiki-skill 共享同一 Obsidian Vault：

- NoteAgents 负责**采集**和**初步结构化**
- 用户可在 Claude Code 中用 `wiki-query`、`wiki-graph` 等命令进一步处理

详见 [llm-wiki-skill 集成方案](doc/llm-wiki-skill%20集成方案.md)

## 测试

```bash
pytest test/ -v
```

## 许可证

MIT License