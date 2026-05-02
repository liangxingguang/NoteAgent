"""
飞书 Webhook 模式测试
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

from platforms import FeishuWebhookServer, FeishuAdapter, FeishuPlatformConfig
from platforms.platform_types import ContentType


class TestFeishuWebhookServer:
    """测试飞书 Webhook 服务器"""

    @pytest.fixture
    def callback(self):
        """测试回调函数"""
        received_events = []

        def mock_callback(event):
            received_events.append(event)

        return mock_callback, received_events

    @pytest.fixture
    def webhook_server(self, callback):
        """创建 Webhook 服务器实例"""
        mock_callback, _ = callback
        return FeishuWebhookServer(
            verification_token="test_token",
            encrypt_key="",
            message_callback=mock_callback,
        )

    def test_server_initialization(self, webhook_server):
        """测试服务器初始化"""
        assert webhook_server is not None
        assert webhook_server.verification_token == "test_token"

    def test_verify_request_success(self, webhook_server):
        """测试请求验证成功"""
        test_event = {
            "header": {
                "token": "test_token",
                "event_type": "im.message.receive_v1",
            }
        }
        assert webhook_server._verify_request(test_event, json.dumps(test_event)) is True

    def test_verify_request_fail(self, webhook_server):
        """测试请求验证失败"""
        test_event = {
            "header": {
                "token": "wrong_token",
                "event_type": "im.message.receive_v1",
            }
        }
        assert webhook_server._verify_request(test_event, json.dumps(test_event)) is False

    def test_url_verification(self, webhook_server):
        """测试 URL 验证"""
        test_event = {
            "type": "url_verification",
            "challenge": "test_challenge",
        }
        # 注意：实际的处理是在 _handle_webhook 中，但这里验证逻辑
        # 该函数返回 challenge 值


class TestFeishuAdapterWebhook:
    """测试飞书适配器 Webhook 模式"""

    @pytest.fixture
    def feishu_config(self):
        """测试配置"""
        return FeishuPlatformConfig(
            enabled=True,
            app_id="cli_test",
            app_secret="secret_test",
            use_webhook=True,
            webhook_host="127.0.0.1",
            webhook_port=8888,
            allowed_user_ids=["ou_test_user"],
        )

    @pytest.fixture
    def adapter(self, feishu_config):
        """创建适配器实例"""
        return FeishuAdapter(feishu_config)

    def test_adapter_with_webhook_config(self, adapter):
        """测试启用 Webhook 的配置"""
        assert adapter.config.use_webhook is True
        assert adapter.config.webhook_host == "127.0.0.1"
        assert adapter.config.webhook_port == 8888

    def test_convert_text_event(self, adapter):
        """测试文本消息转换"""
        test_event = {
            "header": {
                "token": "test_token",
                "event_type": "im.message.receive_v1",
            },
            "event": {
                "message": {
                    "message_id": "msg_123",
                    "chat_id": "chat_456",
                    "msg_type": "text",
                    "body": {"content": json.dumps({"text": "Hello, World!"})},
                },
                "sender": {
                    "sender_id": {
                        "open_id": "ou_test_user",
                        "name": "Test User"
                    }
                }
            }
        }

        unified_msg = adapter.convert_webhook_event(test_event)

        assert unified_msg is not None
        assert unified_msg.content_type == ContentType.TEXT
        assert unified_msg.text == "Hello, World!"
        assert unified_msg.user_id == "ou_test_user"

    def test_convert_file_event(self, adapter):
        """测试文件消息转换"""
        test_event = {
            "header": {
                "token": "test_token",
                "event_type": "im.message.receive_v1",
            },
            "event": {
                "message": {
                    "message_id": "msg_456",
                    "chat_id": "chat_789",
                    "msg_type": "file",
                    "body": {"content": json.dumps({
                        "file_key": "file_abc",
                        "file_name": "test.pdf",
                        "file_size": 10240,
                    })},
                },
                "sender": {
                    "sender_id": {
                        "open_id": "ou_test_user",
                        "name": "Test User"
                    }
                }
            }
        }

        unified_msg = adapter.convert_webhook_event(test_event)

        assert unified_msg is not None
        assert unified_msg.content_type == ContentType.FILE
        assert unified_msg.file_info is not None
        assert unified_msg.file_info.file_id == "file_abc"
        assert unified_msg.file_info.file_name == "test.pdf"
        assert unified_msg.file_info.file_size == 10240

    def test_check_permission_allowed(self, adapter):
        """测试权限检查-允许"""
        assert adapter.check_permission("ou_test_user") is True

    def test_check_permission_denied(self, adapter):
        """测试权限检查-拒绝"""
        assert adapter.check_permission("ou_unknown_user") is False


class TestWebhookModeIntegration:
    """Webhook 模式集成测试"""

    @pytest.fixture
    def feishu_config(self):
        """测试配置"""
        return FeishuPlatformConfig(
            enabled=True,
            app_id="cli_test",
            app_secret="secret_test",
            use_webhook=True,
            webhook_host="127.0.0.1",
            webhook_port=9999,
            allowed_user_ids=["ou_user_1", "ou_user_2"],
        )

    @pytest.fixture
    def adapter(self, feishu_config):
        """创建适配器实例"""
        return FeishuAdapter(feishu_config)

    def test_webhook_event_processing_pipeline(self, adapter):
        """测试 Webhook 事件处理流程"""
        # 模拟收到 Webhook 事件
        test_event = {
            "header": {
                "token": "test_token",
                "event_type": "im.message.receive_v1",
            },
            "event": {
                "message": {
                    "message_id": "msg_test",
                    "chat_id": "chat_test",
                    "msg_type": "text",
                    "body": {"content": json.dumps({"text": "This is a test message"})},
                },
                "sender": {
                    "sender_id": {
                        "open_id": "ou_user_1",
                        "name": "Test User"
                    }
                }
            }
        }

        # 转换为统一消息
        unified_msg = adapter.convert_webhook_event(test_event)

        # 验证消息
        assert unified_msg is not None
        assert unified_msg.platform.value == "feishu"
        assert unified_msg.text == "This is a test message"
        assert unified_msg.user_id == "ou_user_1"


class TestUrlDetection:
    """测试 URL 检测"""

    def test_url_detection_https(self):
        """测试 HTTPS URL"""
        from platforms.feishu_adapter import FeishuAdapter
        from platforms.platform_types import FeishuPlatformConfig

        config = FeishuPlatformConfig(enabled=True, app_id="test", app_secret="test")
        adapter = FeishuAdapter(config)

        assert adapter._is_url("https://example.com") is True
        assert adapter._is_url("https://example.com/path?query=1") is True

    def test_url_detection_http(self):
        """测试 HTTP URL"""
        from platforms.feishu_adapter import FeishuAdapter
        from platforms.platform_types import FeishuPlatformConfig

        config = FeishuPlatformConfig(enabled=True, app_id="test", app_secret="test")
        adapter = FeishuAdapter(config)

        assert adapter._is_url("http://example.com") is True

    def test_url_detection_plain_text(self):
        """测试普通文本"""
        from platforms.feishu_adapter import FeishuAdapter
        from platforms.platform_types import FeishuPlatformConfig

        config = FeishuPlatformConfig(enabled=True, app_id="test", app_secret="test")
        adapter = FeishuAdapter(config)

        assert adapter._is_url("This is just plain text") is False
        assert adapter._is_url("example.com") is False  # 没有协议前缀


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
