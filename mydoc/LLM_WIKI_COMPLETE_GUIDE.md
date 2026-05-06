# LLM Wiki 模块完整使用文档

## 项目总览

LLM Wiki 模块已完成所有 Phase，具备完整的功能！

### 完整特性

| 特性 | 说明 |
|------|------|
| **按日/按月归档** | 灵活切换，可配置 |
| **Pipeline 架构** | Pipe & Filter 模式 |
| **Classification Agent** | 自动分类内容类型 |
| **Self-Correction** | 自动修复格式错误 |
| **ToolUse Agent** | 支持工具调用（预留） |
| **知识网络** | Karpathy 范式，提取实体/概念 |
| **全局索引** | 自动更新 index.md |
| **文件监控** | 保存即整理，后台监控 |

## 快速开始

### 1. 基本使用

```python
from config import get_config
from wiki import WikiWorkflow

# 获取配置
config = get_config()

# 初始化完整工作流
workflow = WikiWorkflow(config.wiki)

# 处理单个文件
saved_path = workflow.process_file("path/to/your_note.md")
```

### 2. 启用文件监控（自动整理）

```python
from wiki import WikiWorkflow
from config import get_config

config = get_config()
workflow = WikiWorkflow(config.wiki)

# 启动监控（后台运行）
watcher = workflow.create_file_watcher(poll_interval=5.0)
watcher.start()  # 保存即整理！
```

### 3. 知识网络功能

```python
from wiki import KnowledgeGraph
from wiki.path_utils import WikiPathManager
from config import get_config

config = get_config()
path_manager = WikiPathManager(config.wiki.wiki_data_root)

kg = KnowledgeGraph(path_manager)

# 导入知识
kg.import_from_notes()

# 查询知识
results = kg.query("Python")
print(f"相关概念: {len(results['concepts'])}")
print(f"相关笔记: {len(results['related_notes'])}")

# 健康检查
health_report = kg.health_check()
```

### 4. 使用 WikiTool 工具（与 NoteAgents 集成）

```python
from tools.wiki_tool import get_wiki_tool

# 获取工具
wiki = get_wiki_tool()

# 处理内容
result = wiki.process_note("你的笔记内容")

# 更新索引
wiki.update_index()

# 导入知识
wiki.import_knowledge()

# 查询知识
wiki.query_knowledge("Python")

# 健康检查
wiki.health_check()

# 获取统计
wiki.get_stats()
```

## 配置说明

在 `config/config.py` 或 `.env` 中配置：

```env
# Wiki 配置
WIKI_ENABLED=true
WIKI_DATA_ROOT=wiki_data/
WIKI_ARCHIVE_STRATEGY=daily  # daily/monthly
WIKI_AUTO_PROCESS=true

# LLM 配置
WIKI_LLM_API_KEY=your_api_key
WIKI_LLM_API_BASE=your_api_base
WIKI_LLM_MODEL=qwen-turbo
```

## 目录结构

```
wiki_data/
├── index.md                    # 全局索引（自动更新）
├── log.md
├── SCHEMA.md
├── raw/
│   ├── auto/                   # 自动收集的笔记
│   │   └── 2026/05/03/
│   └── manual/                 # 人工手写笔记
│       └── 2026/05/03/
├── structured/                 # LLM 加工后的结构化笔记
│   ├── 技术类/
│   ├── 想法类/
│   ├── 学习类/
│   └── 日常类/
└── wiki/                       # 知识网络
    ├── entities/               # 实体
    ├── concepts/               # 概念
    ├── comparisons/            # 对比（预留）
    └── queries/                # 查询历史（预留）
```

## 总结

🎉 LLM Wiki 模块全部完成！
