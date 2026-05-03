#!/usr/bin/env python3
"""
Wiki 配置测试脚本
"""

import sys
import os

# 添加项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print("=" * 70)
print("Wiki 配置测试")
print("=" * 70)

from config import get_config
config = get_config()

print("\nWiki 主开关:")
print(f"  WIKI_ENABLED: {config.wiki.enabled}")

print("\nWiki 路径配置:")
print(f"  WIKI_DATA_ROOT: {config.wiki.wiki_data_root}")
print(f"  WIKI_ARCHIVE_STRATEGY: {config.wiki.archive_strategy}")

print("\nWiki LLM 配置:")
print(f"  WIKI_LLM_MODEL: {config.wiki.llm_model}")
print(f"  WIKI_LLM_RETRY_TIMES: {config.wiki.llm_retry_times}")

print("\nWiki 自动化配置:")
print(f"  WIKI_AUTO_PROCESS: {config.wiki.auto_process}")
print(f"  WIKI_AUTO_IMPORT_WIKI: {config.wiki.auto_import_wiki}")
print(f"  WIKI_FILE_MONITOR_ENABLED: {config.wiki.file_monitor_enabled}")
print(f"  WIKI_FILE_MONITOR_INTERVAL: {config.wiki.file_monitor_interval}")

print("\nWiki 健康检查:")
print(f"  WIKI_HEALTH_CHECK_INTERVAL: {config.wiki.health_check_interval}")

print("\n" + "=" * 70)
print("配置加载完成！")
if config.wiki.enabled:
    print("✅ LLM Wiki 已启用！")
else:
    print("ℹ️ LLM Wiki 未启用（修改 WIKI_ENABLED=true 开启！）")
print("=" * 70)
