"""配置管理模块"""
import os
from typing import Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv



@dataclass
class Config:
    """配置类"""

    tg_bot_token: str = ""
    allowed_user_ids: list[int] = field(default_factory=list)
    use_proxy: bool = False
    proxy_url: str = ""

    ai_api_key: str = ""
    ai_model: str = "qwen-turbo"
    ai_base_url: Optional[str] = None
    ai_temperature: float = 0.7
    ai_max_tokens: int = 2000

    obsidian_vault_path: str = ""

    github_token: str = ""
    github_owner: str = ""
    github_repo: str = ""
    github_branch: str = "main"
    github_enabled: bool = False

    log_level: str = "INFO"
    temp_dir: str = "storage/temp_files"
    log_dir: str = "storage/logs"

    max_file_size: int = 50 * 1024 * 1024
    max_text_length: int = 5000

    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "Config":
        """从环境变量加载配置"""
        env_paths = []
        if env_file:
            env_paths.append(env_file)

        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_paths.append(os.path.join(project_root, ".env"))
        env_paths.append(os.path.join(project_root, "config", ".env"))

        loaded = False
        for path in env_paths:
            if os.path.exists(path):
                load_dotenv(path, override=True)
                loaded = True
                break

        if not loaded:
            load_dotenv(override=True)

        allowed_user_ids_str = os.getenv("ALLOWED_USER_IDS", "")
        allowed_user_ids = []
        if allowed_user_ids_str:
            allowed_user_ids = [
                int(uid.strip()) for uid in allowed_user_ids_str.split(",") if uid.strip()
            ]

        github_enabled_str = os.getenv("GITHUB_ENABLED", "false").lower()
        github_enabled = github_enabled_str in ("true", "1", "yes")

        return cls(
            tg_bot_token=os.getenv("TG_BOT_TOKEN", ""),
            allowed_user_ids=allowed_user_ids,
            use_proxy=os.getenv("USE_PROXY", "false").lower() == "true",
            proxy_url=os.getenv("PROXY_URL", ""),
            ai_api_key=os.getenv("AI_API_KEY", ""),
            ai_model=os.getenv("AI_MODEL", "qwen-turbo"),
            ai_base_url=os.getenv("AI_BASE_URL"),
            ai_temperature=float(os.getenv("AI_TEMPERATURE", "0.7")),
            ai_max_tokens=int(os.getenv("AI_MAX_TOKENS", "2000")),
            obsidian_vault_path=os.getenv("OBSIDIAN_VAULT_PATH", ""),
            github_token=os.getenv("GITHUB_TOKEN", ""),
            github_owner=os.getenv("GITHUB_OWNER", ""),
            github_repo=os.getenv("GITHUB_REPO", ""),
            github_branch=os.getenv("GITHUB_BRANCH", "main"),
            github_enabled=github_enabled,
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            temp_dir=os.getenv("TEMP_DIR", "storage/temp_files"),
            log_dir=os.getenv("LOG_DIR", "storage/logs"),
        )

    def validate(self) -> tuple[bool, str]:
        """验证配置是否完整"""
        if not self.tg_bot_token:
            return False, "TG_BOT_TOKEN 未配置"

        if not self.ai_api_key:
            return False, "AI_API_KEY 未配置"

        if not self.obsidian_vault_path:
            return False, "OBSIDIAN_VAULT_PATH 未配置"

        if self.github_enabled:
            if not self.github_token:
                return False, "GITHUB_ENABLED 为 true 但 GITHUB_TOKEN 未配置"
            if not self.github_owner:
                return False, "GITHUB_ENABLED 为 true 但 GITHUB_OWNER 未配置"
            if not self.github_repo:
                return False, "GITHUB_ENABLED 为 true 但 GITHUB_REPO 未配置"

        return True, ""


_config: Optional[Config] = None


def get_config(env_file: Optional[str] = None) -> Config:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = Config.from_env(env_file)
    return _config


def reload_config(env_file: Optional[str] = None) -> Config:
    """重新加载配置"""
    global _config
    _config = Config.from_env(env_file)
    return _config
