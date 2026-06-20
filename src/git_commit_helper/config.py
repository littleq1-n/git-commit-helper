"""配置加载：从 .env / 环境变量读取，集中管理可调参数。"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """运行配置。字段名对应环境变量（不区分大小写），如 ``llm_base_url`` ↔ ``LLM_BASE_URL``。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM 连接（兼容 OpenAI 协议：DeepSeek/通义/Kimi/Ollama/OpenAI 等）
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_api_key: str = ""
    llm_model: str = "deepseek-chat"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 512

    # 降级处理：失败重试次数
    llm_max_retries: int = 3

    # diff 截断阈值（字符数），防止超出上下文窗口
    diff_max_chars: int = 12000

    # 自定义 prompt 模板路径；为空则使用内置默认模板
    prompt_template_path: str | None = None

    # Conventional Commits 首行长度上限
    subject_max_length: int = 72


def load_settings() -> Settings:
    """加载并返回配置实例。"""
    return Settings()
