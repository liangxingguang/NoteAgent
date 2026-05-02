"""文件操作工具"""

import hashlib
import os

from storage.log_manager import get_logger

logger = get_logger("FileUtils")

# 支持的文件格式
SUPPORTED_EXTENSIONS = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
}


def get_file_extension(filename: str) -> str:
    """获取文件扩展名（小写）

    Args:
        filename: 文件名

    Returns:
        扩展名（不含点）
    """
    return os.path.splitext(filename)[1].lower().lstrip(".")


def is_supported_file(filename: str) -> bool:
    """检查文件格式是否支持

    Args:
        filename: 文件名

    Returns:
        是否支持
    """
    ext = get_file_extension(filename)
    return ext in SUPPORTED_EXTENSIONS


def check_file_size(file_size: int, max_size: int) -> tuple[bool, str]:
    """检查文件大小

    Args:
        file_size: 文件大小（字节）
        max_size: 最大大小（字节）

    Returns:
        (是否通过, 错误信息)
    """
    if file_size > max_size:
        size_mb = file_size / (1024 * 1024)
        max_mb = max_size / (1024 * 1024)
        return False, f"文件过大: {size_mb:.2f}MB，最大支持{max_mb:.2f}MB"
    return True, ""


def get_file_hash(filepath: str) -> str:
    """计算文件MD5哈希值

    Args:
        filepath: 文件路径

    Returns:
        MD5哈希值
    """
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"计算文件哈希失败 {filepath}: {e}", exc_info=True)
        # 如果失败，返回基于时间的哈希
        import time
        return hashlib.md5(str(time.time()).encode()).hexdigest()


def get_text_hash(text: str) -> str:
    """计算文本MD5哈希值

    Args:
        text: 文本内容

    Returns:
        MD5哈希值
    """
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def ensure_dir_exists(dirpath: str) -> bool:
    """确保目录存在，不存在则创建

    Args:
        dirpath: 目录路径

    Returns:
        是否成功
    """
    try:
        os.makedirs(dirpath, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"创建目录失败 {dirpath}: {e}", exc_info=True)
        return False


def check_dir_writable(dirpath: str) -> tuple[bool, str]:
    """检查目录是否可写

    Args:
        dirpath: 目录路径

    Returns:
        (是否可写, 错误信息)
    """
    if not os.path.exists(dirpath):
        return False, f"目录不存在: {dirpath}"

    if not os.path.isdir(dirpath):
        return False, f"不是目录: {dirpath}"

    # 尝试创建临时文件
    try:
        test_file = os.path.join(dirpath, ".write_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        return True, ""
    except Exception as e:
        return False, f"目录不可写: {e}"


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小

    Args:
        size_bytes: 文件大小（字节）

    Returns:
        格式化后的大小字符串
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f}TB"
