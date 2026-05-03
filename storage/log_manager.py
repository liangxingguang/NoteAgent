"""日志管理模块"""

import logging
import os
from logging.handlers import TimedRotatingFileHandler
from typing import Optional


class LogManager:
    """日志管理器"""

    _instance: Optional["LogManager"] = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, log_dir: str = "storage/logs", log_level: str = "INFO"):
        """初始化日志管理器

        Args:
            log_dir: 日志目录
            log_level: 日志级别
        """
        if LogManager._initialized:
            return

        self.log_dir = log_dir
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)

        # 确保日志目录存在
        os.makedirs(log_dir, exist_ok=True)

        # 配置根日志器
        self._setup_logger()

        LogManager._initialized = True

    def _setup_logger(self):
        """配置日志器"""
        logger = logging.getLogger()
        logger.setLevel(self.log_level)
        logger.handlers.clear()  # 清除已有handler

        # 日志格式（包含文件名和行号）
        log_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # 控制台handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(log_format)
        logger.addHandler(console_handler)

        # 文件handler - 按日期滚动
        log_file = os.path.join(self.log_dir, "noteagents.log")
        file_handler = TimedRotatingFileHandler(
            log_file,
            when="midnight",  # 每天午夜滚动
            interval=1,
            backupCount=30,  # 保留30天日志
            encoding="utf-8"
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(log_format)
        file_handler.suffix = "%Y-%m-%d"  # 日志文件后缀
        logger.addHandler(file_handler)

        logger.info("=" * 50)
        logger.info("NoteAgents 日志系统初始化完成")
        logger.info(f"日志级别: {logging.getLevelName(self.log_level)}")
        logger.info("=" * 50)

    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志器

        Args:
            name: 日志器名称

        Returns:
            日志器实例
        """
        return logging.getLogger(name)

    def debug(self, module: str, message: str):
        """记录DEBUG级别日志"""
        self.get_logger(module).debug(message)

    def info(self, module: str, message: str):
        """记录INFO级别日志"""
        self.get_logger(module).info(message)

    def warning(self, module: str, message: str):
        """记录WARNING级别日志"""
        self.get_logger(module).warning(message)

    def error(self, module: str, message: str, exc_info: bool = False):
        """记录ERROR级别日志

        Args:
            module: 模块名称
            message: 日志消息
            exc_info: 是否记录异常堆栈
        """
        self.get_logger(module).error(message, exc_info=exc_info)

    def critical(self, module: str, message: str, exc_info: bool = False):
        """记录CRITICAL级别日志"""
        self.get_logger(module).critical(message, exc_info=exc_info)


# 全局日志管理器实例
_log_manager: Optional[LogManager] = None


def init_log_manager(log_dir: str = "storage/logs", log_level: str = "INFO") -> LogManager | None:
    """初始化日志管理器"""
    global _log_manager
    _log_manager = LogManager(log_dir, log_level)
    return _log_manager


def get_log_manager() -> LogManager:
    """获取日志管理器实例"""
    if _log_manager is None:
        raise RuntimeError("日志管理器未初始化，请先调用 init_log_manager()")
    return _log_manager


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志器（快捷方法）"""
    try:
        return get_log_manager().get_logger(name)
    except RuntimeError:
        # 如果日志管理器未初始化，返回一个基础日志器
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
