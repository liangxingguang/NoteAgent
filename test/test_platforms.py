"""
平台模块单元测试
"""

import pytest
import asyncio
import json
from datetime import datetime
from typing import Tuple

from platforms.platform_types import (
    PlatformType,
    ContentType,
    FileInfo,
    UnifiedMessage,
    PlatformConfig,
    FeishuPlatformConfig,
)
from platforms.base import PlatformAdapter
from platforms.manager import PlatformManager, PlatformStatus
from platforms.coordinator import MessageCoordinator


class TestPlatformTypes:
    """测试平台类型定义"""

    def test_platform_type_enum(self):
        """测试平台类型枚举"""
        assert PlatformType.TELEGRAM.value == "telegram"
        assert PlatformType.FEISHU.value == "feishu"
        assert PlatformType.UNKNOWN.value == "unknown"

    def test_content_type_enum(self):
        """测试内容类型枚举"""
        assert ContentType.TEXT.value == "text"
        assert ContentType.FILE.value == "file"
        assert ContentType.IMAGE.value == "image"

    def test_file_info(self):
        """测试文件信息"""
        file_info = FileInfo(
            file_id="test123",
            file_name="test.pdf",
            file_size=1024,
            mime_type="application/pdf",
        )
        assert file_info.file_id == "test123"
        assert file_info.file_name == "test.pdf"
        assert file_info.file_size == 1024
        assert file_info.file_extension == "pdf"  # 自动推断

    def test_file_info_no_extension(self):
        """测试无扩展名文件名"""
        file_info = FileInfo(
            file_id="test456",
            file_name="README",
            file_size=2048,
        )
        assert file_info.file_extension is None

    def test_unified_message(self):
        """测试统一消息"""
        msg = UnifiedMessage(
            platform=PlatformType.FEISHU,
            message_id="msg123",
            chat_id="chat456",
            user_id="user789",
            user_name="测试用户",
            content_type=ContentType.TEXT,
            text="这是一条测试消息",
        )
        assert msg.platform == PlatformType.FEISHU
        assert msg.is_text() is True
        assert msg.is_file() is False
        assert msg.is_command() is False

    def test_unified_message_file(self):
        """测试文件类型统一消息"""
        file_info = FileInfo(file_id="f1", file_name="test.docx", file_size=5000)
        msg = UnifiedMessage(
            platform=PlatformType.FEISHU,
            message_id="msg456",
            chat_id="chat789",
            user_id="user001",
            content_type=ContentType.FILE,
            file_info=file_info,
        )
        assert msg.is_file() is True

    def test_platform_config(self):
        """测试平台配置"""
        config = PlatformConfig(
            enabled=True,
            allowed_user_ids=["user1", "user2"]
        )
        assert config.enabled is True
        assert config.is_allowed("user1") is True
        assert config.is_allowed("user3") is False
        # 未配置允许用户时默认允许所有
        config2 = PlatformConfig(enabled=True)
        assert config2.is_allowed("anyuser") is True

    def test_feishu_platform_config(self):
        """测试飞书平台配置"""
        config = FeishuPlatformConfig(
            enabled=True,
            app_id="cli_123",
            app_secret="secret456",
            bot_name="NoteAgents",
            allowed_user_ids=["ou_123", "ou_456"],
        )
        assert config.enabled is True
        assert config.app_id == "cli_123"
        assert config.bot_name == "NoteAgents"
        assert config.is_allowed("ou_123") is True
        assert config.is_allowed("ou_789") is False


class MockPlatformAdapter(PlatformAdapter):
    """模拟平台适配器用于测试"""

    def __init__(self, config: PlatformConfig):
        super().__init__(config)
        self.platform_type = PlatformType.UNKNOWN
        self.sent_messages = []
        self.downloaded_files = []
        self._running = False

    async def initialize(self) -> bool:
        return True

    async def start_listening(self):
        self._running = True

    async def stop_listening(self):
        self._running = False

    async def send_message(self, chat_id: str, text: str, **kwargs) -> bool:
        self.sent_messages.append((chat_id, text))
        return True

    async def download_file(self, file_id: str, dest_path: str) -> Tuple[bool, int]:
        self.downloaded_files.append((file_id, dest_path))
        return True, 1024


class MockPlatformManager(PlatformManager):
    """模拟平台管理器"""

    def __init__(self):
        super().__init__()
        self.processed_messages = []


class TestPlatformManager:
    """测试平台管理器"""

    @pytest.fixture
    def manager(self):
        """创建平台管理器"""
        return PlatformManager()

    @pytest.fixture
    def mock_config(self):
        """创建模拟配置"""
        return PlatformConfig(enabled=True)

    @pytest.fixture
    def mock_adapter(self, mock_config):
        """创建模拟适配器"""
        adapter = MockPlatformAdapter(mock_config)
        adapter.platform_type = PlatformType.TELEGRAM
        return adapter

    def test_register_adapter(self, manager, mock_adapter):
        """测试注册适配器"""
        manager.register_adapter(PlatformType.TELEGRAM, mock_adapter)
        assert manager.get_adapter(PlatformType.TELEGRAM) is mock_adapter

    def test_add_message_handler(self, manager):
        """测试添加消息处理器"""
        handler_called = []

        def handler(msg):
            handler_called.append(msg)

        manager.add_message_handler(handler)
        assert len(manager._message_handlers) == 1

    def test_remove_message_handler(self, manager):
        """测试移除消息处理器"""
        handler_called = []

        def handler(msg):
            handler_called.append(msg)

        manager.add_message_handler(handler)
        manager.remove_message_handler(handler)
        assert len(manager._message_handlers) == 0

    @pytest.mark.asyncio
    async def test_initialize_all(self, manager, mock_adapter):
        """测试初始化所有平台"""
        manager.register_adapter(PlatformType.TELEGRAM, mock_adapter)
        success = await manager.initialize_all()
        assert success is True

    @pytest.mark.asyncio
    async def test_platform_status(self, manager, mock_adapter, mock_config):
        """测试平台状态"""
        manager.register_adapter(PlatformType.TELEGRAM, mock_adapter)
        status_list = manager.get_status()
        assert len(status_list) == 1
        assert status_list[0].platform == PlatformType.TELEGRAM
        assert status_list[0].enabled == mock_config.enabled

    @pytest.mark.asyncio
    async def test_get_enabled_platforms(self, manager, mock_adapter):
        """测试获取已启用平台"""
        manager.register_adapter(PlatformType.TELEGRAM, mock_adapter)
        enabled = manager.get_enabled_platforms()
        assert len(enabled) == 1
        assert enabled[0] == PlatformType.TELEGRAM


class TestFeishuAdapter:
    """测试飞书适配器（基础功能）"""

    @pytest.fixture
    def feishu_config(self):
        """测试飞书配置"""
        return FeishuPlatformConfig(
            enabled=True,
            app_id="cli_test",
            app_secret="secret_test",
            allowed_user_ids=["ou_test1", "ou_test2"],
        )

    def test_feishu_adapter_creation(self, feishu_config):
        """测试飞书适配器创建"""
        from platforms.feishu_adapter import FeishuAdapter
        adapter = FeishuAdapter(feishu_config)
        assert adapter.platform_type == PlatformType.FEISHU
        assert adapter.config.enabled is True

    def test_check_permission(self, feishu_config):
        """测试权限检查"""
        from platforms.feishu_adapter import FeishuAdapter
        adapter = FeishuAdapter(feishu_config)
        assert adapter.check_permission("ou_test1") is True
        assert adapter.check_permission("ou_unknown") is False

    def test_is_url_detection(self, feishu_config):
        """测试URL检测"""
        from platforms.feishu_adapter import FeishuAdapter
        adapter = FeishuAdapter(feishu_config)
        assert adapter._is_url("https://example.com") is True
        assert adapter._is_url("http://test.org") is True
        assert adapter._is_url("plain text") is False


class TestFeishuMessageConversion:
    """测试飞书消息转换"""

    @pytest.fixture
    def feishu_config(self):
        return FeishuPlatformConfig(enabled=True, app_id="cli_test", app_secret="secret")

    def test_convert_text_message(self, feishu_config):
        """测试文本消息转换"""
        from platforms.feishu_adapter import FeishuAdapter
        adapter = FeishuAdapter(feishu_config)

        feishu_event = {
            "header": {"event_type": "im.message.receive_v1"},
            "event": {
                "message": {
                    "message_id": "msg_123",
                    "chat_id": "chat_123",
                    "msg_type": "text",
                    "body": {"content": json.dumps({"text": "Hello world"})},
                },
                "sender": {
                    "sender_id": {"open_id": "ou_123", "name": "TestUser"}
                },
            },
        }

        unified_msg = adapter.convert_webhook_event(feishu_event)
        assert unified_msg is not None
        assert unified_msg.platform == PlatformType.FEISHU
        assert unified_msg.content_type == ContentType.TEXT
        assert unified_msg.text == "Hello world"
        assert unified_msg.user_id == "ou_123"

    def test_convert_file_message(self, feishu_config):
        """测试文件消息转换"""
        from platforms.feishu_adapter import FeishuAdapter
        adapter = FeishuAdapter(feishu_config)

        feishu_event = {
            "header": {"event_type": "im.message.receive_v1"},
            "event": {
                "message": {
                    "message_id": "msg_456",
                    "chat_id": "chat_456",
                    "msg_type": "file",
                    "body": {"content": json.dumps({
                        "file_key": "file_789",
                        "file_name": "test.pdf",
                        "file_size": 10240,
                    })},
                },
                "sender": {
                    "sender_id": {"open_id": "ou_456", "name": "FileUser"}
                },
            },
        }

        unified_msg = adapter.convert_webhook_event(feishu_event)
        assert unified_msg is not None
        assert unified_msg.platform == PlatformType.FEISHU
        assert unified_msg.content_type == ContentType.FILE
        assert unified_msg.file_info is not None
        assert unified_msg.file_info.file_id == "file_789"
        assert unified_msg.file_info.file_name == "test.pdf"
