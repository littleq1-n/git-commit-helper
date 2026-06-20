"""hooks 测试：安装/卸载/备份，以及 prepare/validate 运行时。"""

from __future__ import annotations

import os
import stat

import pytest

from git_commit_helper import hooks
from git_commit_helper.llm import GenerationResult


def _make_repo(tmp_path):
    hooks_dir = tmp_path / ".git" / "hooks"
    hooks_dir.mkdir(parents=True)
    return str(tmp_path)


def test_install_writes_executable_hooks(tmp_path):
    repo = _make_repo(tmp_path)
    written = hooks.install(repo)

    assert len(written) == 2
    for path in written:
        assert os.path.isfile(path)
        assert hooks.HOOK_MARKER in open(path, encoding="utf-8").read()
        assert os.stat(path).st_mode & stat.S_IXUSR


def test_install_backs_up_existing(tmp_path):
    repo = _make_repo(tmp_path)
    existing = tmp_path / ".git" / "hooks" / "commit-msg"
    existing.write_text("#!/bin/sh\necho old", encoding="utf-8")

    hooks.install(repo)

    bak = tmp_path / ".git" / "hooks" / "commit-msg.bak"
    assert bak.is_file()
    assert "echo old" in bak.read_text(encoding="utf-8")


def test_uninstall_removes_managed_hooks(tmp_path):
    repo = _make_repo(tmp_path)
    hooks.install(repo)

    removed = hooks.uninstall(repo)

    assert len(removed) == 2
    assert not (tmp_path / ".git" / "hooks" / "commit-msg").exists()


def test_uninstall_keeps_foreign_hook(tmp_path):
    repo = _make_repo(tmp_path)
    foreign = tmp_path / ".git" / "hooks" / "commit-msg"
    foreign.write_text("#!/bin/sh\necho not ours", encoding="utf-8")

    removed = hooks.uninstall(repo)

    assert removed == []
    assert foreign.is_file()


def test_run_validate_pass(tmp_path):
    msg = tmp_path / "MSG"
    msg.write_text("feat: add feature\n", encoding="utf-8")
    assert hooks.run_validate(str(msg)) == 0


def test_run_validate_fail(tmp_path):
    msg = tmp_path / "MSG"
    msg.write_text("不规范的提交信息\n", encoding="utf-8")
    assert hooks.run_validate(str(msg)) == 1


def test_run_validate_ignores_comments(tmp_path):
    msg = tmp_path / "MSG"
    msg.write_text("fix: bug\n# 这是 git 注释，应被忽略\n", encoding="utf-8")
    assert hooks.run_validate(str(msg)) == 0


def test_run_validate_passes_with_body_and_trailer(tmp_path):
    msg = tmp_path / "MSG"
    msg.write_text(
        "feat: add a.txt\n\nCo-authored-by: Cursor <c@c.com>\n"
        "# 请输入提交信息。以 '#' 开头的行将被忽略\n",
        encoding="utf-8",
    )
    assert hooks.run_validate(str(msg)) == 0


def test_run_prepare_generates_when_empty(tmp_path, mocker):
    msg = tmp_path / "MSG"
    msg.write_text("\n# 注释行\n", encoding="utf-8")
    mocker.patch.object(hooks.git_ops, "get_staged_diff", return_value="+++ b/x\n+code")
    import git_commit_helper.llm as llm_mod
    mocker.patch.object(llm_mod, "generate_commit_message",
                        return_value=GenerationResult(message="feat: generated", degraded=False))

    rc = hooks.run_prepare(str(msg))

    assert rc == 0
    assert "feat: generated" in msg.read_text(encoding="utf-8")


def test_run_prepare_skips_when_has_content(tmp_path, mocker):
    msg = tmp_path / "MSG"
    msg.write_text("feat: 用户已写\n", encoding="utf-8")
    gen = mocker.patch("git_commit_helper.llm.generate_commit_message")

    rc = hooks.run_prepare(str(msg))

    assert rc == 0
    gen.assert_not_called()
    assert msg.read_text(encoding="utf-8") == "feat: 用户已写\n"


def test_main_unknown_mode():
    assert hooks.main(["foobar", "x"]) == 2


def test_main_validate(tmp_path):
    msg = tmp_path / "MSG"
    msg.write_text("docs: update\n", encoding="utf-8")
    assert hooks.main(["validate", str(msg)]) == 0
