"""Wiki 工具 - 与 NoteAgents 系统集成"""

import os
from typing import Dict, Any, Optional

from config import get_config
from wiki import (
    WikiWorkflow,
    KnowledgeGraph,
    IndexManager,
    WikiPathManager,
    FileWatcher,
    CategoryManager
)


class WikiTool:
    """Wiki 工具 - 与 NoteAgents 系统集成工具"""

    def __init__(self):
        """初始化 Wiki 工具"""
        self.config = get_config().wiki
        self.path_manager = WikiPathManager(self.config.vault_path)
        self.workflow = WikiWorkflow(self.config)
        self.index_manager = IndexManager(self.path_manager)
        self.kg = KnowledgeGraph(self.path_manager)
        self.category_manager = CategoryManager(self.path_manager)

    def process_note_from_auto(self, note_content: str, source_path: Optional[str] = None) -> Dict[str, Any]:
        """处理平台采集的笔记"""
        if not source_path:
            source_path = "auto_note.md"
        # 保存到 raw/auto/ 目录
        raw_dir = self.path_manager.get_raw_auto_full_path()
        self.path_manager.ensure_directory_exists(raw_dir)
        import uuid
        temp_file = os.path.join(raw_dir, f"auto_{uuid.uuid4().hex[:8]}.md")
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(note_content)
        # 处理笔记（workflow 会判断来源类型）
        saved_path = self.workflow.process_file(temp_file)
        if saved_path:
            return {
                "success": True,
                "saved_path": saved_path,
                "source_type": "auto"
            }
        return {
            "success": False,
            "error": "处理失败"
        }

    def process_note_from_manual(self, note_content: str, source_path: Optional[str] = None) -> Dict[str, Any]:
        """处理手动写的笔记"""
        if not source_path:
            source_path = "manual_note.md"
        # 保存到 raw/manual/ 目录
        raw_dir = self.path_manager.get_raw_manual_full_path()
        self.path_manager.ensure_directory_exists(raw_dir)
        import uuid
        temp_file = os.path.join(raw_dir, f"manual_{uuid.uuid4().hex[:8]}.md")
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(note_content)
        # 处理笔记（workflow 会判断来源类型）
        saved_path = self.workflow.process_file(temp_file)
        if saved_path:
            return {
                "success": True,
                "saved_path": saved_path,
                "source_type": "manual"
            }
        return {
            "success": False,
            "error": "处理失败"
        }

    def process_note(self, note_content: str, source_path: Optional[str] = None, source_type: str = "manual") -> Dict[str, Any]:
        """处理单条笔记（兼容保留）"""
        if source_type == "auto":
            return self.process_note_from_auto(note_content, source_path)
        return self.process_note_from_manual(note_content, source_path)

    def update_index(self) -> Dict[str, Any]:
        """更新全局索引"""
        self.index_manager.update_index()
        return {
            "success": True,
            "message": "索引已更新"
        }

    def import_knowledge(self) -> Dict[str, Any]:
        """导入知识"""
        self.kg.import_from_notes()
        stats = self.kg.get_stats()
        return {
            "success": True,
            "stats": stats
        }

    def query_knowledge(self, keyword: str) -> Dict[str, Any]:
        """查询知识"""
        results = self.kg.query(keyword)
        return {
            "success": True,
            "results": results
        }

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health_report = self.kg.health_check()
        return {
            "success": True,
            "report": health_report
        }

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        notes_stats = {
            "notes": len(self.index_manager.scan_notes())
        }
        kg_stats = self.kg.get_stats()
        return {
            "success": True,
            "notes": notes_stats,
            "knowledge": kg_stats
        }

    def start_watcher(self, poll_interval: float = 5.0) -> FileWatcher:
        """启动文件监控（集成，返回 FileWatcher 实例）"""
        watcher = self.workflow.create_file_watcher(poll_interval)
        watcher.start(daemon=True)
        return watcher

    def list_categories(self) -> Dict[str, Any]:
        """列出所有分类"""
        categories = self.category_manager.list_categories()
        return {
            "success": True,
            "categories": categories
        }

    def create_category(self, category_name: str) -> Dict[str, Any]:
        """创建新分类"""
        return self.category_manager.create_category(category_name)

    def delete_category(self, category_name: str, delete_notes: bool = False) -> Dict[str, Any]:
        """删除分类（可选删除该分类下的笔记）"""
        return self.category_manager.delete_category(category_name, delete_notes)

    def rename_category(self, old_name: str, new_name: str) -> Dict[str, Any]:
        """重命名分类"""
        return self.category_manager.rename_category(old_name, new_name)

    def move_note(
        self,
        note_filename: str,
        from_category: str,
        to_category: str
    ) -> Dict[str, Any]:
        """移动单个笔记"""
        return self.category_manager.move_note(note_filename, from_category, to_category)

    def move_all_notes(
        self,
        from_category: str,
        to_category: str
    ) -> Dict[str, Any]:
        """移动一个分类下的所有笔记到另一个分类"""
        return self.category_manager.move_all_notes(from_category, to_category)

    def get_category_info(self, category_name: str) -> Dict[str, Any]:
        """获取单个分类信息"""
        info = self.category_manager.get_category_info(category_name)
        if info:
            return {
                "success": True,
                "info": info
            }
        else:
            return {
                "success": False,
                "error": f"分类 '{category_name}' 不存在"
            }

    def get_all_category_info(self) -> Dict[str, Any]:
        """获取所有分类信息"""
        info = self.category_manager.get_all_category_info()
        return {
            "success": True,
            "info": info
        }


# 全局实例
_wiki_tool: Optional[WikiTool] = None


def get_wiki_tool() -> WikiTool:
    """获取 Wiki 工具实例"""
    global _wiki_tool
    if _wiki_tool is None:
        _wiki_tool = WikiTool()
    return _wiki_tool
