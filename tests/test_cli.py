"""cli 测试：用 Typer CliRunner mock 各依赖，覆盖 y/e/n 分支与降级、analyze。"""

from __future__ import annotations

from typer.testing import CliRunner

from git_commit_helper import cli
from git_commit_helper.errors import GitCommandError, NoStagedChanges
from git_commit_helper.llm import GenerationResult

runner = CliRunner()


def _patch_common(mocker, diff="+++ b/x\n+code", degraded=False, message="feat: add x"):
    mocker.patch.object(cli.git_ops, "is_git_repo", return_value=True)
    mocker.patch.object(cli.git_ops, "get_staged_diff", return_value=diff)
    mocker.patch.object(
        cli.llm, "generate_commit_message",
        return_value=GenerationResult(message=message, degraded=degraded),
    )


def test_commit_confirm(mocker):
    _patch_common(mocker)
    mocker.patch.object(cli, "_prompt_action", return_value="commit")
    commit = mocker.patch.object(cli.git_ops, "commit", return_value="[main abc] feat: add x")

    result = runner.invoke(cli.app, ["commit"])

    assert result.exit_code == 0
    commit.assert_called_once_with("feat: add x")
    assert "已提交" in result.stdout


def test_commit_cancel(mocker):
    _patch_common(mocker)
    mocker.patch.object(cli, "_prompt_action", return_value="cancel")
    commit = mocker.patch.object(cli.git_ops, "commit")

    result = runner.invoke(cli.app, ["commit"])

    assert result.exit_code == 0
    commit.assert_not_called()
    assert "已取消" in result.stdout


def test_commit_edit(mocker):
    _patch_common(mocker)
    mocker.patch.object(cli, "_prompt_action", return_value="edit")
    mocker.patch.object(cli, "_edit_message", return_value="fix: edited subject")
    commit = mocker.patch.object(cli.git_ops, "commit", return_value="[main def] fix")

    result = runner.invoke(cli.app, ["commit"])

    assert result.exit_code == 0
    commit.assert_called_once_with("fix: edited subject")


def test_commit_no_staged(mocker):
    mocker.patch.object(cli.git_ops, "is_git_repo", return_value=True)
    mocker.patch.object(cli.git_ops, "get_staged_diff", side_effect=NoStagedChanges("无暂存改动"))

    result = runner.invoke(cli.app, ["commit"])

    assert result.exit_code == 1
    assert "无暂存改动" in result.stdout


def test_commit_not_a_repo(mocker):
    mocker.patch.object(cli.git_ops, "is_git_repo", return_value=False)

    result = runner.invoke(cli.app, ["commit"])

    assert result.exit_code == 1
    assert "不是 Git 仓库" in result.stdout


def test_commit_degraded_notice(mocker):
    _patch_common(mocker, degraded=True, message="chore: update x")
    mocker.patch.object(cli, "_prompt_action", return_value="commit")
    mocker.patch.object(cli.git_ops, "commit", return_value="[main abc] chore")

    result = runner.invoke(cli.app, ["commit"])

    assert result.exit_code == 0
    assert "降级" in result.stdout


def test_commit_commit_fails(mocker):
    _patch_common(mocker)
    mocker.patch.object(cli, "_prompt_action", return_value="commit")
    mocker.patch.object(cli.git_ops, "commit", side_effect=GitCommandError("hook 拒绝"))

    result = runner.invoke(cli.app, ["commit"])

    assert result.exit_code == 1
    assert "提交失败" in result.stdout


def test_analyze_ok(mocker):
    mocker.patch.object(cli.git_ops, "is_git_repo", return_value=True)
    raw = "h1\x1ffeat: a\nh2\x1ffix: b"
    mocker.patch.object(cli.git_ops, "get_log", return_value=raw)

    result = runner.invoke(cli.app, ["analyze"])

    assert result.exit_code == 0
    assert "提交历史分析" in result.stdout


def test_analyze_empty(mocker):
    mocker.patch.object(cli.git_ops, "is_git_repo", return_value=True)
    mocker.patch.object(cli.git_ops, "get_log", return_value="")

    result = runner.invoke(cli.app, ["analyze"])

    assert result.exit_code == 0
    assert "暂无提交历史" in result.stdout


def test_analyze_markdown_export(mocker, tmp_path):
    mocker.patch.object(cli.git_ops, "is_git_repo", return_value=True)
    raw = "h1\x1ffeat: a\nh2\x1ffix: b"
    mocker.patch.object(cli.git_ops, "get_log", return_value=raw)
    out = tmp_path / "report.md"

    result = runner.invoke(cli.app, ["analyze", "--markdown", str(out)])

    assert result.exit_code == 0
    assert out.is_file()
    content = out.read_text(encoding="utf-8")
    assert "# 提交历史分析报告" in content
    assert "已生成" in result.stdout


def test_analyze_markdown_empty_repo_no_file(mocker, tmp_path):
    mocker.patch.object(cli.git_ops, "is_git_repo", return_value=True)
    mocker.patch.object(cli.git_ops, "get_log", return_value="")
    out = tmp_path / "report.md"

    result = runner.invoke(cli.app, ["analyze", "--markdown", str(out)])

    assert result.exit_code == 0
    assert not out.exists()
    assert "暂无提交历史" in result.stdout


def test_commit_sensitive_redact_continue(mocker):
    sensitive = "+++ b/.env\n+API_KEY=sk-abcdef0123456789ABCDEF\n"
    _patch_common(mocker, diff=sensitive)
    mocker.patch.object(cli, "_prompt_sensitive", return_value="redact")
    mocker.patch.object(cli, "_prompt_action", return_value="commit")
    gen = mocker.patch.object(
        cli.llm, "generate_commit_message",
        return_value=GenerationResult(message="chore: update config", degraded=False),
    )
    mocker.patch.object(cli.git_ops, "commit", return_value="[main abc] chore")

    result = runner.invoke(cli.app, ["commit"])

    assert result.exit_code == 0
    assert "敏感信息" in result.stdout
    # 发送给 LLM 的 diff 应已脱敏，不含原始密钥
    sent_diff = gen.call_args.args[0]
    assert "sk-abcdef0123456789ABCDEF" not in sent_diff
    assert "REDACTED" in sent_diff


def test_commit_sensitive_cancel(mocker):
    sensitive = "+token=abcdef0123456789\n"
    _patch_common(mocker, diff=sensitive)
    mocker.patch.object(cli, "_prompt_sensitive", return_value="cancel")
    commit = mocker.patch.object(cli.git_ops, "commit")

    result = runner.invoke(cli.app, ["commit"])

    assert result.exit_code == 0
    assert "已取消" in result.stdout
    commit.assert_not_called()


def test_doctor_all_pass(mocker):
    from git_commit_helper.doctor import CheckResult
    mocker.patch.object(
        cli.doctor, "run_checks",
        return_value=[CheckResult(name="X", passed=True, detail="ok")],
    )
    result = runner.invoke(cli.app, ["doctor"])
    assert result.exit_code == 0
    assert "全部检查通过" in result.stdout


def test_doctor_with_failure(mocker):
    from git_commit_helper.doctor import CheckResult
    mocker.patch.object(
        cli.doctor, "run_checks",
        return_value=[CheckResult(name="X", passed=False, detail="bad", suggestion="修一下")],
    )
    result = runner.invoke(cli.app, ["doctor"])
    assert result.exit_code == 1
    assert "未通过" in result.stdout


def test_hook_install_cmd(mocker):
    mocker.patch.object(cli.git_ops, "is_git_repo", return_value=True)
    mocker.patch.object(cli.hooks, "install", return_value=["./.git/hooks/commit-msg"])
    result = runner.invoke(cli.app, ["hook", "install"])
    assert result.exit_code == 0
    assert "已安装" in result.stdout


def test_hook_install_not_repo(mocker):
    mocker.patch.object(cli.git_ops, "is_git_repo", return_value=False)
    result = runner.invoke(cli.app, ["hook", "install"])
    assert result.exit_code == 1
    assert "不是 Git 仓库" in result.stdout


def test_hook_uninstall_cmd(mocker):
    mocker.patch.object(cli.git_ops, "is_git_repo", return_value=True)
    mocker.patch.object(cli.hooks, "uninstall", return_value=["./.git/hooks/commit-msg"])
    result = runner.invoke(cli.app, ["hook", "uninstall"])
    assert result.exit_code == 0
    assert "已移除" in result.stdout


def test_hook_uninstall_none(mocker):
    mocker.patch.object(cli.git_ops, "is_git_repo", return_value=True)
    mocker.patch.object(cli.hooks, "uninstall", return_value=[])
    result = runner.invoke(cli.app, ["hook", "uninstall"])
    assert result.exit_code == 0
    assert "未发现" in result.stdout
