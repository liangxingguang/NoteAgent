"""Phase 1 单元测试"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import WikiConfig
from wiki.path_utils import WikiPathManager


def normalize_path(path: str) -> str:
    """标准化路径，使用正斜杠"""
    return path.replace("\\", "/")


def test_wiki_directory_structure():
    """测试 Wiki 目录结构是否正确创建"""
    assert os.path.exists("wiki_data/")
    assert os.path.exists("wiki_data/raw/")
    assert os.path.exists("wiki_data/raw/auto/")
    assert os.path.exists("wiki_data/raw/manual/")
    assert os.path.exists("wiki_data/structured/")
    assert os.path.exists("wiki_data/structured/技术类/")
    assert os.path.exists("wiki_data/structured/想法类/")
    assert os.path.exists("wiki_data/structured/学习类/")
    assert os.path.exists("wiki_data/structured/日常类/")
    assert os.path.exists("wiki_data/wiki/")
    assert os.path.exists("wiki_data/wiki/entities/")
    assert os.path.exists("wiki_data/wiki/concepts/")
    assert os.path.exists("wiki_data/wiki/comparisons/")
    assert os.path.exists("wiki_data/wiki/queries/")
    assert os.path.exists("wiki_data/SCHEMA.md")
    assert os.path.exists("wiki_data/index.md")
    assert os.path.exists("wiki_data/log.md")
    print("[PASS] 目录结构测试通过")


def test_daily_archive_path():
    """测试按日归档路径生成"""
    manager = WikiPathManager("wiki_data/", "daily")

    path = manager.get_raw_auto_path(datetime(2026, 5, 3))
    assert normalize_path(path) == "raw/auto/2026/05/03/", f"期望 'raw/auto/2026/05/03/', 实际 '{path}'"

    path = manager.get_raw_manual_path(datetime(2026, 5, 15))
    assert normalize_path(path) == "raw/manual/2026/05/15/", f"期望 'raw/manual/2026/05/15/', 实际 '{path}'"

    full_path = manager.get_raw_auto_full_path(datetime(2026, 5, 3))
    assert normalize_path(full_path) == "wiki_data/raw/auto/2026/05/03/", f"期望 'wiki_data/raw/auto/2026/05/03/', 实际 '{full_path}'"

    print("[PASS] 按日归档路径测试通过")


def test_monthly_archive_path():
    """测试按月归档路径生成"""
    manager = WikiPathManager("wiki_data/", "monthly")

    path = manager.get_raw_auto_path(datetime(2026, 5, 3))
    assert normalize_path(path) == "raw/auto/2026/05/", f"期望 'raw/auto/2026/05/', 实际 '{path}'"

    path = manager.get_raw_manual_path(datetime(2026, 5, 15))
    assert normalize_path(path) == "raw/manual/2026/05/", f"期望 'raw/manual/2026/05/', 实际 '{path}'"

    full_path = manager.get_raw_auto_full_path(datetime(2026, 5, 3))
    assert normalize_path(full_path) == "wiki_data/raw/auto/2026/05/", f"期望 'wiki_data/raw/auto/2026/05/', 实际 '{full_path}'"

    print("[PASS] 按月归档路径测试通过")


def test_structured_path():
    """测试结构化内容路径"""
    manager = WikiPathManager("wiki_data/")

    path = manager.get_structured_path("技术类")
    assert normalize_path(path) == "structured/技术类/", f"期望 'structured/技术类/', 实际 '{path}'"

    full_path = manager.get_structured_full_path("想法类")
    assert normalize_path(full_path) == "wiki_data/structured/想法类/", f"期望 'wiki_data/structured/想法类/', 实际 '{full_path}'"

    print("[PASS] 结构化路径测试通过")


def test_wiki_path():
    """测试 Wiki 知识网络路径"""
    manager = WikiPathManager("wiki_data/")

    path = manager.get_wiki_path("entities")
    assert normalize_path(path) == "wiki/entities/", f"期望 'wiki/entities/', 实际 '{path}'"

    full_path = manager.get_wiki_full_path("concepts")
    assert normalize_path(full_path) == "wiki_data/wiki/concepts/", f"期望 'wiki_data/wiki/concepts/', 实际 '{full_path}'"

    print("[PASS] Wiki 路径测试通过")


def test_index_and_log_path():
    """测试索引和日志路径"""
    manager = WikiPathManager("wiki_data/")

    assert manager.get_index_path() == "index.md"
    assert normalize_path(manager.get_index_full_path()) == "wiki_data/index.md"
    assert manager.get_log_path() == "log.md"
    assert normalize_path(manager.get_log_full_path()) == "wiki_data/log.md"
    assert manager.get_schema_path() == "SCHEMA.md"
    assert normalize_path(manager.get_schema_full_path()) == "wiki_data/SCHEMA.md"

    print("[PASS] 索引和日志路径测试通过")


def test_wiki_config():
    """测试 Wiki 配置"""
    from config import Config
    config = Config().wiki

    assert config.enabled == False
    assert config.wiki_data_root == "wiki_data/"
    assert config.archive_strategy == "daily"
    assert config.llm_model == "qwen-turbo"
    assert config.auto_process == True
    assert config.file_monitor_enabled == True
    assert config.file_monitor_interval == 5

    print("[PASS] Wiki 配置测试通过")


def test_wiki_config_from_env():
    """测试从环境变量加载配置"""
    from config import Config, reload_config

    os.environ["WIKI_ENABLED"] = "true"
    os.environ["WIKI_DATA_ROOT"] = "my_wiki_data/"
    os.environ["WIKI_ARCHIVE_STRATEGY"] = "monthly"
    os.environ["WIKI_LLM_MODEL"] = "test-model"
    os.environ["AI_API_KEY"] = "test-key"  # 必须配置才能 pass validate
    os.environ["OBSIDIAN_VAULT_PATH"] = "test-path"

    config = reload_config()

    assert config.wiki.enabled == True
    assert config.wiki.wiki_data_root == "my_wiki_data/"
    assert config.wiki.archive_strategy == "monthly"
    assert config.wiki.llm_model == "test-model"

    del os.environ["WIKI_ENABLED"]
    del os.environ["WIKI_DATA_ROOT"]
    del os.environ["WIKI_ARCHIVE_STRATEGY"]
    del os.environ["WIKI_LLM_MODEL"]
    del os.environ["AI_API_KEY"]
    del os.environ["OBSIDIAN_VAULT_PATH"]

    print("[PASS] Wiki 配置环境变量测试通过")


def test_ensure_directory_exists():
    """测试目录创建"""
    manager = WikiPathManager("wiki_data/")

    test_path = "test_dir/subdir"
    full_path = manager.ensure_directory_exists(test_path)

    assert os.path.exists(full_path)
    assert normalize_path(full_path) == "wiki_data/test_dir/subdir"

    os.rmdir("wiki_data/test_dir/subdir")
    os.rmdir("wiki_data/test_dir")

    print("[PASS] 目录创建测试通过")


if __name__ == "__main__":
    print("=" * 50)
    print("Phase 1 单元测试")
    print("=" * 50)

    test_wiki_directory_structure()
    test_daily_archive_path()
    test_monthly_archive_path()
    test_structured_path()
    test_wiki_path()
    test_index_and_log_path()
    test_wiki_config()
    test_wiki_config_from_env()
    test_ensure_directory_exists()

    print("=" * 50)
    print("所有测试通过!")
    print("=" * 50)
