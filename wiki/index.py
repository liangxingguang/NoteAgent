"""索引管理模块"""

import os
import re
from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Any

from wiki.path_utils import WikiPathManager
from wiki.models import StructuredNote


class NoteParser:
    """从 Markdown 文件解析 StructuredNote"""

    @staticmethod
    def from_markdown(file_path: str) -> StructuredNote:
        """从 Markdown 文件解析"""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        # 解析内容
        title = NoteParser._extract_title(content)
        summary = NoteParser._extract_section(content, "摘要")
        keywords = NoteParser._extract_keywords(content)
        key_points = NoteParser._extract_key_points(content)
        backlinks = NoteParser._extract_backlinks(content)
        optimized_content = NoteParser._extract_section(content, "优化内容")
        source_path = NoteParser._extract_source_path(content)
        source_type = NoteParser._extract_source_type(content)
        created_at = NoteParser._extract_created_at(content)
        # 从目录判断分类
        category = NoteParser._extract_category(file_path)
        return StructuredNote(
            title=title,
            summary=summary,
            keywords=keywords,
            key_points=key_points,
            backlinks=backlinks,
            category=category,
            optimized_content=optimized_content,
            source_path=source_path,
            source_type=source_type,
            created_at=created_at
        )

    @staticmethod
    def _extract_title(content: str) -> str:
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        return match.group(1) if match else "未分类笔记"

    @staticmethod
    def _extract_section(content: str, section_name: str) -> str:
        pattern = rf'##\s+{re.escape(section_name)}\s*\n\n([\s\S]*?)(?=\n##|\Z)'
        match = re.search(pattern, content)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _extract_keywords(content: str) -> List[str]:
        section = NoteParser._extract_section(content, "关键词")
        if not section:
            return []
        return [k.strip() for k in section.split(",") if k.strip()]

    @staticmethod
    def _extract_key_points(content: str) -> List[str]:
        section = NoteParser._extract_section(content, "核心要点")
        if not section:
            return []
        points = re.findall(r'^\d+\.\s+(.+)$', section, re.MULTILINE)
        return [p.strip() for p in points if p.strip()]

    @staticmethod
    def _extract_backlinks(content: str) -> List[str]:
        section = NoteParser._extract_section(content, "双向链接")
        if not section:
            return []
        links = re.findall(r'\[\[([^\]]+)\]\]', section)
        return [l.strip() for l in links if l.strip()]

    @staticmethod
    def _extract_source_path(content: str) -> str:
        match = re.search(r'\*来源:\s*(.+?)\*', content)
        return match.group(1) if match else "unknown"

    @staticmethod
    def _extract_source_type(content: str) -> str:
        match = re.search(r'\*来源类型:\s*(.+?)\*', content)
        if match:
            st = match.group(1).strip()
            if "平台采集" in st:
                return "auto"
        return "manual"

    @staticmethod
    def _extract_created_at(content: str) -> datetime:
        match = re.search(r'\*创建时间:\s*(.+?)\*', content)
        if match:
            try:
                return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
            except:
                pass
        return datetime.now()

    @staticmethod
    def _extract_category(file_path: str) -> str:
        categories = ["技术类", "想法类", "学习类", "日常类"]
        for cat in categories:
            if f"/{cat}/" in file_path.replace("\\", "/"):
                return cat
        return "日常类"


class IndexManager:
    """索引管理类"""

    def __init__(self, path_manager: WikiPathManager):
        self.path_manager = path_manager
        self.categories = ["技术类", "想法类", "学习类", "日常类"]

    def scan_notes(self) -> List[StructuredNote]:
        """扫描所有笔记（所有分类）"""
        notes: List[StructuredNote] = []
        structured_dir = self.path_manager.get_structured_full_path("")
        if not os.path.exists(structured_dir):
            return notes
        # 扫描所有子目录（所有分类
        for category in os.listdir(structured_dir):
            category_dir = os.path.join(structured_dir, category)
            if not os.path.isdir(category_dir):
                continue
            for file_name in os.listdir(category_dir):
                    if file_name.endswith(".md"):
                        file_path = os.path.join(category_dir, file_name)
                        try:
                            note = NoteParser.from_markdown(file_path)
                            note.relative_path = self._get_relative_path(file_path)
                            notes.append(note)
                        except:
                            continue
        # 按创建时间倒序排列
        notes.sort(key=lambda x: x.created_at, reverse=True)
        return notes

    def _get_relative_path(self, full_path: str) -> str:
        """获取相对于 wiki_data 的路径"""
        root = self.path_manager.vault_path
        if full_path.startswith(root):
            return full_path[len(root):].replace("\\", "/").lstrip("/")
        return full_path

    def generate_index(self, notes: List[StructuredNote]) -> str:
        """生成 index.md"""
        md = "# Wiki 索引\n\n"
        md += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        # 统计信息
        md += self._generate_stats(notes)
        # 分类索引
        md += self._generate_category_index(notes)
        # 时间线
        md += self._generate_timeline(notes)
        # 热门关键词
        md += self._generate_keywords(notes)
        return md

    def _generate_stats(self, notes: List[StructuredNote]) -> str:
        md = "## 统计\n\n"
        # 总笔记数
        md += f"- 总笔记数: {len(notes)}\n"
        # 来源类型统计
        source_count = defaultdict(int)
        for note in notes:
            source_count[note.source_type] += 1
        md += f"- 平台采集 (auto): {source_count.get('auto', 0)}\n"
        md += f"- 手动写 (manual): {source_count.get('manual', 0)}\n"
        # 分类统计
        category_count = defaultdict(int)
        all_categories = set()
        for note in notes:
            category_count[note.category] += 1
            all_categories.add(note.category)
        # 输出所有分类（包括新增的）
        for cat in sorted(all_categories):
            md += f"- {cat}: {category_count.get(cat, 0)}\n"
        return md + "\n"

    def _generate_category_index(self, notes: List[StructuredNote]) -> str:
        md = "## 分类索引\n\n"
        # 获取所有分类
        all_categories = set()
        for note in notes:
            all_categories.add(note.category)
        # 输出所有分类
        for category in sorted(all_categories):
            md += f"### {category}\n\n"
            category_notes = [n for n in notes if n.category == category]
            if not category_notes:
                md += "(暂无笔记)\n\n"
                continue
            for note in category_notes:
                src_label = "🤖" if note.source_type == "auto" else "✍️"
                md += f"- {src_label} [{note.title}]({note.relative_path})\n"
            md += "\n"
        return md

    def _generate_timeline(self, notes: List[StructuredNote]) -> str:
        md = "## 时间线\n\n"
        # 按日期分组
        date_groups: Dict[str, List[StructuredNote]] = defaultdict(list)
        for note in notes:
            date_key = note.created_at.strftime("%Y-%m-%d")
            date_groups[date_key].append(note)
        # 生成时间线
        sorted_dates = sorted(date_groups.keys(), reverse=True)
        for date_key in sorted_dates:
            md += f"### {date_key}\n\n"
            for note in date_groups[date_key]:
                src_label = "🤖" if note.source_type == "auto" else "✍️"
                md += f"- {src_label} [{note.title}]({note.relative_path})\n"
            md += "\n"
        return md

    def _generate_keywords(self, notes: List[StructuredNote]) -> str:
        md = "## 热门关键词\n\n"
        keyword_count: Dict[str, int] = defaultdict(int)
        for note in notes:
            for kw in note.keywords:
                keyword_count[kw] += 1
        if not keyword_count:
            md += "(暂无关键词)\n"
            return md
        # 排序取 Top 10
        sorted_keywords = sorted(
            keyword_count.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        for kw, count in sorted_keywords:
            md += f"- {kw} ({count})\n"
        return md + "\n"

    def update_index(self):
        """更新 index.md"""
        notes = self.scan_notes()
        index_content = self.generate_index(notes)
        index_path = os.path.join(self.path_manager.vault_path, "index.md")
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(index_content)
        return index_path
