"""
飞书工具 - 提供消息构建和辅助功能
"""

from typing import Optional, List
from platforms import PlatformType


def build_welcome_message() -> str:
    """构建欢迎消息"""
    return """👋 欢迎使用 NoteAgents（飞书版）！

我可以帮你：
• 📝 发送文本或链接，自动生成笔记
• 📄 发送 PDF/Word/TXT 文件，自动提取内容并生成笔记
• 💾 笔记自动保存到你的 Obsidian 知识库

使用方法：
1. 直接发送文本或链接给我
2. 上传文件
3. 等待处理结果

提示：只有授权用户才能使用哦！"""


def build_help_message() -> str:
    """构建帮助消息"""
    return """📖 使用帮助

支持的内容：
• 文本消息 - 直接输入即可
• 链接 - 自动识别和处理
• PDF 文档 - .pdf 格式
• Word 文档 - .docx 格式
• 文本文件 - .txt 格式

文件限制：
• 单个文件不超过 50MB
• 提取的文本超过 5000 字符会自动截断

处理流程：
1. 接收内容
2. AI 分析和总结
3. 生成 Obsidian 格式笔记
4. 自动保存到知识库
5. 返回处理结果

如有问题，请查看日志或联系管理员。"""


def build_processing_message() -> str:
    """构建处理中消息"""
    return "⏳ 正在处理中，请稍候..."


def build_success_message(filename: str, note_title: Optional[str] = None) -> str:
    """构建成功消息"""
    if note_title:
        return f"""✅ 处理成功！

📝 笔记标题：{note_title}
💾 保存文件：{filename}

笔记已保存到你的 Obsidian 知识库！"""
    else:
        return f"""✅ 处理成功！

💾 保存文件：{filename}

笔记已保存到你的 Obsidian 知识库！"""


def build_error_message(error: str) -> str:
    """构建错误消息"""
    return f"""❌ 处理失败！

错误信息：{error}

请稍后重试或联系管理员。"""


def build_permission_denied_message(user_id: str) -> str:
    """构建权限拒绝消息"""
    return f"""⚠️ 权限不足！

抱歉，您的用户 ID ({user_id}) 不在授权列表中。

如需使用，请联系管理员添加你的用户 ID 到授权列表。"""


def build_platform_start_message(enabled_platforms: List[PlatformType]) -> str:
    """构建平台启动消息"""
    platform_names = []
    for p in enabled_platforms:
        if p == PlatformType.TELEGRAM:
            platform_names.append("Telegram")
        elif p == PlatformType.FEISHU:
            platform_names.append("飞书")
        else:
            platform_names.append(p.value)

    platform_list = "、".join(platform_names)
    return f"""🚀 NoteAgents 已启动！

已启用平台：{platform_list}

等待消息中..."""


def build_webhook_info_message(
    host: str = "0.0.0.0",
    port: int = 8000,
    use_webhook: bool = False,
) -> str:
    """构建 Webhook 模式信息"""
    if not use_webhook:
        return ""

    public_url_hint = """📡 Webhook 模式提示：
请在飞书开放平台配置以下 Webhook URL：
https://your-domain.com/feishu/webhook

注意事项：
1. 需要公网可访问的域名/IP
2. 推荐使用 HTTPS
3. 在飞书开放平台的"事件订阅"中配置"""

    return public_url_hint
