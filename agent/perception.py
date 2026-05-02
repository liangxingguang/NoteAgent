"""感知模块 - 消息接收、解析、权限验证"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from config import get_config
from storage.context_cache import get_user_session_cache
from storage.log_manager import get_logger
from tools.tg_tool import (
    extract_message_info,
    send_message,
    MessageInfo,
    build_permission_denied_message,
)

logger = get_logger("Perception")


class MessageType(Enum):
    """消息类型"""
    TEXT = "text"
    DOCUMENT = "document"
    PHOTO = "photo"
    UNKNOWN = "unknown"


@dataclass
class PerceivedMessage:
    """感知到的消息"""
    info: MessageInfo
    msg_type: MessageType
    is_authorized: bool
    content: Optional[str] = None  # 文本内容或文件路径


class PerceptionModule:
    """感知模块"""

    def __init__(self):
        """初始化感知模块"""
        self.config = get_config()
        self.session_cache = get_user_session_cache()

    def check_permission(self, user_id: int) -> bool:
        """检查用户权限

        Args:
            user_id: 用户ID

        Returns:
            是否有权限
        """
        # 如果没有配置允许的用户，默认允许所有（不推荐）
        if not self.config.allowed_user_ids:
            logger.warning("未配置ALLOWED_USER_IDS，默认允许所有用户")
            return True

        is_allowed = user_id in self.config.allowed_user_ids
        if not is_allowed:
            logger.warning(f"用户权限验证失败: {user_id}")

        return is_allowed

    async def process_update(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> Optional[PerceivedMessage]:
        """处理Update对象

        Args:
            update: Telegram Update对象
            context: 上下文对象

        Returns:
            感知到的消息，如果无法处理则返回None
        """
        # 提取消息信息
        msg_info = extract_message_info(update)
        if not msg_info:
            logger.debug("无法提取消息信息")
            return None

        # 检查权限
        is_authorized = self.check_permission(msg_info.user_id)

        # 如果没有权限，发送拒绝消息并返回
        if not is_authorized:
            await send_message(
                context,
                msg_info.chat_id,
                build_permission_denied_message(msg_info.user_id),
            )
            return PerceivedMessage(
                info=msg_info,
                msg_type=MessageType.UNKNOWN,
                is_authorized=False,
            )

        # 判断消息类型
        msg_type = self._determine_message_type(msg_info)

        # 构建感知消息
        perceived = PerceivedMessage(
            info=msg_info,
            msg_type=msg_type,
            is_authorized=True,
        )

        # 根据类型设置内容
        if msg_type == MessageType.TEXT:
            perceived.content = msg_info.text

        logger.info(f"感知到消息: user={msg_info.user_id}, type={msg_type.value}")

        return perceived

    def _determine_message_type(self, msg_info: MessageInfo) -> MessageType:
        """判断消息类型

        Args:
            msg_info: 消息信息

        Returns:
            消息类型
        """
        if msg_info.is_file:
            if msg_info.file_type == "document":
                return MessageType.DOCUMENT
            elif msg_info.file_type == "photo":
                return MessageType.PHOTO

        if msg_info.text:
            return MessageType.TEXT

        return MessageType.UNKNOWN


# 全局感知模块实例
_perception_module: Optional[PerceptionModule] = None


def init_perception_module() -> PerceptionModule:
    """初始化感知模块"""
    global _perception_module
    _perception_module = PerceptionModule()
    return _perception_module


def get_perception_module() -> PerceptionModule:
    """获取感知模块实例"""
    if _perception_module is None:
        raise RuntimeError("感知模块未初始化，请先调用 init_perception_module()")
    return _perception_module
