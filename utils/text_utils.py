"""文本处理工具"""

import hashlib
import re
from datetime import datetime

from storage.log_manager import get_logger

logger = get_logger("TextUtils")


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """截断文本

    Args:
        text: 原文本
        max_length: 最大长度
        suffix: 截断后缀

    Returns:
        截断后的文本
    """
    if text is None:
        return ""
    
    if len(text) <= max_length:
        return text

    # 保留前面的文本
    truncated = text[:max_length - len(suffix)] + suffix
    logger.debug(f"文本截断: {len(text)} -> {len(truncated)}")
    return truncated


def clean_text(text: str) -> str:
    """清洗文本

    - 去除多余空白字符
    - 去除不可见字符

    Args:
        text: 原文本

    Returns:
        清洗后的文本
    """
    # 去除不可见字符（保留换行）
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # 去除行尾空格
    lines = text.split("\n")
    lines = [line.rstrip() for line in lines]
    text = "\n".join(lines)

    # 去除连续空行（最多保留2个）
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def generate_timestamp(format_str: str = "%Y%m%d_%H%M%S") -> str:
    """生成时间戳字符串

    Args:
        format_str: 格式字符串

    Returns:
        时间戳字符串
    """
    return datetime.now().strftime(format_str)


def generate_unique_filename(prefix: str = "note", extension: str = "md") -> str:
    """生成唯一文件名

    Args:
        prefix: 文件名前缀
        extension: 文件扩展名（不含点）

    Returns:
        唯一文件名
    """
    timestamp = generate_timestamp("%Y%m%d_%H%M%S")
    # 添加随机数避免冲突
    import random
    random_suffix = random.randint(1000, 9999)
    return f"{prefix}_{timestamp}_{random_suffix}.{extension}"


def get_content_hash(content: str) -> str:
    """计算内容哈希值

    Args:
        content: 文本内容

    Returns:
        MD5哈希值
    """
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def extract_keywords(text: str, max_count: int = 10) -> list[str]:
    """简单提取关键词（基于词频）

    Args:
        text: 文本内容
        max_count: 最大关键词数量

    Returns:
        关键词列表
    """
    # 简单实现：按空格分割，统计词频
    # 实际项目可以使用jieba等中文分词库

    # 去除标点
    text = re.sub(r"[^\w\s]", " ", text)

    # 分词
    words = text.lower().split()

    # 过滤停用词
    stopwords = {
        "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
        "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "shall", "can", "need", "dare",
        "and", "or", "but", "if", "because", "as", "until", "while", "of",
        "at", "by", "for", "with", "about", "against", "between", "into",
        "through", "during", "before", "after", "above", "below", "to", "from",
    }

    # 统计词频
    word_count: dict[str, int] = {}
    for word in words:
        if len(word) >= 2 and word not in stopwords:
            word_count[word] = word_count.get(word, 0) + 1

    # 排序
    sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)

    # 返回前N个
    keywords = [word for word, count in sorted_words[:max_count]]
    return keywords


def escape_markdown(text: str) -> str:
    """转义Markdown特殊字符

    Args:
        text: 原文本

    Returns:
        转义后的文本
    """
    special_chars = r"\\`*_{}[]()#+-.!"
    for char in special_chars:
        text = text.replace(char, "\\" + char)
    return text


def extract_urls(text: str) -> list[str]:
    """提取文本中的URL

    Args:
        text: 文本内容

    Returns:
        URL列表
    """
    url_pattern = r"https?://[^\s]+"
    urls = re.findall(url_pattern, text)
    # 去除末尾可能的标点
    cleaned_urls = []
    for url in urls:
        url = url.rstrip(".,;!?)>]}'\"")
        cleaned_urls.append(url)
    return cleaned_urls
