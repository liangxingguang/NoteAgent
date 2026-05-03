"""文件监控模块"""

import os
import time
import threading
import logging
from typing import Callable, Dict, Any
from datetime import datetime

from config import WikiConfig
from wiki.path_utils import WikiPathManager
from wiki.pipeline import NotePipeline
from wiki.saver import NoteSaver
from wiki.index import IndexManager

logger = logging.getLogger(__name__)


class FileWatcher:
    """文件监控类"""

    def __init__(
        self,
        path_manager: WikiPathManager,
        config: WikiConfig,
        on_new_file: Callable[[str], None] = None,
        poll_interval: float = 5.0
    ):
        self.path_manager = path_manager
        self.config = config
        self.on_new_file = on_new_file
        self.poll_interval = poll_interval
        self._running = False
        self._thread = None
        self._file_cache: Dict[str, float] = {}  # 记录文件上次修改时间

    def start(self, daemon: bool = True):
        """启动监控"""
        if self._running:
            return
        self._running = True
        self._scan_initial_files()
        self._thread = threading.Thread(target=self._watch_loop, daemon=daemon)
        self._thread.start()

    def stop(self):
        """停止监控"""
        self._running = False
        if self._thread:
            self._thread.join()

    def _scan_initial_files(self):
        """扫描初始文件，建立缓存（只扫描手动目录）"""
        manual_dir = self.path_manager.get_raw_manual_full_path()
        if os.path.exists(manual_dir):
            self._scan_directory(manual_dir)

    def _scan_directory(self, dir_path: str):
        """递归扫描目录下的所有 .md 文件"""
        try:
            for entry in os.scandir(dir_path):
                if entry.is_file() and entry.name.endswith(".md"):
                    file_path = entry.path
                    mtime = os.path.getmtime(file_path)
                    self._file_cache[file_path] = mtime
                elif entry.is_dir():
                    self._scan_directory(entry.path)
        except PermissionError:
            pass

    def _watch_loop(self):
        """监控循环"""
        while self._running:
            self._check_files()
            time.sleep(self.poll_interval)

    def _check_files(self):
        """检查文件变更（只检查手动目录）"""
        manual_dir = self.path_manager.get_raw_manual_full_path()
        if os.path.exists(manual_dir):
            for file_name in os.listdir(manual_dir):
                if file_name.endswith(".md"):
                    file_path = os.path.join(manual_dir, file_name)
                    mtime = os.path.getmtime(file_path)
                    if file_path not in self._file_cache:
                        self._file_cache[file_path] = mtime
                        self._on_file_created(file_path)
                    elif mtime > self._file_cache[file_path]:
                        self._file_cache[file_path] = mtime
                        self._on_file_modified(file_path)

    def _on_file_created(self, file_path: str):
        """处理新文件"""
        logger.info(f"新文件: {file_path}")
        if self.on_new_file:
            self.on_new_file(file_path)

    def _on_file_modified(self, file_path: str):
        """处理文件修改"""
        logger.info(f"文件修改: {file_path}")
        if self.on_new_file:
            self.on_new_file(file_path)


class WikiWorkflow:
    """Wiki 完整工作流"""

    def __init__(self, config: WikiConfig):
        self.config = config
        self.path_manager = WikiPathManager(config.vault_path)
        self.pipeline = NotePipeline(config)
        self.saver = NoteSaver(self.path_manager)
        self.index_manager = IndexManager(self.path_manager)

    def process_file(self, file_path: str):
        """处理单个文件"""
        logger.info(f"处理文件: {file_path}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            auto_dir = self.path_manager.get_raw_auto_full_path()
            source_type = "auto" if auto_dir in file_path else "manual"
            note = self.pipeline.process(content, file_path, source_type)
            saved_path = self.saver.save_structured_note(note)
            logger.info(f"已保存: {saved_path}")
            if source_type == "auto":
                processed_dir = self.path_manager.get_raw_auto_processed_full_path()
                self.path_manager.ensure_directory_exists(processed_dir)
                import shutil
                processed_path = os.path.join(processed_dir, os.path.basename(file_path))
                shutil.move(file_path, processed_path)
                logger.info(f"已移动原始文件到: {processed_path}")
            self.index_manager.update_index()
            logger.info("索引已更新")
            return saved_path
        except Exception as e:
            logger.error(f"处理失败: {e}")
            return None

    def create_file_watcher(self, poll_interval: float = 5.0) -> FileWatcher:
        """创建文件监控"""
        return FileWatcher(
            path_manager=self.path_manager,
            config=self.config,
            on_new_file=self.process_file,
            poll_interval=poll_interval
        )
