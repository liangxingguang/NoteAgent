"""
飞书富文本消息构建器
支持构建飞书富文本格式消息
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class RichTextElement:
    """富文本元素基类"""
    tag: str = ""


@dataclass
class TextElement(RichTextElement):
    """文本元素"""
    text: str = ""
    style: Optional[Dict[str, Any]] = None
    tag: str = "text"


@dataclass
class LinkElement(RichTextElement):
    """链接元素"""
    text: str = ""
    href: str = ""
    tag: str = "a"


@dataclass
class AtElement(RichTextElement):
    """AT元素"""
    user_id: str = ""
    user_name: Optional[str] = None
    tag: str = "at"


@dataclass
class ImageElement(RichTextElement):
    """图片元素"""
    image_key: str = ""
    tag: str = "img"


class RichTextBuilder:
    """飞书富文本构建器"""

    def __init__(self, title: str = ""):
        self.title = title
        self.elements: List[List[RichTextElement]] = []
        self.current_line: List[RichTextElement] = []

    def add_text(self, text: str, bold: bool = False, italic: bool = False) -> "RichTextBuilder":
        """添加文本"""
        style = {}
        if bold:
            style["bold"] = True
        if italic:
            style["italic"] = True

        element = TextElement(text=text, style=style if style else None)
        self.current_line.append(element)
        return self

    def add_link(self, text: str, href: str) -> "RichTextBuilder":
        """添加链接"""
        element = LinkElement(text=text, href=href)
        self.current_line.append(element)
        return self

    def add_at(self, user_id: str, user_name: Optional[str] = None) -> "RichTextBuilder":
        """AT用户"""
        element = AtElement(user_id=user_id, user_name=user_name)
        self.current_line.append(element)
        return self

    def add_image(self, image_key: str) -> "RichTextBuilder":
        """添加图片"""
        element = ImageElement(image_key=image_key)
        self.current_line.append(element)
        return self

    def new_line(self) -> "RichTextBuilder":
        """换行"""
        if self.current_line:
            self.elements.append(self.current_line)
            self.current_line = []
        return self

    def build(self) -> str:
        """构建飞书富文本消息内容"""
        content = {
            "title": self.title,
            "elements": []
        }

        # 构建元素
        for line in self.elements:
            line_elements = []
            for elem in line:
                if isinstance(elem, TextElement):
                    elem_dict = {"tag": "text", "text": elem.text}
                    if elem.style:
                        elem_dict["style"] = elem.style
                    line_elements.append(elem_dict)
                elif isinstance(elem, LinkElement):
                    line_elements.append({
                        "tag": "a",
                        "text": elem.text,
                        "href": elem.href
                    })
                elif isinstance(elem, AtElement):
                    at_elem = {"tag": "at", "user_id": elem.user_id}
                    if elem.user_name:
                        at_elem["user_name"] = elem.user_name
                    line_elements.append(at_elem)
                elif isinstance(elem, ImageElement):
                    line_elements.append({
                        "tag": "img",
                        "image_key": elem.image_key
                    })
            content["elements"].append(line_elements)

        # 添加当前行
        if self.current_line:
            line_elements = []
            for elem in self.current_line:
                if isinstance(elem, TextElement):
                    elem_dict = {"tag": "text", "text": elem.text}
                    if elem.style:
                        elem_dict["style"] = elem.style
                    line_elements.append(elem_dict)
                elif isinstance(elem, LinkElement):
                    line_elements.append({
                        "tag": "a",
                        "text": elem.text,
                        "href": elem.href
                    })
            content["elements"].append(line_elements)

        return json.dumps(content, ensure_ascii=False)


def build_welcome_rich_text() -> str:
    """构建欢迎消息富文本"""
    builder = RichTextBuilder(title="👋 欢迎使用 NoteAgents")
    builder.add_text("我可以帮你：").new_line()
    builder.add_text("• ").add_text("📝 发送文本或链接", bold=True).add_text("，自动生成笔记").new_line()
    builder.add_text("• ").add_text("📄 发送 PDF/Word/TXT 文件", bold=True).add_text("，自动提取内容").new_line()
    builder.add_text("• ").add_text("💾 自动保存", bold=True).add_text("到你的 Obsidian 知识库").new_line()
    builder.new_line()
    builder.add_text("使用方法：").new_line()
    builder.add_text("1. 直接发送文本或链接给我").new_line()
    builder.add_text("2. 上传文件").new_line()
    builder.add_text("3. 等待处理结果").new_line()
    builder.new_line()
    builder.add_text("💡 提示：输入 /help 获取更多帮助")
    return builder.build()


def build_help_rich_text() -> str:
    """构建帮助消息富文本"""
    builder = RichTextBuilder(title="📖 使用帮助")

    builder.add_text("支持的内容：").new_line()
    builder.add_text("• ").add_text("文本消息", bold=True).add_text(" - 直接输入即可").new_line()
    builder.add_text("• ").add_text("链接", bold=True).add_text(" - 自动识别和处理").new_line()
    builder.add_text("• ").add_text("PDF 文档", bold=True).add_text(" - .pdf 格式").new_line()
    builder.add_text("• ").add_text("Word 文档", bold=True).add_text(" - .docx 格式").new_line()
    builder.add_text("• ").add_text("文本文件", bold=True).add_text(" - .txt 格式").new_line()
    builder.new_line()

    builder.add_text("可用命令：").new_line()
    builder.add_text("/start").add_text(" - 开始使用").new_line()
    builder.add_text("/help").add_text(" - 显示帮助").new_line()
    builder.new_line()

    builder.add_text("文件限制：").new_line()
    builder.add_text("• 单个文件不超过 50MB").new_line()
    builder.add_text("• 提取的文本超过 5000 字符会自动截断").new_line()
    return builder.build()


def build_success_rich_text(filename: str, note_title: Optional[str] = None) -> str:
    """构建成功消息富文本"""
    builder = RichTextBuilder(title="✅ 处理成功！")
    if note_title:
        builder.add_text("📝 笔记标题：").add_text(note_title, bold=True).new_line()
    builder.add_text("💾 保存文件：").add_text(filename, bold=True).new_line()
    builder.new_line()
    builder.add_text("笔记已保存到你的 Obsidian 知识库！")
    return builder.build()


def build_error_rich_text(error: str) -> str:
    """构建错误消息富文本"""
    builder = RichTextBuilder(title="❌ 处理失败")
    builder.add_text("错误信息：").add_text(error, italic=True)
    return builder.build()


def build_command_response(command: str, response_text: str) -> str:
    """构建命令响应富文本"""
    builder = RichTextBuilder(title=f"📋 命令结果: /{command}")
    builder.add_text(response_text)
    return builder.build()


def build_plain_text(text: str) -> str:
    """构建纯文本消息（作为json）"""
    return json.dumps({"text": text}, ensure_ascii=False)
