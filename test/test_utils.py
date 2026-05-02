"""工具模块测试"""

from utils.api_utils import mask_secret, safe_get
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


class TestFileUtils:
    """文件工具测试"""

    def test_get_file_extension(self):
        """测试获取文件扩展名"""
        assert get_file_extension("test.pdf") == "pdf"
        assert get_file_extension("test.docx") == "docx"
        assert get_file_extension("test.TXT") == "txt"
        assert get_file_extension("noextension") == ""
        assert get_file_extension("path/to/file.pdf") == "pdf"

    def test_is_supported_file(self):
        """测试文件类型支持检查"""
        assert is_supported_file("test.pdf") is True
        assert is_supported_file("test.docx") is True
        assert is_supported_file("test.txt") is True
        assert is_supported_file("test.png") is False
        assert is_supported_file("test.exe") is False

    def test_get_text_hash(self):
        """测试文本哈希"""
        hash1 = get_text_hash("test")
        hash2 = get_text_hash("test")
        hash3 = get_text_hash("different")

        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) > 0

    def test_format_file_size(self):
        """测试文件大小格式化"""
        assert format_file_size(0) == "0.00B"
        assert format_file_size(1024) == "1.00KB"
        assert format_file_size(1024 * 1024) == "1.00MB"
        assert format_file_size(1024 * 1024 * 1024) == "1.00GB"
        assert format_file_size(1536) == "1.50KB"
        assert format_file_size(100) == "100.00B"


class TestTextUtils:
    """文本工具测试"""

    def test_truncate_text(self):
        """测试文本截断"""
        text = "这是一段测试文本"
        # 计算：max_length=5, suffix=3 chars, so 5-3=2 -> "这是..."
        assert truncate_text(text, 5) == "这是..."
        # 文本长度为8，小于10，所以返回原文本
        assert truncate_text(text, 10) == text
        assert truncate_text(text, 100) == text
        # 当max_length=0时，Python切片text[:0-3]相当于text[:-3]，结果为"这是一段测..."
        assert truncate_text(text, 0) == "这是一段测..."

    def test_truncate_text_empty(self):
        """测试空文本截断"""
        assert truncate_text("", 10) == ""
        assert truncate_text(None, 10) == ""

    def test_generate_timestamp(self):
        """测试时间戳生成"""
        ts1 = generate_timestamp()
        ts2 = generate_timestamp()

        assert isinstance(ts1, str)
        assert len(ts1) > 0
        assert ts1 == ts2  # 同一秒内应该相同

    def test_clean_text(self):
        """测试文本清洗"""
        assert clean_text("  hello  ") == "hello"
        assert clean_text("hello\n\nworld") == "hello\n\nworld"
        assert clean_text("  hello \n world  ") == "hello\n world"
        assert clean_text("\n\n\n") == ""


class TestApiUtils:
    """API工具测试"""

    def test_mask_secret(self):
        """测试密钥掩码"""
        assert mask_secret("sk-1234567890abcdef") == "sk-1****cdef"
        assert mask_secret("sk-abcdef", show_prefix=4, show_suffix=2) == "sk-a****ef"
        assert mask_secret("short") == "***"
        assert mask_secret("sk-123456", show_prefix=6, show_suffix=0) == "sk-123****"

    def test_mask_secret_empty(self):
        """测试空密钥掩码"""
        assert mask_secret("") == "***"
        assert mask_secret(None) == "***"

    def test_safe_get(self):
        """测试安全获取嵌套字典"""
        data = {
            "a": {
                "b": {
                    "c": "value"
                }
            },
            "list": [1, 2, 3]
        }

        assert safe_get(data, "a.b.c") == "value"
        assert safe_get(data, "a.b") == {"c": "value"}
        assert safe_get(data, "list.0") == 1
        assert safe_get(data, "nonexistent") is None
        assert safe_get(data, "a.nonexistent") is None
        assert safe_get(None, "a.b.c") is None

    def test_safe_get_invalid_path(self):
        """测试无效路径"""
        data = {"a": "value"}
        assert safe_get(data, "") is None
        assert safe_get(data, "a.b.c") is None
