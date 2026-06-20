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
