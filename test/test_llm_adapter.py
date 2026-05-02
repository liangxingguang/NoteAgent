"""LLM 适配器测试脚本"""

import asyncio
from typing import Optional

from config.config import get_config
from tools.llm_adapters import OpenAIAdapter, AnthropicAdapter, GeminiAdapter, create_adapter as create_llm_adapter
# 直接使用相对导入
from tools.model_adapter import get_model_config, create_adapter, MODEL_PRESETS


class TestResult:
    """测试结果"""
    def __init__(self, name: str, passed: bool, message: str = "", details: dict = None):
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details or {}

    def __str__(self):
        status = "✅" if self.passed else "❌"
        result = f"{status} {self.name}"
        if self.message:
            result += f": {self.message}"
        return result


async def test_model_config_preset(model_name: str) -> TestResult:
    """测试模型配置预设"""
    try:
        preset = MODEL_PRESETS.get(model_name.lower())
        if preset is None:
            return TestResult(f"预设配置 [{model_name}]", False, "未找到预设配置")
        if not preset.model_name:
            return TestResult(f"预设配置 [{model_name}]", False, "预设配置不完整")
        return TestResult(f"预设配置 [{model_name}]", True, f"provider={preset.provider.value}")
    except Exception as e:
        return TestResult(f"预设配置 [{model_name}]", False, str(e))


async def test_get_model_config(model_name: str, api_key: str, base_url: Optional[str] = None) -> TestResult:
    """测试获取模型配置"""
    try:
        config = get_model_config(model_name, api_key, base_url)
        if not config:
            return TestResult(f"获取配置 [{model_name}]", False, "返回空配置")
        if not config.model_name:
            return TestResult(f"获取配置 [{model_name}]", False, "配置不完整")
        if not config.provider:
            return TestResult(f"获取配置 [{model_name}]", False, "未设置provider")
        return TestResult(
            f"获取配置 [{model_name}]", True,
            f"provider={config.provider.value}, model={config.model_name}"
        )
    except Exception as e:
        return TestResult(f"获取配置 [{model_name}]", False, str(e))


async def test_adapter_creation(model_name: str, api_key: str, base_url: Optional[str] = None) -> TestResult:
    """测试适配器创建"""
    try:
        model_config = get_model_config(model_name, api_key, base_url)
        adapter = create_adapter(model_config)
        if not adapter:
            return TestResult(f"创建适配器 [{model_name}]", False, "返回空适配器")
        if not hasattr(adapter, 'llm_adapter'):
            return TestResult(f"创建适配器 [{model_name}]", False, "缺少llm_adapter属性")
        return TestResult(f"创建适配器 [{model_name}]", True, type(adapter.llm_adapter).__name__)
    except Exception as e:
        return TestResult(f"创建适配器 [{model_name}]", False, str(e))


async def test_llm_adapter_by_base_url(base_url: str, api_key: str, model: str) -> TestResult:
    """测试根据base_url创建LLM适配器"""
    try:
        adapter = create_llm_adapter(api_key, base_url, 120, model)
        if not adapter:
            return TestResult(f"LLM适配器 [{base_url}]", False, "返回空适配器")

        adapter_type = "Unknown"
        if isinstance(adapter, AnthropicAdapter):
            adapter_type = "AnthropicAdapter"
        elif isinstance(adapter, GeminiAdapter):
            adapter_type = "GeminiAdapter"
        elif isinstance(adapter, OpenAIAdapter):
            adapter_type = "OpenAIAdapter"

        return TestResult(f"LLM适配器 [{base_url}]", True, adapter_type)
    except Exception as e:
        return TestResult(f"LLM适配器 [{base_url}]", False, str(e))


async def test_invoke(model_name: str, api_key: str, base_url: Optional[str] = None) -> TestResult:
    """测试非流式调用"""
    try:
        model_config = get_model_config(model_name, api_key, base_url)
        adapter = create_adapter(model_config)

        messages = [
            {"role": "system", "content": "你是一个助手，回答问题要简洁明了。"},
            {"role": "user", "content": "1+1等于几?"}
        ]

        response = adapter.invoke(messages, temperature=0.7, max_tokens=50)

        if not response:
            return TestResult(f"调用 [{model_name}]", False, "返回空响应")

        if not response.content:
            return TestResult(f"调用 [{model_name}]", False, "响应内容为空")

        details = {
            "latency_ms": response.latency_ms,
            "usage": response.usage,
            "model": response.model
        }

        return TestResult(
            f"调用 [{model_name}]", True,
            f"用时{response.latency_ms}ms, tokens={response.usage.get('total_tokens', 0)}",
            details
        )
    except Exception as e:
        return TestResult(f"调用 [{model_name}]", False, str(e))


async def test_stream_invoke(model_name: str, api_key: str, base_url: Optional[str] = None) -> TestResult:
    """测试流式调用"""
    try:
        model_config = get_model_config(model_name, api_key, base_url)
        adapter = create_adapter(model_config)

        messages = [
            {"role": "system", "content": "你是一个助手。"},
            {"role": "user", "content": "写一首关于春天的诗"}
        ]

        result = await adapter.astream_invoke(messages, temperature=0.7, max_tokens=100)

        if not result:
            return TestResult(f"流式调用 [{model_name}]", False, "返回空结果")

        if len(result) < 5:
            return TestResult(f"流式调用 [{model_name}]", False, f"结果过短: {result}")

        return TestResult(f"流式调用 [{model_name}]", True, f"长度={len(result)}字符")
    except Exception as e:
        return TestResult(f"流式调用 [{model_name}]", False, str(e))


async def test_invoke_with_tools(model_name: str, api_key: str, base_url: Optional[str] = None) -> TestResult:
    """测试工具调用"""
    try:
        model_config = get_model_config(model_name, api_key, base_url)
        adapter = create_adapter(model_config)

        messages = [
            {"role": "system", "content": "你是一个助手，可以使用工具。"},
            {"role": "user", "content": "北京的天气怎么样?"}
        ]

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "获取指定城市的天气",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "城市名称"
                            }
                        },
                        "required": ["city"]
                    }
                }
            }
        ]

        response = adapter.invoke_with_tools(messages, tools, temperature=0.7, max_tokens=200)

        if not response:
            return TestResult(f"工具调用 [{model_name}]", False, "返回空响应")

        details = {
            "has_content": bool(response.content),
            "tool_calls_count": len(response.tool_calls),
            "latency_ms": response.latency_ms
        }

        if response.tool_calls:
            details["first_tool"] = response.tool_calls[0].name

        return TestResult(
            f"工具调用 [{model_name}]", True,
            f"tool_calls={len(response.tool_calls)}, content_length={len(response.content) if response.content else 0}",
            details
        )
    except Exception as e:
        return TestResult(f"工具调用 [{model_name}]", False, str(e))


async def test_thinking_model(model_name: str, api_key: str, base_url: Optional[str] = None) -> TestResult:
    """测试思考模型（如 o1, deepseek-reasoner）"""
    try:
        model_config = get_model_config(model_name, api_key, base_url)
        adapter = create_adapter(model_config)

        if not hasattr(adapter.llm_adapter, '_is_thinking_model'):
            return TestResult(f"思考模型 [{model_name}]", False, "适配器不支持思考模型检测")

        is_thinking = adapter.llm_adapter._is_thinking_model(model_name)

        messages = [
            {"role": "user", "content": "解释为什么天空是蓝色的"}
        ]

        response = adapter.invoke(messages, max_tokens=200)

        details = {
            "is_thinking_model": is_thinking,
            "has_reasoning_content": bool(getattr(response, 'reasoning_content', None)),
            "latency_ms": response.latency_ms
        }

        return TestResult(
            f"思考模型 [{model_name}]", True,
            f"is_thinking={is_thinking}, reasoning={bool(details['has_reasoning_content'])}",
            details
        )
    except Exception as e:
        return TestResult(f"思考模型 [{model_name}]", False, str(e))


async def test_error_handling(model_name: str, api_key: str = "invalid_key", base_url: Optional[str] = None) -> TestResult:
    """测试错误处理"""
    try:
        model_config = get_model_config(model_name, api_key, base_url)
        adapter = create_adapter(model_config)

        messages = [{"role": "user", "content": "test"}]

        try:
            response = adapter.invoke(messages, max_tokens=10)
            if "invalid" in api_key.lower():
                return TestResult(f"错误处理 [{model_name}]", False, "未捕获无效API key错误")
        except Exception as e:
            pass

        return TestResult(f"错误处理 [{model_name}]", True, "错误处理正常")
    except Exception as e:
        return TestResult(f"错误处理 [{model_name}]", False, str(e))


async def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("LLM 适配器测试套件")
    print("=" * 60)

    config = get_config()
    api_key = config.ai_api_key

    if not api_key:
        print("\n❌ 错误: 未配置 AI_API_KEY")
        print("请在 .env 文件中设置 AI_API_KEY")
        return

    print(f"\nAPI Key: {api_key[:8]}...{api_key[-4:]}")
    print(f"默认模型: {config.ai_model}")
    print(f"默认Base URL: {config.ai_base_url or '未设置 (使用默认值)'}")
    print()

    test_suites = [
        ("模型配置预设测试", [
            ("gpt-3.5-turbo", None),
            ("gpt-4", None),
            ("o1", None),
            ("qwen-turbo", None),
            ("qwen-plus", None),
            ("deepseek-chat", None),
            ("deepseek-reasoner", None),
            ("claude-3-haiku", None),
            ("gemini-pro", None),
        ], test_model_config_preset),

        ("模型配置获取测试", [
            ("gpt-3.5-turbo", None),
            ("gpt-4", None),
            ("o1", None),
            ("qwen-turbo", None),
            ("deepseek-chat", None),
            ("deepseek-reasoner", None),
        ], lambda m: test_get_model_config(m, api_key)),

        ("适配器创建测试", [
            ("gpt-3.5-turbo", None),
            ("qwen-turbo", None),
            ("deepseek-chat", None),
        ], lambda m: test_adapter_creation(m, api_key)),

        ("LLM适配器类型测试", [
            ("https://api.openai.com/v1", "key", "gpt-4"),
            ("https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions", "key", "qwen-turbo"),
            ("https://api.anthropic.com/v1/messages", "key", "claude-3-haiku"),
            ("https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent", "key", "gemini-pro"),
        ], lambda u: test_llm_adapter_by_base_url(u[0], u[1], u[2])),
    ]

    all_results = []

    for suite_name, test_cases, test_func in test_suites:
        print(f"\n{suite_name}")
        print("-" * 50)

        for test_case in test_cases:
            if isinstance(test_case, tuple):
                result = await test_func(test_case[0], *test_case[1:])
            else:
                result = await test_func(test_case)
            print(f"  {result}")
            all_results.append(result)

    print("\n" + "=" * 60)
    print("需要实际API调用的测试 (会消耗token)")
    print("=" * 60)

    invoke_tests = [
        ("gpt-3.5-turbo", None),
        ("qwen-turbo", None),
        ("deepseek-chat", None),
    ]

    for model_name, base_url in invoke_tests:
        print(f"\n测试模型: {model_name}")
        print("-" * 50)

        result = await test_invoke(model_name, api_key, base_url)
        print(f"  {result}")
        all_results.append(result)

        await asyncio.sleep(1)

        result = await test_stream_invoke(model_name, api_key, base_url)
        print(f"  {result}")
        all_results.append(result)

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    passed = sum(1 for r in all_results if r.passed)
    failed = sum(1 for r in all_results if not r.passed)

    for result in all_results:
        status = "✅" if result.passed else "❌"
        print(f"  {status} {result.name}: {result.message}")

    print(f"\n通过: {passed}/{len(all_results)}")
    print(f"失败: {failed}/{len(all_results)}")

    if failed > 0:
        print("\n失败的测试:")
        for result in all_results:
            if not result.passed:
                print(f"  - {result.name}: {result.message}")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
