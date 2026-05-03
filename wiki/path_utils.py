"""LLM Wiki 路径管理模块 - 支持按日归档和按月归档"""

import os
from datetime import datetime
from typing import Optional


class WikiPathManager:
    """Wiki 路径管理器

    负责生成和管理 Wiki 知识库的各种路径，支持按日归档和按月归档两种策略。

    按日归档示例: raw/auto/2026/05/03/note.md
    按月归档示例: raw/auto/2026/05/note.md
    """

    def __init__(self, vault_path: str = "wiki_data/", archive_strategy: str = "daily"):
        """初始化路径管理器

        Args:
            vault_path: Wiki 数据根目录路径（使用 OBSIDIAN_VAULT_PATH）
            archive_strategy: 归档策略，daily 或 monthly
        """
        self.vault_path = vault_path.rstrip("/")
        self.archive_strategy = archive_strategy
        if archive_strategy not in ("daily", "monthly"):
            raise ValueError("archive_strategy 必须是 'daily' 或 'monthly'")

    def _ensure_data_prefix(self, path: str) -> str:
        """确保路径以 vault_path 开头"""
        if path.startswith(self.vault_path):
            return path
        return os.path.join(self.vault_path, path)

    def _get_daily_path(self, prefix: str, date: Optional[datetime] = None) -> str:
        """按日归档路径: prefix/YYYY/MM/DD/

        Args:
            prefix: 路径前缀，如 'raw/auto'
            date: 日期，默认为当前时间

        Returns:
            按日归档的相对路径
        """
        if date is None:
            date = datetime.now()
        return f"{prefix}/{date.year}/{date.month:02d}/{date.day:02d}/"

    def _get_monthly_path(self, prefix: str, date: Optional[datetime] = None) -> str:
        """按月归档路径: prefix/YYYY/MM/

        Args:
            prefix: 路径前缀，如 'raw/auto'
            date: 日期，默认为当前时间

        Returns:
            按月归档的相对路径
        """
        if date is None:
            date = datetime.now()
        return f"{prefix}/{date.year}/{date.month:02d}/"

    def _get_archive_path(self, prefix: str, date: Optional[datetime] = None) -> str:
        """根据归档策略获取归档路径"""
        if self.archive_strategy == "daily":
            return self._get_daily_path(prefix, date)
        else:
            return self._get_monthly_path(prefix, date)

    def get_raw_auto_path(self, date: Optional[datetime] = None) -> str:
        """获取自动收集内容的归档路径

        Args:
            date: 日期，默认为当前时间

        Returns:
            自动收集内容的相对归档路径
        """
        return self._get_archive_path("raw/auto", date)

    def get_raw_manual_path(self, date: Optional[datetime] = None) -> str:
        """获取人工手写笔记的归档路径

        Args:
            date: 日期，默认为当前时间

        Returns:
            人工手写笔记的相对归档路径
        """
        return self._get_archive_path("raw/manual", date)

    def get_raw_auto_full_path(self, date: Optional[datetime] = None) -> str:
        """获取自动收集内容的完整路径（绝对路径）"""
        relative_path = self.get_raw_auto_path(date)
        return self._ensure_data_prefix(relative_path)

    def get_raw_manual_full_path(self, date: Optional[datetime] = None) -> str:
        """获取人工手写笔记的完整路径（绝对路径）"""
        relative_path = self.get_raw_manual_path(date)
        return self._ensure_data_prefix(relative_path)

    def get_raw_auto_processed_full_path(self, date: Optional[datetime] = None) -> str:
        """获取已处理的自动收集内容的完整路径（绝对路径）"""
        if date is None:
            date = datetime.now()
        relative_path = self._get_archive_path("raw/auto_processed", date)
        return os.path.join(self.vault_path, relative_path)

    def get_structured_path(self, category: str) -> str:
        """获取结构化内容的路径

        Args:
            category: 分类名称，如 '技术类'

        Returns:
            结构化内容的相对路径
        """
        return f"structured/{category}/"

    def get_structured_full_path(self, category: str) -> str:
        """获取结构化内容的完整路径（绝对路径）"""
        relative_path = self.get_structured_path(category)
        return self._ensure_data_prefix(relative_path)

    def get_wiki_path(self, wiki_type: str) -> str:
        """获取 Wiki 知识网络内容的路径

        Args:
            wiki_type: Wiki 类型，如 'entities', 'concepts', 'comparisons', 'queries'

        Returns:
            Wiki 内容的相对路径
        """
        return f"wiki/{wiki_type}/"

    def get_wiki_full_path(self, wiki_type: str) -> str:
        """获取 Wiki 知识网络内容的完整路径（绝对路径）"""
        relative_path = self.get_wiki_path(wiki_type)
        return self._ensure_data_prefix(relative_path)

    def get_index_path(self) -> str:
        """获取全局索引文件的路径"""
        return "index.md"

    def get_index_full_path(self) -> str:
        """获取全局索引文件的完整路径"""
        return os.path.join(self.vault_path, "index.md")

    def get_log_path(self) -> str:
        """获取操作日志文件的路径"""
        return "log.md"

    def get_log_full_path(self) -> str:
        """获取操作日志文件的完整路径"""
        return os.path.join(self.vault_path, "log.md")

    def get_schema_path(self) -> str:
        """获取规则定义文档的路径"""
        return "SCHEMA.md"

    def get_schema_full_path(self) -> str:
        """获取规则定义文档的完整路径"""
        return os.path.join(self.vault_path, "SCHEMA.md")

    def ensure_directory_exists(self, relative_path: str) -> str:
        """确保目录存在，如果不存在则创建

        Args:
            relative_path: 相对路径

        Returns:
            完整路径
        """
        full_path = self._ensure_data_prefix(relative_path)
        os.makedirs(full_path, exist_ok=True)
        return full_path

    def parse_date_from_path(self, path: str) -> Optional[datetime]:
        """从归档路径中解析日期

        Args:
            path: 归档路径，如 'raw/auto/2026/05/03/' 或 'raw/auto/2026/05/'

        Returns:
            日期对象，如果解析失败则返回 None
        """
        import re

        if self.archive_strategy == "daily":
            pattern = r"(\d{4})/(\d{2})/(\d{2})/"
        else:
            pattern = r"(\d{4})/(\d{2})/"

        match = re.search(pattern, path)
        if match:
            year, month, day = match.groups()
            if self.archive_strategy == "daily":
                return datetime(int(year), int(month), int(day))
            else:
                return datetime(int(year), int(month), 1)
        return None
