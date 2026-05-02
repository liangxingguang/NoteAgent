"""上下文缓存模块"""

import time
from typing import Any, Optional, Dict
from dataclasses import dataclass, field

from .log_manager import get_logger


@dataclass
class CacheItem:
    """缓存项"""
    data: Any
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None


class ContextCache:
    """上下文缓存（内存实现）"""

    def __init__(self, default_ttl_seconds: int = 3600):
        """初始化上下文缓存

        Args:
            default_ttl_seconds: 默认过期时间（秒）
        """
        self._cache: Dict[str, CacheItem] = {}
        self.default_ttl_seconds = default_ttl_seconds
        self.logger = get_logger("ContextCache")

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ):
        """设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            ttl_seconds: 过期时间（秒），不设置则使用默认值
        """
        expires_at = None
        if ttl_seconds is not None:
            expires_at = time.time() + ttl_seconds
        elif self.default_ttl_seconds > 0:
            expires_at = time.time() + self.default_ttl_seconds

        self._cache[key] = CacheItem(data=value, expires_at=expires_at)
        self.logger.debug(f"设置缓存: {key}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存

        Args:
            key: 缓存键
            default: 默认值

        Returns:
            缓存值，如果不存在或已过期则返回默认值
        """
        if key not in self._cache:
            return default

        item = self._cache[key]

        # 检查是否过期
        if item.expires_at is not None and time.time() > item.expires_at:
            self.logger.debug(f"缓存已过期: {key}")
            self.delete(key)
            return default

        return item.data

    def delete(self, key: str) -> bool:
        """删除缓存

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        if key in self._cache:
            del self._cache[key]
            self.logger.debug(f"删除缓存: {key}")
            return True
        return False

    def exists(self, key: str) -> bool:
        """检查缓存是否存在且未过期

        Args:
            key: 缓存键

        Returns:
            是否存在
        """
        if key not in self._cache:
            return False

        item = self._cache[key]
        if item.expires_at is not None and time.time() > item.expires_at:
            self.delete(key)
            return False

        return True

    def clear_expired(self) -> int:
        """清理所有过期缓存

        Returns:
            清理的缓存项数量
        """
        expired_keys = []
        now = time.time()

        for key, item in self._cache.items():
            if item.expires_at is not None and now > item.expires_at:
                expired_keys.append(key)

        for key in expired_keys:
            self.delete(key)

        self.logger.info(f"清理过期缓存: {len(expired_keys)}项")
        return len(expired_keys)

    def clear_all(self):
        """清空所有缓存"""
        count = len(self._cache)
        self._cache.clear()
        self.logger.warning(f"清空所有缓存: {count}项")

    def get_all_keys(self) -> list[str]:
        """获取所有缓存键（包括过期的）

        Returns:
            缓存键列表
        """
        return list(self._cache.keys())

    def size(self) -> int:
        """获取缓存数量（包括过期的）

        Returns:
            缓存项数量
        """
        return len(self._cache)


# 用户会话上下文缓存
class UserSessionCache:
    """用户会话缓存"""

    def __init__(self, ttl_seconds: int = 86400):
        """初始化用户会话缓存

        Args:
            ttl_seconds: 会话过期时间（秒），默认24小时
        """
        self.cache = ContextCache(default_ttl_seconds=ttl_seconds)
        self.logger = get_logger("UserSessionCache")

    def set_user_data(
        self,
        user_id: int,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ):
        """设置用户数据

        Args:
            user_id: 用户ID
            key: 数据键
            value: 数据值
            ttl_seconds: 过期时间
        """
        cache_key = f"user:{user_id}:{key}"
        self.cache.set(cache_key, value, ttl_seconds)

    def get_user_data(
        self,
        user_id: int,
        key: str,
        default: Any = None
    ) -> Any:
        """获取用户数据

        Args:
            user_id: 用户ID
            key: 数据键
            default: 默认值

        Returns:
            数据值
        """
        cache_key = f"user:{user_id}:{key}"
        return self.cache.get(cache_key, default)

    def get_user_session(self, user_id: int) -> Dict[str, Any]:
        """获取用户所有会话数据

        Args:
            user_id: 用户ID

        Returns:
            用户会话数据字典
        """
        prefix = f"user:{user_id}:"
        session_data = {}

        for key in self.cache.get_all_keys():
            if key.startswith(prefix):
                data_key = key[len(prefix):]
                value = self.cache.get(key)
                if value is not None:
                    session_data[data_key] = value

        return session_data

    def clear_user_session(self, user_id: int) -> int:
        """清空用户会话

        Args:
            user_id: 用户ID

        Returns:
            清理的项数
        """
        prefix = f"user:{user_id}:"
        keys_to_delete = [
            key for key in self.cache.get_all_keys()
            if key.startswith(prefix)
        ]

        for key in keys_to_delete:
            self.cache.delete(key)

        self.logger.info(f"清空用户会话: {user_id}, 删除{len(keys_to_delete)}项")
        return len(keys_to_delete)


# 全局缓存实例
_context_cache: Optional[ContextCache] = None
_user_session_cache: Optional[UserSessionCache] = None


def init_context_cache(default_ttl_seconds: int = 3600) -> ContextCache:
    """初始化上下文缓存"""
    global _context_cache
    _context_cache = ContextCache(default_ttl_seconds)
    return _context_cache


def get_context_cache() -> ContextCache:
    """获取上下文缓存实例"""
    if _context_cache is None:
        _context_cache = ContextCache()
    return _context_cache


def init_user_session_cache(ttl_seconds: int = 86400) -> UserSessionCache:
    """初始化用户会话缓存"""
    global _user_session_cache
    _user_session_cache = UserSessionCache(ttl_seconds)
    return _user_session_cache


def get_user_session_cache(_user_session_cache=None) -> UserSessionCache:
    """获取用户会话缓存实例"""
    if _user_session_cache is None:
        _user_session_cache = UserSessionCache()
    return _user_session_cache
