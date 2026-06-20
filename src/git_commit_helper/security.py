"""敏感信息扫描与脱敏：发送 diff 给 LLM 前检测疑似密钥/令牌/敏感文件。

采用正则启发式，注重高置信常见模式；非完备检测，最终由用户确认。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

REDACTION_PLACEHOLDER = "***REDACTED***"

# (类型说明, 正则)。正则中第 1 个捕获组为需要脱敏的敏感值；无捕获组则整体脱敏。
_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("私钥文件头", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("AWS Access Key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("OpenAI/通用 sk- 密钥", re.compile(r"sk-[A-Za-z0-9]{16,}")),
    ("GitHub Token", re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")),
    (
        "键值型密钥(api_key/secret/token/password)",
        re.compile(
            r"(?i)(?:api[_-]?key|secret|token|password|passwd)"
            r"\s*[:=]\s*['\"]?([^\s'\"]{6,})['\"]?"
        ),
    ),
    (
        ".env 敏感变量",
        re.compile(r"(?m)^\+?\s*(?:[A-Z0-9_]*(?:KEY|SECRET|TOKEN|PASSWORD))\s*=\s*(\S+)"),
    ),
]


@dataclass
class Finding:
    """一次敏感命中：类型 + 命中片段。"""

    kind: str
    snippet: str


def scan(diff: str) -> list[Finding]:
    """扫描 diff，返回所有疑似敏感命中（去重）。"""
    findings: list[Finding] = []
    seen: set[tuple[str, str]] = set()
    for kind, pattern in _PATTERNS:
        for match in pattern.finditer(diff):
            snippet = (match.group(1) if match.groups() else match.group(0)).strip()
            key = (kind, snippet)
            if snippet and key not in seen:
                seen.add(key)
                findings.append(Finding(kind=kind, snippet=snippet))
    return findings


def redact(diff: str) -> str:
    """将 diff 中命中的敏感值替换为占位符，返回脱敏后的副本。"""
    redacted = diff
    for _, pattern in _PATTERNS:
        def _sub(m: re.Match) -> str:
            if m.groups():
                # 仅替换敏感值捕获组，保留键名/前缀
                whole = m.group(0)
                value = m.group(1)
                return whole.replace(value, REDACTION_PLACEHOLDER)
            return REDACTION_PLACEHOLDER

        redacted = pattern.sub(_sub, redacted)
    return redacted
