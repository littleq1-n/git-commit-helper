"""git_ops 测试：mock subprocess.run，覆盖正常与异常路径。"""

from __future__ import annotations

import subprocess

import pytest

from git_commit_helper import git_ops
from git_commit_helper.errors import GitCommandError, NoStagedChanges


def _cp(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(args=["git"], returncode=returncode, stdout=stdout, stderr=stderr)


def test_is_git_repo_true(mocker):
    mocker.patch.object(git_ops, "_run", return_value=_cp(stdout="true\n"))
    assert git_ops.is_git_repo() is True


def test_is_git_repo_false(mocker):
    mocker.patch.object(git_ops, "_run", return_value=_cp(returncode=128, stderr="not a git repository"))
    assert git_ops.is_git_repo() is False


def test_get_staged_diff_ok(mocker):
    mocker.patch.object(git_ops, "_run", return_value=_cp(stdout="diff --git a/x b/x\n+hello\n"))
    diff = git_ops.get_staged_diff()
    assert "hello" in diff


def test_get_staged_diff_empty_raises(mocker):
    mocker.patch.object(git_ops, "_run", return_value=_cp(stdout="   \n"))
    with pytest.raises(NoStagedChanges):
        git_ops.get_staged_diff()


def test_get_staged_diff_git_error(mocker):
    mocker.patch.object(git_ops, "_run", return_value=_cp(returncode=128, stderr="fatal: not a git repository"))
    with pytest.raises(GitCommandError):
        git_ops.get_staged_diff()


def test_commit_ok(mocker):
    mocker.patch.object(git_ops, "_run", return_value=_cp(stdout="[main abc123] feat: x\n"))
    out = git_ops.commit("feat: x")
    assert "abc123" in out


def test_commit_fail(mocker):
    mocker.patch.object(git_ops, "_run", return_value=_cp(returncode=1, stderr="pre-commit hook failed"))
    with pytest.raises(GitCommandError):
        git_ops.commit("feat: x")


def test_get_log_ok(mocker):
    raw = "h1\x1ffeat: a\nh2\x1ffix: b"
    mocker.patch.object(git_ops, "_run", return_value=_cp(stdout=raw))
    assert git_ops.get_log(10) == raw


def test_get_log_empty_repo(mocker):
    mocker.patch.object(
        git_ops, "_run",
        return_value=_cp(returncode=128, stderr="fatal: your current branch 'main' does not have any commits yet"),
    )
    assert git_ops.get_log() == ""


def test_get_log_other_error(mocker):
    mocker.patch.object(git_ops, "_run", return_value=_cp(returncode=128, stderr="fatal: bad revision"))
    with pytest.raises(GitCommandError):
        git_ops.get_log()
