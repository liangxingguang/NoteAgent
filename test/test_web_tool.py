"""网页工具测试"""

from tools.ai_summary_tool import is_url, truncate_content
# 直接使用相对导入
from tools.web_tool import WebTool, get_web_tool, WebPageContent


class TestWebTool:
    """WebTool测试"""

    def setup_method(self):
        """每个测试方法前初始化"""
        self.web_tool = WebTool(timeout=10)

    def test_init(self):
        """测试WebTool初始化"""
        tool = WebTool(timeout=30)
        assert tool.timeout == 30
        assert "User-Agent" in tool.headers

    def test_get_web_tool(self):
        """测试获取WebTool实例"""
        tool = get_web_tool(timeout=15)
        assert tool.timeout == 15

    def test_is_valid_url_valid(self):
        """测试有效URL验证"""
        valid_urls = [
            "https://www.example.com",
            "http://example.com",
            "https://example.com/path",
            "https://example.com/path/to/page",
            "https://example.com/path?query=1"
        ]
        for url in valid_urls:
            assert self.web_tool.is_valid_url(url) is True, f"URL应该有效: {url}"

    def test_is_valid_url_invalid(self):
        """测试无效URL验证"""
        invalid_urls = [
            "not-a-url",
            "example.com",
            "ftp://example.com",
            "",
            "htp://invalid",
        ]
        for url in invalid_urls:
            assert self.web_tool.is_valid_url(url) is False, f"URL应该无效: {url}"

    def test_extract_title(self):
        """测试标题提取"""
        from bs4 import BeautifulSoup

        html = BeautifulSoup("<html><head><title>测试标题</title></head><body></body></html>", 'html.parser')
        title = self.web_tool._extract_title(html)
        assert title == "测试标题"

    def test_extract_title_from_h1(self):
        """测试从h1标签提取标题"""
        from bs4 import BeautifulSoup

        html = BeautifulSoup("<html><body><h1>H1标题</h1></body></html>", 'html.parser')
        title = self.web_tool._extract_title(html)
        assert title == "H1标题"

    def test_extract_title_fallback(self):
        """测试标题提取后备"""
        from bs4 import BeautifulSoup

        html = BeautifulSoup("<html><body><p>没有标题</p></body></html>", 'html.parser')
        title = self.web_tool._extract_title(html)
        assert title == "无标题"

    def test_extract_publish_time(self):
        """测试发布时间提取"""
        from bs4 import BeautifulSoup

        html = BeautifulSoup(
            '<html><head><meta property="article:published_time" content="2024-01-15T10:30:00Z"></head></html>',
            'html.parser'
        )
        publish_time = self.web_tool._extract_publish_time(html)
        assert publish_time == "2024-01-15T10:30:00Z"

    def test_extract_author(self):
        """测试作者提取"""
        from bs4 import BeautifulSoup

        html = BeautifulSoup(
            '<html><head><meta name="author" content="测试作者"></head></html>',
            'html.parser'
        )
        author = self.web_tool._extract_author(html)
        assert author == "测试作者"

    def test_extract_description(self):
        """测试描述提取"""
        from bs4 import BeautifulSoup

        html = BeautifulSoup(
            '<html><head><meta name="description" content="测试描述"></head></html>',
            'html.parser'
        )
        desc = self.web_tool._extract_description(html)
        assert desc == "测试描述"

    def test_extract_article_content(self):
        """测试文章内容提取"""
        from bs4 import BeautifulSoup

        html = BeautifulSoup(
            '<html><body><article><p>文章正文内容</p></article></body></html>',
            'html.parser'
        )
        html_content, text_content = self.web_tool._extract_article_content(html)
        assert "文章正文内容" in text_content

    def test_extract_content_from_main(self):
        """测试从main标签提取内容"""
        from bs4 import BeautifulSoup

        html = BeautifulSoup(
            '<html><body><main><p>main中的内容</p></main></body></html>',
            'html.parser'
        )
        _, text_content = self.web_tool._extract_article_content(html)
        assert "main中的内容" in text_content

    def test_extract_content_fallback(self):
        """测试内容提取后备"""
        from bs4 import BeautifulSoup

        html = BeautifulSoup("<html><body><div>一些内容</div></body></html>", 'html.parser')
        _, text_content = self.web_tool._extract_article_content(html)
        assert "一些内容" in text_content

    def test_convert_p_to_markdown(self):
        """测试段落转换"""
        from bs4 import BeautifulSoup

        html = BeautifulSoup("<p>测试段落</p>", 'html.parser')
        p_tag = html.find('p')
        result = self.web_tool._convert_p_to_markdown(p_tag)
        assert result == "测试段落"

    def test_html_to_markdown_basic(self):
        """测试基本HTML转Markdown"""
        html = "<h1>标题1</h1><p>段落内容</p>"
        result = self.web_tool.html_to_markdown(html, "测试", "https://example.com")
        assert "# 标题1" in result
        assert "段落内容" in result
        assert "**来源**: https://example.com" in result

    def test_html_to_markdown_with_author_time(self):
        """测试带作者和时间的HTML转Markdown"""
        html = "<p>内容</p>"
        result = self.web_tool.html_to_markdown(
            html,
            "标题",
            "https://example.com",
            publish_time="2024-01-01",
            author="作者"
        )
        assert "作者" in result
        assert "2024-01-01" in result

    def test_html_to_markdown_lists(self):
        """测试列表转换"""
        html = "<ul><li>项目1</li><li>项目2</li></ul>"
        result = self.web_tool.html_to_markdown(html, "标题", "https://example.com")
        assert "- 项目1" in result
        assert "- 项目2" in result

    def test_html_to_markdown_code(self):
        """测试代码块转换"""
        html = "<pre><code>代码内容</code></pre>"
        result = self.web_tool.html_to_markdown(html, "标题", "https://example.com")
        assert "```" in result
        assert "代码内容" in result

    def test_html_to_markdown_blockquote(self):
        """测试引用转换"""
        html = "<blockquote>引用内容</blockquote>"
        result = self.web_tool.html_to_markdown(html, "标题", "https://example.com")
        assert ">" in result
        assert "引用内容" in result


class TestIsUrl:
    """URL识别测试"""

    def test_is_url_valid(self):
        """测试有效URL识别"""
        valid_urls = [
            "https://www.example.com",
            "http://example.com",
            "https://weibo.com/123456",
            "https://mp.weixin.qq.com/s/test",
            "https://blog.example.com/post/123",
            "https://example.com/path?query=value",
        ]
        for url in valid_urls:
            assert is_url(url) is True, f"应该识别为URL: {url}"

    def test_is_url_invalid(self):
        """测试无效URL识别"""
        invalid_texts = [
            "这不是一个链接",
            "hello world",
            "",
            "www.example.com",
            "example.com",
        ]
        for text in invalid_texts:
            assert is_url(text) is False, f"不应该识别为URL: {text}"

    def test_is_url_with_spaces(self):
        """测试带空格的URL"""
        assert is_url("  https://example.com  ") is True


class TestTruncateContent:
    """内容截断测试"""

    def test_truncate_short_content(self):
        """测试截断短内容"""
        content = "短内容"
        result = truncate_content(content, max_chars=10)
        assert result == content

    def test_truncate_long_content(self):
        """测试截断长内容"""
        content = "这是一段很长的测试内容，用于测试截断功能是否正常工作。"
        result = truncate_content(content, max_chars=10)
        assert len(result) <= 10 + len("[内容已截断...]")
        assert "[内容已截断...]" in result

    def test_truncate_exact_length(self):
        """测试精确长度截断"""
        content = "1234567890"
        result = truncate_content(content, max_chars=10)
        assert result == content

    def test_truncate_empty_content(self):
        """测试空内容截断"""
        assert truncate_content("", max_chars=10) == ""
        assert truncate_content(None, max_chars=10) == ""


class TestWebPageContent:
    """WebPageContent数据类测试"""

    def test_web_page_content_creation(self):
        """测试WebPageContent创建"""
        content = WebPageContent(
            title="测试标题",
            content="正文内容",
            html="<p>HTML内容</p>",
            url="https://example.com",
            publish_time="2024-01-01",
            author="作者"
        )
        assert content.title == "测试标题"
        assert content.content == "正文内容"
        assert content.url == "https://example.com"
        assert content.publish_time == "2024-01-01"
        assert content.author == "作者"

    def test_web_page_content_optional_fields(self):
        """测试可选字段"""
        content = WebPageContent(
            title="标题",
            content="内容",
            html="",
            url="https://example.com"
        )
        assert content.publish_time is None
        assert content.author is None
        assert content.description is None


class TestUrlPatterns:
    """URL模式测试"""

    def test_weibo_url(self):
        """测试微博URL"""
        weibo_urls = [
            "https://weibo.com/1234567890",
            "https://m.weibo.com/detail/123",
        ]
        for url in weibo_urls:
            assert is_url(url) is True

    def test_weixin_url(self):
        """测试微信公众号URL"""
        weixin_urls = [
            "https://mp.weixin.qq.com/s/abc123",
            "https://mp.weixin.qq.com/s?__biz=xxx&mid=xxx",
        ]
        for url in weixin_urls:
            assert is_url(url) is True

    def test_blog_url(self):
        """测试博客URL"""
        blog_urls = [
            "https://medium.com/@user/post",
            "https://dev.to/user/post",
            "https://zhihu.com/p/123456",
        ]
        for url in blog_urls:
            assert is_url(url) is True
