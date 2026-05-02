"""
飞书增强功能测试
测试富文本、命令处理、群聊
"""

import pytest
import json

from platforms.feishu_rich_text import (
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
from platforms.feishu_commands import (
    CommandRegistry,
    CommandContext,
    CommandHandler,
    parse_command,
    is_command_text,
    get_command_handler,
)


class TestRichTextBuilder:
    """测试富文本构建器"""

    def test_basic_text(self):
        """测试基本文本"""
        builder = RichTextBuilder(title="测试")
        builder.add_text("Hello World")
        result = builder.build()
        assert "Hello World" in result

    def test_styled_text(self):
        """测试带样式的文本"""
        builder = RichTextBuilder()
        builder.add_text("Bold", bold=True)
        builder.add_text("Italic", italic=True)
        result = builder.build()
        assert "bold" in result or "italic" in result

    def test_link(self):
        """测试链接元素"""
        builder = RichTextBuilder()
        builder.add_link("OpenAI", "https://openai.com")
        result = builder.build()
        assert "openai.com" in result

    def test_multi_line(self):
        """测试多行文本"""
        builder = RichTextBuilder()
        builder.add_text("Line 1").new_line()
        builder.add_text("Line 2").new_line()
        builder.add_text("Line 3")
        result = builder.build()
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result

    def test_welcome_rich_text(self):
        """测试欢迎消息"""
        result = build_welcome_rich_text()
        assert result is not None
        assert len(result) > 0

    def test_help_rich_text(self):
        """测试帮助消息"""
        result = build_help_rich_text()
        assert result is not None
        assert len(result) > 0

    def test_success_rich_text(self):
        """测试成功消息"""
        result = build_success_rich_text("note_2024.md")
        assert result is not None
        assert "2024.md" in result

    def test_error_rich_text(self):
        """测试错误消息"""
        result = build_error_rich_text("Something went wrong")
        assert result is not None
        assert "wrong" in result.lower()

    def test_plain_text(self):
        """测试纯文本"""
        result = build_plain_text("This is text")
        data = json.loads(result)
        assert data["text"] == "This is text"


class TestCommandHandling:
    """测试命令处理"""

    def test_is_command_text(self):
        """测试命令识别"""
        assert is_command_text("/start") is True
        assert is_command_text("/help") is True
        assert is_command_text("Hello") is False
        assert is_command_text(" /start") is False
        assert is_command_text("") is False

    def test_parse_command(self):
        """测试命令解析"""
        cmd, args = parse_command("/start")
        assert cmd == "start"
        assert args == []

        cmd, args = parse_command("/help")
        assert cmd == "help"
        assert args == []

        cmd, args = parse_command("/command arg1 arg2")
        assert cmd == "command"
        assert args == ["arg1", "arg2"]

    def test_parse_no_command(self):
        """测试非命令文本"""
        cmd, args = parse_command("hello world")
        assert cmd is None

    def test_command_registry(self):
        """测试命令注册"""
        registry = CommandRegistry()

        # 注册一个测试命令
        def dummy_handler(handler, args, ctx):
            return "Hello!"

        registry.register(
            name="test",
            handler=dummy_handler,
            help_text="测试命令",
            aliases=["t"]
        )

        assert registry.get_handler("test") is dummy_handler
        assert registry.get_handler("t") is dummy_handler
        assert registry.get_help_text("test") == "测试命令"

    def test_list_commands(self):
        """测试列出命令"""
        registry = CommandRegistry()
        registry.register(name="cmd1", handler=lambda *args: "", help_text="")
        registry.register(name="cmd2", handler=lambda *args: "", help_text="")

        commands = registry.list_commands()
        assert "cmd1" in commands
        assert "cmd2" in commands

    @pytest.mark.asyncio
    async def test_builtin_commands(self):
        """测试内置命令"""
        handler = get_command_handler()
        ctx = CommandContext(
            command="ping",
            args=[],
            user_id="test_user",
            chat_id="test_chat",
            message_id="msg123",
            platform=None,
        )

        # 测试 ping
        # 注意：实际命令处理需要 asyncio
        result = await handler.handle_command("ping", [], ctx)
        # 应该返回 "Pong! 🏓"
        assert result is not None


class TestCommandAliases:
    """测试命令别名"""

    def test_alias_lookup(self):
        """测试命令别名"""
        registry = CommandRegistry()
        registry.register("start", lambda *args: "", "开始", ["hello", "hi"])
        registry.register("help", lambda *args: "", "帮助", ["?"])

        # 通过别名查找应该返回原命令的 handler
        assert registry.get_handler("hello") is not None
        assert registry.get_handler("?") is not None
