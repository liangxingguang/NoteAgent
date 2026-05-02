"""API调用工具"""

import asyncio
import time
from functools import wraps
from typing import Any, Optional, Dict, Callable, Type, Tuple

import requests

from storage.log_manager import get_logger

logger = get_logger("ApiUtils")


class APIError(Exception):
    """API错误"""
    pass


class APIRetryableError(APIError):
    """可重试的API错误"""
    pass


def retry(
    max_attempts: int = 3,
    delay_seconds: float = 1.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (
        requests.exceptions.RequestException,
        APIRetryableError,
    ),
):
    """重试装饰器

    Args:
        max_attempts: 最大尝试次数
        delay_seconds: 初始延迟时间（秒）
        backoff_factor: 退避因子
        retryable_exceptions: 可重试的异常类型
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay_seconds

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(
                            f"API调用失败（已重试{max_attempts}次）: {e}"
                        )
                        break

                    logger.warning(
                        f"API调用失败（第{attempt}次）: {e}，"
                        f"{current_delay:.1f}秒后重试..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff_factor

            raise last_exception

        return wrapper
    return decorator


@retry(max_attempts=3, delay_seconds=1.0)
def send_post_request(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    json: Optional[Dict[str, Any]] = None,
    data: Optional[Any] = None,
    timeout: int = 30,
    verify_ssl: bool = True,
) -> requests.Response:
    """发送POST请求

    Args:
        url: URL
        headers: 请求头
        json: JSON数据
        data: 表单数据
        timeout: 超时时间（秒）
        verify_ssl: 是否验证SSL证书

    Returns:
        Response对象

    Raises:
        requests.exceptions.RequestException: 请求失败
    """
    logger.debug(f"POST请求: {url}")

    response = requests.post(
        url,
        headers=headers,
        json=json,
        data=data,
        timeout=timeout,
        verify=verify_ssl,
    )

    # 检查响应状态
    response.raise_for_status()

    return response


@retry(max_attempts=3, delay_seconds=1.0)
def send_get_request(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
    verify_ssl: bool = True,
) -> requests.Response:
    """发送GET请求

    Args:
        url: URL
        headers: 请求头
        params: 查询参数
        timeout: 超时时间（秒）
        verify_ssl: 是否验证SSL证书

    Returns:
        Response对象

    Raises:
        requests.exceptions.RequestException: 请求失败
    """
    logger.debug(f"GET请求: {url}")

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=timeout,
        verify=verify_ssl,
    )

    response.raise_for_status()

    return response


@retry(max_attempts=3, delay_seconds=1.0)
def download_file(
    url: str,
    filepath: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 60,
    chunk_size: int = 8192,
) -> int:
    """下载文件

    Args:
        url: 文件URL
        filepath: 保存路径
        headers: 请求头
        timeout: 超时时间（秒）
        chunk_size: 块大小

    Returns:
        下载的文件大小（字节）

    Raises:
        requests.exceptions.RequestException: 请求失败
    """
    logger.info(f"下载文件: {url} -> {filepath}")

    response = requests.get(
        url,
        headers=headers,
        timeout=timeout,
        stream=True,
    )
    response.raise_for_status()

    total_size = 0
    with open(filepath, "wb") as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                total_size += len(chunk)

    logger.info(f"文件下载完成: {filepath}，大小: {total_size}字节")
    return total_size


def parse_json_response(response: requests.Response) -> Dict[str, Any]:
    """解析JSON响应

    Args:
        response: Response对象

    Returns:
        JSON数据

    Raises:
        APIError: 解析失败
    """
    try:
        return response.json()
    except ValueError as e:
        logger.error(f"解析JSON响应失败: {e}")
        logger.debug(f"响应内容: {response.text[:200]}")
        raise APIError(f"JSON解析失败: {e}")


def safe_get(
    data: Dict[str, Any],
    key: str,
    default: Any = None,
    type_converter: Optional[Callable[[Any], Any]] = None,
) -> Any:
    """安全获取字典值

    Args:
        data: 字典数据
        key: 键，支持点号分隔的嵌套键，如 "a.b.c"，也支持列表索引如 "list.0"
        default: 默认值
        type_converter: 类型转换函数

    Returns:
        值
    """
    try:
        keys = key.split(".")
        value = data
        for k in keys:
            # 尝试将键转换为整数（用于列表索引）
            try:
                k_idx = int(k)
                value = value[k_idx]
            except (ValueError, TypeError):
                # 如果转换失败或不是列表，使用字符串键
                value = value[k]

        if type_converter is not None and value is not None:
            value = type_converter(value)

        return value
    except (KeyError, TypeError, IndexError):
        return default


def mask_secret(text: str, show_prefix: int = 4, show_suffix: int = 4) -> str:
    """脱敏敏感信息

    Args:
        text: 原文本
        show_prefix: 显示前缀长度
        show_suffix: 显示后缀长度

    Returns:
        脱敏后的文本
    """
    if not text or len(text) <= show_prefix + show_suffix:
        return "***"

    prefix = text[:show_prefix]
    suffix = text[-show_suffix:] if show_suffix > 0 else ""
    return f"{prefix}****{suffix}"


# === Async versions ===

async def async_send_post_request(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    json: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
) -> Dict[str, Any]:
    """异步发送POST请求

    Args:
        url: URL
        headers: 请求头
        json: JSON数据
        timeout: 超时时间（秒）

    Returns:
        响应JSON

    Raises:
        Exception: 请求失败
    """
    import aiohttp
    
    logger.debug(f"Async POST请求: {url}")

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url,
            headers=headers,
            json=json,
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as response:
            response.raise_for_status()
            return await response.json()


async def async_send_post_request_with_retry(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    json: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
    max_retries: int = 3,
    retry_delay: float = 1.0,
) -> Dict[str, Any]:
    """异步发送POST请求（带重试）

    Args:
        url: URL
        headers: 请求头
        json: JSON数据
        timeout: 超时时间（秒）
        max_retries: 最大重试次数
        retry_delay: 重试延迟（秒）

    Returns:
        响应JSON

    Raises:
        Exception: 请求失败
    """
    import aiohttp
    
    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            return await async_send_post_request(url, headers, json, timeout)
        except Exception as e:
            last_exception = e
            if attempt == max_retries:
                logger.error(f"API调用失败（已重试{max_retries}次）: {e}")
                break

            logger.warning(
                f"API调用失败（第{attempt}次）: {e}，{retry_delay:.1f}秒后重试..."
            )
            await asyncio.sleep(retry_delay)

    raise last_exception
