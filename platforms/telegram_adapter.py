"""
Telegram 平台适配器 - 将 Telegram 消息转换为统一消息格式
"""

import asyncio
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from .base import PlatformAdapter
from .platform_types import (
    UnifiedMessage,
    PlatformType,
    ContentType,
    FileInfo,
    PlatformConfig,
)
from .tg_commands import command_registry, CommandContext
from storage.log_manager import get_logger


logger = get_logger("TelegramAdapter")


@dataclass
class TelegramConfig(PlatformConfig):
    """Telegram 配置"""
    bot_token: str = ""
    poll_interval: float = 1.0
    poll_timeout: int = 20
    use_webhook: bool = False
    webhook_url: str = ""
    webhook_host: str = "0.0.0.0"
    webhook_port: int = 8443
    webhook_secret: str = ""


class TelegramAdapter(PlatformAdapter):
    """Telegram 平台适配器"""

    def __init__(self, config: TelegramConfig):
        super().__init__(config)
        self.config: TelegramConfig = config
        self._application: Optional[Application] = None
        self._running: bool = False
        self._context: Optional[ContextTypes.DEFAULT_TYPE] = None
        self._command_handler_registry = command_registry

    async def initialize(self) -> bool:
        """初始化 Telegram Bot"""
        try:
            self._application = (
                Application.builder().token(self.config.bot_token).build()
            )

            self._application.add_handler(
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, self._handle_text_message
                )
            )
            self._application.add_handler(
                MessageHandler(filters.Document.ALL, self._handle_document_message)
            )
            self._application.add_handler(
                MessageHandler(filters.COMMAND, self._handle_command)
            )

            await self._application.initialize()
            logger.info("Telegram 适配器初始化成功")
            return True

        except Exception as e:
            logger.error(f"Telegram 适配器初始化失败: {e}", exc_info=True)
            return False

    async def start_listening(self):
        """开始监听消息"""
        if not self.config.enabled:
            logger.info("Telegram 功能未启用")
            return

        if not self._application:
            logger.error("Telegram 应用未初始化")
            return

        self._running = True
        
        try:
            if self.config.use_webhook:
                logger.info("Telegram 适配器启动 Webhook 模式")
                await self._start_webhook()
            else:
                logger.info("Telegram 适配器启动轮询模式")
                await self._start_polling()
        except Exception as e:
            logger.error(f"Telegram 消息监听异常: {e}", exc_info=True)
        finally:
            self._running = False

    async def _start_polling(self):
        """启动轮询模式"""
        await self._application.run_polling(
            poll_interval=self.config.poll_interval,
            timeout=self.config.poll_timeout,
            drop_pending_updates=True,
            close_loop=False,
        )

    async def _start_webhook(self):
        """启动 Webhook 模式"""
        if not self.config.webhook_url:
            logger.error("Webhook 模式需要配置 WEBHOOK_URL")
            raise ValueError("WEBHOOK_URL is required for webhook mode")

        # 删除旧的 webhook（如果存在）
        await self._application.bot.delete_webhook()
        
        # 设置新的 webhook
        webhook_kwargs = {}
        if self.config.webhook_secret:
            webhook_kwargs['secret_token'] = self.config.webhook_secret
        
        await self._application.bot.set_webhook(
            url=self.config.webhook_url,
            **webhook_kwargs
        )
        
        logger.info(f"Telegram Webhook 设置成功: {self.config.webhook_url}")
        
        # 启动 Webhook 服务器
        await self._application.run_webhook(
            listen=self.config.webhook_host,
            port=self.config.webhook_port,
            url_path="/telegram/webhook",
            secret_token=self.config.webhook_secret if self.config.webhook_secret else None,
            drop_pending_updates=True,
            close_loop=False,
        )

    async def stop_listening(self):
        """停止监听"""
        self._running = False
        if self._application:
            await self._application.stop()
            await self._application.shutdown()
        logger.info("Telegram 适配器已停止监听")

    async def send_message(self, chat_id: str, text: str, **kwargs) -> bool:
        """发送消息"""
        try:
            if not self._application or not self._application.bot:
                logger.error("Telegram bot 未初始化")
                return False

            chat_id_int = int(chat_id)
            await self._application.bot.send_message(
                chat_id=chat_id_int,
                text=text,
                parse_mode=None,
                disable_web_page_preview=True,
            )
            logger.debug(f"Telegram 消息发送成功: {chat_id}")
            return True

        except Exception as e:
            logger.error(f"Telegram 消息发送异常: {e}", exc_info=True)
            return False

    async def reply_message(
        self,
        message_id: str,
        text: str,
        **kwargs
    ) -> bool:
        """回复消息"""
        try:
            if not self._application or not self._application.bot:
                logger.error("Telegram bot 未初始化")
                return False

            chat_id = kwargs.get("chat_id")
            if not chat_id:
                logger.error("回复消息需要 chat_id 参数")
                return False

            chat_id_int = int(chat_id)
            await self._application.bot.send_message(
                chat_id=chat_id_int,
                text=text,
                parse_mode=None,
                disable_web_page_preview=True,
                reply_to_message_id=int(message_id),
            )
            logger.debug(f"Telegram 回复消息成功: message_id={message_id}")
            return True

        except Exception as e:
            logger.error(f"Telegram 回复消息异常: {e}", exc_info=True)
            return False

    async def download_file(
        self, file_id: str, dest_path: str
    ) -> Tuple[bool, int]:
        """下载文件"""
        try:
            if not self._application or not self._application.bot:
                logger.error("Telegram bot 未初始化")
                return False, 0

            file_obj = await self._application.bot.get_file(file_id)
            await file_obj.download_to_drive(dest_path)

            import os
            file_size = os.path.getsize(dest_path)
            logger.info(f"Telegram 文件下载成功: {dest_path} ({file_size}字节)")
            return True, file_size

        except Exception as e:
            logger.error(f"Telegram 文件下载异常: {e}", exc_info=True)
            return False, 0

    async def _handle_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理命令消息"""
        try:
            message = update.effective_message
            if not message or not message.text:
                return

            user = update.effective_user
            chat = update.effective_chat

            if not user or not chat:
                return

            text = message.text.strip()
            if not text.startswith('/'):
                return

            parts = text[1:].split(maxsplit=1)
            command_name = parts[0].lower()
            args = parts[1].split() if len(parts) > 1 else []

            logger.info(f"收到命令: /{command_name} from user_id={user.id}")

            ctx = CommandContext(
                command=command_name,
                args=args,
                user_id=str(user.id),
                chat_id=str(chat.id),
                message_id=str(message.message_id),
                platform=PlatformType.TELEGRAM,
                update=update,
                context=context,
            )

            handler = self._command_handler_registry.get_handler(command_name)
            if handler:
                response = await handler(self, args, ctx)
                if response:
                    await update.message.reply_text(response)
            else:
                await update.message.reply_text(
                    f"未知命令: /{command_name}\n输入 /help 获取帮助"
                )

        except Exception as e:
            logger.error(f"命令处理异常: {e}", exc_info=True)
            try:
                await update.message.reply_text(f"处理命令时发生错误: {str(e)}")
            except:
                pass

    async def _handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理文本消息"""
        unified_msg = self._convert_to_unified_message(update)
        if unified_msg:
            self._notify_message(unified_msg)

    async def _handle_document_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理文档消息"""
        unified_msg = self._convert_to_unified_message(update)
        if unified_msg:
            self._notify_message(unified_msg)

    def _convert_to_unified_message(self, update: Update) -> Optional[UnifiedMessage]:
        """将 Telegram Update 转换为统一消息格式"""
        try:
            message = update.effective_message
            if not message:
                return None

            user = update.effective_user
            chat = update.effective_chat

            if not user or not chat:
                return None

            message_id = str(message.message_id)
            chat_id = str(chat.id)
            user_id = str(user.id)
            user_name = user.first_name or user.username or ""

            content_type = ContentType.UNKNOWN
            text = None
            file_info = None

            if message.text:
                content_type = ContentType.TEXT
                text = message.text

            elif message.document:
                doc = message.document
                content_type = ContentType.FILE
                file_info = FileInfo(
                    file_id=doc.file_id,
                    file_name=doc.file_name or f"file_{doc.file_id[:8]}",
                    file_size=doc.file_size or 0,
                    mime_type=doc.mime_type,
                )

            elif message.photo:
                photo = message.photo[-1]
                content_type = ContentType.IMAGE
                file_info = FileInfo(
                    file_id=photo.file_id,
                    file_name=f"photo_{photo.file_id[:8]}.jpg",
                    file_size=photo.file_size or 0,
                )

            return UnifiedMessage(
                platform=PlatformType.TELEGRAM,
                message_id=message_id,
                chat_id=chat_id,
                user_id=user_id,
                user_name=user_name,
                content_type=content_type,
                text=text,
                file_info=file_info,
                raw_data={"update_id": update.update_id},
            )

        except Exception as e:
            logger.error(f"Telegram 消息转换失败: {e}", exc_info=True)
            return None