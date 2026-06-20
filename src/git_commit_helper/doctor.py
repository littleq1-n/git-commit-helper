"""环境自检：检查运行所需的依赖与配置，返回结构化结果供 CLI 渲染。"""

from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from dataclasses import dataclass

from . import git_ops
from .config import Settings

MIN_PYTHON = (3, 9)
REQUIRED_PACKAGES = ["typer", "rich", "questionary", "openai", "jinja2", "pydantic_settings"]


@dataclass
class CheckResult:
    """单项检查结果。"""

    name: str
    passed: bool
    detail: str = ""
    suggestion: str = ""


def _check_python() -> CheckResult:
    ok = sys.version_info[:2] >= MIN_PYTHON
    ver = ".".join(map(str, sys.version_info[:3]))
    return CheckResult(
        name="Python 版本",
        passed=ok,
        detail=f"当前 {ver}",
        suggestion="" if ok else f"需要 Python ≥ {MIN_PYTHON[0]}.{MIN_PYTHON[1]}",
    )


def _check_git() -> CheckResult:
    path = shutil.which("git")
    return CheckResult(
        name="git 可用",
        passed=path is not None,
        detail=path or "未找到",
        suggestion="" if path else "请安装 git",
    )


def _check_repo() -> CheckResult:
    ok = git_ops.is_git_repo()
    return CheckResult(
        name="Git 仓库",
        passed=ok,
        detail="是" if ok else "否",
        suggestion="" if ok else "在 Git 仓库中运行，或先 git init",
    )


def _check_env_file() -> CheckResult:
    ok = os.path.isfile(".env")
    return CheckResult(
        name=".env 配置文件",
        passed=ok,
        detail="存在" if ok else "缺失",
        suggestion="" if ok else "执行 cp .env.example .env 并填写",
    )


def _check_llm_config(settings: Settings) -> CheckResult:
    ok = bool(settings.llm_api_key) and bool(settings.llm_base_url) and bool(settings.llm_model)
    missing = [
        n for n, v in [
            ("LLM_API_KEY", settings.llm_api_key),
            ("LLM_BASE_URL", settings.llm_base_url),
            ("LLM_MODEL", settings.llm_model),
        ] if not v
    ]
    return CheckResult(
        name="LLM 配置",
        passed=ok,
        detail="已配置" if ok else f"缺少: {', '.join(missing)}",
        suggestion="" if ok else "在 .env 中补全相应字段",
    )


def _check_packages() -> CheckResult:
    missing = [p for p in REQUIRED_PACKAGES if importlib.util.find_spec(p) is None]
    return CheckResult(
        name="依赖包",
        passed=not missing,
        detail="已安装" if not missing else f"缺少: {', '.join(missing)}",
        suggestion="" if not missing else "pip install -r requirements.txt",
    )


def run_checks(settings: Settings | None = None) -> list[CheckResult]:
    """执行全部检查项，返回结果列表。"""
    settings = settings or Settings()
    return [
        _check_python(),
        _check_git(),
        _check_repo(),
        _check_env_file(),
        _check_llm_config(settings),
        _check_packages(),
    ]
