"""initializer 测试：.env 脚手架渲染与写入（密钥绝不入文件）。"""

from __future__ import annotations

from git_commit_helper import initializer


def _active_lines(content: str) -> list[str]:
    """返回非注释、非空的配置行。"""
    return [ln for ln in content.splitlines() if ln.strip() and not ln.strip().startswith("#")]


def test_render_env_has_no_api_key():
    content = initializer.render_env()
    # 密钥绝不作为有效配置写入 .env（注释中的 export 引导不算）
    assert not any(ln.startswith("LLM_API_KEY=") for ln in _active_lines(content))
    assert "LLM_BASE_URL=" in content
    assert "LLM_MODEL=" in content


def test_render_env_uses_custom_values():
    content = initializer.render_env({"LLM_MODEL": "qwen-plus"})
    assert "LLM_MODEL=qwen-plus" in content


def test_default_values_complete():
    values = initializer.default_values()
    assert values["LLM_BASE_URL"]
    assert values["LLM_MODEL"]


def test_write_env_creates_file(tmp_path):
    path, written = initializer.write_env("X=1\n", directory=str(tmp_path))
    assert written is True
    assert (tmp_path / ".env").read_text(encoding="utf-8") == "X=1\n"


def test_write_env_no_overwrite(tmp_path):
    (tmp_path / ".env").write_text("OLD\n", encoding="utf-8")
    path, written = initializer.write_env("NEW\n", directory=str(tmp_path), overwrite=False)
    assert written is False
    assert (tmp_path / ".env").read_text(encoding="utf-8") == "OLD\n"


def test_write_env_overwrite(tmp_path):
    (tmp_path / ".env").write_text("OLD\n", encoding="utf-8")
    path, written = initializer.write_env("NEW\n", directory=str(tmp_path), overwrite=True)
    assert written is True
    assert (tmp_path / ".env").read_text(encoding="utf-8") == "NEW\n"


def test_api_key_present(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    assert initializer.api_key_present() is False
    monkeypatch.setenv("LLM_API_KEY", "sk-real")
    assert initializer.api_key_present() is True


def test_export_hint():
    assert "export LLM_API_KEY" in initializer.export_hint()
