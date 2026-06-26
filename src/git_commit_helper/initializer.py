"""`gch init` 的配置脚手架逻辑。

设计原则：API Key 不写入项目文件，始终通过环境变量注入，从源头避免随项目泄露。
``.env`` 只保存非敏感配置（base_url / model / 采样参数等）。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

ENV_FILENAME = ".env"

# 写入 .env 的非敏感配置项顺序（key, 默认值, 注释）
_ENV_FIELDS: list[tuple[str, str, str]] = [
    ("LLM_BASE_URL", "https://api.deepseek.com/v1", "LLM 接口地址（兼容 OpenAI 协议）"),
    ("LLM_MODEL", "deepseek-chat", "模型名称"),
    ("LLM_TEMPERATURE", "0.2", "生成温度（0~1，越低越稳定）"),
    ("LLM_MAX_TOKENS", "512", "单次请求最大 token"),
    ("LLM_MAX_RETRIES", "3", "失败重试次数"),
    ("DIFF_MAX_CHARS", "12000", "diff 截断阈值（字符数）"),
    ("SUBJECT_MAX_LENGTH", "72", "Conventional Commits 首行长度上限"),
]

_HEADER = (
    "# 本文件由 `gch init` 生成。API Key 不写入此处，改用环境变量：\n"
    "#   export LLM_API_KEY=\"你的真实密钥\"\n"
    "# 环境变量优先级高于 .env，因此此处不出现密钥也能正常工作。\n"
)


@dataclass
class InitValues:
    """初始化收集到的非敏感配置。"""

    values: dict[str, str] = field(default_factory=dict)

    def get(self, key: str, default: str) -> str:
        return self.values.get(key, default)


def default_values() -> dict[str, str]:
    """返回各配置项的默认值。"""
    return {key: default for key, default, _ in _ENV_FIELDS}


def render_env(values: dict[str, str] | None = None) -> str:
    """根据给定值渲染 .env 文本（不含任何密钥）。"""
    values = values or {}
    lines = [_HEADER]
    for key, default, comment in _ENV_FIELDS:
        lines.append(f"# {comment}")
        lines.append(f"{key}={values.get(key, default)}")
        lines.append("")
    lines.append("# 自定义 prompt 模板路径（可选）")
    lines.append("# PROMPT_TEMPLATE_PATH=templates/prompt_1.j2")
    lines.append("# 自定义周报 prompt 模板路径（可选）")
    lines.append("# REPORT_PROMPT_TEMPLATE_PATH=templates/report.j2")
    lines.append("")
    return "\n".join(lines)


def env_exists(directory: str = ".") -> bool:
    """判断目标目录是否已有 .env。"""
    return os.path.isfile(os.path.join(directory, ENV_FILENAME))


def write_env(content: str, directory: str = ".", overwrite: bool = False) -> tuple[str, bool]:
    """写入 .env 文件。

    返回 ``(path, written)``：当文件已存在且 ``overwrite`` 为 False 时不写入，
    ``written`` 为 False。
    """
    path = os.path.join(directory, ENV_FILENAME)
    if os.path.isfile(path) and not overwrite:
        return path, False
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path, True


def api_key_present() -> bool:
    """检测环境变量中是否已设置 LLM_API_KEY。"""
    return bool(os.environ.get("LLM_API_KEY"))


def export_hint(api_key: str | None = None) -> str:
    """生成设置 API Key 环境变量的引导命令。"""
    placeholder = api_key or "你的真实密钥"
    return f'export LLM_API_KEY="{placeholder}"'
