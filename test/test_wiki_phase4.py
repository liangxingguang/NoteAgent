"""Phase 4: 文件监控 测试用例"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import WikiConfig
from wiki import (
    WikiPathManager,
    FileWatcher,
    WikiWorkflow
)


def test_file_watcher():
    """测试 FileWatcher"""
    print("=" * 70)
    print("测试 FileWatcher")
    print("=" * 70)

    config = WikiConfig()
    path_manager = WikiPathManager("wiki_data/")

    # 创建测试文件
    test_content = """# 测试文件
这是一个用于测试文件监控的内容。
"""
    manual_dir = path_manager.get_raw_manual_full_path()
    path_manager.ensure_directory_exists(manual_dir)
    test_file = os.path.join(manual_dir, "watcher_test.md")

    # 监控回调
    processed_files = []
    def on_new_file(file_path):
        print(f"检测到文件变更: {file_path}")
        processed_files.append(file_path)

    watcher = FileWatcher(
        path_manager=path_manager,
        config=config,
        on_new_file=on_new_file,
        poll_interval=1.0
    )
    watcher.start(daemon=True)

    try:
        # 第一次写入
        print("写入新文件...")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)
        time.sleep(2)
        assert len(processed_files) == 1

        # 第二次写入（修改）
        print("修改文件...")
        with open(test_file, "a", encoding="utf-8") as f:
            f.write("\n新增内容")
        time.sleep(2)
        assert len(processed_files) == 2

        print("[PASS] FileWatcher 测试通过！")
    finally:
        watcher.stop()
        if os.path.exists(test_file):
            os.remove(test_file)
    print()


def test_wiki_workflow():
    """测试 WikiWorkflow：完整工作流"""
    print("=" * 70)
    print("测试 WikiWorkflow 完整工作流")
    print("=" * 70)

    config = WikiConfig()
    workflow = WikiWorkflow(config)

    # 创建测试文件
    test_content = """# 测试 WikiWorkflow
今天学习了 Python 的列表推导式，非常好用！
关键词：Python, 学习, 列表
"""
    test_file = os.path.join(
        workflow.path_manager.get_raw_manual_full_path(),
        "workflow_test.md"
    )
    workflow.path_manager.ensure_directory_exists(os.path.dirname(test_file))
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(test_content)

    try:
        saved_path = workflow.process_file(test_file)
        assert saved_path is not None
        assert os.path.exists(saved_path)
        print(f"[PASS] WikiWorkflow 处理成功！")
        print(f"保存路径: {saved_path}")

        # 验证索引已更新
        index_path = os.path.join(workflow.path_manager.wiki_data_root, "index.md")
        assert os.path.exists(index_path)
        print(f"[PASS] 索引已更新！")
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


if __name__ == "__main__":
    test_file_watcher()
    test_wiki_workflow()
    print("=" * 70)
    print("所有 Phase 4 测试通过！")
    print("=" * 70)
