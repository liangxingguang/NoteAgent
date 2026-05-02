"""模型适配器 - 支持多种AI模型提供商

支持的模型：
- OpenAI: GPT-3.5, GPT-4, o1
- 通义千问: Qwen-Turbo, Qwen-Plus, Qwen-Max
- Anthropic: Claude-3
- Google: Gemini
- DeepSeek: deepseek-chat, deepseek-coder, deepseek-reasoner
- 其他OpenAI兼容接口
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, Tuple

from .llm import LLMResponse, LLMToolResponse
from .llm_adapters import create_adapter as create_llm_adapter, BaseLLMAdapter


class ModelProvider(Enum):
    """模型提供商"""
    OPENAI = "openai"
    QWEN = "qwen"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"
    OPENAI_COMPATIBLE = "openai_compatible"


@dataclass
class ModelConfig:
    """模型配置"""
    provider: ModelProvider
    model_name: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    system_prompt: Optional[str] = None


# 模型预设配置
MODEL_PRESETS = {
    # OpenAI
    "gpt-3.5-turbo": ModelConfig(
        provider=ModelProvider.OPENAI,
        model_name="gpt-3.5-turbo",
        base_url="https://api.openai.com/v1/chat/completions",
    ),
    "gpt-4": ModelConfig(
        provider=ModelProvider.OPENAI,
        model_name="gpt-4",
        base_url="https://api.openai.com/v1/chat/completions",
    ),
    "gpt-4-turbo": ModelConfig(
        provider=ModelProvider.OPENAI,
        model_name="gpt-4-turbo",
        base_url="https://api.openai.com/v1/chat/completions",
    ),
    "o1": ModelConfig(
        provider=ModelProvider.OPENAI,
        model_name="o1",
        base_url="https://api.openai.com/v1/chat/completions",
    ),
    "o1-mini": ModelConfig(
        provider=ModelProvider.OPENAI,
        model_name="o1-mini",
        base_url="https://api.openai.com/v1/chat/completions",
    ),

    # 通义千问
    "qwen-turbo": ModelConfig(
        provider=ModelProvider.QWEN,
        model_name="qwen-turbo",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    ),
    "qwen-plus": ModelConfig(
        provider=ModelProvider.QWEN,
        model_name="qwen-plus",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    ),
    "qwen-max": ModelConfig(
        provider=ModelProvider.QWEN,
        model_name="qwen-max",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    ),

    # Anthropic Claude
    "claude-3-haiku": ModelConfig(
        provider=ModelProvider.ANTHROPIC,
        model_name="claude-3-haiku-20240307",
        base_url="https://api.anthropic.com/v1/messages",
    ),
    "claude-3-sonnet": ModelConfig(
        provider=ModelProvider.ANTHROPIC,
        model_name="claude-3-sonnet-20240229",
        base_url="https://api.anthropic.com/v1/messages",
    ),
    "claude-3-opus": ModelConfig(
        provider=ModelProvider.ANTHROPIC,
        model_name="claude-3-opus-20240229",
        base_url="https://api.anthropic.com/v1/messages",
    ),

    # Google Gemini
    "gemini-pro": ModelConfig(
        provider=ModelProvider.GEMINI,
        model_name="gemini-pro",
        base_url="https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
    ),
    "gemini-1.5-pro": ModelConfig(
        provider=ModelProvider.GEMINI,
        model_name="gemini-1.5-pro",
        base_url="https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent",
    ),

    # DeepSeek
    "deepseek-chat": ModelConfig(
        provider=ModelProvider.DEEPSEEK,
        model_name="deepseek-chat",
        base_url="https://api.deepseek.com/v1/chat/completions",
    ),
    "deepseek-coder": ModelConfig(
        provider=ModelProvider.DEEPSEEK,
        model_name="deepseek-coder",
        base_url="https://api.deepseek.com/v1/chat/completions",
    ),
    "deepseek-reasoner": ModelConfig(
        provider=ModelProvider.DEEPSEEK,
        model_name="deepseek-reasoner",
        base_url="https://api.deepseek.com/v1/chat/completions",
    ),
}


class BaseAdapter:
    """模型适配器基类"""

    def __init__(self, config: ModelConfig):
        self.config = config
        # 创建新的LLM适配器
        self.llm_adapter: BaseLLMAdapter = create_llm_adapter(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=120,
            model=config.model_name
        )

    def prepare_request(self, messages: list) -> Tuple[str, Dict[str, str], Dict[str, Any]]:
        """准备API请求（保持向后兼容）
        Returns:
            (url, headers, payload)
        """
        # 保持向后兼容性
        if hasattr(self.llm_adapter, '_client') and hasattr(self.llm_adapter._client, 'chat') and hasattr(self.llm_adapter._client.chat, 'completions'):
            # OpenAI兼容模式
            url = self.config.base_url or "https://api.openai.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.api_key}",
            }
            payload = {
                "model": self.config.model_name,
                "messages": messages,
                "temperature": self.config.temperature,
            }
            if self.config.max_tokens > 0:
                payload["max_tokens"] = self.config.max_tokens
            return url, headers, payload
        else:
            # 其他适配器
            return "", {}, {}

    def extract_response(self, response_json: Dict[str, Any]) -> str:
        """从响应中提取内容（保持向后兼容）"""
        from ..utils.api_utils import safe_get

        # 尝试OpenAI格式
        content = safe_get(response_json, "choices.0.message.content")
        if content:
            return content

        # 尝试Anthropic格式
        content = safe_get(response_json, "content.0.text")
        if content:
            return content

        # 尝试Gemini格式
        content = safe_get(response_json, "candidates.0.content.parts.0.text")
        if content:
            return content

        return str(response_json)

    def invoke(self, messages: list, **kwargs) -> LLMResponse:
        """非流式调用"""
        return self.llm_adapter.invoke(messages, **kwargs)

    def stream_invoke(self, messages: list, **kwargs) -> str:
        """流式调用"""
        result = ""
        for chunk in self.llm_adapter.stream_invoke(messages, **kwargs):
            result += chunk
        return result

    async def astream_invoke(self, messages: list, **kwargs) -> str:
        """异步流式调用"""
        result = ""
        async for chunk in self.llm_adapter.astream_invoke(messages, **kwargs):
            result += chunk
        return result

    def invoke_with_tools(self, messages: list, tools: list, **kwargs) -> LLMToolResponse:
        """工具调用"""
        return self.llm_adapter.invoke_with_tools(messages, tools, **kwargs)


class OpenAIAdapter(BaseAdapter):
    """OpenAI兼容适配器（支持OpenAI、通义千问兼容模式、DeepSeek等）"""
    pass


class AnthropicAdapter(BaseAdapter):
    """Anthropic Claude适配器"""
    pass


class GeminiAdapter(BaseAdapter):
    """Google Gemini适配器"""
    pass


def create_adapter(config: ModelConfig) -> BaseAdapter:
    """创建模型适配器"""
    # 直接使用新的LLM适配器系统
    return BaseAdapter(config)


def get_model_config(model_name: str, api_key: str, base_url: Optional[str] = None) -> ModelConfig:
    """获取模型配置"""
    # 查找预设配置
    preset = MODEL_PRESETS.get(model_name.lower())

    if preset:
        config = ModelConfig(
            provider=preset.provider,
            model_name=preset.model_name,
            base_url=base_url or preset.base_url,
            api_key=api_key,
        )
    else:
        # 未知模型，使用OpenAI兼容模式
        config = ModelConfig(
            provider=ModelProvider.OPENAI_COMPATIBLE,
            model_name=model_name,
            base_url=base_url or "https://api.openai.com/v1/chat/completions",
            api_key=api_key,
        )

    return config

