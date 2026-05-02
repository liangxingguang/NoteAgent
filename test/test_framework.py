"""测试基础框架"""

import os
import sys


def test_config():
    """测试配置模块"""
    print("=" * 50)
    print("测试配置模块...")
    print("=" * 50)

    from config.config import get_config

    # 创建临时.env文件进行测试
    test_env = os.path.join(os.path.dirname(__file__), ".test.env")
    with open(test_env, "w", encoding="utf-8") as f:
        f.write("""
TG_BOT_TOKEN=test_token_123
ALLOWED_USER_IDS=123456,789012
AI_API_KEY=test_ai_key_456
OBSIDIAN_VAULT_PATH=/test/path
LOG_LEVEL=DEBUG
""")

    config = get_config(test_env)
    print(f"TG Token: {config.tg_bot_token}")
    print(f"Allowed Users: {config.allowed_user_ids}")
    print(f"AI Key: {config.ai_api_key}")
    print(f"Obsidian Path: {config.obsidian_vault_path}")
    print(f"Log Level: {config.log_level}")

    # 验证配置
    is_valid, msg = config.validate()
    print(f"配置验证: {'通过' if is_valid else '失败'} - {msg}")

    # 清理临时文件
    os.remove(test_env)
    print("配置模块测试通过！\n")
    return True


def test_logging():
    """测试日志模块"""
    print("=" * 50)
    print("测试日志模块...")
    print("=" * 50)

    from storage.log_manager import init_log_manager, get_logger

    log_manager = init_log_manager("storage/test_logs", "DEBUG")
    logger = get_logger("Test")

    logger.debug("这是DEBUG日志")
    logger.info("这是INFO日志")
    logger.warning("这是WARNING日志")
    logger.error("这是ERROR日志")

    print("日志模块测试通过！\n")
    return True


def test_temp_manager():
    """测试临时文件管理"""
    print("=" * 50)
    print("测试临时文件管理...")
    print("=" * 50)

    from storage import init_temp_manager

    temp_manager = init_temp_manager("storage/test_temp")

    # 测试获取临时路径
    temp_path = temp_manager.get_temp_path("test.txt")
    print(f"临时文件路径: {temp_path}")

    # 测试创建临时目录
    temp_dir = temp_manager.create_temp_dir()
    print(f"临时目录: {temp_dir}")

    # 测试创建文件
    with open(temp_path, "w", encoding="utf-8") as f:
        f.write("测试内容")

    print("临时文件创建成功")

    # 测试删除文件
    temp_manager.delete_file(temp_path)
    temp_manager.delete_file(temp_dir)

    print("临时文件管理测试通过！\n")
    return True


def test_utils():
    """测试工具模块"""
    print("=" * 50)
    print("测试工具模块...")
    print("=" * 50)

    from utils.file_utils import (
        get_file_extension,
        is_supported_file,
        get_text_hash,
        format_file_size,
    )
    from utils.text_utils import (
        truncate_text,
        generate_timestamp,
        clean_text,
    )
    from utils.api_utils import mask_secret

    # 文件工具测试
    print("文件工具:")
    print(f"  get_file_extension('test.pdf'): {get_file_extension('test.pdf')}")
    print(f"  is_supported_file('test.docx'): {is_supported_file('test.docx')}")
    print(f"  get_text_hash('test'): {get_text_hash('test')}")
    print(f"  format_file_size(1024*1024): {format_file_size(1024*1024)}")

    # 文本工具测试
    print("\n文本工具:")
    long_text = "这是一段很长的文本" * 100
    print(f"  truncate_text: {truncate_text(long_text, 20)}")
    print(f"  generate_timestamp: {generate_timestamp()}")
    print(f"  clean_text: '{clean_text('  测试  \n\n  文本  ')}'")

    # API工具测试
    print("\nAPI工具:")
    secret = "sk-1234567890abcdef"
    print(f"  mask_secret: {mask_secret(secret)}")

    print("\n工具模块测试通过！\n")
    return True


def cleanup_test_files():
    """清理测试文件"""
    import shutil

    test_dirs = ["storage/test_logs", "storage/test_temp"]
    for dir_path in test_dirs:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)

    print("测试文件清理完成！")


def main():
    """主函数"""
    print("\n" + "=" * 50)
    print("NoteAgents 基础框架测试")
    print("=" * 50 + "\n")

    try:
        # 执行所有测试
        test_config()
        test_logging()
        test_temp_manager()
        test_utils()

        print("=" * 50)
        print("所有测试通过！")
        print("=" * 50)

        # 清理测试文件
        cleanup_test_files()

    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
