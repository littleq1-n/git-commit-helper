"""提交历史分析：解析 git log，统计类型分布与 Conventional Commits 合规率。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import validator
from .git_ops import LOG_FIELD_SEP

_TYPE_RE = re.compile(r"^([a-zA-Z]+)(?:\([^)]*\))?!?:")


@dataclass
class Commit:
    """单条提交记录。"""

    hash: str
    subject: str


@dataclass
class Report:
    """历史分析报告。"""

    total: int
    type_counts: dict[str, int] = field(default_factory=dict)
    compliant: int = 0
    non_compliant_subjects: list[str] = field(default_factory=list)

    @property
    def compliance_rate(self) -> float:
        """规范合规率（0~1）；无提交时为 0。"""
        if self.total == 0:
            return 0.0
        return self.compliant / self.total


def parse(raw_log: str) -> list[Commit]:
    """将 git log 原始输出解析为提交记录列表。"""
    commits: list[Commit] = []
    for line in raw_log.splitlines():
        if not line.strip():
            continue
        parts = line.split(LOG_FIELD_SEP)
        if len(parts) >= 2:
            commits.append(Commit(hash=parts[0], subject=parts[1]))
        else:
            commits.append(Commit(hash="", subject=parts[0]))
    return commits


def analyze(commits: list[Commit], subject_max_length: int = 72) -> Report:
    """统计类型分布、提交数与合规率（复用 validator）。"""
    report = Report(total=len(commits))
    for commit in commits:
        result = validator.validate(commit.subject, subject_max_length)
        if result.passed:
            report.compliant += 1
        else:
            report.non_compliant_subjects.append(commit.subject)

        match = _TYPE_RE.match(commit.subject)
        commit_type = match.group(1).lower() if match else "other"
        report.type_counts[commit_type] = report.type_counts.get(commit_type, 0) + 1
    return report


def build_markdown(report: Report) -> str:
    """将报告渲染为 Markdown 文本。"""
    lines = ["# 提交历史分析报告", ""]
    lines.append(f"- 总提交数：{report.total}")
    lines.append(f"- 规范合规率：{report.compliance_rate:.0%}")
    lines.append("")
    lines.append("## 类型分布")
    lines.append("")
    lines.append("| type | 数量 |")
    lines.append("| --- | ---: |")
    for commit_type, count in sorted(report.type_counts.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {commit_type} | {count} |")
    if report.non_compliant_subjects:
        lines.append("")
        lines.append("## 不合规提交")
        lines.append("")
        for subject in report.non_compliant_subjects:
            lines.append(f"- {subject}")
    lines.append("")
    return "\n".join(lines)


def format_stats(report: Report) -> str:
    """将报告统计格式化为文本，供 LLM 周报 prompt 使用。"""
    lines = [
        f"- 总提交数：{report.total}",
        f"- 合规率：{report.compliance_rate:.0%}",
    ]
    for commit_type, count in sorted(report.type_counts.items(), key=lambda kv: -kv[1]):
        lines.append(f"- {commit_type}：{count}")
    return "\n".join(lines)


def format_commits(commits: list[Commit], limit: int = 50) -> str:
    """将提交列表格式化为文本（每行一条 subject），供 LLM 周报 prompt 使用。"""
    subjects = [f"- {c.subject}" for c in commits[:limit]]
    return "\n".join(subjects)


def _heuristic_suggestions(report: Report) -> list[str]:
    """无 LLM 时基于类型分布给出规则版改进建议。"""
    suggestions: list[str] = []
    counts = report.type_counts
    if counts.get("test", 0) == 0 and report.total > 0:
        suggestions.append("缺少 test 类型提交，建议补充测试相关提交")
    if counts.get("docs", 0) > counts.get("feat", 0) and counts.get("feat", 0) >= 0:
        suggestions.append("docs 提交较多，建议增加 feat/test 类型提交以平衡交付")
    if report.compliance_rate < 1 and report.total > 0:
        suggestions.append(
            f"存在 {len(report.non_compliant_subjects)} 条不合规提交，建议规范化提交信息"
        )
    if not suggestions:
        suggestions.append("提交结构良好，继续保持规范化提交")
    return suggestions


def build_weekly_fallback(report: Report, commits: list[Commit]) -> str:
    """LLM 不可用时的规则版周报（与 LLM 输出结构一致）。"""
    lines = ["# Git 提交周报", "", "## 概览", ""]
    lines.append(f"- 总提交数：{report.total}")
    lines.append(f"- 合规率：{report.compliance_rate:.0%}")
    for commit_type, count in sorted(report.type_counts.items(), key=lambda kv: -kv[1]):
        lines.append(f"- {commit_type}：{count}")
    lines += ["", "## 主要变更", ""]
    for commit in commits[:10]:
        lines.append(f"- {commit.subject}")
    lines += ["", "## 建议", ""]
    for suggestion in _heuristic_suggestions(report):
        lines.append(f"- {suggestion}")
    lines.append("")
    return "\n".join(lines)


def build_table(report: Report):
    """将报告渲染为 Rich 表格（供 CLI 展示）。"""
    from rich.table import Table

    table = Table(title="提交历史分析")
    table.add_column("type", style="cyan")
    table.add_column("数量", justify="right")
    for commit_type, count in sorted(report.type_counts.items(), key=lambda kv: -kv[1]):
        table.add_row(commit_type, str(count))
    table.add_section()
    table.add_row("总提交数", str(report.total))
    table.add_row("合规率", f"{report.compliance_rate:.0%}")
    return table
