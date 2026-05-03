"""
Wiki 命令处理器
通过 Telegram/Feishu Bot 管理 Wiki 和分类！
"""

from typing import Tuple, Optional
from config import get_config
from wiki import (
    WikiPathManager,
    CategoryManager,
    IndexManager,
    KnowledgeGraph
)


class WikiCommandHandler:
    """Wiki 命令处理器"""

    def __init__(self):
        """初始化"""
        self.config = get_config()
        self.path_manager = WikiPathManager(self.config.wiki.vault_path)
        self.category_manager = CategoryManager(self.path_manager)
        self.index_manager = IndexManager(self.path_manager)
        self.kg = KnowledgeGraph(self.path_manager)

    def process_command(self, text: str) -> Tuple[bool, str]:
        """处理命令并返回响应消息

        Returns:
            (是否是 Wiki 命令, 响应内容
        """
        text = text.strip()
        if not text.startswith("/"):
            return (False, "")

        # 解析命令
        parts = text.split(" ", 1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        # ==================== 帮助命令 ====================
        if cmd in ["/wikihelp", "/wiki"]:
            return (True, self._get_help_message())

        # ==================== 分类管理 ====================
        elif cmd == "/listcats":
            return (True, self._list_categories())

        elif cmd == "/createcat":
            if not args:
                return (True, "请提供分类名称，如：/createcat 工作笔记")
            result = self.category_manager.create_category(args.strip())
            if result.get("success"):
                return (True, f"✅ 分类 '{args.strip()}' 已创建！")
            else:
                return (True, f"❌ 创建失败：{result.get('error', '未知错误')}")

        elif cmd == "/deletecat":
            if not args:
                return (True, "请提供分类名称，如：/deletecat 旧分类")
            result = self.category_manager.delete_category(args.strip(), delete_notes=True)
            if result.get("success"):
                return (True, f"✅ 分类 '{args.strip()}' 已删除！（含笔记！）")
            else:
                return (True, f"❌ 删除失败：{result.get('error', '未知错误')}")

        elif cmd == "/renamecat":
            if not args or " " not in args:
                return (True, "请提供原分类和新分类，如：/renamecat 旧名 新名")
            old_name, new_name = args.split(" ", 1)
            result = self.category_manager.rename_category(old_name.strip(), new_name.strip())
            if result.get("success"):
                return (True, f"✅ 分类已重命名！")
            else:
                return (True, f"❌ 重命名失败：{result.get('error', '未知错误')}")

        elif cmd == "/catinfo":
            if not args:
                return (True, "请提供分类名称，如：/catinfo 技术类")
            info = self.category_manager.get_category_info(args.strip())
            if info:
                msg = f"""📁 分类信息：\n
名称：{info['name']}
笔记数：{info['note_count']}
大小：{info['total_size_kb']} KB
"""
                if info.get("notes"):
                    msg += "\n笔记列表：\n"
                    for note in info["notes"]:
                        msg += f"- {note}\n"
                return (True, msg)
            else:
                return (True, f"❌ 获取分类信息失败，分类不存在")

        elif cmd == "/movenote":
            if not args:
                return (True, "请提供笔记文件名、来源分类、目标分类，如：\n/movenote 20260503_123456_笔记.md 技术类 工作")
            # 解析参数
            parts = args.split(" ")
            # 过滤空字符串
            parts = [p for p in parts if p.strip()]
            if len(parts) < 3:
                return (True, "请提供 3 个参数：笔记文件名、来源分类、目标分类")
            filename = parts[0]
            from_cat = parts[1]
            to_cat = parts[2]
            result = self.category_manager.move_note(filename, from_cat, to_cat)
            if result.get("success"):
                return (True, f"✅ 笔记已移动！\n{filename}\n从: {from_cat}\n到: {to_cat}")
            else:
                return (True, f"❌ 移动失败：{result.get('error', '未知错误')}")

        elif cmd == "/moveallnotes":
            if not args:
                return (True, "请提供来源分类和目标分类，如：\n/moveallnotes 临时 归档")
            parts = args.split(" ")
            parts = [p for p in parts if p.strip()]
            if len(parts) < 2:
                return (True, "请提供 2 个参数：来源分类、目标分类")
            from_cat = parts[0]
            to_cat = parts[1]
            result = self.category_manager.move_all_notes(from_cat, to_cat)
            if result.get("success"):
                moved = result.get("moved", 0)
                return (True, f"✅ {moved} 条笔记已移动！\n从: {from_cat}\n到: {to_cat}")
            else:
                return (True, f"❌ 移动失败：{result.get('error', '未知错误')}")

        # ==================== Wiki 管理 ====================
        elif cmd == "/wikiinfo":
            all_info = self.category_manager.get_all_category_info()
            kg_stats = self.kg.get_stats()
            msg = f"""📊 Wiki 统计信息：

总分类数：{all_info['total_categories']}
总笔记数：{all_info['total_notes']}
总大小：{all_info['total_size_kb']} KB

知识网络统计：
- 实体数：{kg_stats['entity_count']}
- 概念数：{kg_stats['concept_count']}
"""
            return (True, msg)

        elif cmd == "/wikiupdateindex":
            self.index_manager.update_index()
            return (True, "✅ 全局索引已更新！")

        elif cmd == "/wikiimport":
            self.kg.import_from_notes()
            return (True, "✅ 知识已导入！")

        else:
            return (False, "")

    def _list_categories(self) -> str:
        """列出所有分类"""
        categories = self.category_manager.list_categories()
        if not categories:
            return "暂无分类！"
        msg = "📁 所有分类：\n\n"
        for cat in categories:
            info = self.category_manager.get_category_info(cat)
            if info:
                msg += f"- {cat} ({info['note_count']}条)\n"
            else:
                msg += f"- {cat}\n"
        return msg

    def _get_help_message(self) -> str:
        """返回帮助消息"""
        return """🤖 Wiki 管理 Bot 命令帮助：

分类管理：
- /wikihelp /wiki 显示帮助
- /listcats 列出所有分类
- /createcat [名] 新建分类
- /deletecat [名] 删除分类（会删除该分类下的笔记）
- /renamecat [旧名] [新名] 重命名分类
- /catinfo [名] 查看分类信息（含笔记列表）
- /movenote [文件名] [源分类] [目标分类] 移动单个笔记
- /moveallnotes [源分类] [目标分类] 移动整个分类的笔记

Wiki 管理：
- /wikiinfo 查看 Wiki 统计
- /wikiupdateindex 更新索引
- /wikiimport 导入知识网络"""
