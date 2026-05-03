"""Phase 3: 索引管理 测试用例"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import WikiConfig
from wiki import (
    WikiPathManager,
    NoteSaver,
    StructuredNote,
    IndexManager
)


def test_note_parser():
    """测试 NoteParser：解析 Markdown 笔记"""
    print("=" * 70)
    print("测试 NoteParser")
    print("=" * 70)

    config = WikiConfig()
    path_manager = WikiPathManager("wiki_data/")
    saver = NoteSaver(path_manager)

    # 保存一个测试笔记
    note = StructuredNote(
        title="测试索引管理",
        summary="这是一个用于测试索引管理的笔记，包含摘要和关键词。",
        keywords=["测试", "索引", "Python"],
        key_points=["测试 NoteParser", "测试 IndexManager"],
        backlinks=["链接1"],
        category="技术类",
        optimized_content="这是优化后的内容。",
        source_path="parser_test.md"
    )

    saved_path = saver.save_structured_note(note)
    print(f"[PASS] 测试笔记已保存到: {saved_path}")

    # 测试解析
    from wiki.index import NoteParser
    parsed_note = NoteParser.from_markdown(saved_path)
    assert parsed_note.title == note.title
    assert parsed_note.category == note.category
    assert parsed_note.keywords == note.keywords
    print(f"[PASS] NoteParser 解析成功，标题: {parsed_note.title}")
    print()


def test_index_manager():
    """测试 IndexManager：扫描和索引管理"""
    print("=" * 70)
    print("测试 IndexManager")
    print("=" * 70)

    config = WikiConfig()
    path_manager = WikiPathManager("wiki_data/")
    manager = IndexManager(path_manager)

    # 扫描笔记
    notes = manager.scan_notes()
    print(f"[PASS] 扫描到 {len(notes)} 条笔记")

    # 生成索引
    index_content = manager.generate_index(notes)
    assert "# Wiki 索引" in index_content
    assert "## 统计" in index_content
    print(f"[PASS] 索引内容生成成功")

    # 更新 index.md
    index_path = manager.update_index()
    assert os.path.exists(index_path)
    print(f"[PASS] index.md 已更新到: {index_path}")
    print()


def test_full_workflow():
    """完整工作流测试：保存笔记 -> 扫描 -> 更新索引"""
    print("=" * 70)
    print("测试完整工作流")
    print("=" * 70)

    config = WikiConfig()
    path_manager = WikiPathManager("wiki_data/")
    saver = NoteSaver(path_manager)
    manager = IndexManager(path_manager)

    # 1. 保存几个测试笔记
    test_notes = [
        StructuredNote(
            title="Python 学习笔记",
            summary="关于 Python 列表和字典的学习记录",
            keywords=["Python", "学习", "列表", "字典"],
            key_points=["列表推导式", "字典操作"],
            backlinks=["编程学习"],
            category="学习类",
            optimized_content="Python 学习笔记内容",
            source_path="python_note.md"
        ),
        StructuredNote(
            title="AI 思考",
            summary="关于 AI 未来发展的思考",
            keywords=["AI", "思考", "未来"],
            key_points=["思考 1", "思考 2"],
            backlinks=["技术趋势"],
            category="想法类",
            optimized_content="思考内容",
            source_path="ai_thoughts.md"
        ),
        StructuredNote(
            title="日常记录",
            summary="2026-05-03 的日常记录",
            keywords=["日常"],
            key_points=["日常 1"],
            backlinks=[],
            category="日常类",
            optimized_content="日常内容",
            source_path="daily.md"
        )
    ]

    print("保存测试笔记...")
    for n in test_notes:
        saver.save_structured_note(n)

    # 2. 更新索引
    print("更新索引...")
    index_path = manager.update_index()

    # 3. 验证
    assert os.path.exists(index_path)
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Python 学习笔记" in content
        assert "AI 思考" in content
        assert "日常记录" in content

    print("[PASS] 完整工作流测试通过！")
    print(f"index.md 位置: {index_path}")
    print()


if __name__ == "__main__":
    test_note_parser()
    test_index_manager()
    test_full_workflow()
    print("=" * 70)
    print("所有 Phase 3 测试通过！")
    print("=" * 70)
