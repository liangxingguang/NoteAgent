"""Wiki Pipeline 测试用例"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import WikiConfig
from wiki import (
    NotePipeline,
    ClassificationFilter,
    SelfCorrectionFilter,
    InputType,
    NoteSaver,
    WikiPathManager
)


def test_classification_filter():
    """测试 Classification Agent（分类路由）"""
    config = WikiConfig()
    classifier = ClassificationFilter(config)

    # 测试纯文本
    data = {"content": "今天天气很好，适合出去散步。"}
    result = classifier.process(data)
    assert result["input_type"] == InputType.PURE_TEXT
    print("[PASS] Classification: 纯文本分类正确")

    # 测试 URL
    data = {"content": "看看这篇文章：https://example.com"}
    result = classifier.process(data)
    assert result["input_type"] == InputType.URL
    print("[PASS] Classification: URL 分类正确")

    # 测试问题
    data = {"content": "Python 怎么学习？"}
    result = classifier.process(data)
    assert result["input_type"] == InputType.QUESTION
    print("[PASS] Classification: 问题分类正确")

    # 测试代码
    data = {"content": "```python\ndef hello():\n    print('hello')\n```"}
    result = classifier.process(data)
    assert result["input_type"] == InputType.CODE
    print("[PASS] Classification: 代码分类正确")

    print("[OK] Classification Agent 测试通过!")


def test_self_correction_filter():
    """测试 Self-Correction 机制"""
    config = WikiConfig()
    corrector = SelfCorrectionFilter(config)

    # 测试完整数据
    data = {
        "structured_data": {
            "title": "测试",
            "summary": "摘要",
            "keywords": ["k1"],
            "key_points": ["p1"],
            "backlinks": [],
            "category": "技术类",
            "optimized_content": ""
        }
    }
    result = corrector.process(data)
    assert result["structured_data"]["title"] == "测试"
    print("[PASS] Self-Correction: 完整数据验证通过")

    # 测试缺失字段的数据（应该自动修复）
    data = {
        "structured_data": {
            "title": "测试"
            # 缺少其他字段
        }
    }
    result = corrector.process(data)
    assert "summary" in result["structured_data"]
    print("[PASS] Self-Correction: 缺失字段自动修复")

    # 测试错误类型的数据
    data = {
        "structured_data": {
            "title": "测试",
            "summary": "摘要",
            "keywords": "不是列表",
            "key_points": "也不是列表",
            "backlinks": [],
            "category": "技术类",
            "optimized_content": ""
        }
    }
    result = corrector.process(data)
    assert isinstance(result["structured_data"]["keywords"], list)
    print("[PASS] Self-Correction: 类型错误自动修复")

    print("[OK] Self-Correction 机制测试通过!")


def test_note_pipeline():
    """测试完整的 NotePipeline"""
    config = WikiConfig()
    pipeline = NotePipeline(config)
    path_manager = WikiPathManager("wiki_data/")
    saver = NoteSaver(path_manager)

    # 测试处理（使用默认的 LLM 调用逻辑，虽然没有真的 API）
    note = pipeline.process(
        "这是一条用于测试 Pipeline 的笔记内容，包含一些简单的文本。",
        "pipeline_test.md"
    )

    assert note.title is not None
    assert note.summary is not None
    assert note.category in ["技术类", "想法类", "学习类", "日常类"]

    save_path = saver.save_structured_note(note)
    assert os.path.exists(save_path)
    print(f"[OK] NotePipeline 测试通过! 文件保存至: {save_path}")


class MockNotePipeline(NotePipeline):
    """Mock NotePipeline，不实际调用 LLM"""

    def __init__(self, config: WikiConfig):
        super().__init__(config)

    def _call_llm(self, content: str) -> dict:
        return {
            "title": "Mock 标题",
            "summary": "Mock 摘要，不超过 150 字。",
            "keywords": ["测试", "Mock"],
            "key_points": ["Mock 要点 1", "Mock 要点 2"],
            "backlinks": ["链接 1"],
            "category": "学习类",
            "optimized_content": "Mock 优化后的内容。"
        }


def test_mock_pipeline():
    """使用 Mock 的 Pipeline 测试完整工作流"""
    config = WikiConfig()
    pipeline = MockNotePipeline(config)
    path_manager = WikiPathManager("wiki_data/")
    saver = NoteSaver(path_manager)

    # 完整测试
    test_cases = [
        ("纯文本内容，测试 Pipeline 处理流程。", InputType.PURE_TEXT),
        ("这个链接不错：https://example.com", InputType.URL),
        ("Python 怎么写递归？", InputType.QUESTION)
    ]

    for content, expected_type in test_cases:
        note = pipeline.process(content, "test_case.md")
        assert note.title == "Mock 标题"
        save_path = saver.save_structured_note(note)
        print(f"  - 测试内容: '{content[:30]}...' -> 分类: {expected_type}")
        assert os.path.exists(save_path)

    print("[OK] Mock Pipeline 完整工作流测试通过!")


if __name__ == "__main__":
    print("=" * 60)
    print("Wiki Pipeline 架构测试")
    print("=" * 60)
    print()
    test_classification_filter()
    print()
    test_self_correction_filter()
    print()
    test_mock_pipeline()
    print()
    test_note_pipeline()
    print()
    print("=" * 60)
    print("所有测试通过！Pipeline 架构工作正常！")
    print("=" * 60)
