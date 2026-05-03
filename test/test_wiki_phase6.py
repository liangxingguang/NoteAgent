"""Phase 6: 端到端集成测试"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config, WikiConfig
from wiki import (
    WikiPathManager,
    NotePipeline,
    NoteSaver,
    IndexManager,
    KnowledgeGraph,
    WikiWorkflow
)


def test_end_to_end_workflow():
    """端到端完整工作流测试"""
    print("=" * 80)
    print("端到端集成测试: 创建笔记 → LLM加工 → 保存 → 索引更新 → 知识导入")
    print("=" * 80)

    config = get_config()
    workflow = WikiWorkflow(config.wiki)
    path_manager = WikiPathManager(config.wiki.wiki_data_root)

    # 1. 创建测试笔记（模拟原始笔记）
    print("\n1. 创建原始笔记...")
    test_notes = [
        {
            "title": "Python 列表推导式学习",
            "content": """今天学习了 Python 列表推导式，非常好用！
            基本语法是: [expression for item in iterable]
            例如: [x*2 for x in range(10)]
            """,
            "keywords": ["Python", "列表推导式", "学习"],
            "category": "学习类"
        },
        {
            "title": "AI 大模型应用思考",
            "content": """关于 AI 大模型应用的一些思考，现在很多应用都在用大模型技术。
            比如聊天机器人、内容生成、知识问答等。
            """,
            "keywords": ["AI", "大模型", "应用", "思考"],
            "category": "想法类"
        },
        {
            "title": "NoteAgents 项目开发",
            "content": """今天开发了 NoteAgents 的 LLM Wiki 模块，实现了 Pipeline 架构。
            包括 Classification Agent 和 Self-Correction 机制。
            """,
            "keywords": ["NoteAgents", "LLM", "Wiki", "开发", "项目"],
            "category": "技术类"
        }
    ]

    # 保存到 raw/manual/
    saved_raw_paths = []
    for i, note_data in enumerate(test_notes):
        manual_dir = path_manager.get_raw_manual_full_path()
        path_manager.ensure_directory_exists(manual_dir)
        file_name = f"test_note_{i+1}.md"
        file_path = os.path.join(manual_dir, file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# {note_data['title']}\n\n")
            f.write(note_data['content'])
        saved_raw_paths.append(file_path)
        print(f"   - 笔记{i+1}已保存: {file_name}")

    # 2. 处理笔记（LLM 加工）
    print("\n2. 处理笔记...")
    saved_structured_paths = []
    for file_path in saved_raw_paths:
        saved_path = workflow.process_file(file_path)
        if saved_path:
            saved_structured_paths.append(saved_path)
            print(f"   - 已处理并保存: {os.path.basename(saved_path)}")

    # 3. 更新索引
    print("\n3. 更新索引...")
    index_manager = IndexManager(path_manager)
    index_manager.update_index()
    index_path = os.path.join(path_manager.wiki_data_root, "index.md")
    assert os.path.exists(index_path)
    print(f"   - 索引已更新: index.md")

    # 4. 知识导入
    print("\n4. 导入知识...")
    kg = KnowledgeGraph(path_manager)
    kg.import_from_notes()
    stats = kg.get_stats()
    print(f"   - 统计: 实体={stats['entities']}, 概念={stats['concepts']}, 笔记={stats['notes']}")

    # 5. 查询测试
    print("\n5. 查询测试...")
    results = kg.query("Python")
    print(f"   - 查询'Python': 相关概念={len(results['concepts'])}, 相关笔记={len(results['related_notes'])}")

    # 6. 健康检查
    print("\n6. 健康检查...")
    health = kg.health_check()
    print(f"   - 健康检查: 孤立实体={len(health['isolated_entities'])}, 孤立概念={len(health['isolated_concepts'])}")

    print("\n" + "=" * 80)
    print("端到端集成测试通过！")
    print("=" * 80)

    return True


def test_exceptions():
    """异常处理测试"""
    print("\n" + "=" * 80)
    print("异常处理测试")
    print("=" * 80)

    config = WikiConfig()
    path_manager = WikiPathManager("wiki_data/")
    workflow = WikiWorkflow(config)

    # 1. 测试不存在的文件
    print("\n1. 测试不存在的文件...")
    result = workflow.process_file("non_existent_file.md")
    assert result is None
    print("   - 不存在的文件处理正确")

    # 2. 测试空内容文件
    print("\n2. 测试空内容文件...")
    empty_file = os.path.join(path_manager.get_raw_manual_full_path(), "empty.md")
    with open(empty_file, "w", encoding="utf-8") as f:
        f.write("")
    result = workflow.process_file(empty_file)
    print("   - 空内容文件处理完成")

    print("\n" + "=" * 80)
    print("异常处理测试通过！")
    print("=" * 80)


def test_archive_strategies():
    """归档策略测试（按日 vs 按月）"""
    print("\n" + "=" * 80)
    print("归档策略测试: 按日归档 vs 按月归档")
    print("=" * 80)

    # 测试按日归档
    daily_manager = WikiPathManager("wiki_data_test_daily/", "daily")
    daily_path = daily_manager.get_raw_manual_full_path()
    print(f"\n1. 按日归档路径: {daily_path}")

    # 测试按月归档
    monthly_manager = WikiPathManager("wiki_data_test_monthly/", "monthly")
    monthly_path = monthly_manager.get_raw_manual_full_path()
    print(f"2. 按月归档路径: {monthly_path}")

    print("\n" + "=" * 80)
    print("归档策略测试通过！")
    print("=" * 80)


if __name__ == "__main__":
    test_end_to_end_workflow()
    test_exceptions()
    test_archive_strategies()

    print("\n" + "=" * 80)
    print("🎉 所有 Phase 6 集成测试通过！")
    print("=" * 80)
