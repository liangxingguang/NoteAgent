"""笔记保存器"""

import os
import re
from datetime import datetime

from wiki.models import StructuredNote
from wiki.path_utils import WikiPathManager


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
        timestamp = note.created_at.strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{self._sanitize_title(note.title)}.md"
        save_path = os.path.join(category_dir, filename)
        # 3. 保存为 Markdown
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(note.to_markdown())
        return save_path

    def _sanitize_title(self, title: str) -> str:
        """清理标题为安全文件名"""
        title = re.sub(r'[<>:"/\\|?*]', '_', title)
        return title[:50] if len(title) > 50 else title
