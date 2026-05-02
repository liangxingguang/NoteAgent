"""GitHub 工具测试"""

# 直接使用相对导入
from tools.github_tool import (
    GitHubTool,
    GitHubConfig,
    PushResult,
    get_github_tool,
    init_github_tool,
    create_github_config_from_env,
)


class TestGitHubConfig:
    """GitHubConfig 测试"""

    def test_create_config(self):
        """测试配置创建"""
        config = GitHubConfig(
            token="test_token",
            owner="test_owner",
            repo="test_repo",
            branch="main",
            commit_message="Test commit",
        )
        assert config.token == "test_token"
        assert config.owner == "test_owner"
        assert config.repo == "test_repo"
        assert config.branch == "main"
        assert config.commit_message == "Test commit"

    def test_default_branch(self):
        """测试默认分支"""
        config = GitHubConfig(
            token="test_token",
            owner="test_owner",
            repo="test_repo",
        )
        assert config.branch == "main"

    def test_default_commit_message(self):
        """测试默认提交信息"""
        config = GitHubConfig(
            token="test_token",
            owner="test_owner",
            repo="test_repo",
        )
        assert config.commit_message == "Add note via NoteAgents"


class TestPushResult:
    """PushResult 测试"""

    def test_success_result(self):
        """测试成功结果"""
        result = PushResult(
            success=True,
            file_path="notes/2024-01-01/test.md",
            commit_sha="abc123",
            url="https://github.com/owner/repo/blob/main/notes/2024-01-01/test.md",
        )
        assert result.success is True
        assert result.file_path == "notes/2024-01-01/test.md"
        assert result.commit_sha == "abc123"
        assert result.url is not None
        assert result.error is None

    def test_failure_result(self):
        """测试失败结果"""
        result = PushResult(
            success=False,
            error="Push failed",
        )
        assert result.success is False
        assert result.error == "Push failed"
        assert result.file_path is None

    def test_result_optional_fields(self):
        """测试可选字段"""
        result = PushResult(success=True)
        assert result.file_path is None
        assert result.commit_sha is None
        assert result.url is None


class TestGitHubTool:
    """GitHubTool 测试"""

    def setup_method(self):
        """每个测试前初始化"""
        self.config = GitHubConfig(
            token="test_token",
            owner="test_owner",
            repo="test_repo",
            branch="main",
        )

    def test_init(self):
        """测试工具初始化"""
        tool = GitHubTool(self.config)
        assert tool.config.token == "test_token"
        assert tool.config.owner == "test_owner"
        assert "Authorization" in tool.headers

    def test_validate_config_empty_token(self):
        """测试空Token验证"""
        config = GitHubConfig(token="", owner="test", repo="test")
        tool = GitHubTool(config)
        valid, error = tool._validate_config()
        assert valid is False
        assert "Token" in error

    def test_validate_config_empty_owner(self):
        """测试空Owner验证"""
        config = GitHubConfig(token="test", owner="", repo="test")
        tool = GitHubTool(config)
        valid, error = tool._validate_config()
        assert valid is False
        assert "Owner" in error

    def test_validate_config_empty_repo(self):
        """测试空Repo验证"""
        config = GitHubConfig(token="test", owner="test", repo="")
        tool = GitHubTool(config)
        valid, error = tool._validate_config()
        assert valid is False
        assert "Repo" in error

    def test_validate_config_success(self):
        """测试成功验证"""
        tool = GitHubTool(self.config)
        valid, error = tool._validate_config()
        assert valid is True
        assert error == ""

    def test_get_file_path_simple(self):
        """测试简单文件名路径"""
        tool = GitHubTool(self.config)
        path = tool._get_file_path("test.md")
        assert path == "notes/2024-01-01/test.md"

    def test_get_file_path_with_subdir(self):
        """测试带子目录路径"""
        tool = GitHubTool(self.config)
        path = tool._get_file_path("test.md", subdir="custom")
        assert path == "custom/2024-01-01/test.md"

    def test_get_file_path_auto_adds_md(self):
        """测试自动添加.md扩展名"""
        tool = GitHubTool(self.config)
        path = tool._get_file_path("test")
        assert path.endswith(".md")


class TestModuleFunctions:
    """模块函数测试"""

    def test_init_and_get_github_tool(self):
        """测试初始化和获取工具"""
        config = GitHubConfig(
            token="test_token",
            owner="test_owner",
            repo="test_repo",
        )
        tool = init_github_tool(config)
        assert tool is not None

        retrieved = get_github_tool()
        assert retrieved is tool

    def test_get_github_tool_before_init(self):
        """测试初始化前获取"""
        import tools.github_tool as gh_module
        gh_module._github_tool = None
        result = get_github_tool()
        assert result is None


class TestCreateConfigFromEnv:
    """从环境变量创建配置测试"""

    def test_missing_env_vars(self):
        """测试缺失环境变量"""
        import os
        original_token = os.environ.get("GITHUB_TOKEN")
        original_owner = os.environ.get("GITHUB_OWNER")
        original_repo = os.environ.get("GITHUB_REPO")

        if "GITHUB_TOKEN" in os.environ:
            del os.environ["GITHUB_TOKEN"]
        if "GITHUB_OWNER" in os.environ:
            del os.environ["GITHUB_OWNER"]
        if "GITHUB_REPO" in os.environ:
            del os.environ["GITHUB_REPO"]

        try:
            config = create_github_config_from_env()
            assert config is None
        finally:
            if original_token:
                os.environ["GITHUB_TOKEN"] = original_token
            if original_owner:
                os.environ["GITHUB_OWNER"] = original_owner
            if original_repo:
                os.environ["GITHUB_REPO"] = original_repo

    def test_branch_default(self):
        """测试分支默认值"""
        import os
        os.environ["GITHUB_TOKEN"] = "test_token"
        os.environ["GITHUB_OWNER"] = "test_owner"
        os.environ["GITHUB_REPO"] = "test_repo"

        if "GITHUB_BRANCH" in os.environ:
            original_branch = os.environ["GITHUB_BRANCH"]
        else:
            original_branch = None
            os.environ.pop("GITHUB_BRANCH", None)

        try:
            config = create_github_config_from_env()
            assert config is not None
            assert config.branch == "main"
        finally:
            if original_branch:
                os.environ["GITHUB_BRANCH"] = original_branch
            elif "GITHUB_BRANCH" in os.environ:
                del os.environ["GITHUB_BRANCH"]
