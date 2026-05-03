"""
Telegram 平台适配器 - 将 Telegram 消息转换为统一消息格式
"""
import asyncio
from dataclasses import dataclass
from typing import Optional, Tuple

# 设置 sniffio 以支持 python-telegram-bot
try:
    import sniffio
    from sniffio import AsyncLibraryNotFoundError

    # 保存原始的 sniffio 函数
    _original_current_async_library = sniffio.current_async_library

    def _patched_current_async_library():
        try:
            return _original_current_async_library()
        except AsyncLibraryNotFoundError:
            # 如果无法检测到，默认返回 asyncio
            return "asyncio"

    sniffio.current_async_library = _patched_current_async_library
except ImportError:
    pass

from telegram import Update
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    filters,
)

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
    use_proxy: bool = False
    proxy_url: str = ""
    webhook_url: str = ""
    webhook_host: str = "0.0.0.0"
    webhook_port: int = 8443
    webhook_secret: str = ""


class TelegramAdapter(PlatformAdapter):
    """Telegram 平台适配器（无冲突稳定版）"""

    def __init__(self, config: TelegramConfig):
        super().__init__(config)
        self.config: TelegramConfig = config
        self._application: Optional[Application] = None
        self._running: bool = False
        self._command_handler_registry = command_registry

    async def initialize(self) -> bool:
        """初始化 Telegram Bot（无冲突写法）"""
        try:
            # ✅ 完全避开底层冲突：使用 proxy 参数而不是 request
            from telegram.request import HTTPXRequest

            if self.config.use_proxy and self.config.proxy_url:
                # 使用正确的代理配置
                request = HTTPXRequest(proxy=self.config.proxy_url)
                self._application = (
                    Application.builder()
                    .token(self.config.bot_token)
                    .request(request)
                    .build()
                )
            else:
                self._application = (
                    Application.builder()
                    .token(self.config.bot_token)
                    .build()
                )

            # 注册处理器
            self._application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text_message)
            )
            self._application.add_handler(
                MessageHandler(filters.Document.ALL, self._handle_document_message)
            )
            self._application.add_handler(
                MessageHandler(filters.COMMAND, self._handle_command)
            )

            await self._application.initialize()
            logger.info("✅ Telegram 适配器初始化成功")
            return True

        except Exception as e:
            logger.error(f"❌ Telegram 初始化失败: {e}", exc_info=True)
            return False

    async def start_listening(self):
        if not self.config.enabled or not self._application:
            return

        self._running = True
        try:
            await self._application.start()
            await self._application.updater.start_polling(
                poll_interval=self.config.poll_interval,
                timeout=self.config.poll_timeout,
                drop_pending_updates=True,
            )
            logger.info("✅ Telegram 轮询已启动")

            while self._running:
                await asyncio.sleep(0.2)

        except Exception as e:
            logger.error(f"监听异常: {e}", exc_info=True)
        finally:
            await self.stop_listening()

    async def stop_listening(self):
        self._running = False
        if self._application:
            try:
                await self._application.stop()
                await self._application.shutdown()
            except:
                pass

    # ====================
    # 功能代码保持不变
    # ====================
    async def send_message(self, chat_id: str, text: str, **kwargs) -> bool:
        try:
            await self._application.bot.send_message(chat_id=int(chat_id), text=text, disable_web_page_preview=True)
            return True
        except:
            return False

    async def reply_message(self, message_id: str, text: str, **kwargs) -> bool:
        try:
            await self._application.bot.send_message(
                chat_id=int(kwargs["chat_id"]),
                text=text,
                reply_to_message_id=int(message_id),
            )
            return True
        except:
            return False

    async def download_file(self, file_id: str, dest_path: str) -> Tuple[bool, int]:
        try:
            f = await self._application.bot.get_file(file_id)
            await f.download_to_drive(dest_path)
            import os
            return True, os.path.getsize(dest_path)
        except:
            return False, 0

    async def _handle_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            msg = update.effective_message
            if not msg or not msg.text:
                return
            user = update.effective_user
            chat = update.effective_chat

            text = msg.text.strip()
            if not text.startswith("/"):
                return
            parts = text[1:].split(maxsplit=1)
            cmd = parts[0].lower()
            args = parts[1].split() if len(parts) > 1 else []

            ctx = CommandContext(
                command=cmd,
                args=args,
                user_id=str(user.id),
                chat_id=str(chat.id),
                message_id=str(msg.message_id),
                platform=PlatformType.TELEGRAM,
                update=update,
                context=context,
            )

            handler = self._command_handler_registry.get_handler(cmd)
            if handler:
                res = await handler(self, args, ctx)
                if res:
                    await update.message.reply_text(res)
        except:
            pass

    async def _handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        m = self._convert_to_unified_message(update)
        if m:
            self._notify_message(m)

    async def _handle_document_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        m = self._convert_to_unified_message(update)
        if m:
            self._notify_message(m)

    def _convert_to_unified_message(self, update: Update) -> Optional[UnifiedMessage]:
        try:
            msg = update.effective_message
            user = update.effective_user
            chat = update.effective_chat
            if not msg or not user or not chat:
                return None

            mid = str(msg.message_id)
            cid = str(chat.id)
            uid = str(user.id)
            uname = user.first_name or user.username or ""
            contentType = ContentType.UNKNOWN
            text = None
            file = None

            if msg.text:
                contentType = ContentType.TEXT
                text = msg.text
            elif msg.document:
                d = msg.document
                contentType = ContentType.FILE
                file = FileInfo(
                    file_id=d.file_id,
                    file_name=d.file_name or f"file_{d.file_id[:8]}",
                    file_size=d.file_size or 0,
                    mime_type=d.mime_type,
                )
            elif msg.photo:
                p = msg.photo[-1]
                contentType = ContentType.IMAGE
                file = FileInfo(
                    file_id=p.file_id,
                    file_name=f"photo_{p.file_id[:8]}.jpg",
                    file_size=p.file_size or 0,
                )

            return UnifiedMessage(
                platform=PlatformType.TELEGRAM,
                message_id=mid,
                chat_id=cid,
                user_id=uid,
                user_name=uname,
                content_type=contentType,
                text=text,
                file_info=file,
            )
        except:
            return None