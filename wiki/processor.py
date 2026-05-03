"""LLM 笔记加工器"""

import json
import re
import time
from datetime import datetime
from typing import Dict, Any

from config import WikiConfig
from wiki.models import StructuredNote


class NoteProcessor:
    """LLM 笔记加工器"""

    def __init__(self, config: WikiConfig):
        self.config = config
        self.categories = ["技术类", "想法类", "学习类", "日常类"]

    def process_note(self, content: str, source_path: str) -> StructuredNote:
        """处理单条笔记，返回 StructuredNote"""
        # 1. 调用 LLM 获取结构化数据
        structured_data = self._call_llm(content)
        # 2. 验证数据
        self._validate_structured_data(structured_data)
        # 3. 创建 StructuredNote
        note = StructuredNote(
            title=structured_data["title"],
            summary=structured_data["summary"],
            keywords=structured_data["keywords"],
            key_points=structured_data["key_points"],
            backlinks=structured_data["backlinks"],
            category=structured_data["category"],
            optimized_content=structured_data["optimized_content"],
            source_path=source_path
        )
        return note

    def _call_llm(self, content: str) -> dict:
        """调用 LLM API，带重试机制"""
        for attempt in range(self.config.llm_retry_times):
            try:
                # 使用项目现有的 LLM 调用机制
                from tools.llm_adapters import create_adapter
                llm = create_adapter(
                    api_key=self.config.llm_api_key or "",
                    base_url=self.config.llm_base_url,
                    timeout=30,
                    model=self.config.llm_model
                )
                messages = [
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": f"原始笔记：\n{content}"}
                ]
                response = llm.invoke(messages, temperature=self.config.llm_temperature, max_tokens=self.config.llm_max_tokens)
                # 解析 JSON 响应
                return self._parse_llm_response(response.content)
            except Exception as e:
                if attempt == self.config.llm_retry_times - 1:
                    raise
                time.sleep(2 ** attempt)

    def _parse_llm_response(self, content: str) -> dict:
        """解析 LLM 响应，支持 JSON 嵌入 Markdown 的情况"""
        # 尝试从 ```json 和 ``` 之间提取
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 直接尝试解析
            json_str = content
        # 尝试解析
        try:
            data = json.loads(json_str)
            return data
        except json.JSONDecodeError:
            # 如果解析失败，尝试创建默认结构
            return self._create_default_structured_data()

    def _create_default_structured_data(self) -> dict:
        """创建默认的结构化数据（当 LLM 返回格式不符合预期时）"""
        return {
            "title": "未分类笔记",
            "summary": "LLM 处理失败，请检查 API 配置。",
            "keywords": ["未分类"],
            "key_points": ["笔记内容未成功结构化"],
            "backlinks": [],
            "category": "日常类",
            "optimized_content": ""
        }

    def _get_system_prompt(self) -> str:
        return """你是一个专业的笔记整理助手，负责将原始笔记加工成结构化内容。
你的任务是：
1. 提炼核心标题：简洁、准确、贴合主题
2. 精简摘要：将核心信息浓缩至 150 字以内
3. 提取关键词/标签：提取 3-5 个核心关键词
4. 梳理核心要点：将核心信息拆解为 3-5 条要点
5. 识别双向链接：识别核心概念、关键词，建议 Obsidian 双向链接
6. 自动分类：必须从以下分类选择一个：技术类、想法类、学习类、日常类
7. 内容优化：剔除冗余、口语化信息，保持逻辑清晰、忠于原文

你需要返回 JSON 格式，不要有任何 Markdown 标记。
"""

    def _validate_structured_data(self, data: dict) -> None:
        """验证结构化数据"""
        required_fields = ["title", "summary", "keywords", "key_points", "backlinks", "category", "optimized_content"]
        for field in required_fields:
            if field not in data:
                data[field] = self._get_default_value(field)
        # 验证分类
        if data["category"] not in self.categories:
            data["category"] = "日常类"
        # 验证字数
        if len(data["summary"]) > 150:
            data["summary"] = data["summary"][:147] + "..."

    def _get_default_value(self, field: str) -> Any:
        """获取字段的默认值"""
        defaults = {
            "title": "未分类笔记",
            "summary": "未提供摘要",
            "keywords": ["未分类"],
            "key_points": ["未提供要点"],
            "backlinks": [],
            "category": "日常类",
            "optimized_content": ""
        }
        return defaults.get(field, "")
