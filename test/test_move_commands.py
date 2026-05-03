#!/usr/bin/env python3
"""
测试移动笔记命令
"""

import sys
import os

# 添加项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print("=" * 70)
print("测试移动笔记命令")
print("=" * 70)

from wiki import WikiCommandHandler

handler = WikiCommandHandler()

print("\n1. 测试 /listcats")
is_cmd, msg = handler.process_command("/listcats")
print(f"   {msg}")

print("\n2. 测试 /createcat 临时")
is_cmd, msg = handler.process_command("/createcat 临时")
print(f"   {msg}")

print("\n3. 测试 /createcat 归档")
is_cmd, msg = handler.process_command("/createcat 归档")
print(f"   {msg}")

print("\n4. 测试 /listcats")
is_cmd, msg = handler.process_command("/listcats")
print(f"   {msg}")

print("\n5. 测试 /wikihelp")
is_cmd, msg = handler.process_command("/wikihelp")
print(f"   {msg}")

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)

print("\n📋 使用示例：")
print("----------------------------------------")
print("发送给 Bot 的命令示例：")
print("- /catinfo 技术类 → 查看该分类下的笔记列表")
print("- /movenote 20260503_123456_笔记.md 技术类 工作 → 移动单条")
print("- /moveallnotes 临时 归档 → 移动整个分类")
