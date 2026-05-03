"""LLM Wiki 模块 - 基于 Karpathy 范式的知识管理

支持架构：
- Pipe & Filter 模式
- Classification Agent（分类路由）
- Self-Correction（自我修正）
- ToolUse Agent（轻量级，单轮）
"""

from config import WikiConfig
from .path_utils import WikiPathManager
from .models import StructuredNote
from .processor import NoteProcessor
from .saver import NoteSaver
from .pipeline import (
    Filter,
    ClassificationFilter,
    SelfCorrectionFilter,
    NotePipeline,
    InputType
)
from .tools import (
    ToolUseFilter,
    BaseTool,
    URLFetchTool
)
from .index import (
    IndexManager,
    NoteParser
)
from .watcher import (
    FileWatcher,
    WikiWorkflow
)
from .knowledge import (
    Entity,
    Concept,
    KnowledgeGraph
)
from .category_manager import CategoryManager
from .command_handler import WikiCommandHandler

__all__ = [
    "WikiConfig",
    "WikiPathManager",
    "StructuredNote",
    "NoteProcessor",
    "NoteSaver",
    "Filter",
    "ClassificationFilter",
    "SelfCorrectionFilter",
    "NotePipeline",
    "InputType",
    "ToolUseFilter",
    "BaseTool",
    "URLFetchTool",
    "IndexManager",
    "NoteParser",
    "FileWatcher",
    "WikiWorkflow",
    "Entity",
    "Concept",
    "KnowledgeGraph",
    "CategoryManager",
    "WikiCommandHandler",
]
