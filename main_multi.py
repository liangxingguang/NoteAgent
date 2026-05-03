
#!/usr/bin/env python3
"""
NoteAgents - 多平台 AI 笔记自动收集系统
支持 Telegram 和飞书双平台
"""
import asyncio
import os
import signal
import sys

# 设置 sniffio 以支持 python-telegram-bot（必须放在最前面）
try:
    import sniffio
    from sniffio import AsyncLibraryNotFoundError

    # 保存原始的 sniffio 函数
    _original_current_async_library = sniffio.current_async_library

    def _patched_current_async_library():
        try:
            return _original_current_async_library()
        except AsyncLibraryNotFoundError:
            # 如果无法检测到，默认返回 asyncio
            return "asyncio"

    sniffio.current_async_library = _patched_current_async_library
except ImportError:
    pass

# 应用 nest_asyncio 解决事件循环冲突问题（只在需要时启用）
# 注意：nest_asyncio 可能与 python-telegram-bot 的 anyio 冲突
try:
    import os
    # 检查是否启用了飞书 webhook，这是最需要 nest_asyncio 的场景
    feishu_webhook_enabled = os.getenv("FEISHU_USE_WEBHOOK", "false").lower() == "true"
    tg_webhook_enabled = os.getenv("TG_USE_WEBHOOK", "false").lower() == "true"

    if feishu_webhook_enabled or tg_webhook_enabled:
        import nest_asyncio
        nest_asyncio.apply()
except ImportError:
    pass

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from config.config import get_config
from storage.log_manager import init_log_manager, get_logger
from storage.temp_manager import init_temp_manager
from storage.context_cache import (
    init_context_cache,
    init_user_session_cache,
)
from agent import (
    init_perception_module,
    init_decision_module,
    init_task_scheduler,
    init_exception_handler,
)
from tools.github_tool import (
    init_github_tool,
    create_github_config_from_env,
)
from platforms import (
    PlatformManager,
    PlatformType,
    UnifiedMessage,
    MessageCoordinator,
    setup_platform_manager,
    FeishuAdapter,
)
from tools.feishu_tool import build_platform_start_message
from tools import get_wiki_tool


logger = get_logger("MainMulti")

# 优雅关闭全局标记
is_running = True


def signal_handler(signum, frame):
    """捕获 Ctrl+C / 进程终止，实现优雅关闭"""
    global is_running
    logger.info(f"收到终止信号 [{signum}]，准备优雅关闭...")
    is_running = False


def init_github():
    """初始化 GitHub 工具"""
    config = get_config()
    if config.github_enabled:
        github_config = create_github_config_from_env()
        if github_config:
            init_github_tool(github_config)
            logger.info(f"GitHub 已初始化: {config.github_owner}/{config.github_repo}")
        else:
            logger.warning("GITHUB_ENABLED=true 但无法创建 GitHub 配置")
    else:
        logger.info("GitHub 功能未启用")


def init_modules():
    """初始化所有模块"""
    logger.info("正在初始化模块...")

    config = get_config()
    is_valid, error_msg = config.validate()
    if not is_valid:
        raise RuntimeError(f"配置错误: {error_msg}")

    # 打印配置摘要
    config_summary = []
    if config.telegram.bot_token:
        config_summary.append(f"Telegram: Token={config.telegram.bot_token[:10]}...")
    if config.feishu.enabled:
        config_summary.append(f"飞书: AppID={config.feishu.app_id[:10]}...")
    config_summary.append(f"AI Model={config.ai_model}")

    logger.info(f"配置加载成功: {' | '.join(config_summary)}")

    init_log_manager(config.log_dir, config.log_level)
    init_temp_manager(config.temp_dir)
    init_context_cache()
    init_user_session_cache()

    init_perception_module()
    init_decision_module()
    init_task_scheduler()
    init_exception_handler()
    init_github()

    logger.info("所有模块初始化完成")


class NoteAgentsApp:
    """
    NoteAgents 主应用 - 多平台版本
    集成 LLM Wiki 模块！
    """

    def __init__(self):
        self.config = get_config()
        self.platform_manager = None
        self.coordinator = None
        self.running = True
        self._telegram_task = None
        self._wiki_watcher = None  # LLM Wiki 文件监控

    async def initialize(self):
        """初始化应用"""
        init_modules()

        # 初始化 LLM Wiki 模块
        logger.info("初始化 LLM Wiki 模块...")
        try:
            if self.config.wiki.enabled and self.config.wiki.file_monitor_enabled:
                # 配置为 true 时才启动文件监控
                wiki = get_wiki_tool()
                # 使用配置的间隔
                poll_interval = self.config.wiki.file_monitor_interval
                watcher = wiki.start_watcher(poll_interval=poll_interval)
                self._wiki_watcher = watcher
                logger.info(f"LLM Wiki 文件监控已启动（间隔: {poll_interval}s，保存即整理！）")
            else:
                if not self.config.wiki.enabled:
                    logger.info("LLM Wiki 功能未启用（WIKI_ENABLED=false）")
                else:
                    logger.info("LLM Wiki 文件监控未启用（WIKI_FILE_MONITOR_ENABLED=false）")
        except Exception as e:
            logger.warning(f"LLM Wiki 初始化异常（不影响主流程）: {e}")

        # 设置平台管理器
        self.platform_manager = setup_platform_manager(self.config)

        # 初始化所有平台
        success = await self.platform_manager.initialize_all()
        if not success:
            logger.warning("部分平台初始化失败，但继续运行已启用的平台")

        # 创建消息协调器
        self.coordinator = MessageCoordinator(self.platform_manager)

        # 注册消息处理回调
        self.platform_manager.add_message_handler(self._handle_message)

        # 获取已启用平台
        enabled_platforms = self.platform_manager.get_enabled_platforms()
        if not enabled_platforms:
            raise RuntimeError("没有启用任何平台，请检查配置")

        logger.info(build_platform_start_message(enabled_platforms))

    def _handle_message(self, msg: UnifiedMessage):
        """处理收到的统一消息"""
        # 在后台任务中处理消息
        asyncio.create_task(self.coordinator.process_message(msg))

    async def run(self):
        """运行应用"""
        await self.initialize()

        # 启动所有平台监听
        await self.platform_manager.start_all()

        # 如果启用了 Telegram，使用平台管理器
        if self.config.telegram.enabled and self.config.telegram.bot_token:
            logger.info("Telegram 支持已通过平台管理器配置")

        # 主循环
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("收到退出信号")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """关闭应用"""
        logger.info("正在关闭...")
        if self.platform_manager:
            await self.platform_manager.stop_all()
        logger.info("应用已完全停止")


def print_banner():
    """打印启动横幅"""
    print("=" * 60)
    print("  NoteAgents - 多平台 AI 笔记自动收集系统")
    print("  支持: Telegram | 飞书")
    print("=" * 60)


def main():
    """主函数"""
    print_banner()

    # 注册信号监听
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    app = NoteAgentsApp()

    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        logger.info("接收到退出信号")
    except Exception as e:
        logger.error(f"运行异常: {e}", exc_info=True)
        sys.exit(1)

    logger.info("应用已停止")


if __name__ == "__main__":
    main()
