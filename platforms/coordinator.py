"""
多平台协调器 - 统一处理来自不同平台的消息
集成 LLM Wiki 模块，实现完整流程自动化！
"""

import asyncio
import os
from typing import Optional, Tuple, Dict, Any

from .manager import PlatformManager
from .platform_types import (
    PlatformType,
    ContentType,
    UnifiedMessage,
    FeishuPlatformConfig,
)
from .feishu_adapter import FeishuAdapter
from storage.log_manager import get_logger
from storage.temp_manager import get_temp_manager
from tools import (
    process_file,
    validate_file,
    generate_obsidian_note,
    write_note_to_file,
    cleanup_file,
)
from tools.web_tool import get_web_tool
from tools import get_wiki_tool
from config import get_config
from wiki.command_handler import WikiCommandHandler


logger = get_logger("Coordinator")


class MessageCoordinator:
    """
    消息协调器 - 处理来自不同平台的统一消息
    """

    def __init__(self, platform_manager: PlatformManager, max_concurrent: int = 5):
        self.platform_manager = platform_manager
        self.wiki_command_handler = WikiCommandHandler()
        self._semaphore = asyncio.Semaphore(max_concurrent)

    def _handle_message(self, msg: UnifiedMessage):
        """消息处理入口，供 PlatformManager 调用（非阻塞）"""
        asyncio.create_task(self._process_with_limit(msg))

    async def _process_with_limit(self, msg: UnifiedMessage):
        """带并发限制的消息处理"""
        async with self._semaphore:
            await self.process_message(msg)

    async def process_message(self, msg: UnifiedMessage):
        """处理统一消息"""
        logger.info(f"收到来自 {msg.platform.value} 的消息: user={msg.user_id}, type={msg.content_type.value}")

        try:
            # 获取对应平台的适配器
            adapter = self.platform_manager.get_adapter(msg.platform)
            if not adapter:
                logger.error(f"无法获取平台适配器: {msg.platform.value}")
                return

            # 0. 检查是否为 Wiki 命令（优先处理！
            config = get_config()
            if config.wiki.enabled and msg.content_type == ContentType.TEXT:
                is_wiki_command, response_msg = self.wiki_command_handler.process_command(msg.text)
                if is_wiki_command:
                    logger.info(f"Wiki 命令处理: {msg.text}")
                    if hasattr(adapter, 'send_message'):
                        await adapter.send_message(msg.chat_id, response_msg)
                    return

            # 1. 检查是否为命令
            if msg.content_type == ContentType.COMMAND and hasattr(adapter, 'process_command'):
                handled = await adapter.process_command(msg)
                if handled:
                    logger.info(f"命令已处理: {msg.text}")
                    return

            # 2. 发送处理中消息
            if hasattr(adapter, 'send_message'):
                await adapter.send_message(msg.chat_id, "⏳ 正在处理中，请稍候...")

            # 3. 根据内容类型处理
            result = None

            if msg.content_type == ContentType.TEXT:
                from tools.ai_summary_tool import is_url
                if msg.text and is_url(msg.text.strip()):
                    result = await self._process_url(msg.text.strip())
                else:
                    result = await self._process_text(msg.text)

            elif msg.content_type == ContentType.URL:
                result = await self._process_url(msg.text)

            elif msg.content_type == ContentType.FILE:
                result = await self._process_file(msg, adapter)

            elif msg.content_type == ContentType.IMAGE:
                result = await self._process_image(msg, adapter)

            else:
                error_msg = f"不支持的消息类型: {msg.content_type.value}"
                if hasattr(adapter, 'send_error_message'):
                    await adapter.send_error_message(msg.chat_id, error_msg)
                elif hasattr(adapter, 'send_message'):
                    await adapter.send_message(msg.chat_id, error_msg)
                return

            # 4. 发送结果消息
            if result and result.get("success"):
                filename = result.get("filename", "未知文件")
                if hasattr(adapter, 'send_success_message'):
                    await adapter.send_success_message(msg.chat_id, filename, result.get("note_title"))
                elif hasattr(adapter, 'send_message'):
                    await adapter.send_message(msg.chat_id, f"✅ 处理成功！\n\n💾 保存文件：{filename}")
                logger.info(f"处理完成: {filename}")
            else:
                error_msg = result.get("error", "处理失败") if result else "处理失败"
                if hasattr(adapter, 'send_error_message'):
                    await adapter.send_error_message(msg.chat_id, error_msg)
                elif hasattr(adapter, 'send_message'):
                    await adapter.send_message(msg.chat_id, f"❌ 处理失败！\n\n错误信息：{error_msg}")
                logger.error(f"处理失败: {error_msg}")

        except Exception as e:
            logger.error(f"处理消息异常: {e}", exc_info=True)
            try:
                adapter = self.platform_manager.get_adapter(msg.platform)
                if adapter and hasattr(adapter, 'send_message'):
                    await adapter.send_message(msg.chat_id, f"❌ 处理异常！\n\n错误信息：{str(e)}")
            except Exception as send_error:
                logger.error(f"发送错误消息失败: {send_error}")

    async def _process_text(self, text: str) -> Dict[str, Any]:
        """处理文本消息"""
        logger.info("开始 AI 总结（文本）")
        success, note_content = await generate_obsidian_note(text)
        if not success:
            return {"success": False, "error": note_content}

        logger.info("写入 Obsidian")
        success, note_info = write_note_to_file(note_content)
        if not success:
            return {
                "success": False,
                "error": note_info.error or "写入 Obsidian 失败"
            }

        # LLM Wiki 自动集成已由 ObsidianTool.write_note_to_file() 内部处理
        # 此处不需要再次调用 wiki.process_note_from_auto()
        logger.info("笔记已由 ObsidianTool 自动处理 LLM Wiki 结构化")

        return {
            "success": True,
            "filename": note_info.filename,
        }

    async def _process_url(self, url: str) -> Dict[str, Any]:
        """处理 URL 消息"""
        logger.info(f"开始处理 URL: {url}")

        web_tool = get_web_tool(timeout=30)
        success, content = await web_tool.download_and_convert(url)

        if not success:
            return {"success": False, "error": f"下载网页失败: {content}"}

        logger.info(f"网页内容下载成功，内容长度: {len(content)} 字符")

        from tools.ai_summary_tool import truncate_content
        content = truncate_content(content, max_chars=5000)

        success, note_content = await generate_obsidian_note(content)
        if not success:
            return {"success": False, "error": note_content}

        logger.info("写入 Obsidian")
        success, note_info = write_note_to_file(note_content)
        if not success:
            return {
                "success": False,
                "error": note_info.error or "写入 Obsidian 失败"
            }

        # LLM Wiki 自动集成已由 ObsidianTool.write_note_to_file() 内部处理
        logger.info("笔记已由 ObsidianTool 自动处理 LLM Wiki 结构化")

        return {
            "success": True,
            "filename": note_info.filename,
        }

    async def _process_file(self, msg: UnifiedMessage, adapter) -> Dict[str, Any]:
        """处理文件消息"""
        if not msg.file_info:
            return {"success": False, "error": "文件信息缺失"}

        logger.info(f"下载文件: {msg.file_info.file_name}")
        temp_manager = get_temp_manager()
        dest_path = temp_manager.get_temp_path(msg.file_info.file_name)

        success, file_size = await adapter.download_file(
            msg.file_info.file_id,
            dest_path
        )

        if not success:
            return {"success": False, "error": "文件下载失败"}

        logger.info("验证文件")
        is_valid, error_msg = validate_file(msg.file_info.file_name, file_size)
        if not is_valid:
            cleanup_file(dest_path)
            return {"success": False, "error": error_msg}

        logger.info("提取文件文本")
        success, text, _ = process_file(dest_path, msg.file_info.file_name)
        cleanup_file(dest_path)

        if not success:
            return {"success": False, "error": text}

        logger.info("AI 总结")
        success, note_content = await generate_obsidian_note(
            text,
            title=msg.file_info.file_name
        )
        if not success:
            return {"success": False, "error": note_content}

        logger.info("写入 Obsidian")
        success, note_info = write_note_to_file(
            note_content,
            title=msg.file_info.file_name
        )
        if not success:
            return {
                "success": False,
                "error": note_info.error or "写入 Obsidian 失败"
            }

        # LLM Wiki 自动集成已由 ObsidianTool.write_note_to_file() 内部处理
        logger.info("笔记已由 ObsidianTool 自动处理 LLM Wiki 结构化")

        return {
            "success": True,
            "filename": note_info.filename,
            "note_title": msg.file_info.file_name,
        }

    async def _process_image(self, msg: UnifiedMessage, adapter) -> Dict[str, Any]:
        """处理图片消息（待实现 OCR）"""
        return {
            "success": False,
            "error": "图片消息暂不支持（OCR 功能开发中）"
        }


def setup_platform_manager(config) -> PlatformManager:
    """设置平台管理器（供 main_multi.py 调用）"""
    from .manager import PlatformManager
    from .feishu_adapter import FeishuAdapter, FeishuConfig as AdapterFeishuConfig
    from .telegram_adapter import TelegramAdapter, TelegramConfig as AdapterTelegramConfig

    platform_manager = PlatformManager()

    if config.feishu and config.feishu.enabled:
        feishu_config = AdapterFeishuConfig(
            enabled=True,
            app_id=config.feishu.app_id,
            app_secret=config.feishu.app_secret,
            verification_token=config.feishu.verification_token,
            encrypt_key=config.feishu.encrypt_key,
            bot_name=config.feishu.bot_name,
            allowed_user_ids=config.feishu.allowed_user_ids,
            poll_interval=config.feishu.poll_interval,
            use_webhook=config.feishu.use_webhook,
            webhook_host=config.feishu.webhook_host,
            webhook_port=config.feishu.webhook_port,
        )
        feishu_adapter = FeishuAdapter(feishu_config)
        platform_manager.register_adapter(PlatformType.FEISHU, feishu_adapter)

    # Telegram 配置
    if config.telegram.enabled and config.telegram.bot_token:
        telegram_config = AdapterTelegramConfig(
            enabled=config.telegram.enabled,
            bot_token=config.telegram.bot_token,
            allowed_user_ids=list(map(str, config.telegram.allowed_user_ids)),  # 转换为 str 列表
            poll_interval=config.telegram.poll_interval,
            poll_timeout=config.telegram.poll_timeout,
            use_proxy=config.telegram.use_proxy,
            proxy_url=config.telegram.proxy_url,
            use_webhook=config.telegram.use_webhook,
            webhook_url=config.telegram.webhook_url,
            webhook_host=config.telegram.webhook_host,
            webhook_port=config.telegram.webhook_port,
            webhook_secret=config.telegram.webhook_secret,
        )
        
        telegram_adapter = TelegramAdapter(telegram_config)
        platform_manager.register_adapter(PlatformType.TELEGRAM, telegram_adapter)

    return platform_manager
