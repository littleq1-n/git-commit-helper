## Context

本工具是一个纯软件的命令行程序，目标是读取 Git 暂存区改动，借助 LLM 生成符合 Conventional Commits 规范的提交信息，并提供格式校验与历史分析。约束条件：

- 纯本地运行，仅依赖本地 `git` 命令与一个兼容 OpenAI 协议的远端 LLM 端点。
- 不得修改用户的全局 git 配置；密钥仅通过本地 `.env` 读取，绝不入库。
- 需在弱网/限流/服务异常下保持可用（降级）。
- 目标测试覆盖率 ≥80%，因此模块需易于 mock（隔离副作用：子进程、网络）。

相关文档：动机见 `proposal.md`，需求见 `specs/`（commit-generation / message-validation / prompt-templating / history-analysis）。

## Goals / Non-Goals

**Goals:**
- 清晰的分层模块，副作用（git 子进程、LLM 网络）集中在边界层，便于测试。
- 校验能力独立成模块，供生成流程与历史分析共同复用。
- LLM 提供商可通过配置切换（OpenAI 协议），不改代码。
- LLM 失败时降级到模板兜底，保证 `commit` 流程不中断。

**Non-Goals:**
- 不做多候选 message、git hook 集成、周报、多语言等（属增强版，见 PLAN 第 7 节）。
- 不实现真正的多 provider 适配器抽象（MVP 阶段用单一 OpenAI 兼容客户端 + base_url 切换）。
- 不直接操作 Git 内部对象（统一通过 `git` 命令行）。

## Decisions

### D1: 通过 subprocess 调用 git，而非 GitPython
- **选择**：用 `subprocess.run(["git", ...], capture_output=True, text=True)`。
- **理由**：零额外依赖、行为与用户终端一致、输出便于在测试中 mock。
- **备选**：GitPython —— 引入额外依赖且对 diff/commit 这类简单操作收益有限。

### D2: 用 openai SDK + base_url 切换提供商
- **选择**：`openai.OpenAI(base_url=..., api_key=...)`，模型名走配置。
- **理由**：DeepSeek/通义/Kimi/Ollama/OpenAI 均兼容该协议，一套代码多家可用。
- **备选**：为每家写适配器 —— MVP 阶段过度设计，留作增强版。

### D3: 校验独立成 `validator.py`
- **选择**：用正则解析 `type(scope)?: subject`，返回结构化 `ValidationResult(passed, errors)`。
- **理由**：满足 R8；生成后自动校验、历史分析算合规率均复用同一接口，单一职责、易测。
- **备选**：内联在 cli/llm 中 —— 无法复用、难独立测试。

### D4: 模板用 Jinja2，默认内置 + 可覆盖
- **选择**：内置默认模板字符串；若配置 `PROMPT_TEMPLATE_PATH` 存在则加载之，否则回退默认。
- **理由**：满足 R6，且对用户零配置可用。
- **备选**：f-string 拼接 —— 不支持用户自定义、表达力弱。

### D5: 降级策略 = 有限重试 + 模板兜底
- **选择**：对超时/限流/5xx 做 N 次指数退避重试；耗尽后返回 `chore: update <主改动文件>` 形式的兜底信息并标记 `degraded=True`。
- **理由**：满足 R9，保证 `commit` 流程在无网络/服务异常时仍可走完。
- **备选**：直接报错退出 —— 体验差，不满足"流程不中断"。

### D6: 配置用 pydantic-settings 读取 .env
- **选择**：`Settings` 模型集中管理 base_url/api_key/model/温度/max_tokens/重试次数/模板路径/首行长度阈值。
- **理由**：类型校验 + 默认值 + 环境变量覆盖，单测友好。

### 模块与数据流
```
cli.py (Typer)
 ├─ commit:  git_ops.get_staged_diff → template.render → llm.generate(+重试/降级)
 │           → validator.validate → Rich 展示 → questionary 确认/编辑/取消 → git_ops.commit
 └─ analyze: git_ops.get_log → history.parse → history.analyze(复用 validator) → Rich 报告
config.py / errors.py 为横切支撑
```

## Risks / Trade-offs

- [LLM 输出不稳定，可能夹带解释或代码块] → prompt 明确要求只输出 message；生成后 `validator` 兜底校验，不通过则提示重生成/编辑。
- [diff 过大超出上下文窗口] → 在 `llm` 层按 `LLM_MAX_TOKENS` 截断 diff 后再请求。
- [单一 OpenAI 兼容客户端无法覆盖个别非标端点] → 接受该取舍，多 provider 适配留增强版。
- [subprocess 解析 git 输出受语言环境影响] → 调用时固定 `--porcelain`/稳定参数，必要时设 `LANG=C`。
- [降级兜底信息质量低] → 仅作为不中断流程的保底，并显式提示用户"已降级"以便其手动完善。

## Migration Plan

全新工具，无存量迁移。部署 = 安装依赖 + 配置 `.env`。回滚 = 不安装/移除该 CLI，对仓库无副作用。

## Open Questions

- 编辑模式优先用 `$EDITOR` 还是行内编辑？（倾向：有 `$EDITOR` 则用，否则 questionary 行内）—— 实现时定，不影响 specs。
- 首行长度上限默认 72 是否需可配置？（已决定：放入 config，默认 72）。
