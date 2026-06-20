## Why

标准版已实现核心的提交信息生成闭环。增强版进一步提升**安全性**（避免把密钥发给 LLM）、**易用性**（环境自检、git hook 自动化）与**可交付性**（历史分析导出 Markdown 报告），让工具更贴近真实团队工作流。

## What Changes

- 新增 `gch doctor` 命令：检查运行环境（Python 版本、git、是否 Git 仓库、`.env` 与 LLM 配置、依赖是否安装），输出诊断表与修复建议。
- 新增**敏感信息扫描/脱敏**：在把 diff 发给 LLM 前扫描疑似密钥/令牌/`.env` 等敏感内容；发现时提示用户选择「脱敏后继续 / 取消」。
- `gch analyze` 新增 `--markdown/-m` 选项：将历史分析结果导出为 Markdown 报告文件。
- 新增 `gch hook install` / `gch hook uninstall`：安装 `prepare-commit-msg`（自动生成提交信息）与 `commit-msg`（校验是否符合 Conventional Commits）两个 Git hook。

## Capabilities

### New Capabilities

- `environment-doctor`: 环境自检命令，检查依赖与配置并给出修复建议。
- `sensitive-scanning`: 发送 diff 给 LLM 前扫描敏感信息，支持脱敏或取消。
- `markdown-report`: 历史分析结果导出为 Markdown 报告文件。
- `git-hooks`: 安装/卸载 prepare-commit-msg 与 commit-msg 钩子，实现自动生成与提交校验。

### Modified Capabilities

<!-- 无：标准版 specs 尚未归档至 openspec/specs/，敏感扫描集成已由 sensitive-scanning 能力覆盖 -->
<!-- commit 流程中新增的扫描步骤在实现阶段接入 cli.commit，不改变既有正常/异常行为 -->


## Impact

- **新增代码**：`security.py`（扫描/脱敏）、`doctor.py`（环境检查）、`hooks.py`（hook 安装），`history.py` 增加 Markdown 渲染，`cli.py` 增加 `doctor`/`hook` 子命令与 `analyze --markdown`。
- **依赖**：无新增第三方依赖（沿用标准库 + 既有依赖）。
- **运行环境**：纯软件；hook 安装会在 `.git/hooks/` 下写入脚本文件。
- **兼容性**：所有增强为新增能力，不破坏标准版既有命令行为。
