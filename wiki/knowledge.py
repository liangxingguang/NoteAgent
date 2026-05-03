"""Wiki 知识网络模块 - 基于 Karpathy 范式"""

import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Set
from collections import defaultdict

from wiki.path_utils import WikiPathManager
from wiki.index import IndexManager, NoteParser
from wiki.models import StructuredNote


@dataclass
class Entity:
    """实体"""
    name: str
    description: str
    tags: List[str]
    linked_notes: List[str]
    created_at: datetime = field(default_factory=datetime.now)

    def to_markdown(self) -> str:
        md = f"# 实体: {self.name}\n\n"
        md += f"## 描述\n\n{self.description}\n\n"
        md += f"## 标签\n\n{', '.join(self.tags)}\n\n"
        md += f"## 关联笔记\n\n"
        for note in self.linked_notes:
            md += f"- [{note}](../structured/{note})\n"
        md += f"\n---\n\n"
        md += f"*创建时间: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}*"
        return md


@dataclass
class Concept:
    """概念"""
    name: str
    definition: str
    related_concepts: List[str]
    linked_notes: List[str]
    created_at: datetime = field(default_factory=datetime.now)

    def to_markdown(self) -> str:
        md = f"# 概念: {self.name}\n\n"
        md += f"## 定义\n\n{self.definition}\n\n"
        md += f"## 相关概念\n\n"
        for concept in self.related_concepts:
            md += f"- [[{concept}]]\n"
        md += f"\n## 关联笔记\n\n"
        for note in self.linked_notes:
            md += f"- [{note}](../structured/{note})\n"
        md += f"\n---\n\n"
        md += f"*创建时间: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}*"
        return md


class KnowledgeGraph:
    """知识图谱管理器"""

    def __init__(self, path_manager: WikiPathManager):
        self.path_manager = path_manager
        self.entities: Dict[str, Entity] = {}
        self.concepts: Dict[str, Concept] = {}
        self.note_index: IndexManager = IndexManager(path_manager)

    def import_from_notes(self):
        """从笔记导入知识"""
        notes = self.note_index.scan_notes()
        for note in notes:
            self._process_note(note)
        self._save_knowledge()

    def _process_note(self, note: StructuredNote):
        """处理单条笔记"""
        # 从关键词提取实体和概念
        for kw in note.keywords:
            kw = kw.strip()
            if not kw:
                continue
            # 简单规则：3 字以上或包含技术词汇的视为概念
            if len(kw) > 2 or any(t in kw for t in ["技术", "方法", "模型", "算法", "系统"]):
                self._add_concept(kw, note)
            else:
                self._add_entity(kw, note)

    def _add_entity(self, name: str, note: StructuredNote):
        """添加实体"""
        note_rel_path = f"{note.category}/{os.path.basename(note.relative_path)}" if hasattr(note, 'relative_path') else note.category
        if name in self.entities:
            self.entities[name].linked_notes.append(note_rel_path)
        else:
            self.entities[name] = Entity(
                name=name,
                description=f"在笔记中提及的实体",
                tags=note.keywords,
                linked_notes=[note_rel_path]
            )

    def _add_concept(self, name: str, note: StructuredNote):
        """添加概念"""
        note_rel_path = f"{note.category}/{os.path.basename(note.relative_path)}" if hasattr(note, 'relative_path') else note.category
        if name in self.concepts:
            self.concepts[name].linked_notes.append(note_rel_path)
        else:
            self.concepts[name] = Concept(
                name=name,
                definition=f"在笔记中提及的概念",
                related_concepts=[kw for kw in note.keywords if kw != name],
                linked_notes=[note_rel_path]
            )

    def _save_knowledge(self):
        """保存知识到文件"""
        # 保存实体
        entities_dir = self.path_manager.get_wiki_full_path("entities")
        self.path_manager.ensure_directory_exists("wiki/entities/")
        for entity in self.entities.values():
            file_name = f"{entity.name.replace('/', '_').replace('\\', '_')}.md"
            file_path = os.path.join(entities_dir, file_name)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(entity.to_markdown())
        # 保存概念
        concepts_dir = self.path_manager.get_wiki_full_path("concepts")
        self.path_manager.ensure_directory_exists("wiki/concepts/")
        for concept in self.concepts.values():
            file_name = f"{concept.name.replace('/', '_').replace('\\', '_')}.md"
            file_path = os.path.join(concepts_dir, file_name)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(concept.to_markdown())

    def query(self, keyword: str) -> Dict[str, Any]:
        """查询知识"""
        results = {
            "entities": [],
            "concepts": [],
            "related_notes": []
        }
        keyword_lower = keyword.lower()
        # 查询实体
        for entity in self.entities.values():
            if keyword_lower in entity.name.lower():
                results["entities"].append(entity)
        # 查询概念
        for concept in self.concepts.values():
            if keyword_lower in concept.name.lower():
                results["concepts"].append(concept)
        # 查询相关笔记
        notes = self.note_index.scan_notes()
        for note in notes:
            if any(keyword_lower in kw.lower() for kw in note.keywords) or keyword_lower in note.title.lower():
                results["related_notes"].append(note)
        return results

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        issues = {
            "isolated_entities": [],
            "isolated_concepts": [],
            "broken_links": [],
            "stats": {
                "total_entities": len(self.entities),
                "total_concepts": len(self.concepts)
            }
        }
        # 检查孤立实体（没有关联笔记）
        for entity in self.entities.values():
            if not entity.linked_notes:
                issues["isolated_entities"].append(entity.name)
        # 检查孤立概念
        for concept in self.concepts.values():
            if not concept.linked_notes:
                issues["isolated_concepts"].append(concept.name)
        return issues

    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        return {
            "entities": len(self.entities),
            "concepts": len(self.concepts),
            "notes": len(self.note_index.scan_notes())
        }
