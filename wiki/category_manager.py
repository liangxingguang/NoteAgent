"""分类管理器 - 管理 structured 下的分类"""

import os
import shutil
from typing import List, Dict, Any, Optional
from wiki.path_utils import WikiPathManager


class CategoryManager:
    """分类管理器"""

    def __init__(self, path_manager: WikiPathManager):
        """初始化分类管理器"""
        self.path_manager = path_manager
        self.structured_root = self.path_manager.get_structured_full_path("")
        self.path_manager.ensure_directory_exists(self.structured_root)

    def list_categories(self) -> List[str]:
        """列出所有分类"""
        if not os.path.exists(self.structured_root):
            return []
        categories = []
        for item in os.listdir(self.structured_root):
            item_path = os.path.join(self.structured_root, item)
            if os.path.isdir(item_path):
                categories.append(item)
        return sorted(categories)

    def create_category(self, category_name: str) -> Dict[str, Any]:
        """创建新分类"""
        if not category_name or category_name.strip() == "":
            return {
                "success": False,
                "error": "分类名称不能为空"
            }
        category_dir = self.path_manager.get_structured_full_path(category_name)
        if os.path.exists(category_dir):
            return {
                "success": False,
                "error": f"分类 '{category_name}' 已存在"
            }
        self.path_manager.ensure_directory_exists(category_dir)
        return {
            "success": True,
            "category": category_name,
            "path": category_dir
        }

    def delete_category(self, category_name: str, delete_notes: bool = False) -> Dict[str, Any]:
        """删除分类（可选删除该分类下的笔记）"""
        category_dir = self.path_manager.get_structured_full_path(category_name)
        if not os.path.exists(category_dir):
            return {
                "success": False,
                "error": f"分类 '{category_name}' 不存在"
            }
        note_count = len([f for f in os.listdir(category_dir) if f.endswith(".md")])
        if note_count > 0 and not delete_notes:
            return {
                "success": False,
                "error": f"分类 '{category_name}' 下有 {note_count} 条笔记，设置 delete_notes=true 可一并删除"
            }
        if delete_notes:
            shutil.rmtree(category_dir)
            deleted_count = note_count
        else:
            # 只删除目录（假设目录为空）
            try:
                os.rmdir(category_dir)
                deleted_count = 0
            except:
                return {
                    "success": False,
                    "error": f"分类 '{category_name}' 下有笔记，无法删除"
                }
        return {
            "success": True,
            "category": category_name,
            "deleted_notes": deleted_count
        }

    def move_note(
        self,
        note_filename: str,
        from_category: str,
        to_category: str
    ) -> Dict[str, Any]:
        """移动单个笔记从一个分类到另一个分类"""
        from_dir = self.path_manager.get_structured_full_path(from_category)
        to_dir = self.path_manager.get_structured_full_path(to_category)
        if not os.path.exists(from_dir):
            return {
                "success": False,
                "error": f"源分类 '{from_category}' 不存在"
            }
        if not os.path.exists(to_dir):
            # 目标分类不存在，自动创建
            self.path_manager.ensure_directory_exists(to_dir)
        from_path = os.path.join(from_dir, note_filename)
        if not os.path.exists(from_path):
            return {
                "success": False,
                "error": f"笔记 '{note_filename}' 在源分类 '{from_category}' 中不存在"
            }
        to_path = os.path.join(to_dir, note_filename)
        # 如果目标文件已存在，加上序号
        counter = 1
        base_name, ext = os.path.splitext(note_filename)
        while os.path.exists(to_path):
            to_path = os.path.join(to_dir, f"{base_name}_{counter}{ext}")
            counter += 1
        shutil.move(from_path, to_path)
        return {
            "success": True,
            "note": note_filename,
            "from": from_category,
            "to": to_category,
            "new_path": to_path
        }

    def move_all_notes(
        self,
        from_category: str,
        to_category: str
    ) -> Dict[str, Any]:
        """将一个分类下的所有笔记移动到另一个分类"""
        from_dir = self.path_manager.get_structured_full_path(from_category)
        to_dir = self.path_manager.get_structured_full_path(to_category)
        if not os.path.exists(from_dir):
            return {
                "success": False,
                "error": f"源分类 '{from_category}' 不存在"
            }
        if not os.path.exists(to_dir):
            self.path_manager.ensure_directory_exists(to_dir)
        notes = [f for f in os.listdir(from_dir) if f.endswith(".md")]
        if not notes:
            return {
                "success": True,
                "moved": 0,
                "from": from_category,
                "to": to_category,
                "message": "源分类下无笔记"
            }
        moved_count = 0
        for note in notes:
            from_path = os.path.join(from_dir, note)
            to_path = os.path.join(to_dir, note)
            # 处理重名
            counter = 1
            base_name, ext = os.path.splitext(note)
            while os.path.exists(to_path):
                to_path = os.path.join(to_dir, f"{base_name}_{counter}{ext}")
                counter += 1
            shutil.move(from_path, to_path)
            moved_count += 1
        return {
            "success": True,
            "moved": moved_count,
            "from": from_category,
            "to": to_category
        }

    def rename_category(
        self,
        old_name: str,
        new_name: str
    ) -> Dict[str, Any]:
        """重命名分类（实际上是新建、移动、删除）"""
        # 1. 检查旧分类是否存在
        old_dir = self.path_manager.get_structured_full_path(old_name)
        if not os.path.exists(old_dir):
            return {
                "success": False,
                "error": f"分类 '{old_name}' 不存在"
            }
        # 2. 检查新分类是否已存在
        new_dir = self.path_manager.get_structured_full_path(new_name)
        if os.path.exists(new_dir):
            return {
                "success": False,
                "error": f"分类 '{new_name}' 已存在"
            }
        # 3. 重命名目录
        os.rename(old_dir, new_dir)
        return {
            "success": True,
            "old": old_name,
            "new": new_name
        }

    def get_category_info(self, category_name: str) -> Optional[Dict[str, Any]]:
        """获取分类信息"""
        category_dir = self.path_manager.get_structured_full_path(category_name)
        if not os.path.exists(category_dir):
            return None
        notes = [f for f in os.listdir(category_dir) if f.endswith(".md")]
        note_count = len(notes)
        # 计算大小（粗略）
        total_size = 0
        for note in notes:
            note_path = os.path.join(category_dir, note)
            if os.path.isfile(note_path):
                total_size += os.path.getsize(note_path)
        return {
            "name": category_name,
            "path": category_dir,
            "note_count": note_count,
            "total_size_bytes": total_size,
            "total_size_kb": round(total_size / 1024, 2),
            "notes": notes
        }

    def get_all_category_info(self) -> Dict[str, Any]:
        """获取所有分类信息"""
        categories = self.list_categories()
        info = {}
        total_notes = 0
        total_size = 0
        for cat in categories:
            cat_info = self.get_category_info(cat)
            if cat_info:
                info[cat] = cat_info
                total_notes += cat_info["note_count"]
                total_size += cat_info["total_size_bytes"]
        return {
            "categories": info,
            "total_categories": len(categories),
            "total_notes": total_notes,
            "total_size_bytes": total_size,
            "total_size_kb": round(total_size / 1024, 2)
        }
