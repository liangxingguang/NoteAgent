"""Telegram消息工具"""

from dataclasses import dataclass
from typing import Optional, Tuple

from telegram import Update, File
from telegram.ext import ContextTypes

from storage.log_manager import get_logger
from storage.temp_manager import get_temp_manager


logger = get_logger("TgTool")


@dataclass
class MessageInfo:
    """消息信息"""
    message_id: int
    chat_id: int
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    text: Optional[str] = None
    is_file: bool = False
    file_id: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None  # "document", "photo", etc.


def extract_message_info(update: Update) -> Optional[MessageInfo]:
    """从Update中提取消息信息

    Args:
        update: Telegram Update对象

    Returns:
        消息信息对象
    """
    try:
        # 获取消息对象
        message = update.effective_message
        if not message:
            return None

        user = update.effective_user
        chat = update.effective_chat

        if not user or not chat:
            return None

        info = MessageInfo(
            message_id=message.message_id,
            chat_id=chat.id,
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
        )

        # 检查是否有文本
        if message.text:
            info.text = message.text
            logger.debug(f"收到文本消息: {user.id} - {message.text[:50]}...")

        # 检查是否有文件（文档）
        elif message.document:
            doc = message.document
            info.is_file = True
            info.file_type = "document"
            info.file_id = doc.file_id
            info.file_name = doc.file_name
            info.file_size = doc.file_size
            logger.debug(f"收到文件消息: {user.id} - {doc.file_name} ({doc.file_size}字节)")

        # 检查是否有照片
        elif message.photo:
            # 获取最大的照片
            photo = message.photo[-1]
            info.is_file = True
            info.file_type = "photo"
            info.file_id = photo.file_id
            info.file_size = photo.file_size
            info.file_name = f"photo_{photo.file_id[:8]}.jpg"
            logger.debug(f"收到照片消息: {user.id}")

        # 其他类型
        else:
            logger.debug(f"收到其他类型消息: {user.id} - {message}")

        return info

    except Exception as e:
        logger.error(f"提取消息信息失败: {e}", exc_info=True)
        return None


async def send_message(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    text: str,
    parse_mode: Optional[str] = None,
    disable_web_page_preview: bool = True,
) -> bool:
    """发送文本消息

    Args:
        context: 上下文
        chat_id: 聊天ID
        text: 消息内容
        parse_mode: 解析模式（Markdown, HTML）
        disable_web_page_preview: 是否禁用网页预览

    Returns:
        是否发送成功
    """
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview,
        )
        logger.debug(f"消息发送成功: {chat_id}")
        return True
    except Exception as e:
        logger.error(f"消息发送失败: {chat_id} - {e}", exc_info=True)
        return False


async def download_file(
    context: ContextTypes.DEFAULT_TYPE,
    file_id: str,
    file_name: Optional[str] = None,
) -> Tuple[bool, Optional[str], Optional[int]]:
    """下载文件

    Args:
        context: 上下文
        file_id: 文件ID
        file_name: 文件名（可选，不提供则自动生成）

    Returns:
        (是否成功, 文件路径, 文件大小)
    """
    try:
        # 获取文件对象
        file_obj: File = await context.bot.get_file(file_id)

        # 生成文件名
        if not file_name:
            # 从file_path中提取扩展名
            if file_obj.file_path:
                ext = file_obj.file_path.split(".")[-1]
                file_name = f"download_{file_id[:8]}.{ext}"
            else:
                file_name = f"download_{file_id[:8]}"

        # 获取临时文件路径
        temp_manager = get_temp_manager()
        filepath = temp_manager.get_temp_path(file_name)

        # 下载文件
        await file_obj.download_to_drive(filepath)

        # 获取文件大小
        import os
        file_size = os.path.getsize(filepath)

        logger.info(f"文件下载成功: {file_name} -> {filepath} ({file_size}字节)")
        return True, filepath, file_size

    except Exception as e:
        logger.error(f"文件下载失败: {file_id} - {e}", exc_info=True)
        return False, None, None


def build_welcome_message() -> str:
    """构建欢迎消息

    Returns:
        欢迎消息文本
    """
    return """👋 欢迎使用 NoteAgents！

我可以帮你：
• 📝 发送文本或链接，自动生成笔记
• 📄 发送PDF/DOCX/TXT文件，自动提取内容并生成笔记
• 💾 笔记自动保存到你的Obsidian知识库

使用方法：
1. 直接发送文本或链接给我
2. 上传PDF/DOCX/TXT文件
3. 等待处理结果

提示：只有授权用户才能使用哦！"""


def build_help_message() -> str:
    """构建帮助消息

    Returns:
        帮助消息文本
    """
    return """📖 使用帮助

支持的内容：
• 文本消息 - 直接输入即可
• 链接 - 自动识别和发送
• PDF文档 - .pdf格式文件
• Word文档 - .docx格式文件
• 文本文件 - .txt格式文件

文件限制：
• 单个文件不超过50MB
• 提取的文本内容超过5000字会自动截断

处理流程：
1. 接收内容
2. AI分析和总结
3. 生成Obsidian格式笔记
4. 自动保存到知识库
5. 返回处理结果

如有问题，请查看日志或联系管理员。"""


def build_processing_message() -> str:
    """构建处理中消息

    Returns:
        处理中消息文本
    """
    return "⏳ 正在处理中，请稍候..."


def build_success_message(filename: str, note_title: Optional[str] = None) -> str:
    """构建成功消息

    Args:
        filename: 文件名
        note_title: 笔记标题（可选）

    Returns:
        成功消息文本
    """
    if note_title:
        return f"""✅ 处理成功！

📝 笔记标题：{note_title}
💾 保存文件：{filename}

笔记已保存到你的Obsidian知识库！"""
    else:
        return f"""✅ 处理成功！

💾 保存文件：{filename}

笔记已保存到你的Obsidian知识库！"""


def build_error_message(error: str) -> str:
    """构建错误消息

    Args:
        error: 错误信息

    Returns:
        错误消息文本
    """
    return f"""❌ 处理失败！

错误信息：{error}

请稍后重试或联系管理员。"""


def build_permission_denied_message(user_id: int) -> str:
    """构建权限拒绝消息

    Args:
        user_id: 用户ID

    Returns:
        权限拒绝消息文本
    """
    return f"""⚠️ 权限不足！

抱歉，你的用户ID ({user_id}) 不在授权列表中。

如需使用，请联系管理员添加你的用户ID到授权列表。"""
