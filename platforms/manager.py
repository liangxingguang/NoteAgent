import asyncio
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass

from .platform_types import PlatformType, UnifiedMessage
from .base import PlatformAdapter

from storage.log_manager import get_logger


logger = get_logger("PlatformManager")


@dataclass
class PlatformStatus:
    """平台状态"""
    platform: PlatformType
    enabled: bool
    connected: bool = False
    message_count: int = 0


class PlatformManager:
    """平台管理器"""
    
    def __init__(self):
        self._adapters: Dict[PlatformType, PlatformAdapter] = {}
        self._message_handlers: List[Callable[[UnifiedMessage], None]] = []
        self._tasks: List[asyncio.Task] = []
    
    def register_adapter(self, platform: PlatformType, adapter: PlatformAdapter):
        """注册平台适配器"""
        self._adapters[platform] = adapter
        # 设置消息处理器
        adapter.set_message_handler(self._handle_message)
        logger.info(f"平台适配器已注册: {platform.value}")
    
    def add_message_handler(self, handler: Callable[[UnifiedMessage], None]):
        """添加消息处理器"""
        self._message_handlers.append(handler)
    
    async def initialize_all(self) -> bool:
        """初始化所有平台"""
        success = True
        
        for platform, adapter in self._adapters.items():
            try:
                logger.info(f"正在初始化平台: {platform.value}")
                init_success = await adapter.initialize()
                if init_success:
                    logger.info(f"平台初始化成功: {platform.value}")
                else:
                    logger.error(f"平台初始化失败: {platform.value}")
                    success = False
            except Exception as e:
                logger.error(f"平台初始化异常: {platform.value} - {e}", exc_info=True)
                success = False
        
        return success
    
    async def start_all(self):
        """启动所有平台监听"""
        for platform, adapter in self._adapters.items():
            if adapter.config.enabled:
                task = asyncio.create_task(adapter.start_listening())
                self._tasks.append(task)
                logger.info(f"平台已启动: {platform.value}")
    
    async def stop_all(self):
        """停止所有平台"""
        # 先停止适配器
        for platform, adapter in self._adapters.items():
            try:
                await adapter.stop_listening()
                logger.info(f"平台已停止: {platform.value}")
            except Exception as e:
                logger.error(f"平台停止异常: {platform.value} - {e}", exc_info=True)
        
        # 取消所有任务
        for task in self._tasks:
            if not task.done():
                task.cancel()
        
        # 等待任务结束
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        self._tasks.clear()
    
    def get_status(self) -> List[PlatformStatus]:
        """获取所有平台状态"""
        status_list = []
        for platform, adapter in self._adapters.items():
            status = PlatformStatus(
                platform=platform,
                enabled=adapter.config.enabled
            )
            status_list.append(status)
        return status_list
    
    def get_adapter(self, platform: PlatformType) -> Optional[PlatformAdapter]:
        """获取指定平台的适配器"""
        return self._adapters.get(platform)

    def get_enabled_platforms(self) -> List[PlatformType]:
        """获取已启用平台的列表"""
        enabled = []
        for platform, adapter in self._adapters.items():
            if adapter.config.enabled:
                enabled.append(platform)
        return enabled

    def _handle_message(self, message: UnifiedMessage):
        """处理接收到的消息（内部使用）"""
        logger.debug(f"收到来自 {message.platform.value} 的消息")
        
        for handler in self._message_handlers:
            try:
                handler(message)
            except Exception as e:
                logger.error(f"消息处理器异常: {e}", exc_info=True)