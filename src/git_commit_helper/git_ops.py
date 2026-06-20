"""Git 操作层：统一通过 subprocess 调用 git 命令，便于测试时 mock。"""

from __future__ import annotations

import subprocess
from typing import Sequence

from .errors import GitCommandError, NoStagedChanges

# git log 字段分隔符（单元分隔符 \x1f），记录以换行分隔
LOG_FIELD_SEP = "\x1f"
LOG_FORMAT = f"%H{LOG_FIELD_SEP}%s"


def _run(args: Sequence[str]) -> subprocess.CompletedProcess:
    """执行 git 命令并返回结果（不自动抛错，由调用方判断）。"""
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
    )


def is_git_repo() -> bool:
    """判断当前工作目录是否在一个 Git 仓库内。"""
    result = _run(["rev-parse", "--is-inside-work-tree"])
    return result.returncode == 0 and result.stdout.strip() == "true"


def get_staged_diff() -> str:
    """读取暂存区 diff；为空时抛出 NoStagedChanges。"""
    result = _run(["diff", "--staged"])
    if result.returncode != 0:
        raise GitCommandError(result.stderr.strip() or "git diff --staged 执行失败")
    diff = result.stdout
    if not diff.strip():
        raise NoStagedChanges("暂存区没有改动，请先使用 git add 暂存文件")
    return diff


def commit(message: str) -> str:
    """使用给定信息执行提交；失败时抛出 GitCommandError，成功返回 git 输出摘要。"""
    result = _run(["commit", "-m", message])
    if result.returncode != 0:
        raise GitCommandError(result.stderr.strip() or "git commit 执行失败")
    return result.stdout.strip()


def get_log(count: int = 50) -> str:
    """读取最近 count 条提交的原始日志（每行 ``<hash>\\x1f<subject>``）。

    空仓库（尚无提交）返回空字符串而非抛错。
    """
    result = _run(["log", f"-n{count}", f"--pretty=format:{LOG_FORMAT}"])
    if result.returncode != 0:
        stderr = result.stderr.lower()
        if "does not have any commits" in stderr or "your current branch" in stderr:
            return ""
        raise GitCommandError(result.stderr.strip() or "git log 执行失败")
    return result.stdout
