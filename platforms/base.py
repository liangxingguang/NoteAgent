from abc import ABC, abstractmethod
from typing import Optional, Tuple, Callable
from .platform_types import UnifiedMessage, PlatformConfig


class PlatformAdapter(ABC):
    """平台适配器抽象基类"""
    
    def __init__(self, config: PlatformConfig):
        self.config = config
        self._message_handler: Optional[Callable[[UnifiedMessage], None]] = None
    
    @abstractmethod
    async def initialize(self) -> bool:
        """初始化平台连接
        
        Returns:
            是否初始化成功
        """
        pass
    
    @abstractmethod
    async def start_listening(self):
        """开始监听消息"""
        pass
    
    @abstractmethod
    async def stop_listening(self):
        """停止监听消息"""
        pass
    
    @abstractmethod
    async def send_message(
        self,
        chat_id: str,
        text: str,
        **kwargs
    ) -> bool:
        """发送消息

        Args:
            chat_id: 聊天 ID
            text: 消息内容
            **kwargs: 平台特定参数

        Returns:
            是否发送成功
        """
        pass

    async def reply_message(
        self,
        message_id: str,
        text: str,
        **kwargs
    ) -> bool:
        """回复消息

        Args:
            message_id: 原消息 ID
            text: 回复内容
            **kwargs: 平台特定参数

        Returns:
            是否发送成功
        """
        raise NotImplementedError("该平台不支持回复消息功能")
    
    @abstractmethod
    async def download_file(
        self,
        file_id: str,
        dest_path: str
    ) -> Tuple[bool, int]:
        """下载文件
        
        Args:
            file_id: 文件 ID
            dest_path: 目标路径
            
        Returns:
            (是否成功, 文件大小)
        """
        pass
    
    def set_message_handler(self, handler: Callable[[UnifiedMessage], None]):
        """设置消息处理器
        
        Args:
            handler: 消息处理回调函数
        """
        self._message_handler = handler
    
    def _notify_message(self, message: UnifiedMessage):
        """通知接收到消息（内部使用）"""
        if self._message_handler:
            self._message_handler(message)