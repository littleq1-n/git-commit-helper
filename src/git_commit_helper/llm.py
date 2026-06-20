"""LLM 调用层：渲染 prompt、调用兼容 OpenAI 协议的端点，含重试与降级。"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass

from . import template
from .config import Settings, load_settings

_FALLBACK_FILE_RE = re.compile(r"^\+\+\+ b/(.+)$", re.MULTILINE)


@dataclass
class GenerationResult:
    """生成结果：提交信息 + 是否为降级兜底。"""

    message: str
    degraded: bool = False


def _truncate_diff(diff: str, max_chars: int) -> str:
    """将过长的 diff 截断到阈值，避免超出上下文窗口。"""
    if len(diff) <= max_chars:
        return diff
    return diff[:max_chars] + "\n... [diff 已截断] ..."


def _build_fallback(diff: str) -> str:
    """LLM 不可用时，基于 diff 生成模板兜底提交信息。"""
    match = _FALLBACK_FILE_RE.search(diff)
    if match:
        path = match.group(1).strip()
        return f"chore: update {path}"
    return "chore: update files"


def _backoff_sleep(attempt: int) -> None:
    """指数退避：第 attempt 次失败后等待 2**(attempt-1) 秒。"""
    time.sleep(2 ** (attempt - 1))


def _make_client(settings: Settings):
    """构造 OpenAI 兼容客户端（延迟导入，便于测试时不依赖网络）。"""
    from openai import OpenAI

    return OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)


def _extract_content(response) -> str:
    """从响应中提取纯文本提交信息。"""
    try:
        return (response.choices[0].message.content or "").strip()
    except (AttributeError, IndexError, TypeError):
        return ""


def generate_commit_message(
    diff: str,
    settings: Settings | None = None,
    client=None,
) -> GenerationResult:
    """根据 staged diff 生成提交信息。

    成功返回 ``GenerationResult(message, degraded=False)``；
    达到最大重试仍失败时返回模板兜底信息并标记 ``degraded=True``。
    """
    settings = settings or load_settings()
    truncated = _truncate_diff(diff, settings.diff_max_chars)
    prompt = template.render(truncated, settings.prompt_template_path)

    if client is None:
        client = _make_client(settings)

    attempts = max(1, settings.llm_max_retries)
    for attempt in range(1, attempts + 1):
        try:
            response = client.chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
            )
            content = _extract_content(response)
            if not content:
                raise ValueError("LLM 返回空内容")
            return GenerationResult(message=content, degraded=False)
        except Exception:
            if attempt < attempts:
                _backoff_sleep(attempt)

    # 重试耗尽 -> 降级兜底
    return GenerationResult(message=_build_fallback(diff), degraded=True)
