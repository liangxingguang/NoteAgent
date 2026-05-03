"""Obsidian入库工具 - 目录验证、笔记写入、存储记录"""

import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple

from config.config import get_config
from storage.log_manager import get_logger
from utils.file_utils import ensure_dir_exists, check_dir_writable, get_text_hash
from utils.text_utils import generate_timestamp
from wiki.path_utils import WikiPathManager


logger = get_logger("ObsidianTool")


@dataclass
class NoteInfo:
    """笔记信息"""
    filename: str
    filepath: str
    title: Optional[str] = None
    content_hash: str = ""
    created_at: datetime = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


def extract_title_from_content(content: str) -> Optional[str]:
    """从笔记内容中提取标题

    Args:
        content: 笔记内容

    Returns:
        标题文本
    """
    # 尝试从Frontmatter中提取
    frontmatter_match = re.search(r"^title:\s*(.+)$", content, re.MULTILINE)
    if frontmatter_match:
        return frontmatter_match.group(1).strip()

    # 尝试从第一个Markdown标题提取
    h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if h1_match:
        return h1_match.group(1).strip()

    # 尝试从第一行提取
    first_line = content.strip().split("\n")[0].strip()
    if first_line and len(first_line) < 100:
        return first_line

    return None


def sanitize_filename(title: str, max_length: int = 50) -> str:
    """清理文件名，移除非法字符

    Args:
        title: 原始标题
        max_length: 最大长度

    Returns:
        清理后的文件名
    """
    # 移除非法字符
    title = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "", title)

    # 替换空格
    title = re.sub(r"\s+", "_", title)

    # 截断
    if len(title) > max_length:
        title = title[:max_length]

    return title.strip("_")


def generate_filename(content: str, title: Optional[str] = None) -> str:
    """生成唯一的文件名

    Args:
        content: 笔记内容
        title: 可选的标题

    Returns:
        文件名
    """
    # 获取内容哈希
    content_hash = get_text_hash(content)[:8]

    # 生成时间戳
    timestamp = generate_timestamp("%Y%m%d_%H%M%S")

    # 使用标题或默认前缀
    if title:
        clean_title = sanitize_filename(title)
        return f"{clean_title}_{timestamp}_{content_hash}.md"
    else:
        return f"TG_Note_{timestamp}_{content_hash}.md"


def write_note_to_file(
    content: str,
    filename: Optional[str] = None,
    title: Optional[str] = None,
) -> Tuple[bool, NoteInfo]:
    """写入笔记到Obsidian

    Args:
        content: 笔记内容
        filename: 可选的文件名
        title: 可选的标题

    Returns:
        (是否成功, 笔记信息)
    """
    config = get_config()

    if not config.obsidian_vault_path:
        return False, NoteInfo(filename="", filepath="", error="未配置Obsidian知识库路径")

    vault_dir = config.obsidian_vault_path
    archive_strategy = config.wiki.archive_strategy if config.wiki else "daily"
    wiki_path_manager = WikiPathManager(vault_path=vault_dir, archive_strategy=archive_strategy)
    raw_dir = os.path.join(vault_dir, wiki_path_manager.get_raw_auto_path())

    # 确保目录存在
    if not ensure_dir_exists(raw_dir):
        return False, NoteInfo(filename="", filepath="", error="无法创建Obsidian目录")

    # 检查目录可写
    is_writable, writable_msg = check_dir_writable(vault_dir)
    if not is_writable:
        return False, NoteInfo(filename="", filepath="", error=f"Obsidian目录不可写: {writable_msg}")

    # 提取标题（如果没有提供）
    if not title:
        title = extract_title_from_content(content)

    # 生成文件名
    if not filename:
        filename = generate_filename(content, title)

    # 确保文件名以.md结尾
    if not filename.endswith(".md"):
        filename += ".md"

    filepath = os.path.join(raw_dir, filename)

    # 写入文件
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        # 构建笔记信息
        note_info = NoteInfo(
            filename=filename,
            filepath=filepath,
            title=title,
            content_hash=get_text_hash(content),
        )

        logger.info(f"笔记写入成功: {filepath}")

        # 自动触发 LLM Wiki 结构化处理
        config = get_config()
        if config.wiki and config.wiki.enabled:
            try:
                from tools import get_wiki_tool
                logger.info("自动触发 LLM Wiki 结构化处理...")
                wiki = get_wiki_tool()
                wiki_result = wiki.workflow.process_file(filepath)
                if wiki_result:
                    logger.info(f"LLM Wiki 处理成功: {wiki_result}")
                    wiki.update_index()
                    if config.wiki.auto_import_wiki:
                        wiki.import_knowledge()
                else:
                    logger.warning(f"LLM Wiki 处理失败")
            except Exception as e:
                logger.error(f"LLM Wiki 处理异常: {e}", exc_info=True)

        return True, note_info

    except Exception as e:
        logger.error(f"笔记写入失败: {e}", exc_info=True)
        return False, NoteInfo(filename=filename, filepath=filepath, error=str(e))


def ensure_frontmatter(content: str, title: Optional[str] = None) -> str:
    """确保笔记有Frontmatter

    Args:
        content: 原始内容
        title: 标题

    Returns:
        包含Frontmatter的内容
    """
    # 检查是否已有Frontmatter
    if content.startswith("---\n"):
        # 已有Frontmatter
        return content

    # 提取标题
    if not title:
        title = extract_title_from_content(content) or "笔记"

    # 生成日期
    date_str = datetime.now().strftime("%Y-%m-%d")

    # 构建Frontmatter
    frontmatter = f"""---
title: {title}
date: {date_str}
source: Telegram
---

"""

    return frontmatter + content


def append_source_info(content: str, source_info: str) -> str:
    """添加来源信息到笔记末尾

    Args:
        content: 笔记内容
        source_info: 来源信息

    Returns:
        更新后的内容
    """
    # 检查是否已有来源信息
    source_marker = "---\n\n*来源:"
    if source_marker in content:
        return content

    # 添加来源信息
    source_section = f"\n\n---\n\n*来源: {source_info}*\n"

    return content + source_section
