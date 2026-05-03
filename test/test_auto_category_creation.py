#!/usr/bin/env python3
"""
自动创建分类功能测试
"""

import sys
import os

# 添加项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print("=" * 70)
print("测试：AI 自由建议分类并自动创建")
print("=" * 70)

from config import get_config
from tools import get_wiki_tool

config = get_config()
wiki = get_wiki_tool()

print("\n1. 当前分类列表:")
result = wiki.list_categories()
print(f"   {result}")

print("\n2. 处理一条测试内容（AI 会自由分类）:")
test_content = """
《富爸爸穷爸爸》读书笔记：
核心观点：
- 资产 vs 负债：资产是把钱放进你口袋的东西
- 富人不为钱工作，让钱为自己工作
- 学习财务知识，关注自己的事业
- 税收和公司的力量
"""

result = wiki.process_note(test_content, "test_auto_category_creation.md")
print(f"   处理结果: {result}")

print("\n3. 再次查看分类列表（应该有新分类！）:")
result = wiki.list_categories()
print(f"   {result}")

print("\n4. 查看所有分类信息:")
result = wiki.get_all_category_info()
print(f"   总分类: {result['info']['total_categories']}")
print(f"   总笔记: {result['info']['total_notes']}")

print("\n" + "=" * 70)
print("测试完成！")
print("=" * 70)
