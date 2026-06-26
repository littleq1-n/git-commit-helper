"""命令行入口：commit（生成并提交）与 analyze（历史分析）。"""

from __future__ import annotations

import os
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from . import doctor, git_ops, history, hooks, initializer, llm, security, validator
from .config import load_settings
from .errors import GitCommandError, NoStagedChanges

app = typer.Typer(help="智能 Git 提交助手：生成符合 Conventional Commits 规范的提交信息。")
hook_app = typer.Typer(help="安装/卸载 Git hook（自动生成与提交校验）。")
app.add_typer(hook_app, name="hook")


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


def _prompt_sensitive() -> str:
    """敏感信息命中后交互选择，返回 'redact'（脱敏后继续）或 'cancel'（取消）。"""
    import questionary

    choice = questionary.select(
        "检测到疑似敏感信息，请选择：",
        choices=[
            questionary.Choice("脱敏后继续", "redact"),
            questionary.Choice("取消", "cancel"),
        ],
    ).ask()
    return choice or "cancel"


def _scan_and_handle(console: Console, diff: str) -> str | None:
    """扫描 diff；命中敏感信息时提示用户。

    返回用于发送 LLM 的 diff（可能已脱敏）；用户取消时返回 None。
    """
    findings = security.scan(diff)
    if not findings:
        return diff

    console.print("[yellow]⚠ 检测到疑似敏感信息：[/yellow]")
    for finding in findings:
        console.print(f"  - {finding.kind}: {finding.snippet}")

    if _prompt_sensitive() == "redact":
        console.print("[green]已脱敏，将发送脱敏后的 diff[/green]")
        return security.redact(diff)
    return None


def _render_message(console: Console, message: str, result: validator.ValidationResult) -> None:
    """展示生成的提交信息与校验结果。"""
    console.print(Panel(message, title="生成的提交信息", border_style="cyan"))
    if result.passed:
        console.print("[green]✔ 符合 Conventional Commits 规范[/green]")
    else:
        console.print("[yellow]⚠ 校验未通过：[/yellow] " + "；".join(result.errors))


@app.command("init")
def init_cmd(
    yes: bool = typer.Option(False, "--yes", "-y", help="使用默认值非交互生成，不询问"),
    force: bool = typer.Option(False, "--force", "-f", help="已存在 .env 时直接覆盖"),
) -> None:
    """初始化配置：交互式生成 .env（不含密钥），并引导通过环境变量设置 API Key。"""
    console = Console()

    if initializer.env_exists() and not force:
        if yes:
            console.print("[yellow].env 已存在，使用 --force 可覆盖。已跳过生成。[/yellow]")
            _print_key_guidance(console)
            return
        import questionary

        overwrite = questionary.confirm(".env 已存在，是否覆盖？", default=False).ask()
        if not overwrite:
            console.print("已保留现有 .env。")
            _print_key_guidance(console)
            return
        force = True

    values = initializer.default_values()
    if not yes:
        import questionary

        for key in ("LLM_BASE_URL", "LLM_MODEL", "LLM_TEMPERATURE", "LLM_MAX_TOKENS"):
            answer = questionary.text(f"{key}", default=values[key]).ask()
            if answer is not None and answer.strip():
                values[key] = answer.strip()

    content = initializer.render_env(values)
    path, written = initializer.write_env(content, overwrite=force or yes)
    if written:
        console.print(f"[green]✔ 已生成配置文件：{path}[/green]")
    else:
        console.print(f"[yellow].env 已存在，未覆盖：{path}[/yellow]")

    _print_key_guidance(console)


def _print_key_guidance(console: Console) -> None:
    """打印 API Key 环境变量设置引导（密钥不入项目文件）。"""
    if initializer.api_key_present():
        console.print("[green]✔ 已检测到环境变量 LLM_API_KEY[/green]")
        return
    console.print(
        Panel(
            "为避免密钥随项目泄露，API Key 不写入 .env，请通过环境变量设置：\n\n"
            f"  [cyan]{initializer.export_hint()}[/cyan]\n\n"
            "可将上述命令写入 ~/.bashrc 或 ~/.zshrc 以持久化。",
            title="设置 API Key",
            border_style="yellow",
        )
    )


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

    send_diff = _scan_and_handle(console, diff)
    if send_diff is None:
        console.print("已取消，未提交。")
        raise typer.Exit(code=0)

    gen = llm.generate_commit_message(send_diff, settings=settings)
    message = gen.message
    if gen.degraded:
        console.print("[yellow]⚠ LLM 调用失败，已降级为模板兜底信息，请检查后再提交[/yellow]")

    result = validator.validate(message, settings.subject_max_length)
    _render_message(console, message, result)

    # 交互闭环：编辑后重新校验并回到菜单，用户可继续编辑/提交/取消
    while True:
        action = _prompt_action()
        if action == "cancel":
            console.print("已取消，未提交。")
            raise typer.Exit(code=0)
        if action == "edit":
            message = _edit_message(message)
            result = validator.validate(message, settings.subject_max_length)
            _render_message(console, message, result)
            continue
        break

    try:
        output = git_ops.commit(message)
    except GitCommandError as exc:
        console.print(f"[red]提交失败：{exc}[/red]")
        raise typer.Exit(code=1)

    console.print(f"[green]✔ 已提交[/green] {output}")


def _write_report(console: Console, path: str, content: str) -> None:
    """写入报告文件，自动创建父目录并处理写入异常。"""
    from pathlib import Path

    out = Path(path)
    try:
        if out.parent and not out.parent.exists():
            out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
    except OSError as exc:
        console.print(f"[red]写入报告失败：{exc}[/red]")
        raise typer.Exit(code=1)


@app.command("analyze")
def analyze_cmd(
    count: int = typer.Option(50, "--count", "-n", help="分析最近多少条提交"),
    markdown: Optional[str] = typer.Option(
        None, "--markdown", "-m", help="导出 Markdown 报告到指定路径"
    ),
    ai: bool = typer.Option(
        False, "--ai", help="结合 LLM 生成「Git 提交周报」（概览/主要变更/建议）"
    ),
) -> None:
    """分析提交历史：类型分布、提交数与规范合规率；可选 LLM 周报。"""
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

    if ai:
        gen = llm.generate_weekly_report(report, commits, settings=settings)
        if gen.degraded:
            console.print("[yellow]⚠ LLM 调用失败，已降级为规则版周报[/yellow]")
        if markdown:
            _write_report(console, markdown, gen.message)
            console.print(f"[green]✔ 已生成周报：{markdown}[/green]")
        else:
            from rich.markdown import Markdown

            console.print(Markdown(gen.message))
        return

    if markdown:
        _write_report(console, markdown, history.build_markdown(report))
        console.print(f"[green]✔ 已生成 Markdown 报告：{markdown}[/green]")
    else:
        console.print(history.build_table(report))


@app.command("doctor")
def doctor_cmd() -> None:
    """检查运行环境与配置，输出诊断表并给出修复建议。"""
    from rich.table import Table

    console = Console()
    settings = load_settings()
    results = doctor.run_checks(settings)

    table = Table(title="环境检查 (gch doctor)")
    table.add_column("检查项", style="cyan")
    table.add_column("状态", justify="center")
    table.add_column("详情")
    table.add_column("建议", style="yellow")
    for r in results:
        status = "[green]✔[/green]" if r.passed else "[red]✗[/red]"
        table.add_row(r.name, status, r.detail, r.suggestion)
    console.print(table)

    failed = [r for r in results if not r.passed]
    if failed:
        console.print(f"[red]{len(failed)} 项未通过，请按建议修复[/red]")
        raise typer.Exit(code=1)
    console.print("[green]✔ 全部检查通过[/green]")


@hook_app.command("install")
def hook_install_cmd() -> None:
    """在当前仓库安装 prepare-commit-msg 与 commit-msg 钩子。"""
    console = Console()
    if not git_ops.is_git_repo():
        console.print("[red]当前目录不是 Git 仓库[/red]")
        raise typer.Exit(code=1)
    written = hooks.install(".")
    for path in written:
        console.print(f"[green]✔ 已安装[/green] {path}")


@hook_app.command("uninstall")
def hook_uninstall_cmd() -> None:
    """移除由本工具安装的 Git 钩子。"""
    console = Console()
    if not git_ops.is_git_repo():
        console.print("[red]当前目录不是 Git 仓库[/red]")
        raise typer.Exit(code=1)
    removed = hooks.uninstall(".")
    if removed:
        for path in removed:
            console.print(f"[green]✔ 已移除[/green] {path}")
    else:
        console.print("未发现由本工具安装的 hook")


if __name__ == "__main__":
    app()
