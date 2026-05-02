"""GitHub 推送工具 - 支持将笔记内容推送到 GitHub 仓库"""

import base64
import os
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Tuple, List

import requests

from storage.log_manager import get_logger


logger = get_logger("GitHubTool")


@dataclass
class GitHubConfig:
    """GitHub配置"""
    token: str
    owner: str
    repo: str
    branch: str = "main"
    commit_message: str = "Add note via NoteAgents"


@dataclass
class PushResult:
    """推送结果"""
    success: bool
    file_path: Optional[str] = None
    commit_sha: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None


@dataclass
class PullResult:
    """拉取结果"""
    success: bool
    files: List[dict] = field(default_factory=list)
    total_count: int = 0
    error: Optional[str] = None


class GitHubTool:
    """GitHub 推送/拉取工具"""

    def __init__(self, config: GitHubConfig):
        self.config = config
        self.headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        self.api_base = "https://api.github.com"

    def _validate_config(self) -> Tuple[bool, str]:
        """验证配置"""
        if not self.config.token:
            return False, "GitHub Token 未配置"
        if not self.config.owner:
            return False, "GitHub Owner 未配置"
        if not self.config.repo:
            return False, "GitHub Repo 未配置"
        return True, ""

    def _get_file_path(self, filename: str, subdir: Optional[str] = None) -> str:
        """生成文件路径

        Args:
            filename: 文件名
            subdir: 子目录

        Returns:
            完整的文件路径
        """
        if subdir:
            date_str = datetime.now().strftime("%Y-%m-%d")
            return f"{subdir}/{date_str}/{filename}"
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")
            return f"notes/{date_str}/{filename}"

    def _check_file_exists(self, path: str) -> Tuple[bool, Optional[str]]:
        """检查文件是否存在

        Args:
            path: 文件路径

        Returns:
            (是否存在, 文件SHA)
        """
        url = f"{self.api_base}/repos/{self.config.owner}/{self.config.repo}/contents/{path}"
        params = {"ref": self.config.branch}

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return True, data.get("sha")
            elif response.status_code == 404:
                return False, None
            else:
                response.raise_for_status()
        except Exception as e:
            logger.error(f"检查文件存在失败: {e}")
            return False, None

    def push_note(
        self,
        content: str,
        filename: Optional[str] = None,
        subdir: Optional[str] = None,
        commit_message: Optional[str] = None,
    ) -> PushResult:
        """推送笔记到 GitHub

        Args:
            content: 笔记内容 (Markdown)
            filename: 文件名（不含扩展名），自动生成UUID
            subdir: 子目录
            commit_message: 提交信息

        Returns:
            PushResult
        """
        valid, error = self._validate_config()
        if not valid:
            logger.error(f"GitHub配置验证失败: {error}")
            return PushResult(success=False, error=error)

        if not filename:
            filename = f"note_{uuid.uuid4().hex[:8]}"

        if not filename.endswith(".md"):
            filename += ".md"

        file_path = self._get_file_path(filename, subdir)
        commit_msg = commit_message or self.config.commit_message

        try:
            exists, sha = self._check_file_exists(file_path)

            url = f"{self.api_base}/repos/{self.config.owner}/{self.config.repo}/contents/{file_path}"

            payload = {
                "message": commit_msg,
                "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
                "branch": self.config.branch,
            }

            if sha:
                payload["sha"] = sha

            response = requests.put(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()
            result = PushResult(
                success=True,
                file_path=file_path,
                commit_sha=data.get("commit", {}).get("sha"),
                url=data.get("content", {}).get("html_url"),
            )

            logger.info(f"笔记推送成功: {file_path}")
            return result

        except requests.exceptions.RequestException as e:
            error_msg = f"推送失败: {str(e)}"
            logger.error(error_msg)
            return PushResult(success=False, error=error_msg)

    def create_or_update_file(
        self,
        path: str,
        content: str,
        message: str,
        branch: Optional[str] = None,
    ) -> PushResult:
        """创建或更新文件

        Args:
            path: 文件路径
            content: 文件内容
            message: 提交信息
            branch: 分支（可选）

        Returns:
            PushResult
        """
        valid, error = self._validate_config()
        if not valid:
            return PushResult(success=False, error=error)

        try:
            exists, sha = self._check_file_exists(path)

            url = f"{self.api_base}/repos/{self.config.owner}/{self.config.repo}/contents/{path}"

            payload = {
                "message": message,
                "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
                "branch": branch or self.config.branch,
            }

            if sha:
                payload["sha"] = sha

            response = requests.put(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()
            return PushResult(
                success=True,
                file_path=path,
                commit_sha=data.get("commit", {}).get("sha"),
                url=data.get("content", {}).get("html_url"),
            )

        except requests.exceptions.RequestException as e:
            return PushResult(success=False, error=f"操作失败: {str(e)}")

    def get_file_content(self, path: str, branch: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """获取文件内容

        Args:
            path: 文件路径
            branch: 分支（可选）

        Returns:
            (是否成功, 文件内容, 错误信息)
        """
        valid, error = self._validate_config()
        if not valid:
            return False, None, error

        try:
            url = f"{self.api_base}/repos/{self.config.owner}/{self.config.repo}/contents/{path}"
            params = {"ref": branch or self.config.branch}

            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            content_base64 = data.get("content", "")
            content = base64.b64decode(content_base64).decode("utf-8")

            return True, content, None

        except requests.exceptions.RequestException as e:
            return False, None, f"获取文件失败: {str(e)}"

    def list_files(self, path: str = "", branch: Optional[str] = None, recursive: bool = False) -> Tuple[bool, list, Optional[str]]:
        """列出目录中的文件

        Args:
            path: 目录路径
            branch: 分支（可选）
            recursive: 是否递归列出子目录

        Returns:
            (是否成功, 文件列表, 错误信息)
        """
        valid, error = self._validate_config()
        if not valid:
            return False, [], error

        try:
            url = f"{self.api_base}/repos/{self.config.owner}/{self.config.repo}/contents/{path}"
            params = {"ref": branch or self.config.branch}

            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()

            files = response.json()
            result_files = []

            for f in files:
                if not isinstance(f, dict):
                    continue

                file_info = {
                    "name": f.get("name"),
                    "path": f.get("path"),
                    "type": f.get("type"),
                    "sha": f.get("sha"),
                }

                if f.get("type") == "file" and f.get("name", "").endswith(".md"):
                    result_files.append(file_info)
                elif f.get("type") == "dir" and recursive:
                    sub_files, sub_error = self.list_files(f.get("path"), branch, recursive=True)
                    if sub_files:
                        result_files.extend(sub_files)

            return True, result_files, None

        except requests.exceptions.RequestException as e:
            return False, [], f"列出文件失败: {str(e)}"

    def pull_latest_notes(self, save_dir: str, limit: int = 10) -> PullResult:
        """拉取GitHub仓库中的最新笔记

        Args:
            save_dir: 保存目录
            limit: 最多获取文件数量

        Returns:
            PullResult
        """
        valid, error = self._validate_config()
        if not valid:
            return PullResult(success=False, error=error)

        try:
            success, files, error = self.list_files(recursive=True)
            if not success:
                return PullResult(success=False, error=error)

            if not files:
                return PullResult(success=True, files=[], total_count=0)

            files.sort(key=lambda x: x.get("sha", ""), reverse=True)
            files = files[:limit]

            saved_files = []
            for file_info in files:
                path = file_info.get("path", "")
                content_success, content, content_error = self.get_file_content(path)

                if content_success and content:
                    safe_filename = re.sub(r'[^\w\s\u4e00-\u9fff-]', '_', file_info.get("name", "untitled"))
                    local_path = os.path.join(save_dir, safe_filename)

                    try:
                        os.makedirs(save_dir, exist_ok=True)
                        with open(local_path, 'w', encoding='utf-8') as f:
                            f.write(content)

                        saved_files.append({
                            "name": file_info.get("name"),
                            "path": path,
                            "local_path": local_path,
                        })
                        logger.info(f"已保存文件: {local_path}")
                    except Exception as e:
                        logger.error(f"保存文件失败 {local_path}: {e}")

            return PullResult(
                success=True,
                files=saved_files,
                total_count=len(saved_files),
            )

        except Exception as e:
            error_msg = f"拉取失败: {str(e)}"
            logger.error(error_msg)
            return PullResult(success=False, error=error_msg)

    def pull_all_notes(self, save_dir: str) -> PullResult:
        """拉取GitHub仓库中的所有笔记

        Args:
            save_dir: 保存目录

        Returns:
            PullResult
        """
        valid, error = self._validate_config()
        if not valid:
            return PullResult(success=False, error=error)

        return self.pull_latest_notes(save_dir, limit=999999)


_github_tool: Optional[GitHubTool] = None


def init_github_tool(config: GitHubConfig) -> GitHubTool:
    """初始化 GitHub 工具

    Args:
        config: GitHub配置

    Returns:
        GitHubTool实例
    """
    global _github_tool
    _github_tool = GitHubTool(config)
    return _github_tool


def get_github_tool() -> Optional[GitHubTool]:
    """获取 GitHub 工具实例"""
    return _github_tool


def create_github_config_from_env() -> Optional[GitHubConfig]:
    """从环境变量创建 GitHub 配置

    Returns:
        GitHubConfig或None
    """
    token = os.getenv("GITHUB_TOKEN", "")
    owner = os.getenv("GITHUB_OWNER", "")
    repo = os.getenv("GITHUB_REPO", "")
    branch = os.getenv("GITHUB_BRANCH", "main")

    if not token or not owner or not repo:
        return None

    return GitHubConfig(
        token=token,
        owner=owner,
        repo=repo,
        branch=branch,
    )
