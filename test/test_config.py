"""配置模块测试"""

import os

# 直接使用相对导入
from config.config import Config, get_config, reload_config


class TestConfig:
    """配置类测试"""

    def test_config_from_env(self, temp_env_file):
        """测试从环境变量加载配置"""
        config = Config.from_env(temp_env_file)

        assert config.tg_bot_token == "test_token_123"
        assert config.allowed_user_ids == [123456, 789012]
        assert config.ai_api_key == "test_ai_key_456"
        assert config.ai_model == "qwen-turbo"
        assert config.ai_temperature == 0.7
        assert config.ai_max_tokens == 2000
        assert config.obsidian_vault_path == "/test/path"
        assert config.log_level == "DEBUG"

    def test_config_validate_success(self, temp_env_file):
        """测试配置验证成功"""
        config = Config.from_env(temp_env_file)
        is_valid, msg = config.validate()

        assert is_valid is True
        assert msg == ""

    def test_config_validate_missing_token(self):
        """测试配置验证失败 - 缺少 TG_BOT_TOKEN"""
        config = Config(
            tg_bot_token="",
            allowed_user_ids=[],
            ai_api_key="test_key",
            ai_model="qwen-turbo",
            obsidian_vault_path="/test/path"
        )
        is_valid, msg = config.validate()

        assert is_valid is False
        assert "TG_BOT_TOKEN" in msg

    def test_config_validate_missing_ai_key(self):
        """测试配置验证失败 - 缺少 AI_API_KEY"""
        config = Config(
            tg_bot_token="test_token",
            allowed_user_ids=[],
            ai_api_key="",
            ai_model="qwen-turbo",
            obsidian_vault_path="/test/path"
        )
        is_valid, msg = config.validate()

        assert is_valid is False
        assert "AI_API_KEY" in msg

    def test_config_validate_missing_obsidian_path(self):
        """测试配置验证失败 - 缺少 OBSIDIAN_VAULT_PATH"""
        config = Config(
            tg_bot_token="test_token",
            allowed_user_ids=[],
            ai_api_key="test_key",
            ai_model="qwen-turbo",
            obsidian_vault_path=""
        )
        is_valid, msg = config.validate()

        assert is_valid is False
        assert "OBSIDIAN_VAULT_PATH" in msg

    def test_config_allowed_users_parsing(self):
        """测试用户ID列表解析"""
        with open("test_env_temp.env", "w", encoding="utf-8") as f:
            f.write("""
TG_BOT_TOKEN=test_token
ALLOWED_USER_IDS=111,222,333
AI_API_KEY=test_key
OBSIDIAN_VAULT_PATH=/test
LOG_LEVEL=INFO
""")
        try:
            config = Config.from_env("test_env_temp.env")
            assert config.allowed_user_ids == [111, 222, 333]
        finally:
            os.remove("test_env_temp.env")

    def test_config_default_values(self):
        """测试默认值"""
        with open("test_env_default.env", "w", encoding="utf-8") as f:
            f.write("""
TG_BOT_TOKEN=test_token
AI_API_KEY=test_key
OBSIDIAN_VAULT_PATH=/test
LOG_LEVEL=INFO
""")
        try:
            config = Config.from_env("test_env_default.env")
            assert config.ai_model == "qwen-turbo"
            assert config.ai_temperature == 0.7
            assert config.ai_max_tokens == 2000
            assert config.log_level == "INFO"
        finally:
            os.remove("test_env_default.env")

    def test_get_config_singleton(self, temp_env_file):
        """测试 get_config 单例模式"""
        config1 = get_config(temp_env_file)
        config2 = get_config(temp_env_file)

        assert config1 is config2

    def test_reload_config(self, temp_env_file):
        """测试重新加载配置"""
        config1 = get_config(temp_env_file)

        with open(temp_env_file, "w", encoding="utf-8") as f:
            f.write("""
TG_BOT_TOKEN=new_token
ALLOWED_USER_IDS=999
AI_API_KEY=new_key
OBSIDIAN_VAULT_PATH=/new/path
""")

        config2 = reload_config(temp_env_file)

        assert config2.tg_bot_token == "new_token"
        assert config2.allowed_user_ids == [999]
        assert config2.ai_api_key == "new_key"
