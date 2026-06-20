"""提交信息校验：判断是否符合 Conventional Commits 规范。

可被生成流程（生成后自动校验）与历史分析（统计合规率）复用。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Conventional Commits 允许的 type 集合
ALLOWED_TYPES = {
    "feat", "fix", "docs", "style", "refactor",
    "perf", "test", "build", "ci", "chore", "revert",
}

DEFAULT_SUBJECT_MAX_LENGTH = 72

# 解析首行：type(scope)?!?: subject
_HEADER_RE = re.compile(
    r"^(?P<type>[a-zA-Z]+)(?:\((?P<scope>[^)]*)\))?(?P<bang>!)?:(?P<rest>.*)$"
)


@dataclass
class ValidationResult:
    """校验结果：是否通过 + 错误原因列表。"""

    passed: bool
    errors: list[str] = field(default_factory=list)


def validate(message: str, subject_max_length: int = DEFAULT_SUBJECT_MAX_LENGTH) -> ValidationResult:
    """校验一条提交信息，返回结构化结果。"""
    errors: list[str] = []

    if not message or not message.strip():
        return ValidationResult(passed=False, errors=["提交信息不能为空"])

    lines = message.splitlines()
    first_line = lines[0]

    match = _HEADER_RE.match(first_line)
    if not match:
        errors.append("首行缺少合法的 type 前缀，应形如 'type(scope): subject'")
        # 无法继续解析 type/subject，但仍可校验长度
    else:
        commit_type = match.group("type").lower()
        if commit_type not in ALLOWED_TYPES:
            allowed = ", ".join(sorted(ALLOWED_TYPES))
            errors.append(f"type '{commit_type}' 非法，允许的取值: {allowed}")

        subject = match.group("rest").strip()
        if not subject:
            errors.append("subject 不能为空")

    if len(first_line) > subject_max_length:
        errors.append(f"首行长度 {len(first_line)} 超过上限 {subject_max_length}")

    # 若存在正文，则首行与正文之间必须有一个空行
    if len(lines) > 1 and lines[1].strip() != "":
        errors.append("正文需与首行之间空一行")

    return ValidationResult(passed=not errors, errors=errors)
