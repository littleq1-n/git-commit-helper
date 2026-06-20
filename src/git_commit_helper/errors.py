"""自定义异常类型。"""

from __future__ import annotations


class GitCommitHelperError(Exception):
    """工具内所有异常的基类。"""


class NotAGitRepo(GitCommitHelperError):
    """当前目录不是一个 Git 仓库。"""


class NoStagedChanges(GitCommitHelperError):
    """暂存区没有任何改动。"""


class GitCommandError(GitCommitHelperError):
    """底层 git 命令执行失败。"""


class LLMError(GitCommitHelperError):
    """调用 LLM 过程中发生的错误（含重试耗尽）。"""


class InvalidMessage(GitCommitHelperError):
    """提交信息不符合 Conventional Commits 规范。"""
