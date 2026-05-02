"""临时文件管理模块"""

import os
import shutil
import time
from typing import Optional
from datetime import datetime, timedelta

from .log_manager import get_logger


class TempManager:
    """临时文件管理器"""

    def __init__(self, temp_dir: str = "storage/temp_files"):
        """初始化临时文件管理器

        Args:
            temp_dir: 临时文件目录
        """
        self.temp_dir = temp_dir
        self.logger = get_logger("TempManager")

        # 确保临时目录存在
        os.makedirs(temp_dir, exist_ok=True)
        self.logger.info(f"临时文件目录: {os.path.abspath(temp_dir)}")

    def get_temp_path(self, filename: Optional[str] = None) -> str:
        """获取临时文件路径

        Args:
            filename: 文件名，如果不提供则生成一个唯一文件名

        Returns:
            完整的临时文件路径
        """
        if filename is None:
            # 生成唯一文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"temp_{timestamp}"

        return os.path.join(self.temp_dir, filename)

    def create_temp_dir(self, dir_name: Optional[str] = None) -> str:
        """创建临时目录

        Args:
            dir_name: 目录名，如果不提供则生成一个唯一目录名

        Returns:
            完整的临时目录路径
        """
        if dir_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            dir_name = f"temp_dir_{timestamp}"

        dir_path = os.path.join(self.temp_dir, dir_name)
        os.makedirs(dir_path, exist_ok=True)
        self.logger.debug(f"创建临时目录: {dir_path}")
        return dir_path

    def delete_file(self, filepath: str) -> bool:
        """删除临时文件

        Args:
            filepath: 文件路径

        Returns:
            是否删除成功
        """
        try:
            if os.path.exists(filepath):
                if os.path.isfile(filepath):
                    os.remove(filepath)
                    self.logger.debug(f"删除临时文件: {filepath}")
                    return True
                elif os.path.isdir(filepath):
                    shutil.rmtree(filepath)
                    self.logger.debug(f"删除临时目录: {filepath}")
                    return True
            return False
        except Exception as e:
            self.logger.error(f"删除文件失败 {filepath}: {e}", exc_info=True)
            return False

    def cleanup_expired(self, max_age_hours: int = 24):
        """清理过期临时文件

        Args:
            max_age_hours: 最大保留时间（小时）
        """
        self.logger.info(f"开始清理过期临时文件（保留{max_age_hours}小时）")

        now = time.time()
        max_age_seconds = max_age_hours * 3600

        deleted_count = 0
        freed_space = 0

        for filename in os.listdir(self.temp_dir):
            filepath = os.path.join(self.temp_dir, filename)

            try:
                # 获取文件修改时间
                file_mtime = os.path.getmtime(filepath)
                age_seconds = now - file_mtime

                if age_seconds > max_age_seconds:
                    # 获取文件大小
                    file_size = os.path.getsize(filepath)

                    if self.delete_file(filepath):
                        deleted_count += 1
                        freed_space += file_size
            except Exception as e:
                self.logger.warning(f"处理文件失败 {filename}: {e}")

        # 转换大小为MB
        freed_space_mb = freed_space / (1024 * 1024)
        self.logger.info(f"清理完成：删除{deleted_count}个文件，释放{freed_space_mb:.2f}MB空间")

    def cleanup_all(self):
        """清理所有临时文件"""
        self.logger.warning("清理所有临时文件")

        deleted_count = 0
        for filename in os.listdir(self.temp_dir):
            filepath = os.path.join(self.temp_dir, filename)
            if self.delete_file(filepath):
                deleted_count += 1

        self.logger.info(f"清理完成：删除{deleted_count}个文件")


# 全局临时文件管理器实例
_temp_manager: Optional[TempManager] = None


def init_temp_manager(temp_dir: str = "storage/temp_files") -> TempManager:
    """初始化临时文件管理器"""
    global _temp_manager
    _temp_manager = TempManager(temp_dir)
    return _temp_manager


def get_temp_manager() -> TempManager:
    """获取临时文件管理器实例"""
    if _temp_manager is None:
        raise RuntimeError("临时文件管理器未初始化，请先调用 init_temp_manager()")
    return _temp_manager
