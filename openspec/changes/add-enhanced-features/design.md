## Context

增强版在标准版（`commit`/`analyze` + 8 个模块）基础上扩展。约束沿用标准版：副作用集中在边界层、易于 mock、不修改用户全局配置、密钥不入库。本次新增 4 项能力，需尽量复用既有模块（`validator`/`history`/`llm`/`git_ops`）。

## Goals / Non-Goals

**Goals:**
- 安全：发送 diff 给 LLM 前可扫描并脱敏敏感信息，脱敏只作用于发送副本。
- 自助：`gch doctor` 一键自检环境与配置。
- 可交付：历史分析可导出 Markdown 报告。
- 自动化：通过 git hook 实现「自动生成提交信息」与「提交信息校验」。
- 不破坏标准版任何既有行为，所有新增可独立测试。

**Non-Goals:**
- 不做真正的密钥保险库/加密存储。
- 不做远程 hook 分发（仅本仓库 `.git/hooks/`）。
- 敏感扫描采用正则启发式，不追求 100% 召回。

## Decisions

### D1: 敏感扫描独立成 `security.py`
- **选择**：`scan(diff) -> list[Finding]` + `redact(diff) -> str`，正则匹配常见模式（API key、token、secret、`.env` 行、私钥头）。
- **理由**：单一职责、易测、可被 commit 流程与未来 hook 复用。
- **备选**：内联进 llm/cli —— 不可复用、难测。

### D2: 脱敏只作用于发送副本
- **选择**：在 `cli.commit` 中，扫描原始 diff；用户选脱敏则把 `redact(diff)` 传给 `llm.generate_commit_message`，工作区/暂存区不动。
- **理由**：满足「不修改真实文件」要求，安全可控。

### D3: `doctor.py` 返回结构化检查结果
- **选择**：`run_checks(settings) -> list[CheckResult(name, passed, detail, suggestion)]`，CLI 负责渲染表格与退出码。
- **理由**：逻辑与展示分离，检查项可单测（mock 环境）。

### D4: Markdown 报告复用 history.Report
- **选择**：在 `history.py` 增 `build_markdown(report) -> str`，CLI `analyze --markdown PATH` 写文件。
- **理由**：与既有 `build_table` 并列，零重复统计逻辑。

### D5: hook 脚本调用已安装的 CLI
- **选择**：`hooks.py` 写入两个 shell 脚本：
  - `prepare-commit-msg`：当提交信息文件为空/默认时，调用 `gch` 生成（非交互模式）写入。
  - `commit-msg`：调用工具校验最终信息，不合规则非零退出阻止提交。
- **安装**：写入 `.git/hooks/`，`chmod +x`，已存在则备份 `.bak`。
- **理由**：hook 轻量、与主程序解耦；通过调用 CLI 复用全部既有逻辑。
- **备选**：core.hooksPath —— 改用户配置，违背「不改全局配置」，不采用。

### 数据流（commit 增强后）
```
get_staged_diff → security.scan
   ├─ 无命中 → 原 diff
   └─ 有命中 → 提示 → [脱敏] security.redact / [取消] 退出
        ↓
   llm.generate_commit_message(发送副本) → validator → 展示 → 确认 → commit
```

## Risks / Trade-offs

- [正则脱敏可能漏报/误报] → 采用常见高置信模式，宁可多报并让用户确认；文档注明非完备。
- [hook 在不同 shell/系统下兼容性] → 用 `#!/bin/sh` + 最小依赖，调用已在 PATH 的 `gch`/`python -m`。
- [prepare-commit-msg 自动生成需要 LLM/网络] → 失败时回退标准版降级逻辑，不阻断提交。
- [doctor 网络连通性检查耗时] → 默认仅做本地检查；连通性作为可选项，避免卡住。

## Migration Plan

纯新增能力，无数据迁移。hook 通过 `gch hook install/uninstall` 可逆。

## Open Questions

- prepare-commit-msg 是否默认启用 LLM 生成？倾向：默认启用，失败回退降级信息（不阻断）。实现时确定，不影响 specs。
