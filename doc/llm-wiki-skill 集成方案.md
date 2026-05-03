# llm-wiki-skill 集成方案

## 一、项目分析

### 1.1 llm-wiki-skill 是什么

`llm-wiki-skill` 是一个运行在 **Claude Code 内部** 的 Skill（技能插件），其核心哲学来自 Karpathy：

> **"Knowledge is synthesized at ingest time, not query time"**
> 知识在摄入时编译，而不是在查询时

**核心特性：**
- 多模态文档摄入（PDF、DOCX、PPTX、XLSX、图片等）
- 自动构建可交互的知识图谱（graph.html）
- 支持双向链接（`[[PageName]]`）
- 摄入时合成知识，而非查询时 RAG 检索

### 1.2 目录结构对比

**llm-wiki-skill 标准结构：**
```
<wiki-root>/
 raw/                          # 原始文档（永不修改）
   <topic>/                    # 按主题组织
 wiki/
   index.md                    # 目录索引
   overview.md                 # 跨文档综合摘要
   log.md                      # 操作日志
   sources/                    # 每个源文档的摘要页
   entities/                   # 人物/公司/项目/产品
   concepts/                   # 概念/框架/方法论
   syntheses/                  # 存档的查询答案
   archive/                    # 存档的旧页面
   graph/
     graph.json                # 节点+边数据
     graph.html                 # 基于 vis.js 的可视化
```

**NoteAgents 当前结构：**
```
<Obsidian-vault>/
 raw/
   auto/                       # 自动采集
   auto_processed/             # 已处理的自动采集
   manual/                     # 手动写入
 structured/
   <category>/                 # 按分类组织
     *.md                      # 结构化笔记
 wiki/                         # (未来扩展)
```

### 1.3 命令对比

**llm-wiki-skill 命令：**
| 命令 | 用途 |
|------|------|
| `wiki-config workspace <path>` | 设置工作区路径 |
| `wiki-input <path> [--topic <slug>]` | 摄入任意文件 |
| `wiki-ingest <file>` | 摄入已在 raw/ 中的文件 |
| `wiki-query: <question>` | 查询知识库 |
| `wiki-lint` | 检查孤立页面、断链、矛盾 |
| `wiki-graph` | 构建知识图谱 |

**NoteAgents 当前命令：**
| 命令 | 用途 |
|------|------|
| `/wiki process` | 处理单条笔记 |
| `/wiki index` | 更新索引 |
| `/wiki stats` | 统计信息 |
| `/wiki import` | 导入知识 |
| `/wiki query <keyword>` | 查询知识 |
| `/wiki health` | 健康检查 |

---

## 二、集成方案

### 2.1 方案概述

由于 `llm-wiki-skill` 是 Claude Code 的内置 Skill，无法直接作为 Python 模块导入。集成方案采用**双轨并行 + 输出兼容**策略：

```
┌─────────────────────────────────────────────────────────────────┐
│                      NoteAgents 系统                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │  Feishu      │    │  Telegram    │    │  手动写入     │       │
│  │  消息采集    │    │  消息采集    │    │  raw/manual   │       │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘       │
│         │                   │                   │               │
│         └───────────────────┼───────────────────┘               │
│                             ▼                                    │
│                    ┌──────────────────┐                        │
│                    │   WikiWorkflow    │                        │
│                    │   (NoteAgents)    │                        │
│                    └────────┬─────────┘                        │
│                             │                                   │
│         ┌───────────────────┼───────────────────┐              │
│         ▼                   ▼                   ▼              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │  Obsidian    │    │  llm-wiki    │    │   Claude     │       │
│  │  Vault       │    │  兼容输出    │    │   Code CLI   │       │
│  │  structured/ │    │  wiki/       │    │  (可选调用)   │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 方案一：目录结构兼容（推荐）

将 NoteAgents 的 `Obsidian Vault` 目录结构改造为与 `llm-wiki-skill` 兼容：

**优势：**
- 用户可以直接在 Claude Code 中使用 `llm-wiki-skill` 命令操作同一目录
- 零学习成本，两个系统共享同一数据源
- 不依赖 Claude Code 运行时，NoteAgents 可独立运行

**实现方式：**

```python
# wiki/path_utils.py 改造
class WikiPathManager:
    """兼容 llm-wiki-skill 目录结构的路径管理器"""

    def __init__(self, vault_path: str):
        self.vault_path = vault_path

        # llm-wiki-skill 兼容路径
        self.raw_path = os.path.join(vault_path, "raw")
        self.wiki_path = os.path.join(vault_path, "wiki")
        self.graph_path = os.path.join(vault_path, "wiki", "graph")

        # 确保目录存在
        self._ensure_llm_wiki_structure()

    def _ensure_llm_wiki_structure(self):
        """创建 llm-wiki-skill 兼容目录结构"""
        subdirs = [
            "raw",                    # 原始文档
            "wiki",                   # Wiki 主目录
            "wiki/sources",           # 源文档摘要
            "wiki/entities",           # 实体
            "wiki/concepts",           # 概念
            "wiki/syntheses",          # 查询答案存档
            "wiki/archive",            # 归档
            "wiki/graph",              # 知识图谱
        ]
        for subdir in subdirs:
            self.ensure_directory_exists(os.path.join(self.vault_path, subdir))
```

### 2.3 方案二：命令兼容层

在 NoteAgents 中实现与 `llm-wiki-skill` 兼容的命令接口：

```python
# wiki/command_handler.py 添加兼容命令
class WikiCommandHandler:
    """兼容 llm-wiki-skill 命令的命令处理器"""

    def __init__(self, wiki_tool: 'WikiTool'):
        self.wiki_tool = wiki_tool

    async def handle_wiki_input(self, path: str, topic: Optional[str] = None) -> Dict[str, Any]:
        """
        wiki-input 命令 - 摄入任意文件
        用法: wiki-input <path> [--topic <slug>]
        """
        # 1. 复制文件到 raw/<topic>/
        topic = topic or "general"
        dest_raw = os.path.join(self.wiki_tool.path_manager.raw_path, topic)
        self.wiki_tool.path_manager.ensure_directory_exists(dest_raw)

        import shutil
        filename = os.path.basename(path)
        dest_path = os.path.join(dest_raw, filename)
        shutil.copy2(path, dest_path)

        # 2. 执行摄入流程
        result = self.wiki_tool.process_note_from_auto(
            note_content=self._read_file_content(path),
            source_path=dest_path
        )

        # 3. 更新 wiki/index.md, wiki/overview.md
        await self._update_wiki_index(topic, result)

        # 4. 追加操作日志
        await self._append_log(f"Ingested: {filename} -> {dest_path}")

        return result

    async def handle_wiki_ingest(self, file: str) -> Dict[str, Any]:
        """
        wiki-ingest 命令 - 摄入已在 raw/ 中的文件
        用法: wiki-ingest <file>
        """
        raw_file_path = os.path.join(self.wiki_tool.path_manager.raw_path, file)
        if not os.path.exists(raw_file_path):
            return {"success": False, "error": f"File not found: {raw/file}"}

        with open(raw_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        return self.wiki_tool.process_note_from_auto(content, source_path=raw_file_path)

    async def handle_wiki_query(self, question: str) -> Dict[str, Any]:
        """
        wiki-query 命令 - 查询知识库
        用法: wiki-query: <question>
        """
        return self.wiki_tool.query_knowledge(question)

    async def handle_wiki_graph(self) -> Dict[str, Any]:
        """
        wiki-graph 命令 - 构建知识图谱
        用法: wiki-graph
        """
        # 生成 graph.json 和 graph.html
        return self.wiki_tool.build_knowledge_graph()

    async def handle_wiki_lint(self) -> Dict[str, Any]:
        """
        wiki-lint 命令 - 检查问题
        用法: wiki-lint
        """
        return self.wiki_tool.health_check()
```

### 2.4 方案三：调用 Claude Code CLI（可选增强）

对于高级用户，可以在 NoteAgents 中调用 Claude Code 来执行 `llm-wiki-skill` 命令：

```python
# tools/claude_wiki_tool.py
import subprocess
from typing import Dict, Any, Optional

class ClaudeWikiTool:
    """通过 Claude Code CLI 调用 llm-wiki-skill"""

    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path

    def _run_claude(self, command: str) -> Dict[str, Any]:
        """执行 Claude Code 命令"""
        try:
            result = subprocess.run(
                ["claude", "-p", command],
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
        except FileNotFoundError:
            return {"success": False, "error": "Claude Code CLI 未安装"}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "命令执行超时"}

    def wiki_config_workspace(self, path: str) -> Dict[str, Any]:
        """设置工作区"""
        return self._run_claude(f"wiki-config workspace {path}")

    def wiki_input(self, path: str, topic: Optional[str] = None) -> Dict[str, Any]:
        """摄入文件"""
        cmd = f"wiki-input {path}"
        if topic:
            cmd += f" --topic {topic}"
        return self._run_claude(cmd)

    def wiki_query(self, question: str) -> Dict[str, Any]:
        """查询"""
        return self._run_claude(f"wiki-query: {question}")

    def wiki_graph(self) -> Dict[str, Any]:
        """构建图谱"""
        return self._run_claude("wiki-graph")
```

---

## 三、目录结构改造

### 3.1 目标结构

将 NoteAgents 的 Vault 改造成同时兼容 Obsidian 和 llm-wiki-skill：

```
<vault-root>/
 ├── raw/                              # 原始文档（llm-wiki-skill 标准）
 │   ├── auto/                         # 自动采集
 │   │   └── YYYY/MM/DD/
 │   │       └── *.md
 │   ├── auto_processed/               # 已处理的自动采集
 │   │   └── YYYY/MM/DD/
 │   │       └── *.md
 │   └── manual/                        # 手动写入
 │       └── *.md
 │
 ├── structured/                       # 结构化笔记（Obsidian 标准）
 │   └── <category>/
 │       └── *.md
 │
 ├── wiki/                             # Wiki 目录（llm-wiki-skill 标准）
 │   ├── index.md                      # 目录索引
 │   ├── overview.md                   # 综合摘要
 │   ├── log.md                        # 操作日志
 │   ├── sources/                      # 源文档摘要
 │   │   └── <slug>.md
 │   ├── entities/                     # 实体页面
 │   │   └── <name>.md
 │   ├── concepts/                     # 概念页面
 │   │   └── <concept>.md
 │   ├── syntheses/                    # 查询答案存档
 │   ├── archive/                      # 归档
 │   └── graph/                        # 知识图谱
 │       ├── graph.json
 │       └── graph.html
 │
 └── .obsidian/                        # Obsidian 配置
```

### 3.2 路径管理器改造

```python
# wiki/path_utils.py
class WikiPathManager:
    """双重兼容的路径管理器（Obsidian + llm-wiki-skill）"""

    def __init__(self, vault_path: str):
        self.vault_path = vault_path

        # Obsidian 兼容路径
        self.structured_path = os.path.join(vault_path, "structured")

        # llm-wiki-skill 兼容路径
        self.raw_path = os.path.join(vault_path, "raw")
        self.wiki_path = os.path.join(vault_path, "wiki")
        self.graph_path = os.path.join(vault_path, "wiki", "graph")

    def get_raw_auto_full_path(self, date: datetime = None) -> str:
        """获取自动采集原始路径"""
        if date is None:
            date = datetime.now()
        return os.path.join(
            self.raw_path, "auto",
            date.strftime("%Y/%m/%d")
        )

    def get_wiki_sources_path(self, slug: str) -> str:
        """获取源文档摘要路径"""
        return os.path.join(self.wiki_path, "sources", f"{slug}.md")

    def get_wiki_entities_path(self, name: str) -> str:
        """获取实体页面路径"""
        safe_name = self._sanitize_filename(name)
        return os.path.join(self.wiki_path, "entities", f"{safe_name}.md")

    def get_wiki_concepts_path(self, concept: str) -> str:
        """获取概念页面路径"""
        safe_concept = self._sanitize_filename(concept)
        return os.path.join(self.wiki_path, "concepts", f"{safe_concept}.md")

    def _sanitize_filename(self, name: str) -> str:
        """文件名清理"""
        # 移除不合法字符
        import re
        return re.sub(r'[<>:"/\\|?*]', '_', name)
```

---

## 四、知识图谱集成

### 4.1 图谱数据模型

```python
# wiki/knowledge.py 增强
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class GraphNode(BaseModel):
    """图谱节点"""
    id: str
    label: str
    type: str  # "source" | "entity" | "concept" | "synthesis"
    slug: str
    connections: List[str] = []
    metadata: dict = {}

class GraphEdge(BaseModel):
    """图谱边"""
    source: str
    target: str
    type: str  # "EXTRACTED" | "INFERRED"
    confidence: float = Field(ge=0.0, le=1.0)

class KnowledgeGraph:
    """知识图谱管理器"""

    def __init__(self, path_manager: WikiPathManager):
        self.path_manager = path_manager
        self.graph_file = os.path.join(path_manager.graph_path, "graph.json")
        self.html_file = os.path.join(path_manager.graph_path, "graph.html")

    def build_graph(self) -> Dict[str, Any]:
        """构建知识图谱"""
        nodes, edges = self._extract_nodes_and_edges()

        # 保存 graph.json
        graph_data = {
            "nodes": [n.model_dump() for n in nodes],
            "edges": [e.model_dump() for e in edges],
            "generated_at": datetime.now().isoformat()
        }
        with open(self.graph_file, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=2)

        # 生成 graph.html
        self._generate_html(nodes, edges)

        return {
            "success": True,
            "nodes_count": len(nodes),
            "edges_count": len(edges),
            "graph_file": self.graph_file,
            "html_file": self.html_file
        }

    def _generate_html(self, nodes: List[GraphNode], edges: List[GraphEdge]):
        """生成可视化 HTML"""
        html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Knowledge Graph</title>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body { margin: 0; padding: 0; overflow: hidden; }
        #network { width: 100vw; height: 100vh; }
    </style>
</head>
<body>
    <div id="network"></div>
    <script>
        const nodes = new vis.DataSet(NODES_PLACEHOLDER);
        const edges = new vis.DataSet(EDGES_PLACEHOLDER);
        const container = document.getElementById('network');
        const data = { nodes, edges };
        const options = {
            nodes: {
                shape: 'box',
                font: { size: 14 }
            },
            edges: {
                arrows: 'to'
            },
            physics: { enabled: true }
        };
        new vis.Network(container, data, options);
    </script>
</body>
</html>"""
        # 替换占位符并写入
        import re
        nodes_json = json.dumps([self._node_to_vis(n) for n in nodes])
        edges_json = json.dumps([self._edge_to_vis(e) for e in edges])
        html = html_template.replace("NODES_PLACEHOLDER", nodes_json)
        html = html.replace("EDGES_PLACEHOLDER", edges_json)
        with open(self.html_file, "w", encoding="utf-8") as f:
            f.write(html)

    def _node_to_vis(self, node: GraphNode) -> dict:
        """转换为 vis.js 节点格式"""
        colors = {
            "source": "#98FB98",
            "entity": "#87CEEB",
            "concept": "#DDA0DD",
            "synthesis": "#F0E68C"
        }
        return {
            "id": node.id,
            "label": node.label,
            "color": colors.get(node.type, "#CCCCCC")
        }

    def _edge_to_vis(self, edge: GraphEdge) -> dict:
        """转换为 vis.js 边格式"""
        return {
            "from": edge.source,
            "to": edge.target,
            "arrows": "to",
            "color": "gray" if edge.type == "EXTRACTED" else "red"
        }
```

---

## 五、实施步骤

### 5.1 第一阶段：目录结构改造

```python
# wiki/path_utils.py
def upgrade_directory_structure(self):
    """升级目录结构以兼容 llm-wiki-skill"""
    import shutil

    # 1. 创建 wiki/ 目录结构
    wiki_dirs = [
        "wiki/sources",
        "wiki/entities",
        "wiki/concepts",
        "wiki/syntheses",
        "wiki/archive",
        "wiki/graph"
    ]
    for d in wiki_dirs:
        self.ensure_directory_exists(os.path.join(self.vault_path, d))

    # 2. 迁移现有数据（如果需要）
    # ...

    # 3. 创建 wiki/index.md
    index_path = os.path.join(self.vault_path, "wiki", "index.md")
    if not os.path.exists(index_path):
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("# Wiki Index\n\n")
            f.write("## Sources\n\n")
            f.write("## Entities\n\n")
            f.write("## Concepts\n\n")

    # 4. 创建 wiki/overview.md
    overview_path = os.path.join(self.vault_path, "wiki", "overview.md")
    if not os.path.exists(overview_path):
        with open(overview_path, "w", encoding="utf-8") as f:
            f.write("# Overview\n\n")
            f.write("> This wiki is maintained by AI. Last updated: \n\n")

    # 5. 创建 wiki/log.md
    log_path = os.path.join(self.vault_path, "wiki", "log.md")
    if not os.path.exists(log_path):
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("# Operation Log\n\n")
```

### 5.2 第二阶段：命令兼容层

```python
# wiki/command_handler.py 添加
async def handle_wiki_command(self, command: str, args: list) -> Dict[str, Any]:
    """统一处理 wiki 命令"""
    handlers = {
        "wiki-config": self._handle_wiki_config,
        "wiki-input": self._handle_wiki_input,
        "wiki-ingest": self._handle_wiki_ingest,
        "wiki-query": self._handle_wiki_query,
        "wiki-lint": self._handle_wiki_lint,
        "wiki-graph": self._handle_wiki_graph,
    }

    handler = handlers.get(command)
    if not handler:
        return {"success": False, "error": f"Unknown command: {command}"}

    return await handler(args)
```

### 5.3 第三阶段：知识图谱集成

```python
# 启用知识图谱功能
WIKI_KNOWLEDGE_GRAPH_ENABLED=true
WIKI_GRAPH_HTML_PATH=${OBSIDIAN_VAULT_PATH}/wiki/graph/graph.html
```

---

## 六、配置项

### 6.1 环境变量

```ini
# .env

# ============ LLM Wiki 基础配置 ============
OBSIDIAN_VAULT_PATH=D:/Obsidian/Vault

# ============ llm-wiki-skill 兼容配置 ============
# 是否启用 llm-wiki-skill 兼容模式
WIKI_LLM_WIKI_COMPAT=false

# 是否构建知识图谱
WIKI_KNOWLEDGE_GRAPH_ENABLED=true

# Claude Code CLI 路径（可选，用于调用 llm-wiki-skill）
CLAUDE_CODE_PATH=claude
```

### 6.2 配置读取

```python
# config/config.py
class WikiConfig(BaseModel):
    # ... 现有配置 ...

    # llm-wiki-skill 兼容
    llm_wiki_compat: bool = Field(default=False, alias="WIKI_LLM_WIKI_COMPAT")
    knowledge_graph_enabled: bool = Field(default=True, alias="WIKI_KNOWLEDGE_GRAPH_ENABLED")
    claude_code_path: str = Field(default="claude", alias="CLAUDE_CODE_PATH")
```

---

## 七、使用示例

### 7.1 NoteAgents 处理流程

```python
# 1. 用户通过飞书发送 URL
message = await adapter.receive_message()
content = await web_tool.fetch_content(message.url)

# 2. NoteAgents 处理
result = wiki_tool.process_note(content, source_type="auto")

# 3. 同时更新 llm-wiki-skill 兼容结构
if config.wiki.llm_wiki_compat:
    wiki_handler.update_sources(result)      # wiki/sources/
    wiki_handler.update_entities(result)      # wiki/entities/
    wiki_handler.update_concepts(result)     # wiki/concepts/
    wiki_handler.update_overview(result)      # wiki/overview.md
    wiki_handler.append_log(f"Processed: {result['title']}")  # wiki/log.md
```

### 7.2 Claude Code 中使用

```bash
# 用户可以在 Claude Code 中直接操作同一 Vault
$ wiki-query: 这篇文档的核心观点是什么？
$ wiki-lint
$ wiki-graph
```

---

## 八、风险与限制

| 风险/限制 | 级别 | 说明 | 缓解措施 |
|-----------|------|------|----------|
| 目录结构变更 | 中 | 改造可能影响现有数据 | 提供迁移脚本 |
| Claude Code 依赖 | 低 | 方案三依赖外部 CLI | 提供纯 Python 回退 |
| 图谱生成性能 | 低 | 大量笔记时可能较慢 | 增量更新 |
| 双向链接冲突 | 低 | Obsidian 和 llm-wiki-skill 格式一致 | 统一使用 `[[...]]` |

---

## 九、总结

### 9.1 方案对比

| 方案 | 复杂度 | 依赖 | 推荐场景 |
|------|--------|------|----------|
| 目录结构兼容 | 低 | 无 | 大多数用户 |
| 命令兼容层 | 中 | 无 | 需要 CLI 风格操作 |
| Claude Code CLI | 高 | Claude Code | 高级用户/开发者 |

### 9.2 推荐路径

1. **立即实施**：目录结构兼容（方案一）
2. **短期规划**：命令兼容层（方案二）
3. **长期探索**：Claude Code CLI 集成（方案三）

### 9.3 核心价值

- **数据共享**：NoteAgents 采集 + llm-wiki-skill 整理，用户可在两个界面操作同一数据
- **知识深化**：llm-wiki-skill 提供更深度的知识组织和图谱可视化
- **生态整合**：融入 Claude Code 生态，发挥 AI 整理的优势