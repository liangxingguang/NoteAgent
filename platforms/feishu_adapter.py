"""
飞书平台适配器 - 使用 lark-oapi SDK
"""

import asyncio
import json
from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple

from lark_oapi import Client
from lark_oapi.api.im.v1 import CreateMessageRequest, CreateMessageRequestBody

from .base import PlatformAdapter
from .platform_types import (
    UnifiedMessage,
    PlatformType,
    ContentType,
    FileInfo,
    PlatformConfig
)
from storage.log_manager import get_logger


logger = get_logger("FeishuAdapter")


@dataclass
class FeishuConfig(PlatformConfig):
    """飞书配置"""
    app_id: str = ""
    app_secret: str = ""
    verification_token: str = ""
    encrypt_key: str = ""
    bot_name: str = "NoteAgents"
    poll_interval: float = 1.0


class FeishuAdapter(PlatformAdapter):
    """飞书平台适配器"""

    def __init__(self, config: FeishuConfig):
        super().__init__(config)
        self.config: FeishuConfig = config
        self._client: Optional[Client] = None
        self._running: bool = False
        self._last_processed_timestamp: int = 0

    async def initialize(self) -> bool:
        """初始化飞书连接"""
        try:
            self._client = Client.builder() \
                .app_id(self.config.app_id) \
                .app_secret(self.config.app_secret) \
                .build()

            success = await self._test_connection()
            if not success:
                logger.error("飞书连接测试失败")
                return False

            logger.info("飞书适配器初始化成功")
            return True

        except Exception as e:
            logger.error(f"飞书适配器初始化失败: {e}", exc_info=True)
            return False

    async def start_listening(self):
        """开始监听消息（轮询模式）"""
        if not self.config.enabled:
            logger.info("飞书功能未启用")
            return

        self._running = True
        logger.info("飞书适配器开始监听消息")

        while self._running:
            try:
                messages = await self._fetch_new_messages()

                for msg in messages:
                    unified_msg = self._convert_to_unified_message(msg)
                    if unified_msg:
                        self._notify_message(unified_msg)

                await asyncio.sleep(self.config.poll_interval)

            except Exception as e:
                logger.error(f"飞书消息监听异常: {e}", exc_info=True)
                await asyncio.sleep(2)

    async def stop_listening(self):
        """停止监听"""
        self._running = False
        logger.info("飞书适配器已停止监听")

    async def send_message(
        self,
        chat_id: str,
        text: str,
        **kwargs
    ) -> bool:
        """发送消息"""
        try:
            receive_id_type = "chat_id" if chat_id.startswith("oc_") else "open_id"

            request = CreateMessageRequest.builder() \
                .receive_id_type(receive_id_type) \
                .body(CreateMessageRequestBody.builder()
                      .receive_id(chat_id)
                      .msg_type("text")
                      .content(f'{{"text": "{text}"}}')
                      .build()) \
                .build()

            response = self._client.im.v1.message.create(request)

            if response.success():
                logger.debug(f"飞书消息发送成功: {chat_id}")
                return True
            else:
                logger.error(f"飞书消息发送失败: {response.msg}")
                return False

        except Exception as e:
            logger.error(f"飞书消息发送异常: {e}", exc_info=True)
            return False

    async def reply_message(
        self,
        message_id: str,
        text: str,
        **kwargs
    ) -> bool:
        """回复消息（通过 reply_id 方式）"""
        try:
            from lark_oapi.api.im.v1 import ReplyMessageRequest, ReplyMessageRequestBody

            request = ReplyMessageRequest.builder() \
                .message_id(message_id) \
                .body(ReplyMessageRequestBody.builder()
                      .msg_type("text")
                      .content(f'{{"text": "{text}"}}')
                      .build()) \
                .build()

            response = self._client.im.v1.message.reply(request)

            if response.success():
                logger.debug(f"飞书回复消息成功: message_id={message_id}")
                return True
            else:
                logger.error(f"飞书回复消息失败: {response.msg}")
                return False

        except Exception as e:
            logger.error(f"飞书回复消息异常: {e}", exc_info=True)
            return False

    async def download_file(
        self,
        file_key: str,
        dest_path: str
    ) -> Tuple[bool, int]:
        """下载文件"""
        try:
            from lark_oapi.api.im.v1 import DownloadFileRequest

            request = DownloadFileRequest.builder() \
                .file_key(file_key) \
                .build()

            response = self._client.im.v1.file.download(request)

            if response.success():
                data = response.data
                if data and hasattr(data, 'content'):
                    content = data.content
                    if isinstance(content, bytes):
                        with open(dest_path, "wb") as f:
                            f.write(content)
                        file_size = len(content)
                        logger.info(f"飞书文件下载成功: {dest_path} ({file_size}字节)")
                        return True, file_size

            logger.error(f"飞书文件下载失败: {response.msg}")
            return False, 0

        except Exception as e:
            logger.error(f"飞书文件下载异常: {e}", exc_info=True)
            return False, 0

    async def _test_connection(self) -> bool:
        """测试连接"""
        try:
            from lark_oapi.api.bot.v3 import GetBotInfoRequest

            request = GetBotInfoRequest.builder().build()
            response = self._client.bot.v3.bot.get(request)

            if response.success():
                bot_info = response.data
                if bot_info and hasattr(bot_info, 'app_name'):
                    logger.info(f"飞书机器人信息: {bot_info.app_name}")
                return True
            else:
                logger.error(f"连接测试失败: {response.msg}")
                return False

        except Exception as e:
            logger.error(f"连接测试异常: {e}", exc_info=True)
            return False

    async def _fetch_new_messages(self) -> list:
        """获取新消息（轮询模式）"""
        try:
            from lark_oapi.api.im.v1 import ListMessageRequest

            request = ListMessageRequest.builder() \
                .container_id_type("p2p") \
                .container_id(self.config.app_id) \
                .sort_type("ByCreateTimeAsc") \
                .page_size(20) \
                .build()

            response = self._client.im.v1.message.list(request)

            if response.success():
                return response.data.items if response.data and hasattr(response.data, 'items') else []
            else:
                logger.error(f"获取消息失败: {response.msg}")
                return []

        except Exception as e:
            logger.error(f"获取消息异常: {e}", exc_info=True)
            return []

    def _convert_to_unified_message(self, msg: Any) -> Optional[UnifiedMessage]:
        """将飞书消息转换为统一消息格式"""
        try:
            if not hasattr(msg, 'msg_type') or not hasattr(msg, 'message_id'):
                logger.warning(f"消息对象格式不正确: {type(msg)}")
                return None

            msg_type = msg.msg_type
            content = msg.content

            content_type = ContentType.UNKNOWN
            text = None
            file_info = None

            if msg_type == "text":
                content_type = ContentType.TEXT
                import json
                try:
                    content_dict = json.loads(content) if isinstance(content, str) else content
                    text = content_dict.get("text", "") if isinstance(content_dict, dict) else ""
                except:
                    text = str(content)

            elif msg_type == "file":
                content_type = ContentType.FILE
                import json
                try:
                    content_dict = json.loads(content) if isinstance(content, str) else content
                    file_key = content_dict.get("file_key", "") if isinstance(content_dict, dict) else ""
                    file_name = content_dict.get("file_name", "unknown") if isinstance(content_dict, dict) else "unknown"
                    file_info = FileInfo(
                        file_id=file_key,
                        file_name=file_name,
                        file_size=0,
                        mime_type=None,
                    )
                except:
                    file_info = None

            return UnifiedMessage(
                platform=PlatformType.FEISHU,
                message_id=msg.message_id or "",
                chat_id=msg.chat_id or "",
                user_id=msg.sender.id if hasattr(msg, 'sender') and hasattr(msg.sender, 'id') else "",
                user_name=msg.sender.name if hasattr(msg, 'sender') and hasattr(msg.sender, 'name') else "",
                content_type=content_type,
                text=text,
                file_info=file_info,
                raw_data=msg.__dict__ if hasattr(msg, '__dict__') else {},
            )

        except Exception as e:
            logger.error(f"消息转换失败: {e}", exc_info=True)
            return None

    def convert_webhook_event_to_message(self, event_dict: Dict[str, Any]) -> Optional[UnifiedMessage]:
        """将 webhook 事件转换为统一消息格式"""
        try:
            logger.debug(f"处理 webhook 事件: {json.dumps(event_dict, ensure_ascii=False)}")

            # 从事件字典中提取消息信息
            event = event_dict.get("event", event_dict)  # 兼容不同格式
            message = event.get("message", {})
            
            if not message:
                logger.warning("事件中未找到 message")
                return None

            # 提取基本信息
            msg_type = message.get("msg_type", "")
            message_id = message.get("message_id", "")
            content = message.get("content", "")
            
            # 获取发送者信息
            sender = message.get("sender", {})
            user_id = sender.get("sender_id", {}).get("open_id", "") if isinstance(sender, dict) else ""
            user_name = sender.get("sender_id", {}).get("union_id", "") if isinstance(sender, dict) else ""
            
            # 获取聊天 ID
            chat_id = message.get("chat_id", "")

            # 解析内容
            content_type = ContentType.UNKNOWN
            text = None
            file_info = None

            if msg_type == "text":
                content_type = ContentType.TEXT
                try:
                    content_dict = json.loads(content) if isinstance(content, str) else content
                    text = content_dict.get("text", "") if isinstance(content_dict, dict) else str(content)
                except:
                    text = str(content)

            elif msg_type == "file":
                content_type = ContentType.FILE
                try:
                    content_dict = json.loads(content) if isinstance(content, str) else content
                    file_key = content_dict.get("file_key", "") if isinstance(content_dict, dict) else ""
                    file_name = content_dict.get("file_name", "unknown") if isinstance(content_dict, dict) else "unknown"
                    file_info = FileInfo(
                        file_id=file_key,
                        file_name=file_name,
                        file_size=0,
                        mime_type=None,
                    )
                except:
                    file_info = None

            elif msg_type == "image":
                content_type = ContentType.IMAGE
                try:
                    content_dict = json.loads(content) if isinstance(content, str) else content
                    file_key = content_dict.get("image_key", "") if isinstance(content_dict, dict) else ""
                    file_info = FileInfo(
                        file_id=file_key,
                        file_name=f"image_{file_key[:8]}.jpg" if file_key else "unknown.jpg",
                        file_size=0,
                        mime_type="image/jpeg",
                    )
                except:
                    file_info = None

            # 构建统一消息
            unified_msg = UnifiedMessage(
                platform=PlatformType.FEISHU,
                message_id=message_id,
                chat_id=chat_id,
                user_id=user_id,
                user_name=user_name,
                content_type=content_type,
                text=text,
                file_info=file_info,
                raw_data=event_dict,
            )

            logger.info(f"Webhook 事件转换成功: msg_id={message_id}, type={content_type.value}")
            return unified_msg

        except Exception as e:
            logger.error(f"Webhook 事件转换失败: {e}", exc_info=True)
            return None
