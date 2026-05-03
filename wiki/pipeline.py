"""Wiki Pipeline 基础架构

包含：
- Filter 基类（Pipe & Filter 模式）
- Classification Agent（分类路由）
- Self-Correction 机制
"""

import json
import re
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field, ValidationError
from config import WikiConfig
from storage.log_manager import get_logger
from tools.model_adapter import create_adapter, get_model_config
from wiki.models import StructuredNote

logger = get_logger("Pipeline")


class LlmStructuredOutput(BaseModel):
    """LLM 返回的结构化数据模型（支持中英文字段别名）"""
    title: str = Field(alias="核心标题", description="核心标题")
    summary: str = Field(alias="精简摘要", description="精简摘要")
    keywords: List[str] = Field(alias="关键词", description="关键词列表")
    key_points: List[str] = Field(alias="核心要点", description="核心要点列表")
    backlinks: List[str] = Field(alias="双向链接", description="双向链接列表")
    category: str = Field(alias="自动分类", description="自动分类")
    optimized_content: Optional[str] = Field(alias="内容优化", default="", description="优化后的内容")

    model_config = {"populate_by_name": True}


class InputType(Enum):
    """输入类型枚举（Classification Agent 使用）"""
    PURE_TEXT = "pure_text"  # 纯文本
    URL = "url"  # 包含链接
    IMAGE = "image"  # 图片（待实现）
    QUESTION = "question"  # 问题
    CODE = "code"  # 代码片段
    UNKNOWN = "unknown"


class Filter(ABC):
    """Filter 基类（Pipe & Filter 模式）"""

    @abstractmethod
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理数据并返回"""
        pass


class ClassificationFilter(Filter):
    """Classification Agent（分类路由）"""

    def __init__(self, config: WikiConfig):
        self.config = config
        self.url_pattern = re.compile(r'https?://\S+')

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分类输入"""
        content = data.get("content", "")
        data["input_type"] = self._classify(content)
        return data

    def _classify(self, content: str) -> InputType:
        """判断输入类型"""
        if not content:
            return InputType.UNKNOWN
        # 检查是否包含 URL
        if self.url_pattern.search(content):
            return InputType.URL
        # 检查是否是问题
        if content.endswith('?') or content.endswith('？') or \
           any(keyword in content for keyword in ["什么", "怎么", "如何", "为什么", "怎样"]):
            return InputType.QUESTION
        # 检查是否包含代码特征
        if any(code_mark in content for code_mark in ["```", "def ", "import ", "class ", "function "]):
            return InputType.CODE
        return InputType.PURE_TEXT


class SelfCorrectionFilter(Filter):
    """Self-Correction 机制"""

    def __init__(self, config: WikiConfig, max_attempts: int = 3):
        self.config = config
        self.max_attempts = max_attempts

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理并尝试修复数据"""
        if "structured_data" not in data:
            return data
        attempt = 0
        while attempt < self.max_attempts:
            try:
                self._validate_structured_data(data["structured_data"])
                return data
            except (ValueError, KeyError) as e:
                attempt += 1
                if attempt < self.max_attempts:
                    # 尝试修复
                    data["structured_data"] = self._attempt_repair(data["structured_data"])
                else:
                    raise
        return data

    def _validate_structured_data(self, data: Dict[str, Any]) -> None:
        """验证结构化数据"""
        required_fields = [
            "title", "summary", "keywords",
            "key_points", "backlinks",
            "category", "optimized_content"
        ]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        if not isinstance(data.get("keywords"), list):
            raise ValueError("Keywords must be a list")
        if not isinstance(data.get("key_points"), list):
            raise ValueError("Key points must be a list")

    def _attempt_repair(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """尝试修复结构化数据"""
        repaired = dict(data)
        defaults = {
            "title": "未分类笔记",
            "summary": "笔记内容未成功解析",
            "keywords": ["未分类"],
            "key_points": ["要点未成功提取"],
            "backlinks": [],
            "category": "日常类",
            "optimized_content": ""
        }
        for key, default in defaults.items():
            if key not in repaired:
                repaired[key] = default
        if not isinstance(repaired.get("keywords"), list):
            repaired["keywords"] = ["未分类"]
        if not isinstance(repaired.get("key_points"), list):
            repaired["key_points"] = ["要点未成功提取"]
        return repaired


def _get_system_prompt() -> str:
    return """你是一个专业的笔记整理助手，负责将原始笔记加工成结构化内容。
你的任务是：
1. 提炼核心标题：简洁、准确、贴合主题
2. 精简摘要：将核心信息浓缩至 150 字以内
3. 提取关键词/标签：提取 3-5 个核心关键词
4. 梳理核心要点：将核心信息拆解为 3-5 条要点
5. 识别双向链接：识别核心概念、关键词，建议 Obsidian 双向链接
6. 自动分类：根据内容自由选择合适的分类（如：技术类、工作、学习、生活、想法、读书笔记、代码片段等，不要仅局限于固定分类！）
7. 内容优化：剔除冗余、口语化信息，保持逻辑清晰、忠于原文

你必须返回严格的 JSON 格式，字段名必须为英文：
{
    "title": "核心标题",
    "summary": "精简摘要",
    "keywords": ["关键词1", "关键词2", ...],
    "key_points": ["要点1", "要点2", ...],
    "backlinks": ["[[链接1]]", "[[链接2]]", ...],
    "category": "分类",
    "optimized_content": "优化后的内容"
}

不要有任何 Markdown 标记，不要添加额外解释。
"""


def _create_structured_note(data: Dict[str, Any]) -> StructuredNote:
    """创建 StructuredNote"""
    logger.info(f"the content: {data}")
    return StructuredNote(
        title=data["structured_data"]["title"],
        summary=data["structured_data"]["summary"],
        keywords=data["structured_data"]["keywords"],
        key_points=data["structured_data"]["key_points"],
        backlinks=data["structured_data"]["backlinks"],
        category=data["structured_data"]["category"],
        optimized_content=data["structured_data"]["optimized_content"],
        source_path=data["source_path"],
        source_type=data.get("source_type", "manual")
    )


def _create_default_structured_data(content:str) -> dict:
    """创建默认的结构化数据"""
    return {
        "title": "未分类笔记",
        "summary": "LLM 处理失败，请检查 API 配置。",
        "keywords": ["未分类"],
        "key_points": ["笔记内容未成功结构化"],
        "backlinks": [],
        "category": "日常类",
        "optimized_content": content
    }


def _parse_llm_response(content: str) -> dict:
    """解析 LLM 响应（使用 Pydantic 模型自动验证和字段映射）"""
    logger.info(f"解析 LLM 响应: {content[:200]}...")
    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_str = content
    try:
        data = json.loads(json_str)
        # 使用 Pydantic 模型解析，自动支持中英文字段别名
        parsed = LlmStructuredOutput(**data)
        return parsed.model_dump()
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败: {e}")
        return _create_default_structured_data(content)
    except ValidationError as e:
        logger.error(f"数据结构验证失败: {e}")
        return _create_default_structured_data(content)


class NotePipeline:
    """完整的笔记处理 Pipeline（Pipe & Filter 架构）"""

    def __init__(self, config: WikiConfig):
        self.config = config
        self.filters: List[Filter] = []

        # 注册默认 filters
        self.filters.append(ClassificationFilter(config))
        self.filters.append(SelfCorrectionFilter(config))

    def add_filter(self, filter: Filter):
        """添加 Filter"""
        self.filters.append(filter)

    def process(self, content: str, source_path: str, source_type: str = "manual") -> StructuredNote:
        """处理完整流程

        Args:
            source_type: 'auto' 或 'manual'
        """
        data: Dict[str, Any] = {
            "content": content,
            "source_path": source_path,
            "source_type": source_type,
            "structured_data": None
        }
        # 1. 执行 LLM 处理
        data["structured_data"] = self._call_llm(content)
        # 2. 执行 Pipeline
        for filter in self.filters:
            data = filter.process(data)
        # 3. 创建 StructuredNote
        return _create_structured_note(data)

    def _call_llm(self, content: str) -> Dict[str, Any]:
        """调用 LLM"""
        try:
            logger.info(f"创建 LLM adapter: model={self.config.llm_model}, base_url={self.config.llm_base_url}")
            model_config = get_model_config(
                model_name=self.config.llm_model,
                api_key=self.config.llm_api_key or "",
                base_url=self.config.llm_base_url
            )
            model_config.temperature = self.config.llm_temperature
            model_config.max_tokens = self.config.llm_max_tokens

            adapter = create_adapter(model_config)
            logger.info(f"调用AI API: {model_config.provider.value}/{model_config.model_name}")

            messages = [
                {"role": "system", "content": _get_system_prompt()},
                {"role": "user", "content": f"原始笔记：\n{content}"}
            ]
            response = adapter.invoke(
                messages,
                temperature=self.config.llm_temperature,
                max_tokens=self.config.llm_max_tokens
            )
            logger.info(f"AI API调用成功 - 用时: {response.latency_ms}ms")
            return _parse_llm_response(response.content)
        except Exception as e:
            import traceback
            logger.error(f"LLM 调用失败: {e}")
            logger.error(traceback.format_exc())
            return _create_default_structured_data(content)
