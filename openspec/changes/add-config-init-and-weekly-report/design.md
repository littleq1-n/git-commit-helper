# Design: 配置初始化与 LLM 提交周报

## 架构概览

本变更不引入新分层，沿用既有「CLI 编排 → 领域模块（git_ops/llm/history/security/...）→ 配置」的结构，新增一个无状态的配置脚手架模块 `initializer.py`，并在 `llm` 与 `history` 中扩展周报相关函数。

## 模块划分

### Module: initializer
- 职责：渲染 / 写入 `.env`（仅非敏感配置），检测与引导 API Key 环境变量。
- 关键接口：`render_env(values)`、`write_env(content, directory, overwrite)`、`default_values()`、`api_key_present()`、`export_hint(api_key)`。
- 设计约束：**绝不**把密钥写入返回内容；密钥仅出现在打印给用户的引导命令中。

### Module: llm（扩展）
- `generate_weekly_report(report, commits, settings, client)`：复用内部 `_complete`（带重试/退避/异常分类）；失败时调用 `history.build_weekly_fallback` 降级。

### Module: history（扩展）
- `format_stats` / `format_commits`：将统计与提交列表格式化为 prompt 文本。
- `build_weekly_fallback`：规则版周报，`_heuristic_suggestions` 基于类型分布给建议（缺 test / docs 偏多 / 存在不合规）。

### Module: security（扩展）
- `scan_and_redact(diff) -> (safe_diff, findings)`：非交互封装，供 git hook 等无人值守路径复用，保证与交互式 commit 的脱敏策略一致。

## 数据模型

- 复用既有 `history.Report` / `history.Commit` / `llm.GenerationResult` / `security.Finding`，不新增持久化结构。

## 技术选型说明

- **密钥走环境变量而非文件**：pydantic-settings 中环境变量优先级高于 `.env`，因此项目内不出现密钥也能正常加载；从源头消除 `.env` 误提交导致的泄露。
- **周报降级而非报错**：与标准版「LLM 失败降级」一致的可用性原则，保证离线/限流时仍能产出可读周报。
- **复用 `_complete` 而非复制重试逻辑**：提交信息与周报共享同一套重试/退避/异常分类，避免逻辑分叉。
- **hook 固化 `sys.executable`**：规避未激活 venv 或 GUI 客户端 PATH 不含本包导致的 hook 失败。
