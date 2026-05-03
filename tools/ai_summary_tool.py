"""AI总结工具 - 提示词构造、第三方AI调用、结果验证"""

import re
from typing import Optional, Tuple

from config.config import get_config
from .model_adapter import (
    create_adapter,
    get_model_config,
)
from storage.log_manager import get_logger
from utils.text_utils import clean_text
from .web_tool import get_web_tool

logger = get_logger("AiSummaryTool")


def build_obsidian_note_prompt(content: str, title: Optional[str] = None) -> str:
    """构建Obsidian笔记生成提示词

    Args:
        content: 原始内容
        title: 可选的标题提示

    Returns:
        完整的提示词
    """
    prompt_parts = [
        "请根据以下内容生成一篇Obsidian格式的笔记。",
        "",
        "笔记要求：",
        "1. 生成一个简短清晰的标题（放在开头",
        "2. 提炼一个简短摘要（100-200字）",
        "3. 提取3-8个关键词（使用 #标签",
        "4. 结构化整理，保留重要内容的核心内容",
        "5. 使用适当的Markdown格式（标题、列表、引用等",
        "6. 保持客观准确，不要编造内容",
        "",
        "输出格式（严格遵循以下模板：",
        "---",
        "title: [笔记标题]",
        "tags: [关键词1,关键词2,关键词3]",
        "date: [当前日期]",
        "---",
        "",
        "## 摘要",
        "",
        "[摘要内容]",
        "",
        "## 正文",
        "",
        "[正文内容]",
        "",
        "---",
        "需要总结的内容：",
        "",
        content,
    ]

    return "\n".join(prompt_parts)


def build_simple_summary_prompt(content: str) -> str:
    """构建简化的总结提示词

    Args:
        content: 原始内容

    Returns:
        提示词
    """
    return f"""请将以下内容总结为一篇Obsidian格式的笔记：

{content}

请生成一个标题、摘要和整理后的正文内容。"""


async def call_ai_api(prompt: str, system_prompt: Optional[str] = None) -> Tuple[bool, str]:
    """调用AI API

    Args:
        prompt: 用户提示词
        system_prompt: 系统提示词（可选）

    Returns:
        (是否成功, AI响应或错误信息)
    """
    config = get_config()

    if not config.ai_api_key:
        return False, "未配置AI_API_KEY"

    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        model_config = get_model_config(
            model_name=config.ai_model,
            api_key=config.ai_api_key,
            base_url=config.ai_base_url,
        )
        model_config.temperature = config.ai_temperature
        model_config.max_tokens = config.ai_max_tokens
        model_config.system_prompt = system_prompt

        adapter = create_adapter(model_config)

        logger.info(f"调用AI API: {model_config.provider.value}/{model_config.model_name}")

        response = adapter.invoke(
            messages,
            temperature=config.ai_temperature,
            max_tokens=config.ai_max_tokens
        )

        logger.info(f"AI API调用成功 - 用时: {response.latency_ms}ms,  tokens: {response.usage.get('total_tokens', 0)}")
        return True, response.content

    except Exception as e:
        logger.error(f"AI API调用失败: {e}", exc_info=True)
        return False, f"AI调用失败: {str(e)}"


async def call_ai_api_stream(prompt: str, system_prompt: Optional[str] = None) -> Tuple[bool, str]:
    """流式调用AI API

    Args:
        prompt: 用户提示词
        system_prompt: 系统提示词（可选）

    Returns:
        (是否成功, AI响应或错误信息)
    """
    config = get_config()

    if not config.ai_api_key:
        return False, "未配置AI_API_KEY"

    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        model_config = get_model_config(
            model_name=config.ai_model,
            api_key=config.ai_api_key,
            base_url=config.ai_base_url,
        )
        model_config.temperature = config.ai_temperature
        model_config.max_tokens = config.ai_max_tokens
        model_config.system_prompt = system_prompt

        adapter = create_adapter(model_config)

        logger.info(f"流式调用AI API: {model_config.provider.value}/{model_config.model_name}")

        result = await adapter.astream_invoke(
            messages,
            temperature=config.ai_temperature,
            max_tokens=config.ai_max_tokens
        )

        logger.info("AI API流式调用成功")
        return True, result

    except Exception as e:
        logger.error(f"AI API流式调用失败: {e}", exc_info=True)
        return False, f"AI调用失败: {str(e)}"


async def generate_obsidian_note(content: str, title_hint: Optional[str] = None, use_stream: bool = False) -> Tuple[bool, str]:
    """生成Obsidian笔记

    Args:
        content: 原始内容
        title_hint: 标题提示
        use_stream: 是否使用流式调用

    Returns:
        (是否成功, 生成的笔记或错误信息)
    """
    logger.info(f"开始生成Obsidian笔记，内容长度: {len(content)}字符")

    prompt = build_obsidian_note_prompt(content, title_hint)

    if use_stream:
        success, result = await call_ai_api_stream(prompt)
    else:
        success, result = await call_ai_api(prompt)

    if not success:
        return False, result

    result = clean_text(result)

    is_valid, validated = validate_note_result(result)

    if not is_valid:
        logger.warning(f"笔记格式验证失败，但仍然使用该结果")

    logger.info("Obsidian笔记生成成功")
    return True, result


async def summarize_webpage(url: str, use_stream: bool = False) -> Tuple[bool, str]:
    """下载网页内容并生成摘要

    Args:
        url: 网页URL
        use_stream: 是否使用流式调用

    Returns:
        (是否成功, 生成的笔记或错误信息)
    """
    logger.info(f"开始处理网页内容: {url}")

    web_tool = get_web_tool(timeout=30)
    success, content = await web_tool.download_and_convert(url)

    if not success:
        logger.error(f"下载网页内容失败: {content}")
        return False, f"下载网页失败: {content}"

    logger.info(f"网页内容下载成功，内容长度: {len(content)}字符")

    content = clean_text(content)

    content = truncate_content(content, max_chars=5000)

    success, result = await generate_obsidian_note(
        content=content,
        title_hint=None,
        use_stream=use_stream
    )

    if not success:
        return False, result

    return True, result


async def download_webpage_markdown(url: str) -> Tuple[bool, str]:
    """下载网页内容并保存为Markdown文件

    Args:
        url: 网页URL

    Returns:
        (是否成功, Markdown内容或错误信息)
    """
    logger.info(f"开始下载网页内容: {url}")

    web_tool = get_web_tool(timeout=30)
    success, content = await web_tool.download_and_convert(url)

    if not success:
        logger.error(f"下载网页内容失败: {content}")
        return False, f"下载网页失败: {content}"

    logger.info(f"网页Markdown转换成功，内容长度: {len(content)}字符")
    return True, content


def is_url(text: str) -> bool:
    """检查文本是否为URL

    Args:
        text: 待检查的文本

    Returns:
        是否为URL
    """
    url_pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return bool(url_pattern.match(text.strip()))


def truncate_content(content: str, max_chars: int = 5000) -> str:
    """截断内容

    Args:
        content: 原始内容
        max_chars: 最大字符数

    Returns:
        截断后的内容
    """
    if len(content) <= max_chars:
        return content

    return content[:max_chars] + "\n\n[内容已截断...]"


def validate_note_result(content: str) -> Tuple[bool, str]:
    """验证笔记结果

    Args:
        content: 生成的笔记内容

    Returns:
        (是否有效, 处理后的内容)
    """
    if not content or len(content.strip()) < 10:
        return False, content

    has_title = "#" in content[:100]
    has_frontmatter = "---" in content[:100]

    if not has_title and not has_frontmatter:
        content = "---\ntitle: 笔记\ndate: 2024-01-01\n---\n\n## 内容\n\n" + content

    return True, content
