"""ToolUse Filter（可选模块）

轻量级融合 ReactAgent 的 Acting 思想
- 根据 Classification 结果，决定是否调用工具
- 不做复杂循环推理，单轮即可
"""

import re
import urllib.request
from typing import Dict, Any
from abc import ABC, abstractmethod

from config import WikiConfig
from wiki.pipeline import Filter, InputType


class BaseTool(ABC):
    """工具基类"""

    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass

    @abstractmethod
    def can_handle(self, data: Dict[str, Any]) -> bool:
        """是否可以处理此数据"""
        pass

    @abstractmethod
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具"""
        pass


class URLFetchTool(BaseTool):
    """URL 抓取工具"""

    def __init__(self):
        self.url_pattern = re.compile(r'https?://\S+')

    def name(self) -> str:
        return "url_fetch"

    def can_handle(self, data: Dict[str, Any]) -> bool:
        return data.get("input_type") == InputType.URL

    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """抓取 URL 内容（简单实现）"""
        content = data.get("content", "")
        urls = self.url_pattern.findall(content)
        if urls:
            url = urls[0]
            try:
                with urllib.request.urlopen(url, timeout=10) as response:
                    fetched_content = response.read().decode('utf-8', errors='ignore')
                data["original_content"] = content
                data["content"] = fetched_content
                data["fetched_from"] = url
                data["tool_used"] = self.name()
            except Exception as e:
                data["fetch_error"] = str(e)
        return data


class ToolUseFilter(Filter):
    """ToolUse Agent（轻量级，单轮）"""

    def __init__(self, config: WikiConfig):
        self.config = config
        self.tools: list[BaseTool] = [
            URLFetchTool()
        ]

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """按需调用工具"""
        for tool in self.tools:
            if tool.can_handle(data):
                data = tool.execute(data)
        return data

    def add_tool(self, tool: BaseTool):
        """添加自定义工具"""
        self.tools.append(tool)
