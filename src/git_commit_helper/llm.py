"""LLM 调用层：渲染 prompt、调用兼容 OpenAI 协议的端点，含重试与降级。"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass

from . import history, template
from .config import Settings, load_settings

logger = logging.getLogger(__name__)

_FALLBACK_FILE_RE = re.compile(r"^\+\+\+ b/(.+)$", re.MULTILINE)

# 不可重试的错误（鉴权/请求非法等），命中后立即降级而非空耗重试。
_FATAL_ERROR_NAMES = {
    "AuthenticationError",
    "PermissionDeniedError",
    "BadRequestError",
    "NotFoundError",
}


@dataclass
class GenerationResult:
    """生成结果：文本 + 是否为降级兜底。"""

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


def _is_fatal(exc: Exception) -> bool:
    """判断异常是否属于不可重试的致命错误。"""
    return type(exc).__name__ in _FATAL_ERROR_NAMES


def _make_client(settings: Settings):
    """构造 OpenAI 兼容客户端（延迟导入，便于测试时不依赖网络）。"""
    from openai import OpenAI

    return OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)


def _extract_content(response) -> str:
    """从响应中提取纯文本内容。"""
    try:
        return (response.choices[0].message.content or "").strip()
    except (AttributeError, IndexError, TypeError):
        return ""


def _complete(prompt: str, settings: Settings, client) -> str:
    """带重试的单次补全；全部失败时抛出最后一个异常。"""
    attempts = max(1, settings.llm_max_retries)
    last_exc: Exception | None = None
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
            return content
        except Exception as exc:  # 网络/SDK 异常类型繁多，统一兜底但记录原因
            last_exc = exc
            logger.warning("LLM 第 %d/%d 次调用失败：%s", attempt, attempts, exc)
            if _is_fatal(exc):
                logger.warning("检测到不可重试错误，停止重试：%s", type(exc).__name__)
                break
            if attempt < attempts:
                _backoff_sleep(attempt)
    raise last_exc if last_exc else RuntimeError("LLM 调用失败")


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

    try:
        if client is None:
            client = _make_client(settings)
        content = _complete(prompt, settings, client)
        return GenerationResult(message=content, degraded=False)
    except Exception as exc:
        logger.warning("LLM 生成提交信息失败（%s），已降级为模板兜底", exc)
        return GenerationResult(message=_build_fallback(diff), degraded=True)


def generate_weekly_report(
    report: history.Report,
    commits: list[history.Commit],
    settings: Settings | None = None,
    client=None,
) -> GenerationResult:
    """结合 LLM 生成「Git 提交周报」（概览 / 主要变更 / 建议）。

    LLM 不可用时降级为基于规则的静态周报并标记 ``degraded=True``，流程不中断。
    """
    settings = settings or load_settings()
    stats = history.format_stats(report)
    commit_lines = history.format_commits(commits)
    prompt = template.render_report(stats, commit_lines, settings.report_prompt_template_path)

    try:
        if client is None:
            client = _make_client(settings)
        content = _complete(prompt, settings, client)
        return GenerationResult(message=content, degraded=False)
    except Exception as exc:
        logger.warning("LLM 生成周报失败（%s），已降级为规则版周报", exc)
        return GenerationResult(
            message=history.build_weekly_fallback(report, commits),
            degraded=True,
        )
