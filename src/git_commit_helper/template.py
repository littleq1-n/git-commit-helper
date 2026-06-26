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

# 内置默认周报 prompt 模板，引导模型输出固定三段式结构
DEFAULT_REPORT_TEMPLATE = """\
你是研发团队的技术助理。请根据下面的 Git 提交统计与提交列表，生成一份简洁的中文「Git 提交周报」。

要求：
- 使用 Markdown 格式，且必须包含且仅包含以下三个二级标题（顺序固定）：
  ## 概览
  ## 主要变更
  ## 建议
- 「概览」用无序列表列出：总提交数、合规率，以及各 type 的数量。
- 「主要变更」从提交列表中挑选重要的提交，按类型归纳为要点（不要逐条罗列全部）。
- 「建议」基于类型分布给出 1~3 条可执行改进建议（如测试/文档覆盖、规范合规）。
- 标题用「# Git 提交周报」开头。只输出 Markdown 正文，不要代码块包裹、不要多余解释。

统计数据：
{{ stats }}

提交列表：
{{ commits }}
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


def render_report(stats: str, commits: str, template_path: str | None = None) -> str:
    """渲染周报 prompt，将统计与提交列表注入模板。

    未配置路径或路径不存在时回退内置默认周报模板。
    """
    source = DEFAULT_REPORT_TEMPLATE
    if template_path and os.path.isfile(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            source = f.read()
    return Template(source).render(stats=stats, commits=commits)
