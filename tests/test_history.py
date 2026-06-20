"""history 测试：解析、统计、合规率、空仓库。"""

from __future__ import annotations

from git_commit_helper import history
from git_commit_helper.git_ops import LOG_FIELD_SEP


def _raw(*pairs):
    return "\n".join(f"{h}{LOG_FIELD_SEP}{s}" for h, s in pairs)


def test_parse_ok():
    raw = _raw(("h1", "feat: a"), ("h2", "fix: b"))
    commits = history.parse(raw)
    assert len(commits) == 2
    assert commits[0].hash == "h1"
    assert commits[0].subject == "feat: a"


def test_parse_empty():
    assert history.parse("") == []


def test_analyze_counts_and_rate():
    commits = history.parse(_raw(
        ("h1", "feat: a"),
        ("h2", "feat: b"),
        ("h3", "fix: c"),
        ("h4", "random non compliant"),
    ))
    report = history.analyze(commits)

    assert report.total == 4
    assert report.type_counts["feat"] == 2
    assert report.type_counts["fix"] == 1
    assert report.compliant == 3
    assert report.compliance_rate == 0.75
    assert "random non compliant" in report.non_compliant_subjects


def test_analyze_empty_repo():
    report = history.analyze([])
    assert report.total == 0
    assert report.compliance_rate == 0.0
    assert report.type_counts == {}


def test_build_table_returns_table():
    from rich.table import Table

    report = history.analyze(history.parse(_raw(("h1", "feat: a"))))
    table = history.build_table(report)
    assert isinstance(table, Table)


def test_build_markdown_content():
    commits = history.parse(_raw(
        ("h1", "feat: a"),
        ("h2", "fix: b"),
        ("h3", "随便写的不合规"),
    ))
    report = history.analyze(commits)
    md = history.build_markdown(report)

    assert "# 提交历史分析报告" in md
    assert "总提交数：3" in md
    assert "| type | 数量 |" in md
    assert "| feat | 1 |" in md
    assert "## 不合规提交" in md
    assert "随便写的不合规" in md
