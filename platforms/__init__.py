"""
多平台支持模块
支持 Telegram、飞书等多个消息平台
"""

from .platform_types import (
    PlatformType,
    ContentType,
    FileInfo,
    UnifiedMessage,
    PlatformConfig,
    FeishuPlatformConfig,
    TelegramPlatformConfig,
)
from .base import PlatformAdapter
from .manager import PlatformManager, PlatformStatus
from .feishu_adapter import FeishuAdapter
from .telegram_adapter import TelegramAdapter
from .feishu_webhook import FeishuWebhookServer, create_webhook_server
from .feishu_rich_text import (
    RichTextBuilder,
    TextElement,
    LinkElement,
    AtElement,
    ImageElement,
    build_welcome_rich_text,
    build_help_rich_text,
    build_success_rich_text,
    build_error_rich_text,
    build_plain_text,
)
from .feishu_commands import (
    CommandRegistry as FeishuCommandRegistry,
    CommandContext as FeishuCommandContext,
    CommandHandler as FeishuCommandHandler,
    get_command_handler as get_feishu_command_handler,
    parse_command as parse_feishu_command,
    is_command_text as is_feishu_command_text,
)
from .tg_commands import (
    CommandRegistry,
    CommandContext,
    CommandHandler,
    get_command_handler,
    parse_command,
    is_command_text,
    command_registry,
)
from .coordinator import MessageCoordinator, setup_platform_manager

__all__ = [
    # 平台类型
    "PlatformType",
    "ContentType",
    "FileInfo",
    "UnifiedMessage",
    "PlatformConfig",
    "FeishuPlatformConfig",
    "TelegramPlatformConfig",
    # 适配器
    "PlatformAdapter",
    "FeishuAdapter",
    "TelegramAdapter",
    # 平台管理
    "PlatformManager",
    "PlatformStatus",
    "MessageCoordinator",
    "setup_platform_manager",
    # Webhook
    "FeishuWebhookServer",
    "create_webhook_server",
    # 富文本
    "RichTextBuilder",
    "TextElement",
    "LinkElement",
    "AtElement",
    "ImageElement",
    "build_welcome_rich_text",
    "build_help_rich_text",
    "build_success_rich_text",
    "build_error_rich_text",
    "build_plain_text",
    # 命令 (Telegram)
    "CommandRegistry",
    "CommandContext",
    "CommandHandler",
    "get_command_handler",
    "parse_command",
    "is_command_text",
    "command_registry",
    # 命令 (Feishu - 别名)
    "FeishuCommandRegistry",
    "FeishuCommandContext",
    "FeishuCommandHandler",
    "get_feishu_command_handler",
    "parse_feishu_command",
    "is_feishu_command_text",
]
