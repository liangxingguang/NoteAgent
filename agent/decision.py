"""决策模块 - 意图识别、流程决策、工具选择"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

from .perception import PerceivedMessage, MessageType
from storage.log_manager import get_logger



logger = get_logger("Decision")


class IntentType(Enum):
    """意图类型"""
    PROCESS_TEXT = "process_text"
    PROCESS_URL = "process_url"
    PROCESS_FILE = "process_file"
    PROCESS_PHOTO = "process_photo"
    PUSH_GITHUB = "push_github"
    PULL_GITHUB = "pull_github"
    HELP = "help"
    START = "start"
    UNKNOWN = "unknown"


@dataclass
class Decision:
    """决策结果"""
    intent: IntentType
    tool_sequence: List[str]
    priority: int = 0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class DecisionModule:
    """决策模块"""

    TOOL_FILE_PROCESS = "file_processor"
    TOOL_AI_SUMMARY = "ai_summarizer"
    TOOL_OBSIDIAN = "obsidian_writer"
    TOOL_GITHUB_PUSH = "github_pusher"
    TOOL_GITHUB_PULL = "github_puller"
    TOOL_CLEANUP = "cleanup"
    TOOL_WEB_DOWNLOAD = "web_downloader"

    def __init__(self):
        pass

    def make_decision(self, message: PerceivedMessage) -> Optional[Decision]:
        """根据感知到的消息做出决策

        Args:
            message: 感知到的消息

        Returns:
            决策结果
        """
        if not message.is_authorized:
            return None

        intent = self._recognize_intent(message)

        if intent == IntentType.UNKNOWN:
            logger.warning(f"无法识别的意图: {message.info}")
            return None

        tool_sequence = self._determine_tool_sequence(intent, message)

        decision = Decision(
            intent=intent,
            tool_sequence=tool_sequence,
            priority=self._calculate_priority(intent, message),
        )

        logger.info(f"做出决策: intent={intent.value}, tools={tool_sequence}")
        return decision

    def _recognize_intent(self, message: PerceivedMessage) -> IntentType:
        """识别用户意图

        Args:
            message: 感知到的消息

        Returns:
            意图类型
        """
        if message.msg_type == MessageType.TEXT and message.content:
            text = message.content.strip().lower()
            original_text = message.content.strip()

            if text in ["/start", "start"]:
                return IntentType.START

            if text in ["/help", "help", "帮助", "?"]:
                return IntentType.HELP

            if text.startswith("/push") or text.startswith("/github"):
                return IntentType.PUSH_GITHUB

            if text.startswith("/pull"):
                return IntentType.PULL_GITHUB

            if "推送" in original_text or "github" in original_text.lower():
                return IntentType.PUSH_GITHUB

            if "拉取" in original_text or "pull" in original_text.lower():
                return IntentType.PULL_GITHUB

        if message.msg_type == MessageType.TEXT:
            from tools.ai_summary_tool import is_url
            content = message.content or ""
            if is_url(content.strip()):
                return IntentType.PROCESS_URL
            return IntentType.PROCESS_TEXT

        if message.msg_type == MessageType.DOCUMENT:
            return IntentType.PROCESS_FILE

        if message.msg_type == MessageType.PHOTO:
            return IntentType.PROCESS_PHOTO

        return IntentType.UNKNOWN

    def _determine_tool_sequence(self, intent: IntentType, message: PerceivedMessage) -> List[str]:
        """确定工具调用序列

        Args:
            intent: 意图类型
            message: 感知到的消息

        Returns:
            工具名称列表（按调用顺序）
        """
        sequence = []

        if intent == IntentType.PROCESS_TEXT:
            sequence = [
                self.TOOL_AI_SUMMARY,
                self.TOOL_OBSIDIAN,
            ]

        elif intent == IntentType.PROCESS_URL:
            sequence = [
                self.TOOL_WEB_DOWNLOAD,
                self.TOOL_AI_SUMMARY,
                self.TOOL_OBSIDIAN,
            ]

        elif intent == IntentType.PROCESS_FILE:
            sequence = [
                self.TOOL_FILE_PROCESS,
                self.TOOL_AI_SUMMARY,
                self.TOOL_OBSIDIAN,
                self.TOOL_CLEANUP,
            ]

        elif intent == IntentType.PUSH_GITHUB:
            sequence = [
                self.TOOL_GITHUB_PUSH,
            ]

        elif intent == IntentType.PULL_GITHUB:
            sequence = [
                self.TOOL_GITHUB_PULL,
            ]

        elif intent == IntentType.PROCESS_PHOTO:
            sequence = []

        elif intent in [IntentType.START, IntentType.HELP]:
            sequence = []

        return sequence

    def _calculate_priority(self, intent: IntentType, message: PerceivedMessage) -> int:
        """计算优先级

        Args:
            intent: 意图类型
            message: 感知到的消息

        Returns:
            优先级值（数字越小优先级越高）
        """
        base_priority = 10

        if intent == IntentType.PROCESS_FILE:
            base_priority = 5

        if intent == IntentType.PROCESS_URL:
            base_priority = 6

        if intent == IntentType.PUSH_GITHUB:
            base_priority = 7

        if intent == IntentType.PULL_GITHUB:
            base_priority = 7

        return base_priority


_decision_module: Optional[DecisionModule] = None


def init_decision_module() -> DecisionModule:
    """初始化决策模块"""
    global _decision_module
    _decision_module = DecisionModule()
    return _decision_module


def get_decision_module() -> DecisionModule:
    """获取决策模块实例"""
    if _decision_module is None:
        raise RuntimeError("决策模块未初始化，请先调用 init_decision_module()")
    return _decision_module
