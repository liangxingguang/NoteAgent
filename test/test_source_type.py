#!/usr/bin/env python3
"""
测试来源类型（auto vs manual）
"""

import sys
import os

# 添加项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print("=" * 70)
print("测试来源类型区分")
print("=" * 70)

from tools import get_wiki_tool

wiki = get_wiki_tool()

print("\n1. 测试 auto 来源（平台采集）")
result_auto = wiki.process_note_from_auto("这是一条 Telegram 发的内容")
print(f"   auto 结果: {result_auto}")

print("\n2. 测试 manual 来源（手动写）")
result_manual = wiki.process_note_from_manual("这是一条手动写的内容")
print(f"   manual 结果: {result_manual}")

print("\n3. 列出分类")
result = wiki.list_categories()
print(f"   分类: {result}")

print("\n4. 更新索引")
result = wiki.update_index()
print(f"   结果: {result}")

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)
