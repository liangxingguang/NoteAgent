"""
Telegram 命令处理器
处理 /start、/help 等命令
"""

import re
from typing import Dict, Callable, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass, field
from storage.log_manager import get_logger

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes

logger = get_logger("TgCommands")


@dataclass
class CommandContext:
    """命令上下文"""
    command: str = ""
    args: list = field(default_factory=list)
    user_id: str = ""
    chat_id: str = ""
    message_id: str = ""
    platform: Any = None
    update: Any = None
    context: Any = None


class CommandRegistry:
    """命令注册表"""

    def __init__(self):
        self.commands: Dict[str, Callable] = {}
        self.aliases: Dict[str, str] = {}
        self.help_texts: Dict[str, str] = {}

    def register(self, name: str, handler: Callable, help_text: str = "", aliases: Optional[list[str]] = None):
        """注册命令"""
        self.commands[name] = handler
        self.help_texts[name] = help_text
        if aliases:
            for alias in aliases:
                self.aliases[alias] = name

    def get_handler(self, name: str) -> Optional[Callable]:
        """获取命令处理器"""
        name_lower = name.lower()
        if name_lower in self.commands:
            return self.commands[name_lower]
        if name_lower in self.aliases:
            return self.commands[self.aliases[name_lower]]
        return None

    def get_help_text(self, name: str) -> str:
        """获取帮助文本"""
        name_lower = name.lower()
        if name_lower in self.help_texts:
            return self.help_texts[name_lower]
        if name_lower in self.aliases and self.aliases[name_lower] in self.help_texts:
            return self.help_texts[self.aliases[name_lower]]
        return ""

    def list_commands(self) -> list[str]:
        """列出所有命令"""
        return list(self.commands.keys())


def parse_command(text: str) -> tuple[Optional[str], list[str]]:
    """
    解析命令文本
    返回 (命令名, 参数列表)
    """
    if not text or not text.startswith('/'):
        return None, []

    parts = text[1:].strip().split(maxsplit=1)
    command = parts[0].lower() if parts else None
    args = parts[1].split() if len(parts) > 1 else []

    return command, args


def is_command_text(text: str) -> bool:
    """判断是否为命令文本"""
    return bool(text and text.strip().startswith('/'))


command_registry = CommandRegistry()


class CommandHandler:
    """Telegram 命令处理器"""

    def __init__(self, context: Any = None):
        self.context = context
        self.registry = command_registry

    async def handle_command(self, command: str, args: list[str], ctx: CommandContext) -> Optional[str]:
        """处理命令"""
        handler = self.registry.get_handler(command)
        if handler:
            try:
                return await handler(self, args, ctx)
            except Exception as e:
                logger.error(f"命令处理异常: /{command} - {e}", exc_info=True)
                return f"处理命令时发生错误: {str(e)}"
        else:
            return f"未知命令: /{command}\n输入 /help 获取帮助"


def get_command_handler() -> CommandHandler:
    """获取命令处理器实例"""
    return CommandHandler()


async def handle_start(handler: CommandHandler, args: list[str], ctx: CommandContext) -> str:
    """处理 /start 命令"""
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


async def handle_help(handler: CommandHandler, args: list[str], ctx: CommandContext) -> str:
    """处理 /help 命令"""
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


async def handle_ping(handler: CommandHandler, args: list[str], ctx: CommandContext) -> str:
    """处理 /ping 命令"""
    return "🏓 Pong!"


async def handle_about(handler: CommandHandler, args: list[str], ctx: CommandContext) -> str:
    """处理 /about 命令"""
    return """NoteAgents - AI 笔记自动收集系统
版本: 0.2.0
平台: Telegram
功能: 文本/链接/文件 AI 总结，自动保存到 Obsidian"""


command_registry.register(
    name="start",
    handler=handle_start,
    help_text="开始使用",
    aliases=["hello"]
)

command_registry.register(
    name="help",
    handler=handle_help,
    help_text="显示帮助信息",
    aliases=["?", "h"]
)

command_registry.register(
    name="ping",
    handler=handle_ping,
    help_text="测试在线状态"
)

command_registry.register(
    name="about",
    handler=handle_about,
    help_text="关于机器人"
)