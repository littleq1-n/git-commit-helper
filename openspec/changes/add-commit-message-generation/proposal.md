## Why

开发者手写 Git 提交信息时常常随意、不统一，难以符合 Conventional Commits 规范，影响变更追溯、自动化版本管理与团队协作。本变更引入一个命令行工具，读取暂存区改动并借助 LLM 自动生成规范的提交信息，同时提供格式校验与历史分析，降低规范化提交的心智负担。

## What Changes

- 新增 CLI 工具 `git-commit-helper`（命令 `gch`），提供 `commit` 与 `analyze` 两个子命令。
- `commit` 子命令：读取 `git diff --staged` → 调用 LLM 生成 1 条 Conventional Commits 提交信息 → 终端展示 → 用户确认/编辑/取消 → 可选执行 `git commit`。
- 支持**自定义 prompt 模板**（Jinja2），用户可覆盖默认生成风格。
- 新增 **commit message 格式校验**：独立模块校验是否符合 Conventional Commits 规范，生成后自动校验。
- LLM 调用具备**降级处理**：超时/限流/服务错误时指数退避重试，重试耗尽后回退到模板兜底信息，保证流程不中断。
- `analyze` 子命令：解析 `git log`，统计提交类型分布、提交数与规范合规率。
- 通过 `.env` 切换不同 LLM 提供商（兼容 OpenAI 协议：DeepSeek/通义/Kimi/Ollama/OpenAI 等）。

## Capabilities

### New Capabilities

- `commit-generation`: 读取暂存 diff、调用 LLM 生成提交信息、展示与交互确认（确认/编辑/取消）、可选执行提交，以及 LLM 失败时的重试与降级兜底。
- `message-validation`: 校验提交信息是否符合 Conventional Commits 规范（type 合法性、subject 非空、首行长度限制、body/footer 结构）。
- `prompt-templating`: 加载与渲染自定义 Jinja2 prompt 模板，缺失时回退内置默认模板。
- `history-analysis`: 解析 Git 提交历史，统计类型分布、提交数量与规范合规率并输出报告。

### Modified Capabilities

<!-- 无：本项目为全新能力，openspec/specs/ 下暂无既有规范 -->

## Impact

- **新增代码**：`src/git_commit_helper/` 下的 `cli.py`、`git_ops.py`、`llm.py`、`validator.py`、`template.py`、`history.py`、`config.py`、`errors.py`。
- **依赖**：typer、rich、questionary、openai、pydantic-settings、jinja2、pytest（已在 `requirements.txt` 声明）。
- **运行环境**：纯软件，依赖一个兼容 OpenAI 协议的 LLM 端点（通过 `.env` 配置）。
- **外部系统**：调用本地 `git` 命令与远端 LLM API；不修改用户的全局 git 配置。
