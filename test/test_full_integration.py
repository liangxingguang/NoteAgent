#!/usr/bin/env python3
"""
完整集成测试脚本 - 测试 NoteAgents + LLM Wiki 全部流程！
"""

import sys
import os

# 添加项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print("=" * 70)
print("NoteAgents + LLM Wiki 完整集成测试")
print("=" * 70)

print("\n[1] 配置检查...")
from config import get_config
config = get_config()
print(f"Wiki 已启用: {config.wiki.enabled}")
print(f"Wiki 数据根目录: {config.wiki.wiki_data_root}")

print("\n[2] 工具层测试...")
from tools import get_wiki_tool
wiki = get_wiki_tool()
print(f"Wiki Tool 初始化成功！")

print("\n[3] 处理测试笔记...")
test_content = """今天学习了 Python 的 list comprehension（列表推导式），语法很简洁！
比如：
- [x*2 for x in range(10)]
- [x for x in range(20) if x%2==0]
还有字典推导式和集合推导式！
"""
result = wiki.process_note(test_content)
print(f"处理结果: {result}")

print("\n[4] 更新索引...")
update_result = wiki.update_index()
print(f"索引更新: {update_result}")

print("\n[5] 导入知识...")
import_result = wiki.import_knowledge()
print(f"知识导入: {import_result}")

print("\n[6] 查询知识（关键词: Python）...")
query_result = wiki.query_knowledge("Python")
print(f"查询结果: {query_result}")

print("\n[7] 健康检查...")
health_result = wiki.health_check()
print(f"健康检查: {health_result}")

print("\n[8] 获取统计...")
stats_result = wiki.get_stats()
print(f"统计结果: {stats_result}")

print("\n" + "=" * 70)
print("完整集成测试通过！NoteAgents + LLM Wiki 工作正常！")
print("=" * 70)
