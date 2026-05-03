#!/usr/bin/env python3
"""
Wiki Bot 命令测试
"""

import sys
import os

# 添加项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print("=" * 70)
print("Wiki 命令处理器测试")
print("=" * 70)

from config import get_config
from wiki import WikiCommandHandler

config = get_config()
handler = WikiCommandHandler()

print("\n1. 测试 /wikihelp:")
is_cmd, msg = handler.process_command("/wikihelp")
print(f"   is_cmd: {is_cmd}")
print(f"   响应: {msg[:50]}...")

print("\n2. 测试 /listcats:")
is_cmd, msg = handler.process_command("/listcats")
print(f"   is_cmd: {is_cmd}")
print(f"   响应: {msg}")

print("\n3. 测试 /createcat 工作测试:")
is_cmd, msg = handler.process_command("/createcat 工作测试")
print(f"   is_cmd: {is_cmd}")
print(f"   响应: {msg}")

print("\n4. 测试 /listcats（再次）:")
is_cmd, msg = handler.process_command("/listcats")
print(f"   is_cmd: {is_cmd}")
print(f"   响应: {msg}")

print("\n5. 测试 /renamecat 工作测试 临时分类:")
is_cmd, msg = handler.process_command("/renamecat 工作测试 临时分类")
print(f"   is_cmd: {is_cmd}")
print(f"   响应: {msg}")

print("\n6. 测试 /deletecat 临时分类:")
is_cmd, msg = handler.process_command("/deletecat 临时分类")
print(f"   is_cmd: {is_cmd}")
print(f"   响应: {msg}")

print("\n" + "=" * 70)
print("测试完成！")
print("=" * 70)

print("\n\nBot 使用示例:")
print("-" * 70)
print("发送给 Bot：")
print("  /wikihelp  # 显示帮助")
print("  /listcats  # 列出所有分类")
print("  /createcat 新分类  # 新建分类")
print("  /renamecat 旧名 新名  # 重命名")
print("  /deletecat 分类名  # 删除分类（含笔记）")
print("  /wikiinfo  # 查看 Wiki 统计")
print("  /wikiupdateindex  # 更新索引")
print("  /wikiimport  # 导入知识")
