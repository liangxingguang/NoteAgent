"""
飞书命令处理器
处理 /start、/help 等命令
"""

import re
from typing import Dict, Callable, Optional, Any
from dataclasses import dataclass
from storage.log_manager import get_logger


logger = get_logger("FeishuCommands")


@dataclass
class CommandContext:
    """命令上下文"""
    command: str
    args: list[str]
    user_id: str
    chat_id: str
    message_id: str
    platform: Any


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
        if name in self.commands:
            return self.commands[name]
        if name in self.aliases:
            return self.commands[self.aliases[name]]
        return None

    def get_help_text(self, name: str) -> str:
        """获取帮助文本"""
        if name in self.help_texts:
            return self.help_texts[name]
        if name in self.aliases and self.aliases[name] in self.help_texts:
            return self.help_texts[self.aliases[name]]
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

    # 移除开头的 / 并分割
    parts = text[1:].strip().split(maxsplit=1)
    command = parts[0].lower() if parts else None
    args = parts[1].split() if len(parts) > 1 else []

    return command, args


def is_command_text(text: str) -> bool:
    """判断是否为命令文本"""
    return text.strip().startswith('/')


# 创建全局命令注册表
command_registry = CommandRegistry()


class CommandHandler:
    """飞书命令处理器"""

    def __init__(self, context: Any = None):
        self.context = context
        self.registry = command_registry

    async def handle_command(self, command: str, args: list[str], ctx: CommandContext) -> Optional[str]:
        """
        处理命令
        返回响应文本
        """
        handler = self.registry.get_handler(command)
        if handler:
            try:
                return await handler(self, args, ctx)
            except Exception as e:
                logger.error(f"命令处理异常: /{command} - {e}", exc_info=True)
                return f"处理命令时发生错误: {str(e)}"
        else:
            # 未知命令
            return f"未知命令: /{command}\n输入 /help 获取帮助"


# 内置命令实现
async def handle_start(handler: CommandHandler, args: list[str], ctx: CommandContext) -> str:
    """处理 /start 命令"""
    from platforms.feishu_rich_text import build_welcome_rich_text
    # 注意：这里返回特殊标记表示使用富文本
    return "__RICH_TEXT_WELCOME__"


async def handle_help(handler: CommandHandler, args: list[str], ctx: CommandContext) -> str:
    """处理 /help 命令"""
    from platforms.feishu_rich_text import build_help_rich_text
    # 注意：这里返回特殊标记表示使用富文本
    return "__RICH_TEXT_HELP__"


async def handle_ping(handler: CommandHandler, args: list[str], ctx: CommandContext) -> str:
    """处理 /ping 命令"""
    return "Pong! 🏓"


async def handle_about(handler: CommandHandler, args: list[str], ctx: CommandContext) -> str:
    """处理 /about 命令"""
    return """NoteAgents - AI 笔记自动收集系统
版本: 0.2.0
平台: 飞书
功能: 文本/链接/文件 AI 总结，自动保存到 Obsidian"""


# 注册内置命令
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
    aliases=["?"]
)

command_registry.register(
    name="ping",
    handler=handle_ping,
    help_text="检查服务是否在线",
    aliases=["p"]
)

command_registry.register(
    name="about",
    handler=handle_about,
    help_text="关于本机器人",
    aliases=["info"]
)


def get_command_handler() -> CommandHandler:
    """获取命令处理器实例"""
    return CommandHandler()
