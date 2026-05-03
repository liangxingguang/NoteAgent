"""Phase 2 单元测试"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import WikiConfig
from wiki.path_utils import WikiPathManager
from wiki.models import StructuredNote
from wiki.saver import NoteSaver


class MockNoteProcessor:
    """模拟的 NoteProcessor，不实际调用 LLM"""

    def __init__(self, config: WikiConfig):
        self.config = config

    def process_note(self, content: str, source_path: str) -> StructuredNote:
        """模拟处理笔记，返回固定结果"""
        return StructuredNote(
            title="测试笔记标题",
            summary="这是一条用于测试的摘要，不超过 150 字。",
            keywords=["测试", "验证", "开发"],
            key_points=["要点 1", "要点 2", "要点 3"],
            backlinks=["链接 1", "链接 2"],
            category="技术类",
            optimized_content="这是优化后的内容。",
            source_path=source_path
        )


def test_structured_note():
    """测试 StructuredNote 类"""
    note = StructuredNote(
        title="测试标题",
        summary="这是一个测试摘要，用于验证功能。",
        keywords=["测试", "验证"],
        key_points=["要点1", "要点2"],
        backlinks=["链接1"],
        category="技术类",
        optimized_content="优化后的内容",
        source_path="test.md"
    )
    md = note.to_markdown()
    assert "# 测试标题" in md
    assert "## 摘要" in md
    assert "测试摘要" in md
    print("[PASS] StructuredNote 测试通过")


def test_structured_note_to_markdown():
    """测试 StructuredNote.to_markdown() 方法"""
    note = StructuredNote(
        title="Markdown 测试",
        summary="测试 Markdown 生成功能",
        keywords=["Markdown", "测试"],
        key_points=["要点一", "要点二", "要点三"],
        backlinks=["链接 A", "链接 B"],
        category="学习类",
        optimized_content="这是优化后的内容。",
        source_path="markdown_test.md"
    )
    md = note.to_markdown()
    assert "# Markdown 测试" in md
    assert "## 关键词" in md
    assert "Markdown" in md
    assert "## 核心要点" in md
    assert "1. 要点一" in md
    assert "## 双向链接" in md
    assert "[[链接 A]]" in md
    assert "## 优化内容" in md
    print("[PASS] StructuredNote.to_markdown() 测试通过")


def test_note_saver():
    """测试 NoteSaver 类"""
    config = WikiConfig()
    path_manager = WikiPathManager("wiki_data/")
    saver = NoteSaver(path_manager)

    note = StructuredNote(
        title="测试保存功能",
        summary="这是一个测试摘要",
        keywords=["测试"],
        key_points=["要点"],
        backlinks=[],
        category="日常类",
        optimized_content="测试内容",
        source_path="test_save.md"
    )

    save_path = saver.save_structured_note(note)
    assert os.path.exists(save_path)
    print(f"[PASS] NoteSaver 测试通过，文件已保存至: {save_path}")

    # 验证文件内容
    with open(save_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "# 测试保存功能" in content


def test_path_utils_integration():
    """测试 PathUtils 与 Saver 的集成"""
    path_manager = WikiPathManager("wiki_data/")
    saver = NoteSaver(path_manager)

    note = StructuredNote(
        title="路径集成测试",
        summary="测试路径管理和保存的集成",
        keywords=["集成", "路径"],
        key_points=["集成要点"],
        backlinks=[],
        category="技术类",
        optimized_content="集成内容",
        source_path="integration_test.md"
    )

    save_path = saver.save_structured_note(note)
    print(f"[PASS] 路径管理集成测试通过，保存路径: {save_path}")
    assert "wiki_data/structured/技术类" in save_path.replace("\\", "/")


def test_full_workflow():
    """测试完整工作流（使用 MockNoteProcessor）"""
    config = WikiConfig(enabled=True)
    path_manager = WikiPathManager("wiki_data/")
    processor = MockNoteProcessor(config)
    saver = NoteSaver(path_manager)

    test_content = "这是一条测试笔记，用于验证完整工作流功能。"
    note = processor.process_note(test_content, "workflow_test.md")
    save_path = saver.save_structured_note(note)

    assert os.path.exists(save_path)
    print(f"[PASS] 完整工作流测试通过，文件已保存至: {save_path}")


if __name__ == "__main__":
    print("=" * 50)
    print("Phase 2 单元测试")
    print("=" * 50)

    test_structured_note()
    test_structured_note_to_markdown()
    test_note_saver()
    test_path_utils_integration()
    test_full_workflow()

    print("=" * 50)
    print("所有测试通过!")
    print("=" * 50)
