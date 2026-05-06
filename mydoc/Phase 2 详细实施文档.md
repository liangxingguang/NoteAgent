# Phase 2: LLM 加工能力 - 详细实施文档

## 一、实施目标

Phase 2 是 LLM Wiki 功能的核心，实现 LLM 内容结构化加工，将原始内容转化为标准化的结构化笔记。

**核心交付物**：
1. StructuredNote 类 - 结构化笔记数据模型
2. NoteProcessor 类 - LLM 加工核心类
3. 加工结果保存功能

## 二、结构化笔记数据模型

### 2.1 字段定义

| 字段 | 说明 | 格式 | 必填 |
|------|------|------|------|
| title | 核心标题 | 字符串 | 是 |
| summary | 摘要（150字以内） | 字符串 | 是 |
| keywords | 关键词/标签（3-5个） | 列表 | 是 |
| key_points | 核心要点（3-5条） | 列表 | 是 |
| backlinks | 双向链接 | 列表 | 是 |
| category | 分类（技术/想法/学习/日常） | 枚举 | 是 |
| optimized_content | 优化后的内容 | 字符串 | 是 |
| source_path | 源文件路径 | 字符串 | 是 |
| created_at | 创建时间 | 日期时间 | 是 |

### 2.2 类设计

```python
@dataclass
class StructuredNote:
    """结构化笔记数据模型"""
    title: str
    summary: str
    keywords: List[str]
    key_points: List[str]
    backlinks: List[str]
    category: str
    optimized_content: str
    source_path: str
    created_at: datetime = field(default_factory=datetime.now)

    def to_markdown(self) -> str:
        """转换为 Markdown 格式"""
        md = f"# {self.title}\n\n"
        md += f"## 摘要\n\n{self.summary}\n\n"
        md += f"## 关键词\n\n{', '.join(self.keywords)}\n\n"
        md += f"## 核心要点\n\n"
        for i, point in enumerate(self.key_points, 1):
            md += f"{i}. {point}\n"
        md += "\n"
        if self.backlinks:
            md += f"## 双向链接\n\n{', '.join([f'[[{link}]]' for link in self.backlinks])}\n\n"
        md += f"## 优化内容\n\n{self.optimized_content}\n\n"
        md += f"---\n\n"
        md += f"*来源: {self.source_path}*\n"
        md += f"*创建时间: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}*\n"
        return md
```

## 三、NoteProcessor 核心类设计

### 3.1 核心功能

| 功能 | 说明 |
|------|------|
| process_note() | 处理单条笔记，返回 StructuredNote |
| retry_llm_call() | LLM API 重试机制 |
| validate_result() | 验证加工结果完整性 |

### 3.2 LLM 提示词设计

#### 系统提示词
```
你是一个专业的笔记整理助手，负责将原始笔记加工成结构化内容。
你的任务是：
1. 提炼核心标题：简洁、准确、贴合主题
2. 精简摘要：将核心信息浓缩至 150 字以内
3. 提取关键词/标签：提取 3-5 个核心关键词
4. 梳理核心要点：将核心信息拆解为 3-5 条要点
5. 识别双向链接：识别核心概念、关键词，建议 Obsidian 双向链接
6. 自动分类：自动划分为技术类、想法类、学习类、日常类
7. 内容优化：剔除冗余、口语化信息，保持逻辑清晰、忠于原文

你需要返回 JSON 格式，不要有任何 Markdown 标记。
```

#### 用户提示词
```
原始笔记：
{content}
```

#### 期望输出格式
```json
{
  "title": "核心标题",
  "summary": "150字以内摘要",
  "keywords": ["关键词1", "关键词2", "关键词3"],
  "key_points": ["要点1", "要点2", "要点3"],
  "backlinks": ["链接1", "链接2"],
  "category": "技术类",
  "optimized_content": "优化后的完整内容"
}
```

### 3.3 类实现

```python
class NoteProcessor:
    """LLM 笔记加工器"""

    def __init__(self, config: WikiConfig):
        self.config = config
        self.categories = ["技术类", "想法类", "学习类", "日常类"]

    def process_note(self, content: str, source_path: str) -> StructuredNote:
        """处理单条笔记"""
        # 1. 调用 LLM 获取结构化数据
        structured_data = self._call_llm(content)
        # 2. 验证数据
        self._validate_structured_data(structured_data)
        # 3. 创建 StructuredNote
        note = StructuredNote(
            title=structured_data["title"],
            summary=structured_data["summary"],
            keywords=structured_data["keywords"],
            key_points=structured_data["key_points"],
            backlinks=structured_data["backlinks"],
            category=structured_data["category"],
            optimized_content=structured_data["optimized_content"],
            source_path=source_path
        )
        return note

    def _call_llm(self, content: str) -> dict:
        """调用 LLM API，带重试机制"""
        for attempt in range(self.config.llm_retry_times):
            try:
                # 使用项目现有的 LLM 调用机制
                from tools.llm_adapters import get_llm_adapter
                llm = get_llm_adapter(
                    api_key=self.config.llm_api_key,
                    model=self.config.llm_model,
                    base_url=self.config.llm_base_url
                )
                response = llm.generate(
                    system_prompt=self._get_system_prompt(),
                    user_prompt=f"原始笔记：\n{content}"
                )
                # 解析 JSON 响应
                import json
                return json.loads(response)
            except Exception as e:
                if attempt == self.config.llm_retry_times - 1:
                    raise
                import time
                time.sleep(2 ** attempt)

    def _get_system_prompt(self) -> str:
        return """你是一个专业的笔记整理助手，负责将原始笔记加工成结构化内容。
你的任务是：
1. 提炼核心标题：简洁、准确、贴合主题
2. 精简摘要：将核心信息浓缩至 150 字以内
3. 提取关键词/标签：提取 3-5 个核心关键词
4. 梳理核心要点：将核心信息拆解为 3-5 条要点
5. 识别双向链接：识别核心概念、关键词，建议 Obsidian 双向链接
6. 自动分类：必须从以下分类选择一个：技术类、想法类、学习类、日常类
7. 内容优化：剔除冗余、口语化信息，保持逻辑清晰、忠于原文

你需要返回 JSON 格式，不要有任何 Markdown 标记。
"""

    def _validate_structured_data(self, data: dict) -> None:
        """验证结构化数据"""
        required_fields = ["title", "summary", "keywords", "key_points", "backlinks", "category", "optimized_content"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"缺少必填字段: {field}")
        # 验证分类
        if data["category"] not in self.categories:
            data["category"] = "日常类"  # 默认分类
        # 验证字数
        if len(data["summary"]) > 150:
            data["summary"] = data["summary"][:147] + "..."
```

## 四、加工结果保存功能

### 4.1 NoteSaver 类设计

```python
class NoteSaver:
    """笔记保存器"""

    def __init__(self, path_manager: WikiPathManager):
        self.path_manager = path_manager

    def save_structured_note(self, note: StructuredNote) -> str:
        """保存结构化笔记，返回保存路径"""
        # 1. 获取分类目录
        category_dir = self.path_manager.get_structured_full_path(note.category)
        self.path_manager.ensure_directory_exists(category_dir)
        # 2. 生成文件名
        import os
        timestamp = note.created_at.strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{self._sanitize_title(note.title)}.md"
        save_path = os.path.join(category_dir, filename)
        # 3. 保存为 Markdown
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(note.to_markdown())
        return save_path

    def _sanitize_title(self, title: str) -> str:
        """清理标题为安全文件名"""
        import re
        title = re.sub(r'[<>:"/\\|?*]', '_', title)
        return title[:50] if len(title) > 50 else title
```

## 五、模块整合

### 5.1 目录结构

```
wiki/
├── __init__.py
├── path_utils.py
├── models.py          # 数据模型（StructuredNote）
├── processor.py       # NoteProcessor
└── saver.py           # NoteSaver
```

### 5.2 __init__.py 更新

```python
from config import WikiConfig
from .path_utils import WikiPathManager
from .models import StructuredNote
from .processor import NoteProcessor
from .saver import NoteSaver

__all__ = [
    "WikiConfig",
    "WikiPathManager",
    "StructuredNote",
    "NoteProcessor",
    "NoteSaver"
]
```

## 六、实施检查清单

- [ ] StructuredNote 类实现完成
- [ ] StructuredNote.to_markdown() 方法实现完成
- [ ] NoteProcessor 类实现完成
- [ ] LLM 提示词设计完成
- [ ] 重试机制实现完成
- [ ] 数据验证逻辑实现完成
- [ ] NoteSaver 类实现完成
- [ ] 文件名生成逻辑实现完成
- [ ] 模块整合完成
- [ ] 单元测试通过

## 七、测试验证

### 7.1 StructuredNote 测试

```python
def test_structured_note():
    note = StructuredNote(
        title="测试标题",
        summary="这是一个测试摘要，用于验证功能。",
        keywords=["测试", "验证"],
        key_points=["要点1", "要点2"],
        backlinks=["链接1"],
        category="技术类",
        optimized_content="优化后的内容",
        source_path="test.md"
    )
    md = note.to_markdown()
    assert "# 测试标题" in md
    assert "## 摘要" in md
    assert "测试摘要" in md
```

### 7.2 集成测试（模拟 LLM）

```python
def test_integration():
    config = WikiConfig(enabled=True, llm_api_key="test_key")
    path_manager = WikiPathManager("wiki_data/")
    processor = NoteProcessor(config)
    saver = NoteSaver(path_manager)

    # 测试流程
    test_content = "这是一条测试笔记，用于验证 NoteProcessor 和 NoteSaver 的功能。"
    note = processor.process_note(test_content, "test.md")
    save_path = saver.save_structured_note(note)
    assert os.path.exists(save_path)
```

## 八、预估工作量

| 任务 | 预估时间 |
|------|----------|
| StructuredNote 类实现 | 15 分钟 |
| NoteProcessor 类实现 | 40 分钟 |
| NoteSaver 类实现 | 20 分钟 |
| 模块整合 | 10 分钟 |
| 单元测试 | 25 分钟 |
| **总计** | **约 110 分钟** |

## 九、风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| LLM API 调用失败 | 高 | 实现重试机制 |
| LLM 返回格式不符合预期 | 中 | 严格 JSON 验证和默认值 |
| 分类错误 | 中 | 提供默认分类 |
