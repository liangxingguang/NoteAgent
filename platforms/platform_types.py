"""
平台类型定义 - 统一的消息类型和数据结构
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime


class PlatformType(Enum):
    """平台类型"""
    TELEGRAM = "telegram"
    FEISHU = "feishu"
    WECHAT = "wechat"  # 预留
    DINGTALK = "dingtalk"  # 预留
    UNKNOWN = "unknown"


class ContentType(Enum):
    """内容类型"""
    TEXT = "text"
    FILE = "file"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    RICH_TEXT = "rich_text"
    URL = "url"
    COMMAND = "command"
    UNKNOWN = "unknown"


@dataclass
class FileInfo:
    """文件信息（平台无关）"""
    file_id: str
    file_name: str
    file_size: int = 0
    mime_type: Optional[str] = None
    file_extension: Optional[str] = None

    def __post_init__(self):
        # 自动推断文件扩展名
        if not self.file_extension and self.file_name:
            parts = self.file_name.split(".")
            if len(parts) > 1:
                self.file_extension = parts[-1].lower()


@dataclass
class UnifiedMessage:
    """统一消息格式 - 所有平台消息转换为此格式"""
    platform: PlatformType
    message_id: str
    chat_id: str
    user_id: str
    user_name: Optional[str] = None
    content_type: ContentType = ContentType.UNKNOWN
    text: Optional[str] = None
    file_info: Optional[FileInfo] = None
    raw_data: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def is_text(self) -> bool:
        """是否是文本消息"""
        return self.content_type == ContentType.TEXT and self.text is not None

    def is_file(self) -> bool:
        """是否是文件消息"""
        return self.content_type in (ContentType.FILE, ContentType.IMAGE, ContentType.VIDEO, ContentType.AUDIO) and self.file_info is not None

    def is_command(self) -> bool:
        """是否是命令消息"""
        return self.content_type == ContentType.COMMAND


@dataclass
class PlatformConfig:
    """平台配置基类"""
    enabled: bool = False
    allowed_user_ids: list[str] = field(default_factory=list)

    def is_allowed(self, user_id: str) -> bool:
        """检查用户是否有权限"""
        if not self.allowed_user_ids:
            return True  # 未配置时默认允许所有
        return str(user_id) in self.allowed_user_ids


@dataclass
class FeishuPlatformConfig(PlatformConfig):
    """飞书平台配置"""
    app_id: str = ""
    app_secret: str = ""
    verification_token: str = ""
    encrypt_key: str = ""
    bot_name: str = "NoteAgents"
    poll_interval: float = 1.0
    use_webhook: bool = False
    webhook_host: str = "0.0.0.0"
    webhook_port: int = 8000


@dataclass
class TelegramPlatformConfig(PlatformConfig):
    """Telegram 平台配置（预留）"""
    bot_token: str = ""
    poll_interval: float = 1.0
    use_proxy: bool = False
    proxy_url: str = ""
