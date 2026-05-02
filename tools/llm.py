"""LLM 核心模块 - 响应类和基础功能"""

from typing import Optional, List, Dict, Any, Iterator, AsyncIterator
from dataclasses import dataclass


@dataclass
class StreamStats:
    """流式调用统计信息"""
    model: str
    usage: Dict[str, int]
    latency_ms: int
    reasoning_content: Optional[str] = None


@dataclass
class ToolCall:
    """工具调用信息"""
    id: str
    name: str
    arguments: str


@dataclass
class LLMResponse:
    """LLM 响应"""
    content: str
    model: str
    usage: Dict[str, int]
    latency_ms: int
    reasoning_content: Optional[str] = None


@dataclass
class LLMToolResponse:
    """LLM 工具调用响应"""
    content: Optional[str]
    tool_calls: List[ToolCall]
    model: str
    usage: Dict[str, int]
    latency_ms: int
