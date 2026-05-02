"""临时文件清理工具 - 即时清理、定时清理"""

import os
from typing import Optional, List

from storage.log_manager import get_logger
from storage.temp_manager import get_temp_manager
from config.config import get_config


logger = get_logger("TempCleanTool")


def cleanup_file(filepath: str) -> bool:
    """删除单个临时文件

    Args:
        filepath: 文件路径

    Returns:
        是否成功
    """
    try:
        if not os.path.exists(filepath):
            logger.debug(f"文件不存在，无需删除: {filepath}")
            return True

        if os.path.isfile(filepath):
            os.remove(filepath)
            logger.info(f"删除临时文件: {filepath}")
            return True

        if os.path.isdir(filepath):
            import shutil
            shutil.rmtree(filepath)
            logger.info(f"删除临时目录: {filepath}")
            return True

        return False

    except Exception as e:
        logger.error(f"删除文件失败: {filepath} - {e}", exc_info=True)
        return False


def cleanup_files(filepaths: List[str]) -> int:
    """删除多个临时文件

    Args:
        filepaths: 文件路径列表

    Returns:
        成功删除的数量
    """
    success_count = 0
    for filepath in filepaths:
        if cleanup_file(filepath):
            success_count += 1
    return success_count


def cleanup_expired_temp_files(max_age_hours: Optional[int] = None) -> int:
    """清理过期的临时文件

    Args:
        max_age_hours: 最大保留时间（小时），如果不提供则使用配置

    Returns:
        删除的文件数量
    """
    config = get_config()

    if max_age_hours is None:
        max_age_hours = 24  # 默认24小时

    temp_manager = get_temp_manager()
    temp_dir = temp_manager.temp_dir

    if not os.path.exists(temp_dir):
        return 0

    logger.info(f"开始清理过期临时文件（保留{max_age_hours}小时）: {temp_dir}")

    import time
    now = time.time()
    max_age_seconds = max_age_hours * 3600

    deleted_count = 0

    try:
        for filename in os.listdir(temp_dir):
            filepath = os.path.join(temp_dir, filename)

            try:
                # 获取文件修改时间
                file_mtime = os.path.getmtime(filepath)
                age_seconds = now - file_mtime

                if age_seconds > max_age_seconds:
                    if cleanup_file(filepath):
                        deleted_count += 1

            except Exception as e:
                logger.warning(f"处理文件失败: {filename} - {e}")

    except Exception as e:
        logger.error(f"清理临时文件失败: {e}", exc_info=True)

    logger.info(f"清理完成: 删除{deleted_count}个文件")
    return deleted_count


def cleanup_all_temp_files() -> int:
    """清理所有临时文件

    Returns:
        删除的文件数量
    """
    temp_manager = get_temp_manager()
    temp_dir = temp_manager.temp_dir

    if not os.path.exists(temp_dir):
        return 0

    logger.warning(f"清理所有临时文件: {temp_dir}")

    deleted_count = 0

    try:
        for filename in os.listdir(temp_dir):
            filepath = os.path.join(temp_dir, filename)
            if cleanup_file(filepath):
                deleted_count += 1

    except Exception as e:
        logger.error(f"清理临时文件失败: {e}", exc_info=True)

    return deleted_count
