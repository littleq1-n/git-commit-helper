"""llm 测试：正常生成、空响应降级、重试后成功、全失败降级、截断。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from git_commit_helper import llm
from git_commit_helper.config import Settings


def _fake_response(content):
    """构造形如 openai 响应的对象：response.choices[0].message.content。"""
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


def _settings(**kw):
    base = dict(llm_api_key="k", llm_model="m", llm_max_retries=3, diff_max_chars=12000)
    base.update(kw)
    return Settings(**base)


@pytest.fixture(autouse=True)
def _no_sleep(mocker):
    # 避免真实退避等待拖慢测试
    mocker.patch.object(llm, "_backoff_sleep", return_value=None)


def test_generate_ok():
    client = SimpleNamespace()
    client.chat = SimpleNamespace()
    client.chat.completions = SimpleNamespace(
        create=lambda **kw: _fake_response("feat: add x")
    )

    result = llm.generate_commit_message("diff", settings=_settings(), client=client)

    assert result.degraded is False
    assert result.message == "feat: add x"


def test_empty_response_falls_back():
    client = SimpleNamespace()
    client.chat = SimpleNamespace()
    client.chat.completions = SimpleNamespace(create=lambda **kw: _fake_response(""))

    result = llm.generate_commit_message(
        "+++ b/src/app.py\n+code", settings=_settings(), client=client
    )

    assert result.degraded is True
    assert result.message.startswith("chore: update")


def test_retry_then_ok(mocker):
    calls = {"n": 0}

    def create(**kw):
        calls["n"] += 1
        if calls["n"] == 1:
            raise TimeoutError("timeout")
        return _fake_response("fix: recovered")

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))

    result = llm.generate_commit_message("diff", settings=_settings(), client=client)

    assert result.degraded is False
    assert result.message == "fix: recovered"
    assert calls["n"] == 2


def test_fallback_on_total_failure():
    def create(**kw):
        raise ConnectionError("down")

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))

    result = llm.generate_commit_message(
        "+++ b/main.py\n+x", settings=_settings(llm_max_retries=2), client=client
    )

    assert result.degraded is True
    assert "main.py" in result.message


def test_truncate_diff():
    long_diff = "x" * 100
    assert llm._truncate_diff(long_diff, 50).startswith("x" * 50)
    assert "截断" in llm._truncate_diff(long_diff, 50)
    assert llm._truncate_diff("short", 50) == "short"


def test_build_fallback_no_file():
    assert llm._build_fallback("no diff markers") == "chore: update files"
