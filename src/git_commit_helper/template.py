"""Prompt 模板：内置默认模板 + 可选的用户自定义 Jinja2 模板。"""

from __future__ import annotations

import os

from jinja2 import Template

# 内置默认 prompt 模板，含 Conventional Commits 规则说明与 diff 占位符
DEFAULT_TEMPLATE = """\
你是一个资深工程师，请根据下面的 git staged diff 生成一条规范的提交信息。

要求：
- 严格遵循 Conventional Commits 规范，格式为 `type(scope): subject`。
- type 仅可取: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert。
- subject 使用祈使句、简洁、首行不超过 72 字符。
- 只输出提交信息本身，不要输出解释、代码块或多余内容。

git diff (staged):
{{ diff }}
"""


def load_template_source(template_path: str | None) -> tuple[str, bool]:
    """加载模板源码。

    返回 ``(source, used_default)``：当未配置路径或路径不存在时回退默认模板，
    此时 ``used_default`` 为 True。
    """
    if template_path and os.path.isfile(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read(), False
    return DEFAULT_TEMPLATE, True


def render(diff: str, template_path: str | None = None, **ctx) -> str:
    """渲染 prompt，将 diff 等上下文注入模板。"""
    source, _ = load_template_source(template_path)
    return Template(source).render(diff=diff, **ctx)
