#!/usr/bin/env python3
"""
Telegram AI Note Auto Collection System - Main Entry Point
官方轮询版本 + 可配置轮询参数 + 优雅关闭
"""
import asyncio
import os
import signal
import sys

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from config.config import get_config
from config import Config
from storage.log_manager import init_log_manager, get_logger
from storage.temp_manager import init_temp_manager
from storage.context_cache import (
    init_context_cache,
    init_user_session_cache,
)
from agent import (
    init_perception_module,
    get_perception_module,
    init_decision_module,
    get_decision_module,
    init_task_scheduler,
    init_exception_handler,
    IntentType,
    TaskResult,
)
from tools import (
    send_message,
    download_file,
    build_welcome_message,
    build_help_message,
    build_processing_message,
    build_success_message,
    build_error_message,
    process_file,
    validate_file,
    generate_obsidian_note,
    write_note_to_file,
    cleanup_file,
)
from tools.web_tool import get_web_tool
from tools.github_tool import (
    init_github_tool,
    get_github_tool,
    create_github_config_from_env,
)

logger = get_logger("Main")

# 优雅关闭全局标记
is_running = True


def signal_handler(signum, frame):
    """捕获 Ctrl+C / 进程终止，实现优雅关闭"""
    global is_running
    logger.info(f"收到终止信号 [{signum}]，准备优雅关闭Bot...")
    is_running = False


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"收到 /start 命令: {update.effective_user.id}")
    await send_message(context, update.effective_chat.id, build_welcome_message())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"收到 /help 命令: {update.effective_user.id}")
    await send_message(context, update.effective_chat.id, build_help_message())


async def push_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"收到 /push 命令: {update.effective_user.id}")

    github_tool = get_github_tool()
    if not github_tool:
        await send_message(
            context,
            update.effective_chat.id,
            build_error_message("GitHub 未配置，请检查环境变量"),
        )
        return

    await send_message(
        context,
        update.effective_chat.id,
        build_processing_message(),
    )

    config = get_config()
    obsidian_path = config.obsidian_vault_path

    if not obsidian_path or not os.path.exists(obsidian_path):
        await send_message(
            context,
            update.effective_chat.id,
            build_error_message("Obsidian 路径未配置或不存在"),
        )
        return

    md_files = []
    for root, _, files in os.walk(obsidian_path):
        for file in files:
            if file.endswith(".md"):
                filepath = os.path.join(root, file)
                md_files.append((filepath, os.path.getmtime(filepath)))

    if not md_files:
        await send_message(
            context,
            update.effective_chat.id,
            build_error_message("未找到任何笔记文件"),
        )
        return

    md_files.sort(key=lambda x: x[1], reverse=True)
    latest_file = md_files[0][0]

    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            content = f.read()

        filename = os.path.basename(latest_file)

        result = github_tool.push_note(
            content=content,
            filename=filename,
            commit_message=f"Add note: {filename}",
        )

        if result.success:
            await send_message(
                context,
                update.effective_chat.id,
                build_success_message(f"已推送 {filename}\n{result.url}"),
            )
        else:
            await send_message(
                context,
                update.effective_chat.id,
                build_error_message(f"推送失败: {result.error}"),
            )

    except Exception as e:
        logger.error(f"推送失败: {e}", exc_info=True)
        await send_message(
            context,
            update.effective_chat.id,
            build_error_message(f"推送失败: {str(e)}"),
        )


async def pull_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"收到 /pull 命令: {update.effective_user.id}")

    github_tool = get_github_tool()
    if not github_tool:
        await send_message(
            context,
            update.effective_chat.id,
            build_error_message("GitHub 未配置，请检查环境变量"),
        )
        return

    await send_message(
        context,
        update.effective_chat.id,
        build_processing_message(),
    )

    config = get_config()
    obsidian_path = config.obsidian_vault_path

    if not obsidian_path:
        await send_message(
            context,
            update.effective_chat.id,
            build_error_message("Obsidian 路径未配置"),
        )
        return

    try:
        result = github_tool.pull_latest_notes(obsidian_path, limit=10)

        if result.success:
            if result.total_count == 0:
                await send_message(
                    context,
                    update.effective_chat.id,
                    build_success_message("仓库中没有找到笔记文件"),
                )
            else:
                file_names = [f.get("name", "unknown") for f in result.files]
                files_list = "\n".join(file_names)
                await send_message(
                    context,
                    update.effective_chat.id,
                    build_success_message(f"已拉取 {result.total_count} 个文件:\n{files_list}"),
                )
        else:
            await send_message(
                context,
                update.effective_chat.id,
                build_error_message(f"拉取失败: {result.error}"),
            )

    except Exception as e:
        logger.error(f"拉取失败: {e}", exc_info=True)
        await send_message(
            context,
            update.effective_chat.id,
            build_error_message(f"拉取失败: {str(e)}"),
        )


async def github_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await push_command(update, context)


async def process_url_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    url: str,
) -> TaskResult:
    await send_message(
        context,
        update.effective_chat.id,
        build_processing_message(),
    )

    logger.info(f"开始处理URL: {url}")

    web_tool = get_web_tool(timeout=30)
    success, content = await web_tool.download_and_convert(url)

    if not success:
        return TaskResult(success=False, error=f"下载网页失败: {content}")

    logger.info(f"网页内容下载成功，内容长度: {len(content)}字符")

    from tools.ai_summary_tool import truncate_content
    content = truncate_content(content, max_chars=5000)

    success, note_content = await generate_obsidian_note(content)

    if not success:
        return TaskResult(success=False, error=note_content)

    logger.info("写入Obsidian")
    success, note_info = write_note_to_file(note_content)
    if not success:
        return TaskResult(success=False, error=note_info.error or "写入Obsidian失败")

    return TaskResult(
        success=True,
        data={
            "note_content": note_content,
            "note_info": note_info,
            "filename": note_info.filename,
        },
    )


async def process_text_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
) -> TaskResult:
    await send_message(
        context,
        update.effective_chat.id,
        build_processing_message(),
    )

    logger.info("开始AI总结")
    success, note_content = await generate_obsidian_note(text)
    if not success:
        return TaskResult(success=False, error=note_content)

    logger.info("写入Obsidian")
    success, note_info = write_note_to_file(note_content)
    if not success:
        return TaskResult(success=False, error=note_info.error or "写入Obsidian失败")

    return TaskResult(
        success=True,
        data={
            "note_content": note_content,
            "note_info": note_info,
            "filename": note_info.filename,
        },
    )


async def process_file_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> TaskResult:
    await send_message(
        context,
        update.effective_chat.id,
        build_processing_message(),
    )

    logger.info("下载文件")
    document = update.effective_message.document
    filename = document.file_name or f"file_{document.file_id}"

    success, filepath, file_size = await download_file(
        context,
        document.file_id,
        filename,
    )
    if not success:
        return TaskResult(success=False, error="文件下载失败")

    logger.info("验证文件")
    is_valid, error_msg = validate_file(filename, file_size or 0)
    if not is_valid:
        cleanup_file(filepath)
        return TaskResult(success=False, error=error_msg)

    logger.info("提取文件文本")
    success, text, _ = process_file(filepath, filename)
    cleanup_file(filepath)
    if not success:
        return TaskResult(success=False, error=text)

    logger.info("AI总结")
    success, note_content = await generate_obsidian_note(text, title=filename)
    if not success:
        return TaskResult(success=False, error=note_content)

    logger.info("写入Obsidian")
    success, note_info = write_note_to_file(note_content, title=filename)
    if not success:
        return TaskResult(success=False, error=note_info.error or "写入Obsidian失败")

    return TaskResult(
        success=True,
        data={
            "note_content": note_content,
            "note_info": note_info,
            "filename": note_info.filename,
        },
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"收到消息: user_id={user_id}")

    try:
        perception_module = get_perception_module()
        perceived_msg = await perception_module.process_update(update, context)

        if not perceived_msg:
            logger.warning("无法处理消息")
            return

        if not perceived_msg.is_authorized:
            logger.warning(f"用户无权限: {user_id}")
            return

        decision_module = get_decision_module()
        decision = decision_module.make_decision(perceived_msg)

        if not decision:
            logger.warning("无法做出决策")
            await send_message(
                context,
                update.effective_chat.id,
                build_error_message("无法识别的消息类型"),
            )
            return

        result = None

        if decision.intent == IntentType.START:
            await start_command(update, context)
            return

        if decision.intent == IntentType.HELP:
            await help_command(update, context)
            return

        if decision.intent == IntentType.PROCESS_URL:
            url = perceived_msg.info.text.strip()
            result = await process_url_message(update, context, url)

        elif decision.intent == IntentType.PROCESS_TEXT:
            text = perceived_msg.info.text
            result = await process_text_message(update, context, text)

        elif decision.intent == IntentType.PROCESS_FILE:
            result = await process_file_message(update, context)

        elif decision.intent == IntentType.PUSH_GITHUB:
            await push_command(update, context)
            return

        elif decision.intent == IntentType.PULL_GITHUB:
            await pull_command(update, context)
            return

        else:
            await send_message(
                context,
                update.effective_chat.id,
                build_error_message("不支持的消息类型"),
            )
            return

        if result and result.success:
            filename = result.data.get("filename", "未知文件") if result.data else "未知文件"
            await send_message(
                context,
                update.effective_chat.id,
                build_success_message(filename),
            )
            logger.info(f"处理完成: {filename}")
        else:
            error_msg = result.error if result else "处理失败"
            await send_message(
                context,
                update.effective_chat.id,
                build_error_message(error_msg),
            )
            logger.error(f"处理失败: {error_msg}")

    except Exception as e:
        logger.error(f"处理消息异常: {e}", exc_info=True)
        await send_message(
            context,
            update.effective_chat.id,
            build_error_message(f"处理异常: {str(e)}"),
        )


def init_github():
    config = get_config()
    if config.github_enabled:
        github_config = create_github_config_from_env()
        if github_config:
            init_github_tool(github_config)
            logger.info(f"GitHub 已初始化: {config.github_owner}/{config.github_repo}")
        else:
            logger.warning("GITHUB_ENABLED=true 但无法创建GitHub配置")
    else:
        logger.info("GitHub 功能未启用")


def init_modules():
    logger.info("正在初始化模块...")

    config = get_config()
    is_valid, error_msg = config.validate()
    if not is_valid:
        raise RuntimeError(f"配置错误: {error_msg}")

    logger.info(f"配置加载成功: TG Token={config.tg_bot_token[:10]}..., AI Model={config.ai_model}")

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


def build_tg_application(config: Config):
    if config is None:
        return None
    if config.use_proxy:
        app = Application.builder().token(config.tg_bot_token).proxy(config.proxy_url).build()
        return app
    else:
        return Application.builder().token(config.tg_bot_token).build()


def run_bot():
    config = get_config()
    init_modules()

    logger.info("正在启动Telegram Bot【官方原生轮询】...")
    application = build_tg_application(config)

    # 注册路由
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("push", push_command))
    application.add_handler(CommandHandler("pull", pull_command))
    application.add_handler(CommandHandler("github", github_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_message))

    # ========== 官方原生 run_polling + 可配置参数 ==========
    poll_interval = getattr(config, "poll_interval", 1)
    timeout = getattr(config, "poll_timeout", 20)

    application.run_polling(
        poll_interval=poll_interval,
        timeout=timeout,
        drop_pending_updates=True,
        close_loop=False
    )


def main():
    print("=" * 60)
    print("  Telegram AI Note Auto Collection System")
    print("  官方轮询 | 可配置轮询参数 | 优雅关闭")
    print("=" * 60)

    # 注册信号监听：优雅关闭
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        run_bot()
    except KeyboardInterrupt:
        logger.info("接收到退出信号，Bot 正在优雅退出...")
    except Exception as e:
        logger.error(f"运行异常: {e}", exc_info=True)
        sys.exit(1)

    logger.info("Bot 已完全停止")


if __name__ == "__main__":
    main()