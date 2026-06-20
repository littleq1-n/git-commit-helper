"""config 模块测试：默认值与环境变量覆盖。"""

from __future__ import annotations

from git_commit_helper.config import Settings


def test_defaults(monkeypatch, tmp_path):
    # 在一个没有 .env 的临时目录中加载，验证默认值
    monkeypatch.chdir(tmp_path)
    for var in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL", "LLM_MAX_RETRIES"):
        monkeypatch.delenv(var, raising=False)

    settings = Settings()

    assert settings.llm_model == "deepseek-chat"
    assert settings.llm_temperature == 0.2
    assert settings.llm_max_retries == 3
    assert settings.subject_max_length == 72
    assert settings.prompt_template_path is None


def test_env_override(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.setenv("LLM_MODEL", "qwen2.5")
    monkeypatch.setenv("LLM_MAX_RETRIES", "5")
    monkeypatch.setenv("SUBJECT_MAX_LENGTH", "50")

    settings = Settings()

    assert settings.llm_base_url == "http://localhost:11434/v1"
    assert settings.llm_model == "qwen2.5"
    assert settings.llm_max_retries == 5
    assert settings.subject_max_length == 50
