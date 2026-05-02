"""异常处理模块 - 异常捕获、分类、自愈、反馈"""

from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Optional, Callable, Type, Tuple


class ExceptionCategory(Enum):
    """异常分类"""
    RECOVERABLE = "recoverable"  # 可恢复（如网络问题）
    UNRECOVERABLE = "unrecoverable"  # 不可恢复（如配置缺失）
    RETRY_EXHAUSTED = "retry_exhausted"  # 重试次数耗尽


@dataclass
class HandledException:
    """已处理的异常"""
    exception: Exception
    category: ExceptionCategory
    message: str
    should_retry: bool = False
    retry_count: int = 0
    max_retries: int = 3


class ExceptionHandler:
    """异常处理器"""

    def __init__(self):
        """初始化异常处理器"""
        from storage.log_manager import get_logger
        self.logger = get_logger("ExceptionHandler")

        # 可恢复的异常类型
        self.recoverable_exceptions: Tuple[Type[Exception], ...] = (
            # 网络相关
            ConnectionError,
            TimeoutError,
            # requests相关（如果导入的话）
        )

        # 尝试导入requests异常
        try:
            import requests.exceptions
            self.recoverable_exceptions += (
                requests.exceptions.RequestException,
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
            )
        except ImportError:
            pass

        # 异常统计
        self.exception_count: dict[str, int] = {}

    def categorize_exception(self, exc: Exception) -> ExceptionCategory:
        """对异常进行分类

        Args:
            exc: 异常对象

        Returns:
            异常分类
        """
        # 检查是否是可恢复的异常类型
        if isinstance(exc, self.recoverable_exceptions):
            return ExceptionCategory.RECOVERABLE

        # 检查异常消息中的关键词
        exc_msg = str(exc).lower()
        recoverable_keywords = [
            "timeout", "timed out", "connection", "network",
            "temporarily", "retry", "unavailable", "busy",
            "rate limit", "too many requests",
        ]

        for keyword in recoverable_keywords:
            if keyword in exc_msg:
                return ExceptionCategory.RECOVERABLE

        return ExceptionCategory.UNRECOVERABLE

    def handle_exception(
        self,
        exc: Exception,
        module: str = "Unknown",
        context: Optional[dict] = None,
    ) -> HandledException:
        """处理异常

        Args:
            exc: 异常对象
            module: 模块名称
            context: 上下文信息

        Returns:
            已处理的异常对象
        """
        # 分类
        category = self.categorize_exception(exc)

        # 记录异常
        exc_type = type(exc).__name__
        self.logger.error(
            f"[{module}] 捕获异常: {exc_type} - {exc}",
            exc_info=True,
        )

        # 统计
        self.exception_count[exc_type] = self.exception_count.get(exc_type, 0) + 1

        # 构建用户友好的消息
        user_message = self._build_user_message(exc, category)

        # 创建处理结果
        handled = HandledException(
            exception=exc,
            category=category,
            message=user_message,
            should_retry=(category == ExceptionCategory.RECOVERABLE),
        )

        # 记录上下文（如果有）
        if context:
            self.logger.debug(f"异常上下文: {context}")

        return handled

    def _build_user_message(self, exc: Exception, category: ExceptionCategory) -> str:
        """构建用户友好的异常消息

        Args:
            exc: 异常对象
            category: 异常分类

        Returns:
            用户消息
        """
        if category == ExceptionCategory.RECOVERABLE:
            return "遇到临时问题，正在尝试自动恢复..."

        # 通用错误消息
        return f"处理失败：{str(exc)}"

    def get_exception_stats(self) -> dict[str, int]:
        """获取异常统计

        Returns:
            异常统计字典
        """
        return self.exception_count.copy()

    def reset_stats(self):
        """重置统计"""
        self.exception_count.clear()


# 重试装饰器
def with_exception_handling(
    max_retries: int = 3,
    retry_delay: float = 1.0,
    backoff_factor: float = 2.0,
    module: str = "Unknown",
):
    """异常处理装饰器

    Args:
        max_retries: 最大重试次数
        retry_delay: 初始重试延迟（秒）
        backoff_factor: 退避因子
        module: 模块名称
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            handler = ExceptionHandler()
            import time

            last_exception = None
            current_delay = retry_delay

            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    handled = handler.handle_exception(e, module, kwargs)

                    if not handled.should_retry or attempt == max_retries:
                        break

                    handler.logger.warning(
                        f"第{attempt}次尝试失败，{current_delay:.1f}秒后重试..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff_factor

            # 重试耗尽
            handler.logger.error(f"重试次数已耗尽（{max_retries}次）")
            raise last_exception

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            handler = ExceptionHandler()
            import time

            last_exception = None
            current_delay = retry_delay

            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    handled = handler.handle_exception(e, module, kwargs)

                    if not handled.should_retry or attempt == max_retries:
                        break

                    handler.logger.warning(
                        f"第{attempt}次尝试失败，{current_delay:.1f}秒后重试..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff_factor

            # 重试耗尽
            handler.logger.error(f"重试次数已耗尽（{max_retries}次）")
            raise last_exception

        # 判断函数是否是异步的
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# 全局异常处理器实例
_exception_handler: Optional[ExceptionHandler] = None


def init_exception_handler() -> ExceptionHandler | None:
    """初始化异常处理器"""
    global _exception_handler
    _exception_handler = ExceptionHandler()
    return _exception_handler


def get_exception_handler(_exception_handler=None) -> ExceptionHandler:
    """获取异常处理器实例"""
    if _exception_handler is None:
        _exception_handler = ExceptionHandler()
    return _exception_handler
