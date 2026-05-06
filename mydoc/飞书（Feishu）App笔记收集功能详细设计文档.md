# 飞书（Feishu）App笔记收集功能详细设计文档

# 1. 文档概述

## 1.1 文档目的

本文档旨在详细设计 NoteAgents 系统的飞书（Feishu/Lark）App 集成功能，实现「飞书消息/文件收集→AI 总结→Obsidian 自动入库」的自动化链路，与现有 Telegram 集成平行共存，为用户提供多平台内容收集能力。

## 1.2 核心需求

- **多平台支持**：在保持现有 Telegram 功能完整的前提下，新增飞书作为内容收集入口
- **功能对等**：飞书集成应支持与 Telegram 相同的内容类型（文本、链接、文件）
- **架构复用**：复用现有的 AI 总结、Obsidian 入库、异常处理等核心业务逻辑
- **独立配置**：支持独立启用/禁用飞书功能，独立配置权限控制
- **用户体验**：提供与 Telegram 版本一致的用户交互体验

## 1.3 设计原则

1. **平台抽象**：设计统一的消息接入接口，Telegram 和飞书作为不同实现
2. **业务复用**：业务逻辑层保持不变，仅扩展接入层
3. **配置驱动**：通过配置文件控制平台启用状态
4. **渐进式集成**：先实现核心功能，再扩展高级特性
5. **向后兼容**：不破坏现有 Telegram 功能

# 2. 整体架构设计

## 2.1 扩展后的分层架构

系统在原有 5 层架构基础上，扩展用户交互层和接入层以支持多平台：

```
┌─────────────────────────────────────────────────────────────┐
│                    用户交互层 (扩展)                          │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  Telegram 客户端  │         │   飞书客户端      │         │
│  └──────────────────┘         └──────────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    接入层 (重构/扩展)                        │
│  ┌──────────────────────┐    ┌──────────────────────┐      │
│  │  Telegram 接入模块   │    │   飞书接入模块       │      │
│  │  (保持不变)          │    │   (新增)             │      │
│  └──────────────────────┘    └──────────────────────┘      │
│  ┌───────────────────────────────────────────────────┐     │
│  │         统一消息抽象层 (新增)                       │     │
│  │  - 通用消息格式定义                                │     │
│  │  - 平台适配器接口                                  │     │
│  │  - 权限校验统一处理                                │     │
│  └───────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    业务逻辑层 (复用)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │感知模块  │ │决策模块  │ │任务调度  │ │异常处理  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    数据存储层 (复用)                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    基础设施层 (扩展)                         │
│  - 新增飞书 OpenAPI 调用能力                                │
│  - 飞书事件订阅机制                                         │
└─────────────────────────────────────────────────────────────┘
```

## 2.2 关键设计决策

### 2.2.1 平台适配器模式

采用适配器模式将不同平台的消息转换为统一格式：

```python
# 统一消息抽象
@dataclass
class UnifiedMessage:
    platform: PlatformType  # TELEGRAM 或 FEISHU
    message_id: str
    chat_id: str
    user_id: str
    user_name: Optional[str]
    content_type: ContentType  # TEXT, FILE, URL
    text: Optional[str]
    file_info: Optional[FileInfo]
    timestamp: datetime

# 平台适配器接口
class PlatformAdapter(ABC):
    @abstractmethod
    async def receive_message(self) -> Optional[UnifiedMessage]:
        pass
    
    @abstractmethod
    async def send_message(self, chat_id: str, text: str):
        pass
    
    @abstractmethod
    async def download_file(self, file_id: str) -> Tuple[bool, str, int]:
        pass
```

### 2.2.2 飞书接入方式选择

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **Webhook（事件订阅）** | 实时性好，官方推荐 | 需要公网 IP/域名，部署复杂 | ⭐⭐⭐ |
| **轮询（定期获取）** | 无需公网 IP，部署简单 | 实时性稍差，有 API 调用频率限制 | ⭐⭐⭐⭐⭐ |
| **飞书 Stream 模式** | 实时，WebSocket | 较新，文档较少 | ⭐⭐ |

**推荐方案**：初期采用**轮询模式**，与 Telegram 保持一致的部署模型，降低部署复杂度。后续可支持 Webhook 模式作为可选配置。

### 2.2.3 飞书应用类型选择

| 类型 | 适用场景 | 本项目适配 |
|------|----------|-----------|
| **自建应用（企业内部）** | 企业内部使用 | ✅ 适合个人使用 |
| **应用商店应用** | 公开分发 | ❌ 审核复杂 |

**推荐**：自建应用（企业内部开发）模式。

# 3. 飞书平台集成详细设计

## 3.1 飞书应用配置

### 3.1.1 需要获取的配置项

```env
# === 飞书 Configuration ===
FEISHU_ENABLED=false
FEISHU_APP_ID=cli_xxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxx
FEISHU_VERIFICATION_TOKEN=xxxxxxxxxx
FEISHU_ENCRYPT_KEY=xxxxxxxxxx
FEISHU_BOT_NAME=NoteAgents
FEISHU_ALLOWED_USER_IDS=ou_xxxxxxxxxx,ou_yyyyyyyyyy
```

### 3.1.2 飞书应用权限配置

需要在飞书开放平台申请以下权限：

| 权限名称 | 权限描述 | 用途 |
|----------|----------|------|
| `im:message` | 获取与发送单聊、群聊消息 | 接收用户消息 |
| `im:message.group_at_msg` | 获取群组中@Bot的消息 | 群聊场景 |
| `im:message.group_at_msg:readonly` | 读取群组@Bot消息 | 群聊场景 |
| `im:resource` | 下载与上传消息中的资源文件 | 下载文件 |
| `contact:user.id:readonly` | 获取用户 ID | 权限校验 |

## 3.2 飞书接入模块设计

### 3.2.1 文件结构

```
NoteAgents/
├── platforms/                    # 新增：多平台支持目录
│   ├── __init__.py
│   ├── base.py                  # 平台适配器基类
│   ├── platform_types.py        # 类型定义
│   ├── telegram_adapter.py      # Telegram 适配器（从现有代码迁移）
│   └── feishu_adapter.py        # 飞书适配器（新增）
├── tools/
│   ├── tg_tool.py               # 保持不变
│   └── feishu_tool.py           # 新增：飞书工具
├── config/
│   └── config.py                # 扩展配置
└── main.py                      # 重构：支持多平台启动
```

### 3.2.2 核心类型定义 (`platforms/platform_types.py`)

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime


class PlatformType(Enum):
    """平台类型"""
    TELEGRAM = "telegram"
    FEISHU = "feishu"


class ContentType(Enum):
    """内容类型"""
    TEXT = "text"
    FILE = "file"
    IMAGE = "image"
    RICH_TEXT = "rich_text"
    UNKNOWN = "unknown"


@dataclass
class FileInfo:
    """文件信息（平台无关）"""
    file_id: str
    file_name: str
    file_size: int
    mime_type: Optional[str] = None
    file_extension: Optional[str] = None


@dataclass
class UnifiedMessage:
    """统一消息格式"""
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


@dataclass
class PlatformConfig:
    """平台配置基类"""
    enabled: bool = False
    allowed_user_ids: list[str] = field(default_factory=list)
```

### 3.2.3 平台适配器基类 (`platforms/base.py`)

```python
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
```

### 3.2.4 飞书适配器实现 (`platforms/feishu_adapter.py`)

```python
import asyncio
import time
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

import requests
import aiohttp

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
    poll_interval: float = 1.0  # 轮询间隔（秒）


class FeishuAdapter(PlatformAdapter):
    """飞书平台适配器"""
    
    def __init__(self, config: FeishuConfig):
        super().__init__(config)
        self.config: FeishuConfig = config
        self._tenant_access_token: Optional[str] = None
        self._token_expire_time: float = 0
        self._session: Optional[aiohttp.ClientSession] = None
        self._running: bool = False
        self._last_processed_timestamp: int = 0
        
    async def initialize(self) -> bool:
        """初始化飞书连接"""
        try:
            self._session = aiohttp.ClientSession()
            # 获取 tenant_access_token
            success = await self._refresh_token()
            if not success:
                logger.error("无法获取飞书访问令牌")
                return False
            
            # 测试连接
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
                # 检查令牌是否需要刷新
                await self._check_and_refresh_token()
                
                # 获取消息
                messages = await self._fetch_new_messages()
                
                # 处理消息
                for msg in messages:
                    unified_msg = self._convert_to_unified_message(msg)
                    if unified_msg:
                        self._notify_message(unified_msg)
                
                # 等待下一次轮询
                await asyncio.sleep(self.config.poll_interval)
                
            except Exception as e:
                logger.error(f"飞书消息监听异常: {e}", exc_info=True)
                await asyncio.sleep(2)  # 出错时稍长时间重试
    
    async def stop_listening(self):
        """停止监听"""
        self._running = False
        if self._session:
            await self._session.close()
        logger.info("飞书适配器已停止监听")
    
    async def send_message(
        self,
        chat_id: str,
        text: str,
        **kwargs
    ) -> bool:
        """发送消息"""
        try:
            url = "https://open.feishu.cn/open-apis/im/v1/messages"
            
            headers = {
                "Authorization": f"Bearer {self._tenant_access_token}",
                "Content-Type": "application/json"
            }
            
            # 构造富文本消息（支持 Markdown 格式）
            content = {
                "msg_type": "text",
                "content": {
                    "text": text
                }
            }
            
            # 群聊或单聊
            if chat_id.startswith("oc_"):
                # 群聊
                content["receive_id_type"] = "chat_id"
            else:
                # 单聊
                content["receive_id_type"] = "user_id"
            
            content["receive_id"] = chat_id
            
            async with self._session.post(url, headers=headers, json=content) as resp:
                result = await resp.json()
                if result.get("code") == 0:
                    logger.debug(f"飞书消息发送成功: {chat_id}")
                    return True
                else:
                    logger.error(f"飞书消息发送失败: {result}")
                    return False
                    
        except Exception as e:
            logger.error(f"飞书消息发送异常: {e}", exc_info=True)
            return False
    
    async def download_file(
        self,
        file_key: str,
        dest_path: str
    ) -> Tuple[bool, int]:
        """下载文件"""
        try:
            url = f"https://open.feishu.cn/open-apis/im/v1/files/{file_key}"
            
            headers = {
                "Authorization": f"Bearer {self._tenant_access_token}"
            }
            
            async with self._session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    with open(dest_path, "wb") as f:
                        f.write(data)
                    file_size = len(data)
                    logger.info(f"飞书文件下载成功: {dest_path} ({file_size}字节)")
                    return True, file_size
                else:
                    logger.error(f"飞书文件下载失败: {resp.status}")
                    return False, 0
                    
        except Exception as e:
            logger.error(f"飞书文件下载异常: {e}", exc_info=True)
            return False, 0
    
    # ============ 内部方法 ============
    
    async def _refresh_token(self) -> bool:
        """刷新访问令牌"""
        try:
            url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
            
            data = {
                "app_id": self.config.app_id,
                "app_secret": self.config.app_secret
            }
            
            async with self._session.post(url, json=data) as resp:
                result = await resp.json()
                if result.get("code") == 0:
                    self._tenant_access_token = result["tenant_access_token"]
                    # 提前 5 分钟过期
                    self._token_expire_time = time.time() + result["expire"] - 300
                    logger.info("飞书令牌刷新成功")
                    return True
                else:
                    logger.error(f"飞书令牌获取失败: {result}")
                    return False
                    
        except Exception as e:
            logger.error(f"飞书令牌刷新异常: {e}", exc_info=True)
            return False
    
    async def _check_and_refresh_token(self):
        """检查并在需要时刷新令牌"""
        if time.time() >= self._token_expire_time:
            await self._refresh_token()
    
    async def _test_connection(self) -> bool:
        """测试连接"""
        try:
            # 获取机器人信息
            url = "https://open.feishu.cn/open-apis/bot/v3/info"
            
            headers = {
                "Authorization": f"Bearer {self._tenant_access_token}"
            }
            
            async with self._session.get(url, headers=headers) as resp:
                result = await resp.json()
                return result.get("code") == 0
                
        except Exception as e:
            logger.error(f"飞书连接测试异常: {e}", exc_info=True)
            return False
    
    async def _fetch_new_messages(self) -> list[Dict[str, Any]]:
        """获取新消息
        
        注：飞书没有直接的"获取消息列表"API，需要使用事件订阅
        此处采用简化方案：实际生产建议使用 Webhook 事件订阅
        """
        # TODO: 实现事件订阅或使用飞书的消息同步机制
        # 临时返回空列表，实际实现需接入飞书事件系统
        return []
    
    def _convert_to_unified_message(self, feishu_msg: Dict[str, Any]) -> Optional[UnifiedMessage]:
        """将飞书消息转换为统一消息格式"""
        try:
            # 解析飞书消息格式
            # 参考：https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/im-v1/message/events/receive
            header = feishu_msg.get("header", {})
            event = feishu_msg.get("event", {})
            message = event.get("message", {})
            sender = event.get("sender", {})
            
            message_id = message.get("message_id", "")
            chat_id = message.get("chat_id", "")
            user_id = sender.get("sender_id", {}).get("open_id", "")
            user_name = sender.get("sender_id", {}).get("name", "")
            
            # 判断消息类型
            msg_type = message.get("msg_type", "")
            content = message.get("body", {}).get("content", {})
            
            content_type = ContentType.UNKNOWN
            text = None
            file_info = None
            
            if msg_type == "text":
                content_type = ContentType.TEXT
                text = content.get("text", "")
                
            elif msg_type == "file":
                content_type = ContentType.FILE
                file_info = FileInfo(
                    file_id=content.get("file_key", ""),
                    file_name=content.get("file_name", ""),
                    file_size=content.get("file_size", 0)
                )
                
            elif msg_type == "image":
                content_type = ContentType.IMAGE
                file_info = FileInfo(
                    file_id=content.get("image_key", ""),
                    file_name=f"image_{message_id[:8]}.png",
                    file_size=0
                )
            
            # 构造统一消息
            return UnifiedMessage(
                platform=PlatformType.FEISHU,
                message_id=message_id,
                chat_id=chat_id,
                user_id=user_id,
                user_name=user_name,
                content_type=content_type,
                text=text,
                file_info=file_info,
                raw_data=feishu_msg
            )
            
        except Exception as e:
            logger.error(f"飞书消息转换失败: {e}", exc_info=True)
            return None
```

## 3.3 配置模块扩展

### 3.3.1 配置类扩展 (`config/config.py`)

```python
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FeishuConfig:
    """飞书配置"""
    enabled: bool = False
    app_id: str = ""
    app_secret: str = ""
    verification_token: str = ""
    encrypt_key: str = ""
    bot_name: str = "NoteAgents"
    allowed_user_ids: list[str] = field(default_factory=list)
    poll_interval: float = 1.0


@dataclass
class Config:
    # ... 现有配置 ...
    
    # 飞书配置
    feishu: FeishuConfig = field(default_factory=FeishuConfig)
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "Config":
        # ... 现有配置加载 ...
        
        # 加载飞书配置
        feishu_enabled_str = os.getenv("FEISHU_ENABLED", "false").lower()
        feishu_enabled = feishu_enabled_str in ("true", "1", "yes")
        
        feishu_allowed_user_ids_str = os.getenv("FEISHU_ALLOWED_USER_IDS", "")
        feishu_allowed_user_ids = []
        if feishu_allowed_user_ids_str:
            feishu_allowed_user_ids = [
                uid.strip() for uid in feishu_allowed_user_ids_str.split(",") if uid.strip()
            ]
        
        feishu_config = FeishuConfig(
            enabled=feishu_enabled,
            app_id=os.getenv("FEISHU_APP_ID", ""),
            app_secret=os.getenv("FEISHU_APP_SECRET", ""),
            verification_token=os.getenv("FEISHU_VERIFICATION_TOKEN", ""),
            encrypt_key=os.getenv("FEISHU_ENCRYPT_KEY", ""),
            bot_name=os.getenv("FEISHU_BOT_NAME", "NoteAgents"),
            allowed_user_ids=feishu_allowed_user_ids,
            poll_interval=float(os.getenv("FEISHU_POLL_INTERVAL", "1.0")),
        )
        
        return cls(
            # ... 现有参数 ...
            feishu=feishu_config,
        )
    
    def validate(self) -> tuple[bool, str]:
        # ... 现有验证 ...
        
        # 验证飞书配置
        if self.feishu.enabled:
            if not self.feishu.app_id:
                return False, "FEISHU_ENABLED 为 true 但 FEISHU_APP_ID 未配置"
            if not self.feishu.app_secret:
                return False, "FEISHU_ENABLED 为 true 但 FEISHU_APP_SECRET 未配置"
        
        return True, ""
```

### 3.3.2 环境变量示例 (`config/.env.example` 扩展)

在现有基础上添加：

```env
# === 飞书 Configuration ===
# 是否启用飞书功能
FEISHU_ENABLED=false

# 飞书应用凭证（从飞书开放平台获取）
FEISHU_APP_ID=cli_xxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxx

# 飞书事件订阅配置（Webhook 模式需要）
FEISHU_VERIFICATION_TOKEN=xxxxxxxxxxxxx
FEISHU_ENCRYPT_KEY=xxxxxxxxxxxxx

# 机器人名称
FEISHU_BOT_NAME=NoteAgents

# 飞书允许的用户ID列表（open_id，逗号分隔）
# 获取方法：给飞书机器人发消息，查看日志中的 user_id
FEISHU_ALLOWED_USER_IDS=ou_xxxxxxxxxxxxx,ou_yyyyyyyyyyyyy

# 飞书轮询间隔（秒）
FEISHU_POLL_INTERVAL=1.0
```

## 3.4 主程序重构

### 3.4.1 多平台协调器设计

新增 `platforms/manager.py`：

```python
import asyncio
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass

from .platform_types import PlatformType, UnifiedMessage
from .base import PlatformAdapter
from .feishu_adapter import FeishuAdapter, FeishuConfig
# from .telegram_adapter import TelegramAdapter  # 后续迁移

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
    
    def _handle_message(self, message: UnifiedMessage):
        """处理接收到的消息（内部使用）"""
        logger.debug(f"收到来自 {message.platform.value} 的消息")
        
        for handler in self._message_handlers:
            try:
                handler(message)
            except Exception as e:
                logger.error(f"消息处理器异常: {e}", exc_info=True)
```

### 3.4.2 主程序重构 (`main.py`)

重构后的主程序结构：

```python
# ... 现有导入 ...

from platforms.manager import PlatformManager
from platforms.platform_types import PlatformType, UnifiedMessage, ContentType
from platforms.feishu_adapter import FeishuAdapter, FeishuConfig


logger = get_logger("Main")


class NoteAgentsApp:
    """NoteAgents 主应用"""
    
    def __init__(self):
        self.config = get_config()
        self.platform_manager = PlatformManager()
        self.running = True
        
        # 初始化信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理"""
        logger.info(f"收到终止信号 [{signum}]，正在优雅关闭...")
        self.running = False
    
    async def initialize(self):
        """初始化应用"""
        # 验证配置
        is_valid, error_msg = self.config.validate()
        if not is_valid:
            raise RuntimeError(f"配置错误: {error_msg}")
        
        # 初始化存储
        init_log_manager(self.config.log_dir, self.config.log_level)
        init_temp_manager(self.config.temp_dir)
        init_context_cache()
        init_user_session_cache()
        
        # 初始化核心模块
        init_perception_module()
        init_decision_module()
        init_task_scheduler()
        init_exception_handler()
        init_github()
        
        # 初始化平台适配器
        self._setup_platforms()
        
        # 初始化平台
        success = await self.platform_manager.initialize_all()
        if not success:
            raise RuntimeError("平台初始化失败")
        
        # 注册消息处理器
        self.platform_manager.add_message_handler(self._process_unified_message)
    
    def _setup_platforms(self):
        """设置平台适配器"""
        # 飞书适配器
        if self.config.feishu.enabled:
            feishu_config = FeishuConfig(
                enabled=True,
                app_id=self.config.feishu.app_id,
                app_secret=self.config.feishu.app_secret,
                verification_token=self.config.feishu.verification_token,
                encrypt_key=self.config.feishu.encrypt_key,
                bot_name=self.config.feishu.bot_name,
                allowed_user_ids=self.config.feishu.allowed_user_ids,
                poll_interval=self.config.feishu.poll_interval,
            )
            feishu_adapter = FeishuAdapter(feishu_config)
            self.platform_manager.register_adapter(PlatformType.FEISHU, feishu_adapter)
        
        # TODO: Telegram 适配器迁移
        # 保持现有 Telegram 功能暂时不变
    
    async def _process_unified_message(self, message: UnifiedMessage):
        """处理统一消息格式"""
        # 根据平台类型选择处理方式
        if message.platform == PlatformType.FEISHU:
            await self._process_feishu_message(message)
        elif message.platform == PlatformType.TELEGRAM:
            # 现有处理逻辑
            pass
    
    async def _process_feishu_message(self, message: UnifiedMessage):
        """处理飞书消息"""
        try:
            # 1. 权限校验
            if not self._check_feishu_permission(message.user_id):
                logger.warning(f"飞书用户无权限: {message.user_id}")
                return
            
            # 2. 获取飞书适配器
            feishu_adapter = self.platform_manager.get_adapter(PlatformType.FEISHU)
            if not feishu_adapter:
                return
            
            # 3. 发送处理中消息
            await feishu_adapter.send_message(message.chat_id, "⏳ 正在处理中，请稍候...")
            
            # 4. 根据内容类型处理
            result = None
            
            if message.content_type == ContentType.TEXT:
                # 检查是否是 URL
                from tools.ai_summary_tool import is_url
                if is_url(message.text.strip()):
                    result = await self._process_url(message.text)
                else:
                    result = await self._process_text(message.text)
                    
            elif message.content_type == ContentType.FILE:
                result = await self._process_file(message, feishu_adapter)
            
            # 5. 发送结果消息
            if result and result.success:
                filename = result.data.get("filename", "未知文件") if result.data else "未知文件"
                success_msg = f"✅ 处理成功！\n\n💾 保存文件：{filename}\n\n笔记已保存到你的 Obsidian 知识库！"
                await feishu_adapter.send_message(message.chat_id, success_msg)
                logger.info(f"飞书消息处理完成: {filename}")
            else:
                error_msg = result.error if result else "处理失败"
                await feishu_adapter.send_message(message.chat_id, f"❌ 处理失败！\n\n错误信息：{error_msg}")
                logger.error(f"飞书消息处理失败: {error_msg}")
                
        except Exception as e:
            logger.error(f"飞书消息处理异常: {e}", exc_info=True)
            try:
                feishu_adapter = self.platform_manager.get_adapter(PlatformType.FEISHU)
                if feishu_adapter:
                    await feishu_adapter.send_message(
                        message.chat_id,
                        f"❌ 处理异常！\n\n错误信息：{str(e)}"
                    )
            except:
                pass
    
    def _check_feishu_permission(self, user_id: str) -> bool:
        """检查飞书用户权限"""
        if not self.config.feishu.allowed_user_ids:
            logger.warning("飞书未配置允许用户，默认允许所有")
            return True
        
        return user_id in self.config.feishu.allowed_user_ids
    
    async def _process_text(self, text: str):
        """处理文本消息（复用现有逻辑）"""
        success, note_content = await generate_obsidian_note(text)
        if not success:
            return TaskResult(success=False, error=note_content)
        
        success, note_info = write_note_to_file(note_content)
        if not success:
            return TaskResult(success=False, error=note_info.error or "写入 Obsidian 失败")
        
        return TaskResult(
            success=True,
            data={
                "note_content": note_content,
                "note_info": note_info,
                "filename": note_info.filename,
            }
        )
    
    async def _process_url(self, url: str):
        """处理 URL 消息（复用现有逻辑）"""
        web_tool = get_web_tool(timeout=30)
        success, content = await web_tool.download_and_convert(url)
        
        if not success:
            return TaskResult(success=False, error=f"下载网页失败: {content}")
        
        from tools.ai_summary_tool import truncate_content
        content = truncate_content(content, max_chars=5000)
        
        success, note_content = await generate_obsidian_note(content)
        if not success:
            return TaskResult(success=False, error=note_content)
        
        success, note_info = write_note_to_file(note_content)
        if not success:
            return TaskResult(success=False, error=note_info.error or "写入 Obsidian 失败")
        
        return TaskResult(
            success=True,
            data={
                "note_content": note_content,
                "note_info": note_info,
                "filename": note_info.filename,
            }
        )
    
    async def _process_file(self, message: UnifiedMessage, feishu_adapter):
        """处理文件消息"""
        if not message.file_info:
            return TaskResult(success=False, error="文件信息缺失")
        
        # 1. 下载文件
        temp_manager = get_temp_manager()
        dest_path = temp_manager.get_temp_path(message.file_info.file_name)
        
        success, file_size = await feishu_adapter.download_file(
            message.file_info.file_id,
            dest_path
        )
        
        if not success:
            return TaskResult(success=False, error="文件下载失败")
        
        # 2. 验证文件
        is_valid, error_msg = validate_file(message.file_info.file_name, file_size)
        if not is_valid:
            cleanup_file(dest_path)
            return TaskResult(success=False, error=error_msg)
        
        # 3. 提取文本
        success, text, _ = process_file(dest_path, message.file_info.file_name)
        cleanup_file(dest_path)
        
        if not success:
            return TaskResult(success=False, error=text)
        
        # 4. AI 总结
        success, note_content = await generate_obsidian_note(text, title=message.file_info.file_name)
        if not success:
            return TaskResult(success=False, error=note_content)
        
        # 5. 写入 Obsidian
        success, note_info = write_note_to_file(note_content, title=message.file_info.file_name)
        if not success:
            return TaskResult(success=False, error=note_info.error or "写入 Obsidian 失败")
        
        return TaskResult(
            success=True,
            data={
                "note_content": note_content,
                "note_info": note_info,
                "filename": note_info.filename,
            }
        )
    
    async def run(self):
        """运行应用"""
        # 初始化
        await self.initialize()
        
        # 启动平台监听
        await self.platform_manager.start_all()
        
        # 启动 Telegram（保持现有逻辑）
        # TODO: 后续将 Telegram 迁移到适配器模式
        telegram_task = asyncio.create_task(self._run_telegram())
        
        logger.info("NoteAgents 启动成功")
        
        # 主循环
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("收到退出信号")
        finally:
            # 停止所有平台
            await self.platform_manager.stop_all()
            telegram_task.cancel()
            try:
                await telegram_task
            except asyncio.CancelledError:
                pass
    
    async def _run_telegram(self):
        """运行 Telegram Bot（保持现有逻辑）"""
        # 现有 Telegram 启动逻辑
        config = get_config()
        application = build_tg_application(config)
        
        # 注册现有 handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("push", push_command))
        application.add_handler(CommandHandler("pull", pull_command))
        application.add_handler(CommandHandler("github", github_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(MessageHandler(filters.Document.ALL, handle_message))
        
        # 运行
        poll_interval = getattr(config, "poll_interval", 1)
        timeout = getattr(config, "poll_timeout", 20)
        
        await application.run_polling(
            poll_interval=poll_interval,
            timeout=timeout,
            drop_pending_updates=True,
            close_loop=False
        )


def main():
    print("=" * 60)
    print("  NoteAgents - 多平台 AI 笔记自动收集系统")
    print("=" * 60)
    
    app = NoteAgentsApp()
    
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        logger.info("应用已停止")
    except Exception as e:
        logger.error(f"运行异常: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

# 4. 飞书事件订阅（Webhook 模式）详细设计

## 4.1 Webhook 模式架构

作为轮询模式的升级，Webhook 模式提供更好的实时性：

```
飞书服务器 → Nginx/公网服务器 → NoteAgents Webhook 服务
                (可选反向代理)
```

## 4.2 Webhook 服务实现

新增 `platforms/feishu_webhook.py`：

```python
from aiohttp import web, Request
import json
import hmac
import hashlib
import base64
from typing import Optional, Dict, Any

from storage.log_manager import get_logger


logger = get_logger("FeishuWebhook")


class FeishuWebhookServer:
    """飞书 Webhook 服务"""
    
    def __init__(self, config: FeishuConfig, message_callback):
        self.config = config
        self.message_callback = message_callback
        self.app = web.Application()
        self._setup_routes()
    
    def _setup_routes(self):
        """设置路由"""
        self.app.router.add_post("/feishu/webhook", self._handle_webhook)
    
    async def _handle_webhook(self, request: Request):
        """处理 Webhook 请求"""
        try:
            # 读取请求体
            body = await request.read()
            data = json.loads(body.decode("utf-8"))
            
            # 验证请求（加密模式）
            if self.config.encrypt_key:
                if not self._verify_request(data, body):
                    return web.json_response({"code": 403, "msg": "验证失败"}, status=403)
            
            # 处理 URL 验证
            if data.get("type") == "url_verification":
                return web.json_response({
                    "challenge": data.get("challenge")
                })
            
            # 处理事件
            if data.get("header", {}).get("event_type") == "im.message.receive_v1":
                await self._handle_message_event(data)
            
            return web.json_response({"code": 0, "msg": "success"})
            
        except Exception as e:
            logger.error(f"Webhook 处理异常: {e}", exc_info=True)
            return web.json_response({"code": 500, "msg": "internal error"}, status=500)
    
    def _verify_request(self, data: Dict[str, Any], body: bytes) -> bool:
        """验证请求来源"""
        try:
            # 验证 verification_token
            token = data.get("header", {}).get("token")
            if token != self.config.verification_token:
                return False
            
            return True
        except Exception as e:
            logger.error(f"请求验证失败: {e}", exc_info=True)
            return False
    
    async def _handle_message_event(self, event_data: Dict[str, Any]):
        """处理消息事件"""
        try:
            # 转换为统一消息格式
            # ... 转换逻辑同前 ...
            # 调用回调
            if self.message_callback:
                pass
        except Exception as e:
            logger.error(f"消息事件处理异常: {e}", exc_info=True)
    
    async def start(self, host: str = "0.0.0.0", port: int = 8000):
        """启动 Webhook 服务"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        logger.info(f"飞书 Webhook 服务已启动: {host}:{port}")
```

# 5. 分阶段实施计划

## 5.1 第一阶段：基础架构

目标：建立多平台支持的基础架构

- [ ] 创建 `platforms/` 目录结构
- [ ] 实现统一消息类型定义
- [ ] 实现平台适配器基类
- [ ] 实现平台管理器
- [ ] 扩展配置模块支持飞书配置
- [ ] 更新 `.env.example`
- [ ] 编写平台模块单元测试

## 5.2 第二阶段：飞书核心功能

目标：实现飞书基础消息处理

- [ ] 实现飞书适配器（轮询模式）
- [ ] 实现飞书消息转换逻辑
- [ ] 实现飞书文件下载
- [ ] 实现飞书消息发送
- [ ] 实现飞书权限校验
- [ ] 重构主程序支持多平台
- [ ] 保持现有 Telegram 功能完全兼容
- [ ] 编写飞书模块集成测试

## 5.3 第三阶段：Webhook 模式（可选）

目标：提供更高实时性的 Webhook 模式

- [ ] 实现飞书 Webhook 服务
- [ ] 实现请求验证逻辑
- [ ] 实现事件处理
- [ ] 支持配置切换轮询/Webhook 模式
- [ ] 编写 Webhook 模式文档

## 5.4 第四阶段：优化与增强

目标：完善功能与体验

- [ ] 支持飞书富文本消息
- [ ] 支持飞书群聊
- [ ] 支持命令交互（/start, /help 等）
- [ ] 添加飞书使用说明文档
- [ ] 添加飞书部署指南
- [ ] 性能优化

## 5.5 第五阶段：Telegram 迁移（可选）

目标：统一架构

- [ ] 将 Telegram 接入迁移到适配器模式
- [ ] 重构代码统一消息处理流程
- [ ] 确保完全向后兼容

# 6. 依赖管理

## 6.1 新增依赖

在 `requirements.txt` 中添加：

```
# 飞书集成依赖
aiohttp>=3.9.0  # 已存在
# 飞书官方 SDK（可选，也可直接调用 HTTP API）
# lark-oapi>=1.2.0
```

**推荐方案**：直接使用 aiohttp 调用飞书 OpenAPI，减少第三方依赖。

# 7. 测试策略

## 7.1 单元测试

- 测试统一消息类型转换
- 测试平台适配器基类
- 测试配置加载
- 测试权限校验逻辑

## 7.2 集成测试

- 测试飞书消息收发（使用测试账号）
- 测试文件处理流程
- 测试端到端工作流

## 7.3 测试文件结构

```
test/
├── test_platforms/
│   ├── __init__.py
│   ├── test_platform_types.py
│   ├── test_platform_manager.py
│   └── test_feishu_adapter.py
└── ... 现有测试 ...
```

# 8. 部署文档

## 8.1 飞书应用创建步骤

1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 进入「开发者后台」→「创建应用」→「创建自建应用」
3. 填写应用基本信息：
   - 应用名称：NoteAgents
   - 应用描述：AI 笔记自动收集助手
   - 应用图标：上传自定义图标
4. 提交创建后获取 App ID 和 App Secret
5. 进入「权限管理」，申请所需权限
6. 进入「添加应用能力」，添加「机器人」能力
7. 进入「版本管理与发布」，创建版本并发布
8. 在「凭证与基础信息」中获取配置信息

## 8.2 用户 ID 获取方法

1. 配置好飞书集成并启动服务
2. 在飞书中搜索机器人名称并发起对话
3. 发送任意消息
4. 查看服务日志，从中获取 `user_id`（格式为 `ou_` 开头）
5. 将 `user_id` 添加到 `FEISHU_ALLOWED_USER_IDS` 配置

# 9. 风险与限制

## 9.1 飞书平台限制

| 限制项 | 说明 | 应对方案 |
|--------|------|----------|
| API 调用频率 | 按应用层级限流 | 合理控制轮询频率，使用 Webhook |
| 文件大小 | 单文件限制 100MB | 与 Telegram 保持一致的限制 |
| 审核要求 | 发布需审核 | 先使用测试版，审核通过后正式发布 |

## 9.2 部署限制

- Webhook 模式需要公网可访问的服务器
- 国内服务器访问飞书 API 通常无需代理
- 建议使用与 Telegram 相同的服务器部署

# 10. 监控与运维

## 10.1 日志设计

- 平台连接状态日志
- 消息接收与处理日志
- API 调用失败日志
- 权限校验失败日志

## 10.2 健康检查

- 平台连接状态监控
- 令牌有效期监控
- 文件存储空间监控

# 11. 总结

本设计文档详细说明了如何在现有 NoteAgents 系统基础上扩展飞书平台集成能力：

1. **架构清晰**：采用适配器模式实现多平台支持
2. **渐进式实施**：分 5 个阶段逐步实现，降低风险
3. **业务复用**：最大化复用现有核心业务逻辑
4. **部署友好**：初期使用轮询模式，降低部署复杂度
5. **可扩展**：预留 Webhook 模式接口，方便后续升级

通过本方案的实施，NoteAgents 将支持从飞书和 Telegram 两个平台收集内容，为用户提供更大的便利性。
