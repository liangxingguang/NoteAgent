"""Phase 5: Wiki 知识网络 测试用例"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import WikiConfig
from wiki import (
    WikiPathManager,
    KnowledgeGraph
)


def test_knowledge_graph():
    """测试 KnowledgeGraph 完整功能"""
    print("=" * 70)
    print("测试 KnowledgeGraph")
    print("=" * 70)

    config = WikiConfig()
    path_manager = WikiPathManager("wiki_data/")
    kg = KnowledgeGraph(path_manager)

    # 1. 导入知识
    print("1. 导入知识...")
    kg.import_from_notes()
    stats = kg.get_stats()
    print(f"   - 实体数: {stats['entities']}")
    print(f"   - 概念数: {stats['concepts']}")
    print(f"   - 笔记数: {stats['notes']}")

    # 2. 验证实体和概念已保存
    entities_dir = path_manager.get_wiki_full_path("entities")
    concepts_dir = path_manager.get_wiki_full_path("concepts")
    assert os.path.exists(entities_dir)
    assert os.path.exists(concepts_dir)
    print(f"[PASS] 知识已保存到目录!")

    # 3. 查询功能测试
    print("\n2. 查询功能测试...")
    results = kg.query("Python")
    print(f"   - 相关实体: {len(results['entities'])}")
    print(f"   - 相关概念: {len(results['concepts'])}")
    print(f"   - 相关笔记: {len(results['related_notes'])}")

    # 4. 健康检查
    print("\n3. 健康检查...")
    health = kg.health_check()
    print(f"   - 孤立实体: {len(health['isolated_entities'])}")
    print(f"   - 孤立概念: {len(health['isolated_concepts'])}")

    print("\n" + "=" * 70)
    print("[PASS] KnowledgeGraph 测试通过！")
    print("=" * 70)


def test_stats():
    """测试统计功能"""
    print("\n" + "=" * 70)
    print("测试统计功能")
    print("=" * 70)

    config = WikiConfig()
    path_manager = WikiPathManager("wiki_data/")
    kg = KnowledgeGraph(path_manager)

    stats = kg.get_stats()
    assert "entities" in stats
    assert "concepts" in stats
    assert "notes" in stats
    print(f"[PASS] 统计信息: {stats}")


if __name__ == "__main__":
    test_knowledge_graph()
    test_stats()
    print("\n所有 Phase 5 测试通过！")
