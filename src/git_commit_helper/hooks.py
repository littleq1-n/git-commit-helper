"""Git hook 安装/卸载，以及 hook 脚本运行时逻辑。

- prepare-commit-msg：用户未显式提供信息时，自动生成 Conventional Commits 信息。
- commit-msg：校验最终提交信息是否符合规范，不符合则阻止提交。

hook 脚本通过 ``python -m git_commit_helper.hooks <mode> <file>`` 调用本模块。
"""

from __future__ import annotations

import os
import stat
import sys

from . import git_ops

HOOK_MARKER = "# git-commit-helper-managed"

_PREPARE_SCRIPT = f"""\
#!/bin/sh
{HOOK_MARKER}
# 当未通过 -m / 合并 / 模板等方式提供信息时($2 为空)，自动生成提交信息
if [ -z "$2" ]; then
    python -m git_commit_helper.hooks prepare "$1" || true
fi
"""

_COMMIT_MSG_SCRIPT = f"""\
#!/bin/sh
{HOOK_MARKER}
# 校验提交信息是否符合 Conventional Commits 规范
python -m git_commit_helper.hooks validate "$1"
"""

_HOOKS = {
    "prepare-commit-msg": _PREPARE_SCRIPT,
    "commit-msg": _COMMIT_MSG_SCRIPT,
}


def _hooks_dir(repo_root: str) -> str:
    return os.path.join(repo_root, ".git", "hooks")


def install(repo_root: str = ".") -> list[str]:
    """安装 hook 脚本，返回已写入的文件路径列表。已存在则备份为 .bak。"""
    hooks_dir = _hooks_dir(repo_root)
    os.makedirs(hooks_dir, exist_ok=True)
    written: list[str] = []
    for name, content in _HOOKS.items():
        path = os.path.join(hooks_dir, name)
        if os.path.exists(path):
            os.replace(path, path + ".bak")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        mode = os.stat(path).st_mode
        os.chmod(path, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        written.append(path)
    return written


def uninstall(repo_root: str = ".") -> list[str]:
    """移除由本工具安装的 hook 脚本，返回已移除的文件路径列表。"""
    hooks_dir = _hooks_dir(repo_root)
    removed: list[str] = []
    for name in _HOOKS:
        path = os.path.join(hooks_dir, name)
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                if HOOK_MARKER in f.read():
                    os.remove(path)
                    removed.append(path)
    return removed


def run_prepare(msg_file: str) -> int:
    """prepare-commit-msg 运行时：若提交信息文件为空则自动生成并写入。"""
    from . import llm

    try:
        existing = ""
        if os.path.isfile(msg_file):
            with open(msg_file, "r", encoding="utf-8") as f:
                existing = f.read()
        # 仅当没有实质内容（忽略注释行）时才自动生成
        meaningful = [ln for ln in existing.splitlines() if ln.strip() and not ln.startswith("#")]
        if meaningful:
            return 0

        diff = git_ops.get_staged_diff()
        result = llm.generate_commit_message(diff)
        with open(msg_file, "w", encoding="utf-8") as f:
            f.write(result.message + "\n" + existing)
        return 0
    except Exception:
        # 自动生成失败不应阻断提交
        return 0


def run_validate(msg_file: str) -> int:
    """commit-msg 运行时：校验提交信息，不合规返回非零阻止提交。"""
    from .validator import validate

    with open(msg_file, "r", encoding="utf-8") as f:
        content = f.read()
    # 仅剔除 git 注释行，保留空行分隔以维持 subject/body 结构
    lines = [ln for ln in content.splitlines() if not ln.startswith("#")]
    message = "\n".join(lines).strip("\n")
    result = validate(message)
    if result.passed:
        return 0
    sys.stderr.write("提交信息不符合 Conventional Commits 规范：\n")
    for err in result.errors:
        sys.stderr.write(f"  - {err}\n")
    return 1


def main(argv: list[str] | None = None) -> int:
    """模块入口：``python -m git_commit_helper.hooks <prepare|validate> <file>``。"""
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 2:
        sys.stderr.write("用法: python -m git_commit_helper.hooks <prepare|validate> <msg_file>\n")
        return 2
    mode, msg_file = argv
    if mode == "prepare":
        return run_prepare(msg_file)
    if mode == "validate":
        return run_validate(msg_file)
    sys.stderr.write(f"未知模式: {mode}\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
