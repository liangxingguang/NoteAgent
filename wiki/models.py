"""LLM Wiki 数据模型"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import List


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
    source_type: str = "manual"  # 'auto' 或 'manual'
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
        md += f"*来源类型: {'🤖 平台采集' if self.source_type == 'auto' else '✍️  手动写'}*\n"
        md += f"*创建时间: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}*\n"
        return md
