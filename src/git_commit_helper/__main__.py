"""模块入口：支持 ``python -m git_commit_helper``。"""

from __future__ import annotations

from .cli import app


def main() -> None:
    app()


if __name__ == "__main__":
    main()
