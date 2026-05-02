"""pytest 配置文件"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """在测试开始前配置环境"""
    # 确保项目根目录在路径的最前面
    project_root = Path(__file__).parent.parent
    root_str = str(project_root)
    
    # 移除可能存在的重复路径
    sys.path = [p for p in sys.path if project_root not in Path(p).parents]
    
    # 将项目根目录添加到最前面
    sys.path.insert(0, root_str)


# 尝试导入 NoteAgents 包，如果失败则添加本地包到路径
try:
    import NoteAgents
except ImportError:
    # 如果无法导入 NoteAgents 包，说明没有以可编辑模式安装
    # 添加本地包目录到路径
    sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_env_file():
    """创建临时环境变量文件"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False, encoding='utf-8') as f:
        f.write("""
TG_BOT_TOKEN=test_token_123
ALLOWED_USER_IDS=123456,789012
AI_API_KEY=test_ai_key_456
AI_MODEL=qwen-turbo
AI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=2000
OBSIDIAN_VAULT_PATH=/test/path
LOG_LEVEL=DEBUG
TEMP_DIR=storage/temp_files
LOG_DIR=storage/logs
""")
        temp_path = f.name

    yield temp_path

    # 清理
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture
def sample_messages():
    """示例对话消息"""
    return [
        {"role": "system", "content": "你是一个助手，回答问题要简洁明了。"},
        {"role": "user", "content": "1+1等于几?"}
    ]


@pytest.fixture
def sample_tools():
    """示例工具定义"""
    return [
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
