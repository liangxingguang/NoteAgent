"""网页内容抓取工具（生产稳定版，专为AI总结设计）"""
import re
import uuid
from dataclasses import dataclass
from typing import Optional, Tuple

import requests
import trafilatura
from bs4 import BeautifulSoup

from storage.log_manager import get_logger
from storage.temp_manager import get_temp_manager

logger = get_logger("WebTool")


@dataclass
class WebPageContent:
    """网页结构化内容（专为AI总结优化）"""
    title: str
    content: str
    url: str
    author: Optional[str] = None
    publish_time: Optional[str] = None


class WebTool:
    """稳定版网页抓取工具（专为Telegram机器人+AI总结设计）"""

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }

    def is_valid_url(self, url: str) -> bool:
        """验证URL"""
        return url.startswith(("http://", "https://"))

    def fetch_content(self, url: str) -> Tuple[bool, WebPageContent | str]:
        """抓取并自动提取文章正文（最稳定）"""
        try:
            logger.info(f"抓取网页: {url}")

            # 1. 下载
            response = requests.get(
                url, headers=self.headers, timeout=self.timeout, verify=False
            )
            response.raise_for_status()

            # 2. 全自动提取正文（核心：不会崩溃、支持99%网站）
            content = trafilatura.extract(
                response.text,
                include_formatting=False,
                include_links=False,
                include_images=False,
                no_fallback=False,
                favor_precision=True
            )

            if not content:
                return False, "无法提取网页正文"

            # 3. 标题
            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.title.string.strip() if soup.title else "无标题"

            # 4. 构建结果
            result = WebPageContent(
                title=title,
                content=content,
                url=url
            )

            logger.info(f"抓取完成: {title}")
            return True, result

        except Exception as e:
            logger.error(f"抓取失败: {str(e)}", exc_info=True)
            return False, f"抓取失败: {str(e)}"

    def to_markdown(self, content: WebPageContent) -> str:
        """转为干净的Markdown（给AI最舒服格式）"""
        md = f"# {content.title}\n\n"
        md += f"**来源**: {content.url}\n\n"
        if content.author:
            md += f"**作者**: {content.author}\n"
        if content.publish_time:
            md += f"**时间**: {content.publish_time}\n"
        md += "\n---\n\n"
        md += content.content
        return md

    async def download_and_convert(self, url: str) -> Tuple[bool, str]:
        """对外接口：直接返回可用于AI总结的Markdown"""
        success, result = self.fetch_content(url)
        if not success:
            return False, result
        return True, self.to_markdown(result)


def get_web_tool(timeout: int = 15) -> WebTool:
    return WebTool(timeout=timeout)