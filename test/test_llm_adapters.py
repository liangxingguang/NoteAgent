"""LLM 适配器测试"""

from unittest.mock import patch, MagicMock

import pytest

from tools.llm_adapters import (
    OpenAIAdapter,
    AnthropicAdapter,
    GeminiAdapter,
    create_adapter as create_llm_adapter,
)
# 直接使用相对导入
from tools.model_adapter import (
    get_model_config,
    create_adapter,
    ModelProvider,
    MODEL_PRESETS,
)


class TestModelPresets:
    """模型预设测试"""

    def test_openai_presets(self):
        """测试 OpenAI 模型预设"""
        for model in ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "o1", "o1-mini"]:
            preset = MODEL_PRESETS.get(model.lower())
            assert preset is not None, f"Missing preset for {model}"
            assert preset.provider == ModelProvider.OPENAI
            assert "openai.com" in preset.base_url

    def test_qwen_presets(self):
        """测试通义千问模型预设"""
        for model in ["qwen-turbo", "qwen-plus", "qwen-max"]:
            preset = MODEL_PRESETS.get(model.lower())
            assert preset is not None, f"Missing preset for {model}"
            assert preset.provider == ModelProvider.QWEN
            assert "dashscope.aliyuncs.com" in preset.base_url

    def test_anthropic_presets(self):
        """测试 Anthropic 模型预设"""
        for model in ["claude-3-haiku", "claude-3-sonnet", "claude-3-opus"]:
            preset = MODEL_PRESETS.get(model.lower())
            assert preset is not None, f"Missing preset for {model}"
            assert preset.provider == ModelProvider.ANTHROPIC
            assert "anthropic.com" in preset.base_url

    def test_gemini_presets(self):
        """测试 Gemini 模型预设"""
        for model in ["gemini-pro", "gemini-1.5-pro"]:
            preset = MODEL_PRESETS.get(model.lower())
            assert preset is not None, f"Missing preset for {model}"
            assert preset.provider == ModelProvider.GEMINI

    def test_deepseek_presets(self):
        """测试 DeepSeek 模型预设"""
        for model in ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"]:
            preset = MODEL_PRESETS.get(model.lower())
            assert preset is not None, f"Missing preset for {model}"
            assert preset.provider == ModelProvider.DEEPSEEK
            assert "deepseek.com" in preset.base_url


class TestGetModelConfig:
    """获取模型配置测试"""

    def test_get_config_from_preset(self):
        """测试从预设获取配置"""
        config = get_model_config("gpt-3.5-turbo", "test-key")
        assert config.model_name == "gpt-3.5-turbo"
        assert config.provider == ModelProvider.OPENAI
        assert config.api_key == "test-key"

    def test_get_config_custom_base_url(self):
        """测试自定义 base_url"""
        custom_url = "https://custom.api.com/v1"
        config = get_model_config("gpt-3.5-turbo", "test-key", custom_url)
        assert config.base_url == custom_url

    def test_get_config_unknown_model(self):
        """测试未知模型使用默认配置"""
        config = get_model_config("unknown-model", "test-key")
        assert config.provider == ModelProvider.OPENAI_COMPATIBLE
        assert config.model_name == "unknown-model"

    def test_get_config_preset_preserves_base_url(self):
        """测试预设配置的 base_url 被正确保留"""
        config = get_model_config("qwen-turbo", "test-key")
        assert "dashscope.aliyuncs.com" in config.base_url


class TestLLMAdapterCreation:
    """LLM 适配器创建测试"""

    def test_create_openai_adapter(self):
        """测试创建 OpenAI 适配器"""
        adapter = create_llm_adapter("key", "https://api.openai.com/v1", 120, "gpt-4")
        assert isinstance(adapter, OpenAIAdapter)

    def test_create_anthropic_adapter(self):
        """测试创建 Anthropic 适配器"""
        adapter = create_llm_adapter("key", "https://api.anthropic.com/v1/messages", 120, "claude-3-haiku")
        assert isinstance(adapter, AnthropicAdapter)

    def test_create_gemini_adapter(self):
        """测试创建 Gemini 适配器"""
        adapter = create_llm_adapter("key", "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent", 120, "gemini-pro")
        assert isinstance(adapter, GeminiAdapter)

    def test_create_default_adapter(self):
        """测试默认创建 OpenAI 适配器"""
        adapter = create_llm_adapter("key", None, 120, "gpt-4")
        assert isinstance(adapter, OpenAIAdapter)


class TestModelAdapter:
    """模型适配器测试"""

    def test_create_model_adapter(self, temp_env_file):
        """测试创建模型适配器"""
        config = get_model_config("qwen-turbo", "test-key")
        adapter = create_adapter(config)
        assert adapter is not None
        assert hasattr(adapter, 'llm_adapter')

    def test_model_adapter_has_invoke_method(self, temp_env_file):
        """测试模型适配器有 invoke 方法"""
        config = get_model_config("qwen-turbo", "test-key")
        adapter = create_adapter(config)
        assert hasattr(adapter, 'invoke')
        assert callable(adapter.invoke)

    def test_model_adapter_has_stream_invoke_method(self, temp_env_file):
        """测试模型适配器有流式调用方法"""
        config = get_model_config("qwen-turbo", "test-key")
        adapter = create_adapter(config)
        assert hasattr(adapter, 'stream_invoke')
        assert callable(adapter.stream_invoke)

    def test_model_adapter_has_invoke_with_tools_method(self, temp_env_file):
        """测试模型适配器有工具调用方法"""
        config = get_model_config("qwen-turbo", "test-key")
        adapter = create_adapter(config)
        assert hasattr(adapter, 'invoke_with_tools')
        assert callable(adapter.invoke_with_tools)


class TestOpenAIAdapter:
    """OpenAI 适配器单元测试"""

    def test_is_thinking_model(self):
        """测试思考模型判断"""
        adapter = OpenAIAdapter("key", "https://api.openai.com/v1", 120, "gpt-4")

        assert adapter._is_thinking_model("o1") is True
        assert adapter._is_thinking_model("o1-mini") is True
        assert adapter._is_thinking_model("gpt-4") is False
        assert adapter._is_thinking_model("deepseek-reasoner") is True
        assert adapter._is_thinking_model("qwen-reasoner") is True

    @pytest.mark.asyncio
    async def test_astream_invoke_returns_async_iterator(self):
        """测试异步流式调用返回异步迭代器"""
        adapter = OpenAIAdapter("key", "https://api.openai.com/v1", 120, "gpt-4")

        messages = [{"role": "user", "content": "hello"}]

        with patch.object(adapter, 'stream_invoke') as mock_stream:
            mock_stream.return_value = iter(["chunk1", "chunk2", "chunk3"])

            result = []
            async for chunk in adapter.astream_invoke(messages):
                result.append(chunk)

            assert result == ["chunk1", "chunk2", "chunk3"]


class TestAnthropicAdapter:
    """Anthropic 适配器测试"""

    def test_convert_messages(self):
        """测试消息格式转换"""
        adapter = AnthropicAdapter("key", "https://api.anthropic.com", 120, "claude-3-haiku")

        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"}
        ]

        system, converted = adapter._convert_messages(messages)

        assert system == "You are helpful"
        assert len(converted) == 1
        assert converted[0]["role"] == "user"
        assert converted[0]["content"] == "Hello"


class TestGeminiAdapter:
    """Gemini 适配器测试"""

    def test_convert_messages(self):
        """测试消息格式转换"""
        adapter = GeminiAdapter("key", "https://generativelanguage.googleapis.com", 120, "gemini-pro")

        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]

        system, converted = adapter._convert_messages(messages)

        assert system == "You are helpful"
        assert len(converted) == 2
        assert converted[0]["role"] == "user"
        assert converted[1]["role"] == "model"


class TestIntegration:
    """集成测试（需要 mock）"""

    @pytest.mark.asyncio
    async def test_invoke_with_mock_response(self):
        """测试使用 mock 响应的调用"""
        config = get_model_config("gpt-3.5-turbo", "test-key")
        adapter = create_adapter(config)

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello, world!"
        mock_response.choices[0].message.reasoning_content = None
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        with patch.object(adapter.llm_adapter._client.chat.completions, 'create', return_value=mock_response):
            messages = [{"role": "user", "content": "Hi"}]
            response = adapter.invoke(messages)

            assert response.content == "Hello, world!"
            assert response.model == "gpt-3.5-turbo"
            assert response.usage["total_tokens"] == 15

    def test_prepare_request_compatibility(self):
        """测试 prepare_request 向后兼容性"""
        config = get_model_config("qwen-turbo", "test-key")
        adapter = create_adapter(config)

        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hi"}
        ]

        url, headers, payload = adapter.prepare_request(messages)

        assert url != ""
        assert "Content-Type" in headers
        assert payload["model"] == "qwen-turbo"
        assert payload["messages"] == messages
