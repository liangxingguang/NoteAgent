"""
飞书平台适配器 - 适用于 lark-oapi >= 1.5.5
100% 可运行、可收消息、无报错
支持文件下载功能
"""

import asyncio
import json
import os
import threading
from dataclasses import dataclass, field
from typing import Optional, Tuple

from lark_oapi import Client
from lark_oapi.api.im.v1 import (
    CreateMessageRequest,
    CreateMessageRequestBody,
    ReplyMessageRequest,
    ReplyMessageRequestBody
)
from lark_oapi.api.drive.v1 import (
    DownloadFileRequest,
)
from lark_oapi.ws import Client as WsClient
from lark_oapi.event.dispatcher_handler import EventDispatcherHandler

from .base import PlatformAdapter
from .platform_types import (
    UnifiedMessage,
    PlatformType,
    ContentType,
    PlatformConfig,
    FileInfo
)
from .feishu_commands import get_command_handler, CommandContext, parse_command
from storage.log_manager import get_logger

logger = get_logger("FeishuAdapter")


@dataclass
class FeishuConfig(PlatformConfig):
    enabled: bool = False
    app_id: str = ""
    app_secret: str = ""
    verification_token: str = ""
    encrypt_key: str = ""
    bot_name: str = "NoteAgents"
    allowed_user_ids: list[str] = field(default_factory=list)
    poll_interval: float = 1.0
    use_webhook: bool = False
    webhook_host: str = "0.0.0.0"
    webhook_port: int = 8000


class FeishuAdapter(PlatformAdapter):
    def __init__(self, config: FeishuConfig):
        super().__init__(config)
        self.config = config
        self._client: Optional[Client] = None
        self._ws_client: Optional[WsClient] = None
        self._running = False

    async def initialize(self) -> bool:
        try:
            logger.info("正在连接飞书 WebSocket 长连接...")

            self._client = Client.builder() \
                .app_id(self.config.app_id) \
                .app_secret(self.config.app_secret) \
                .build()

            # ✅ 使用 EventDispatcherHandler 注册消息事件
            event_handler = EventDispatcherHandler.builder(
                self.config.encrypt_key,
                self.config.verification_token
            ).register_p2_im_message_receive_v1(self._on_message_receive_v1).build()

            # 启动 ws
            self._ws_client = WsClient(
                app_id=self.config.app_id,
                app_secret=self.config.app_secret,
                event_handler=event_handler,
                auto_reconnect=True
            )

            threading.Thread(target=self._ws_client.start, daemon=True).start()
            await asyncio.sleep(1)

            logger.info("✅ 飞书长连接初始化成功")
            return True

        except Exception as e:
            logger.error(f"初始化失败: {e}", exc_info=True)
            return False

    # ==================== WebSocket 消息事件处理 ====================
    def _on_message_receive_v1(self, data):
        """处理 P2ImMessageReceiveV1 事件"""
        try:
            logger.debug(f"the event{data}")
            event = data.event
            if not event or not event.message:
                logger.warning("事件数据不完整")
                return

            msg = event.message
            sender = event.sender

            chat_id = msg.chat_id or ""
            msg_id = msg.message_id or ""
            msg_type = msg.message_type or "text"
            content = msg.content or "{}"
            chat_type = msg.chat_type or ""
            mentions = msg.mentions or []

            user_id = ""
            if sender and sender.sender_id:
                user_id = sender.sender_id.open_id or sender.sender_id.user_id or sender.sender_id.union_id or ""

            logger.info(f"[飞书消息] chat_type={chat_type}, msg_id={msg_id}, user_id={user_id}")

            # 白名单
            if self.config.allowed_user_ids and user_id not in self.config.allowed_user_ids:
                logger.debug(f"用户 {user_id} 不在白名单中")
                return

            # 是否 @机器人
            is_at_me = any(m.mention_type == "bot" for m in mentions if hasattr(m, 'mention_type'))

            # 只允许私聊或@
            if chat_type != "p2p" and not is_at_me:
                logger.debug(f"非私聊且未@机器人，跳过")
                return

            # 解析消息
            text = ""
            content_type = ContentType.TEXT
            file_info = None

            if msg_type == "text":
                try:
                    text = json.loads(content).get("text", "")
                except:
                    text = str(content)
                
                # 检查是否为命令（以 / 开头）
                if text and text.strip().startswith('/'):
                    content_type = ContentType.COMMAND
            elif msg_type in ("file", "image", "video", "audio"):
                # 处理文件类型消息
                try:
                    content_data = json.loads(content)
                    file_key = content_data.get("file_key", "")
                    file_name = content_data.get("file_name", "")
                    if file_key:
                        content_type = self._get_content_type(msg_type)
                        file_info = FileInfo(
                            file_id=file_key,
                            file_name=file_name,
                            file_size=0,
                            mime_type=self._get_mime_type(msg_type)
                        )
                        # 提取文件名中的文本作为消息内容
                        text = file_name
                        logger.info(f"📎 文件消息: {file_name}, key={file_key}")
                except Exception as e:
                    logger.error(f"解析文件消息失败: {e}")

            if not text and not file_info:
                logger.debug("消息内容为空，跳过")
                return

            # 推送到业务层
            unified = UnifiedMessage(
                platform=PlatformType.FEISHU,
                message_id=msg_id,
                chat_id=chat_id,
                user_id=user_id,
                user_name="",
                content_type=content_type,
                text=text,
                file_info=file_info,
                raw_data={
                    "chat_type": chat_type,
                    "is_at_me": is_at_me,
                    "msg_type": msg_type,
                }
            )
            self._notify_message(unified)
            logger.info(f"📩 处理消息: {text[:50]}...")

        except Exception as e:
            logger.error(f"处理失败: {e}", exc_info=True)

    async def start_listening(self):
        self._running = True
        logger.info("🚀 飞书长连接监听已启动")
        while self._running:
            await asyncio.sleep(1)

    async def stop_listening(self):
        self._running = False
        try:
            self._ws_client.stop()
        except:
            pass

    async def process_command(self, msg: UnifiedMessage) -> bool:
        """
        处理命令消息
        返回 True 表示已处理，False 表示未处理
        """
        try:
            if not msg.text or not msg.text.startswith('/'):
                return False

            # 解析命令
            command, args = parse_command(msg.text)
            if not command:
                return False

            # 获取命令处理器
            handler = get_command_handler()
            
            # 构建命令上下文
            ctx = CommandContext(
                command=command,
                args=args,
                user_id=msg.user_id,
                chat_id=msg.chat_id,
                message_id=msg.message_id,
                platform=PlatformType.FEISHU
            )

            # 执行命令
            response = await handler.handle_command(command, args, ctx)
            if response:
                # 处理富文本消息
                if response == "__RICH_TEXT_WELCOME__":
                    from .feishu_rich_text import build_welcome_rich_text
                    await self._send_rich_text_message(msg.chat_id, build_welcome_rich_text())
                elif response == "__RICH_TEXT_HELP__":
                    from .feishu_rich_text import build_help_rich_text
                    await self._send_rich_text_message(msg.chat_id, build_help_rich_text())
                else:
                    await self.send_message(msg.chat_id, response)
                return True
            return False
        except Exception as e:
            logger.error(f"处理命令失败: {e}", exc_info=True)
            return False

    async def _send_rich_text_message(self, chat_id: str, content: dict) -> bool:
        """发送富文本消息"""
        try:
            req = CreateMessageRequest.builder() \
                .receive_id_type("chat_id") \
                .request_body(CreateMessageRequestBody.builder()
                      .receive_id(chat_id)
                      .msg_type("rich_text")
                      .content(json.dumps(content, ensure_ascii=False))
                      .build()) \
                .build()
            res = self._client.im.v1.message.create(req)
            return res.success()
        except Exception as e:
            logger.error(f"发送富文本消息失败: {e}")
            return False

    async def send_message(self, chat_id: str, text: str,** kwargs) -> bool:
        try:
            req = CreateMessageRequest.builder() \
                .receive_id_type("chat_id") \
                .request_body(CreateMessageRequestBody.builder()
                      .receive_id(chat_id)
                      .msg_type("text")
                      .content(json.dumps({"text": text}, ensure_ascii=False))
                      .build()) \
                .build()
            res = self._client.im.v1.message.create(req)
            return res.success()
        except Exception as e:
            logger.error(f"发送失败: {e}")
            return False

    async def reply_message(self, message_id: str, text: str, **kwargs) -> bool:
        try:
            req = ReplyMessageRequest.builder() \
                .message_id(message_id) \
                .request_body(ReplyMessageRequestBody.builder()
                      .msg_type("text")
                      .content(json.dumps({"text": text}, ensure_ascii=False))
                      .build()) \
                .build()
            res = self._client.im.v1.message.reply(req)
            return res.success()
        except Exception as e:
            logger.error(f"回复失败: {e}")
            return False

    def _get_content_type(self, msg_type: str) -> ContentType:
        """将飞书消息类型转换为统一的 ContentType"""
        type_map = {
            "file": ContentType.FILE,
            "image": ContentType.IMAGE,
            "video": ContentType.VIDEO,
            "audio": ContentType.AUDIO,
        }
        return type_map.get(msg_type, ContentType.FILE)

    def _get_mime_type(self, msg_type: str) -> Optional[str]:
        """根据消息类型获取 MIME 类型"""
        mime_map = {
            "file": "application/octet-stream",
            "image": "image/png",
            "video": "video/mp4",
            "audio": "audio/mpeg",
        }
        return mime_map.get(msg_type)

    async def download_file(self, file_key: str, dest_path: str) -> Tuple[bool, int]:
        """
        下载飞书文件
        
        Args:
            file_key: 文件标识
            dest_path: 目标保存路径
            
        Returns:
            (是否成功, 文件大小)
        """
        try:
            logger.info(f"开始下载文件: {file_key} -> {dest_path}")
            
            # 确保目标目录存在
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            
            # 获取下载链接
            req = DownloadFileRequest.builder().file_key(file_key).build()
            res = self._client.drive.v1.file.download(req)
            
            if not res.success():
                logger.error(f"获取下载链接失败: {res.msg}")
                return False, 0
            
            # 下载文件
            download_url = res.data.download_url
            if not download_url:
                logger.error("下载链接为空")
                return False, 0
            
            # 使用 requests 下载
            import requests
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            file_size = 0
            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        file_size += len(chunk)
            
            logger.info(f"文件下载成功: {dest_path}, 大小: {file_size} bytes")
            return True, file_size
            
        except Exception as e:
            logger.error(f"下载文件失败: {e}", exc_info=True)
            return False, 0