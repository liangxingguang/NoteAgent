"""ToolUse Filter 使用示例

展示如何在现有架构上轻量级添加工具调用能力！
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import WikiConfig
from wiki import (
    NotePipeline,
    ToolUseFilter,
    ClassificationFilter,
    SelfCorrectionFilter,
    NoteSaver,
    WikiPathManager
)


def main():
    print("=" * 70)
    print("ToolUse Filter 使用示例")
    print("=" * 70)
    print()

    config = WikiConfig()

    # 方式 1: 使用默认的 NotePipeline（不含 ToolUse）
    print("方式 1: 使用默认 NotePipeline")
    print("-" * 70)
    pipeline_basic = NotePipeline(config)
    note_basic = pipeline_basic.process(
        "今天学习了 Python 列表推导式，非常有用！",
        "basic_test.md"
    )
    print(f"  - 标题: {note_basic.title}")
    print(f"  - 分类: {note_basic.category}")
    print()

    # 方式 2: 自定义 Pipeline，添加 ToolUseFilter
    print("方式 2: 自定义 Pipeline + ToolUseFilter")
    print("-" * 70)
    # 注意：不继承 NotePipeline，自己组装，因为 NotePipeline 内部固定了 filters
    # 这里展示如何完全自定义
    from wiki.pipeline import Filter
    from typing import Dict, Any

    class CustomPipeline:
        def __init__(self, config: WikiConfig):
            self.config = config
            self.filters: list[Filter] = [
                ClassificationFilter(config),
                ToolUseFilter(config),
                SelfCorrectionFilter(config)
            ]

        def process(self, content: str, source_path: str):
            data: Dict[str, Any] = {"content": content, "source_path": source_path}
            # 1. 先执行 Classification 和 ToolUse
            for filter in self.filters[:-1]:
                data = filter.process(data)
            # 2. 模拟处理
            data["structured_data"] = {
                "title": "测试标题（已通过 Pipeline）",
                "summary": f"处理后的内容（是否调用了工具: {data.get('tool_used', 'no')}）",
                "keywords": ["测试"],
                "key_points": ["要点"],
                "backlinks": [],
                "category": "技术类",
                "optimized_content": data.get("content", content)
            }
            # 3. 执行 Self-Correction
            data = self.filters[-1].process(data)
            return data

    pipeline_custom = CustomPipeline(config)
    result = pipeline_custom.process(
        "这是纯文本测试",
        "custom_test.md"
    )
    print(f"  - 纯文本: 是否调用工具? {result.get('tool_used', 'no')}")

    # 测试 URL 处理（注意：实际网络请求可能失败，仅展示架构）
    result_url = pipeline_custom.process(
        "看看这个：https://example.com",
        "url_test.md"
    )
    print(f"  - URL: 是否调用工具? {result_url.get('tool_used', 'no')}")
    print()

    print("=" * 70)
    print("架构说明:")
    print("  - 不采用完整 ReactAgent（太重了！）")
    print("  - 采用 Pipe & Filter + Classification + ToolUse + Self-Correction")
    print("  - ToolUse 是单轮，不做复杂循环")
    print("  - 适合个人笔记整理场景！")
    print("=" * 70)


if __name__ == "__main__":
    main()
