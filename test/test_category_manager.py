#!/usr/bin/env python3
"""
分类管理功能测试脚本
"""

import sys
import os

# 添加项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print("=" * 70)
print("Wiki 分类管理功能测试")
print("=" * 70)

from config import get_config
from wiki import WikiPathManager, CategoryManager

config = get_config()
path_manager = WikiPathManager(config.wiki.wiki_data_root)
category_manager = CategoryManager(path_manager)

print("\n1. 列出所有分类:")
categories = category_manager.list_categories()
print(f"   当前分类: {categories}")

print("\n2. 创建一个新分类 'test_category':")
result = category_manager.create_category("test_category")
print(f"   结果: {result}")

print("\n3. 再次列出分类:")
categories = category_manager.list_categories()
print(f"   分类列表: {categories}")

print("\n4. 获取分类信息:")
info = category_manager.get_category_info("test_category")
print(f"   分类信息: {info}")

print("\n5. 重命名分类 'test_category' -> 'temp_notes':")
result = category_manager.rename_category("test_category", "temp_notes")
print(f"   结果: {result}")

print("\n6. 获取所有分类信息:")
all_info = category_manager.get_all_category_info()
print(f"   总分类: {all_info['total_categories']}")
print(f"   总笔记: {all_info['total_notes']}")
print(f"   总大小: {all_info['total_size_kb']} KB")

print("\n7. 重命名 'temp_notes' -> 'test_category'（恢复）:")
result = category_manager.rename_category("temp_notes", "test_category")
print(f"   结果: {result}")

print("\n8. 删除分类 'test_category':")
result = category_manager.delete_category("test_category", delete_notes=True)
print(f"   结果: {result}")

print("\n" + "=" * 70)
print("分类管理功能测试完成！")
print("=" * 70)

print("\n\nWikiTool 使用示例:")
print("-" * 70)
print("from tools import get_wiki_tool")
print("wiki = get_wiki_tool()")
print("")
print("wiki.list_categories()  # 列出分类")
print("wiki.create_category('new_cat')  # 新建")
print("wiki.rename_category('old', 'new')  # 重命名")
print("wiki.delete_category('old', delete_notes=True)  # 删除")
print("wiki.move_note('file.md', 'cat1', 'cat2')  # 移动单条笔记")
print("wiki.move_all_notes('cat1', 'cat2')  # 移动全部笔记")
