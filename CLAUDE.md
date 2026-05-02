# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NoteAgents is a Telegram-based AI note auto-collection system that enables the workflow: "Send to TG → AI Summary → Obsidian Auto-storage". It uses a **custom AI Agent architecture built from scratch** (no LangChain/AutoGPT dependencies) for lightweight, customizable operation.

## Core Features

- **Multi-format Content Collection**: Supports text, links, PDF, Word (docx), and TXT files
- **AI-Powered Summarization**: Integrates with third-party LLMs (Qwen, GPT-3.5/4, Claude, Gemini, DeepSeek) to generate Obsidian-compatible notes
- **Automatic Obsidian Storage**: Writes summarized notes directly to a local Obsidian vault
- **Permission Control**: Restricts access to authorized users only
- **Exception Handling & Self-Healing**: Automatic retries for recoverable errors
- **24/7 Operation**: Uses systemd for process management and auto-restart
- **Multi-LLM Support**: Supports OpenAI, Anthropic, Google Gemini, DeepSeek, and OpenAI-compatible APIs

## Architecture

### 5-Layer Architecture

1. **User Interaction Layer**: Telegram client (mobile/PC)
2. **Access Layer**: TG bot integration, message parsing, permission validation
3. **Business Logic Layer**: Custom AI Agent core (perception, decision, task scheduling, exception handling)
4. **Data Storage Layer**: Temporary files, logs, context cache, Obsidian vault
5. **Infrastructure Layer**: Linux server, Python runtime, systemd service

### Custom AI Agent Core Modules

Located in `agent/` directory:
- `perception.py`: Message listening, parsing, context collection, permission validation
- `decision.py`: Intent recognition, process decision-making, tool selection, priority management
- `task_scheduler.py`: Task decomposition, scheduling, execution monitoring, retry logic
- `exception_handler.py`: Exception capture, classification, self-healing, feedback

### Custom Toolset

Located in `tools/` directory:
- `tg_tool.py`: TG message handling
- `file_tool.py`: File parsing and text extraction
- `ai_summary_tool.py`: AI summarization with streaming support
- `obsidian_tool.py`: Obsidian storage
- `temp_clean_tool.py`: Temporary file cleanup
- `model_adapter.py`: Multi-LLM adapter (OpenAI, Anthropic, Gemini, DeepSeek)
- `llm_adapters.py`: LLM adapter implementations

## Project Structure

```
NoteAgents/
├── agent/                    # Custom AI Agent core (no framework dependencies)
│   ├── perception.py         # Message listening, parsing, context collection
│   ├── decision.py           # Intent recognition, process decision-making
│   ├── task_scheduler.py     # Task decomposition, scheduling, monitoring
│   └── exception_handler.py  # Exception handling and self-healing
├── tools/                    # Custom toolset
│   ├── tg_tool.py            # TG message handling
│   ├── file_tool.py          # File parsing and text extraction
│   ├── ai_summary_tool.py    # AI summarization
│   ├── obsidian_tool.py      # Obsidian storage
│   ├── temp_clean_tool.py    # Temporary file cleanup
│   ├── model_adapter.py      # Multi-LLM adapter
│   ├── llm.py                # LLM response types
│   └── llm_adapters.py       # LLM adapter implementations
├── storage/                  # Data storage
│   ├── temp_files/           # Temporary file storage
│   ├── logs/                 # Log files
│   └── context_cache.py      # In-memory context cache
├── config/                   # Configuration
│   ├── config.py             # Config loading logic
│   └── .env.example         # Environment variable template
├── test/                     # Test suite
│   ├── conftest.py          # pytest configuration
│   ├── test_config.py       # Config module tests
│   ├── test_utils.py        # Utils module tests
│   └── test_llm_adapters.py # LLM adapter tests
├── doc/                      # Design documentation
├── requirements.txt          # Python dependencies
├── pyproject.toml           # Project configuration
├── setup.bat                # Windows initialization script (uv)
├── setup.sh                 # Linux/macOS initialization script (uv)
├── .python-version          # Python version specification
└── main.py                  # Project entry point
```

## Common Commands

### Development Setup (使用 uv)

```bash
# 快速初始化项目（Windows）
setup.bat

# 快速初始化项目（Linux/macOS）
chmod +x setup.sh
./setup.sh

# 手动初始化（使用 uv）
uv venv .venv
source .venv/bin/activate  # Linux/macOS
# 或: .venv\Scripts\activate  # Windows
uv pip install -r requirements.txt

# 手动初始化（使用 pip）
pip install -r requirements.txt
```

### Testing

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

### Configuration

1. Copy `.env.example` to `.env`
2. Fill in required configuration:
   - `TG_BOT_TOKEN`: Telegram bot token from BotFather
   - `ALLOWED_USER_IDS`: Authorized Telegram user IDs (comma-separated)
   - `AI_API_KEY`: Third-party LLM API key
   - `AI_MODEL`: Model name (qwen-turbo, gpt-3.5-turbo, claude-3-haiku, etc.)
   - `AI_BASE_URL`: API base URL (optional, for custom endpoints)
   - `AI_TEMPERATURE`: Sampling temperature (default: 0.7)
   - `AI_MAX_TOKENS`: Max tokens (default: 2000)
   - `OBSIDIAN_VAULT_PATH`: Path to local Obsidian vault
   - `LOG_LEVEL`: Logging level (INFO/DEBUG/WARNING/ERROR)
   - `TEMP_DIR`: Temporary file directory
   - `LOG_DIR`: Log file directory

### Running the System

```bash
# Development mode
python main.py

# Production mode (systemd service)
systemctl start tg_ai_agent_note_bot
systemctl stop tg_ai_agent_note_bot
systemctl restart tg_ai_agent_note_bot
systemctl status tg_ai_agent_note_bot

# View service logs
journalctl -u tg_ai_agent_note_bot -f
```

### Log Monitoring

```bash
# View real-time logs
tail -f storage/logs/system.log

# View error logs
grep ERROR storage/logs/system.log
```

## Supported LLM Models

The framework supports multiple LLM providers via automatic adapter detection:

| Provider | Models | Base URL Detection |
|----------|--------|-------------------|
| OpenAI | gpt-3.5-turbo, gpt-4, gpt-4-turbo, o1, o1-mini | api.openai.com |
| Qwen | qwen-turbo, qwen-plus, qwen-max | dashscope.aliyuncs.com |
| Anthropic | claude-3-haiku, claude-3-sonnet, claude-3-opus | anthropic.com |
| Gemini | gemini-pro, gemini-1.5-pro | generativelanguage.googleapis.com |
| DeepSeek | deepseek-chat, deepseek-coder, deepseek-reasoner | api.deepseek.com |

## Key Design Principles

1. **No Framework Dependencies**: Custom AI Agent built from scratch, no LangChain/AutoGPT
2. **Lightweight Design**: Minimal dependencies, simple deployment
3. **Modular Architecture**: Clear separation between Agent core, tools, and storage
4. **Exception-Driven**: Comprehensive error handling with self-healing capabilities
5. **Configuration-Driven**: All sensitive configs in .env file, no hardcoding
6. **Multi-LLM Support**: Unified adapter system for different LLM providers

## Constraints & Limitations

- **File Support**: PDF, Word (docx), TXT only (≤50MB each)
- **Text Limit**: Files with >5000 characters are truncated
- **Single User**: Currently supports single authorized user only
- **Network Requirement**: Server needs access to TG API and LLM API
- **No Public IP**: Uses Polling mode, no public IP/port required

## Development Notes

- **Python Version**: 3.12+
- **Key Dependencies**: python-telegram-bot, PyPDF2, python-docx, requests, python-dotenv
- **LLM Dependencies**: openai, anthropic, google-genai (optional)
- **No Redis**: Uses Python dict for in-memory context cache
- **No Database**: Uses file system for Obsidian notes and logs

## Documentation Resources

Design documents in Chinese are available in the `doc/` directory:
- Architecture design document
- Functional design document (custom AI Agent)
- Functional design document (Python version)

## Relationship with HelloAgents

NoteAgents is a sibling project to HelloAgents (in the adjacent directory). While HelloAgents is a production-grade multi-agent framework, NoteAgents intentionally uses a **custom, lightweight AI Agent architecture built from scratch** without any framework dependencies.
