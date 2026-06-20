"""命令行入口：commit（生成并提交）与 analyze（历史分析）。"""

from __future__ import annotations

import os

import typer
from rich.console import Console
from rich.panel import Panel

from . import git_ops, history, llm, validator
from .config import load_settings
from .errors import GitCommandError, NoStagedChanges

app = typer.Typer(help="智能 Git 提交助手：生成符合 Conventional Commits 规范的提交信息。")


def _prompt_action() -> str:
    """交互式选择操作，返回 'commit' / 'edit' / 'cancel'。"""
    import questionary

    choice = questionary.select(
        "请选择操作：",
        choices=[
            questionary.Choice("提交", "commit"),
            questionary.Choice("编辑后提交", "edit"),
            questionary.Choice("取消", "cancel"),
        ],
    ).ask()
    return choice or "cancel"


def _edit_message(message: str) -> str:
    """编辑提交信息：优先使用 $EDITOR，否则行内编辑。"""
    if os.environ.get("EDITOR"):
        import click

        edited = click.edit(message)
        return (edited or message).strip()

    import questionary

    edited = questionary.text("编辑提交信息：", default=message).ask()
    return (edited or message).strip()


def _render_message(console: Console, message: str, result: validator.ValidationResult) -> None:
    """展示生成的提交信息与校验结果。"""
    console.print(Panel(message, title="生成的提交信息", border_style="cyan"))
    if result.passed:
        console.print("[green]✔ 符合 Conventional Commits 规范[/green]")
    else:
        console.print("[yellow]⚠ 校验未通过：[/yellow] " + "；".join(result.errors))


@app.command("commit")
def commit_cmd() -> None:
    """读取暂存区改动，生成提交信息并交互确认后提交。"""
    console = Console()
    settings = load_settings()

    if not git_ops.is_git_repo():
        console.print("[red]当前目录不是 Git 仓库[/red]")
        raise typer.Exit(code=1)

    try:
        diff = git_ops.get_staged_diff()
    except NoStagedChanges as exc:
        console.print(f"[yellow]{exc}[/yellow]")
        raise typer.Exit(code=1)
    except GitCommandError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)

    gen = llm.generate_commit_message(diff, settings=settings)
    message = gen.message
    if gen.degraded:
        console.print("[yellow]⚠ LLM 调用失败，已降级为模板兜底信息，请检查后再提交[/yellow]")

    result = validator.validate(message, settings.subject_max_length)
    _render_message(console, message, result)

    action = _prompt_action()
    if action == "cancel":
        console.print("已取消，未提交。")
        raise typer.Exit(code=0)

    if action == "edit":
        message = _edit_message(message)
        result = validator.validate(message, settings.subject_max_length)
        if not result.passed:
            console.print("[yellow]编辑后仍不符合规范：[/yellow] " + "；".join(result.errors))

    try:
        output = git_ops.commit(message)
    except GitCommandError as exc:
        console.print(f"[red]提交失败：{exc}[/red]")
        raise typer.Exit(code=1)

    console.print(f"[green]✔ 已提交[/green] {output}")


@app.command("analyze")
def analyze_cmd(
    count: int = typer.Option(50, "--count", "-n", help="分析最近多少条提交"),
) -> None:
    """分析提交历史：类型分布、提交数与规范合规率。"""
    console = Console()
    settings = load_settings()

    if not git_ops.is_git_repo():
        console.print("[red]当前目录不是 Git 仓库[/red]")
        raise typer.Exit(code=1)

    commits = history.parse(git_ops.get_log(count))
    if not commits:
        console.print("暂无提交历史")
        raise typer.Exit(code=0)

    report = history.analyze(commits, settings.subject_max_length)
    console.print(history.build_table(report))


if __name__ == "__main__":
    app()
