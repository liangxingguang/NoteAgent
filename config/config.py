"""配置管理模块"""
import os
from typing import Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv


@dataclass
class FeishuConfig:
    """飞书平台配置"""
    enabled: bool = False
    app_id: str = ""
    app_secret: str = ""
    verification_token: str = ""
    encrypt_key: str = ""
    bot_name: str = "NoteAgents"
    allowed_user_ids: list[str] = field(default_factory=list)
    poll_interval: float = 1.0
    use_webhook: bool = False
    webhook_host: str = "0.0.0.0"
    webhook_port: int = 8000


@dataclass
class TelegramConfig:
    """Telegram 平台配置"""
    enabled: bool = False
    bot_token: str = ""
    allowed_user_ids: list[int] = field(default_factory=list)
    use_proxy: bool = False
    proxy_url: str = ""
    poll_interval: float = 1.0
    poll_timeout: int = 20
    use_webhook: bool = False
    webhook_url: str = ""
    webhook_host: str = "0.0.0.0"
    webhook_port: int = 8443
    webhook_secret: str = ""


@dataclass
class WikiConfig:
    """LLM Wiki 配置"""
    enabled: bool = False
    vault_path: str = ""
    archive_strategy: str = "daily"

    llm_api_key: str = ""
    llm_model: str = "qwen-turbo"
    llm_base_url: Optional[str] = None
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000
    llm_retry_times: int = 3

    auto_process: bool = True
    auto_import_wiki: bool = False

    file_monitor_enabled: bool = True
    file_monitor_interval: int = 5

    health_check_interval: int = 7

    structured_categories: list[str] = field(
        default_factory=lambda: ["技术类", "想法类", "学习类", "日常类"]
    )


@dataclass
class Config:
    """配置类"""

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

    # 飞书配置
    feishu: FeishuConfig = field(default_factory=FeishuConfig)
    
    # Telegram 配置（新）
    telegram: TelegramConfig = field(default_factory=TelegramConfig)

    # Wiki 配置
    wiki: WikiConfig = field(default_factory=WikiConfig)

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

        # 解析 Telegram 允许的用户 ID
        allowed_user_ids_str = os.getenv("ALLOWED_USER_IDS", "")
        allowed_user_ids = []
        if allowed_user_ids_str:
            allowed_user_ids = [
                int(uid.strip()) for uid in allowed_user_ids_str.split(",") if uid.strip()
            ]

        # GitHub 配置
        github_enabled_str = os.getenv("GITHUB_ENABLED", "false").lower()
        github_enabled = github_enabled_str in ("true", "1", "yes")

        # 飞书配置
        feishu_enabled_str = os.getenv("FEISHU_ENABLED", "false").lower()
        feishu_enabled = feishu_enabled_str in ("true", "1", "yes")

        feishu_allowed_user_ids_str = os.getenv("FEISHU_ALLOWED_USER_IDS", "")
        feishu_allowed_user_ids = []
        if feishu_allowed_user_ids_str:
            feishu_allowed_user_ids = [
                uid.strip() for uid in feishu_allowed_user_ids_str.split(",") if uid.strip()
            ]

        feishu_config = FeishuConfig(
            enabled=feishu_enabled,
            app_id=os.getenv("FEISHU_APP_ID", ""),
            app_secret=os.getenv("FEISHU_APP_SECRET", ""),
            verification_token=os.getenv("FEISHU_VERIFICATION_TOKEN", ""),
            encrypt_key=os.getenv("FEISHU_ENCRYPT_KEY", ""),
            bot_name=os.getenv("FEISHU_BOT_NAME", "NoteAgents"),
            allowed_user_ids=feishu_allowed_user_ids,
            poll_interval=float(os.getenv("FEISHU_POLL_INTERVAL", "1.0")),
            use_webhook=os.getenv("FEISHU_USE_WEBHOOK", "false").lower() in ("true", "1", "yes"),
            webhook_host=os.getenv("FEISHU_WEBHOOK_HOST", "0.0.0.0"),
            webhook_port=int(os.getenv("FEISHU_WEBHOOK_PORT", "8000")),
        )

        # Telegram 配置
        tg_enabled = os.getenv("TG_ENABLED", "true").lower() in ("true", "1", "yes")
        tg_enabled_str = os.getenv("TG_USE_WEBHOOK", "false").lower()
        tg_use_webhook = tg_enabled_str in ("true", "1", "yes")
        tg_bot_token = os.getenv("TG_BOT_TOKEN", "")
        telegram_config = TelegramConfig(
            enabled=tg_enabled and bool(tg_bot_token),
            bot_token=tg_bot_token,
            allowed_user_ids=allowed_user_ids,
            use_proxy=os.getenv("TG_USE_PROXY", "false").lower() == "true",
            proxy_url=os.getenv("TG_PROXY_URL", ""),
            poll_interval=float(os.getenv("TG_POLL_INTERVAL", "1.0")),
            poll_timeout=int(os.getenv("TG_POLL_TIMEOUT", "20")),
            use_webhook=tg_use_webhook,
            webhook_url=os.getenv("TG_WEBHOOK_URL", ""),
            webhook_host=os.getenv("TG_WEBHOOK_HOST", "0.0.0.0"),
            webhook_port=int(os.getenv("TG_WEBHOOK_PORT", "8443")),
            webhook_secret=os.getenv("TG_WEBHOOK_SECRET", ""),
        )

        # Wiki 配置
        wiki_enabled_str = os.getenv("WIKI_ENABLED", "false").lower()
        wiki_enabled = wiki_enabled_str in ("true", "1", "yes")
        wiki_config = WikiConfig(
            enabled=wiki_enabled,
            vault_path=os.getenv("OBSIDIAN_VAULT_PATH", ""),
            archive_strategy=os.getenv("WIKI_ARCHIVE_STRATEGY", "daily"),
            llm_api_key=os.getenv("WIKI_LLM_API_KEY", os.getenv("AI_API_KEY", "")),
            llm_model=os.getenv("WIKI_LLM_MODEL") or os.getenv("AI_MODEL", "qwen-turbo"),
            llm_base_url=os.getenv("WIKI_LLM_BASE_URL") or os.getenv("AI_BASE_URL"),
            llm_temperature=float(os.getenv("WIKI_LLM_TEMPERATURE", "0.7")),
            llm_max_tokens=int(os.getenv("WIKI_LLM_MAX_TOKENS", "2000")),
            llm_retry_times=int(os.getenv("WIKI_LLM_RETRY_TIMES", "3")),
            auto_process=os.getenv("WIKI_AUTO_PROCESS", "true").lower() in ("true", "1", "yes"),
            auto_import_wiki=os.getenv("WIKI_AUTO_IMPORT_WIKI", "false").lower() in ("true", "1", "yes"),
            file_monitor_enabled=os.getenv("WIKI_FILE_MONITOR_ENABLED", "true").lower() in ("true", "1", "yes"),
            file_monitor_interval=int(os.getenv("WIKI_FILE_MONITOR_INTERVAL", "5")),
            health_check_interval=int(os.getenv("WIKI_HEALTH_CHECK_INTERVAL", "7")),
        )

        return cls(
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
            feishu=feishu_config,
            telegram=telegram_config,
            wiki=wiki_config,
        )

    def validate(self) -> tuple[bool, str]:
        """验证配置是否完整"""
        # 验证必配项 - 至少需要 Telegram 或飞书其中之一启用
        has_telegram = self.telegram.enabled and bool(self.telegram.bot_token)
        has_feishu = self.feishu.enabled and bool(self.feishu.app_id) and bool(self.feishu.app_secret)

        if not has_telegram and not has_feishu:
            return False, "需要至少配置 TG_BOT_TOKEN 或启用飞书并配置 FEISHU_APP_ID/FEISHU_APP_SECRET"

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

        # 验证飞书配置（如果启用）
        if self.feishu.enabled:
            if not self.feishu.app_id:
                return False, "FEISHU_ENABLED 为 true 但 FEISHU_APP_ID 未配置"
            if not self.feishu.app_secret:
                return False, "FEISHU_ENABLED 为 true 但 FEISHU_APP_SECRET 未配置"

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
