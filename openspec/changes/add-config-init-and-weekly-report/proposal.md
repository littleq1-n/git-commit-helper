## Why

评审反馈暴露三类问题需要收口：(1) 密钥安全——本地 `.env` 易混入真实 key 而泄露；(2) 打包与可移植性——运行依赖未声明、git hook 路径绕过敏感扫描且硬编码 `python`；(3) 增强版历史分析仅做统计，价值有限。本变更引入 `gch init` 配置脚手架（密钥强制走环境变量）、将历史分析升级为**结合 LLM 的提交周报**，并修复安全/打包/健壮性问题。

## What Changes

- 新增 `gch init`：交互/非交互生成 `.env`（仅非敏感配置），引导通过环境变量 `LLM_API_KEY` 注入密钥，**密钥不写入任何项目文件**。
- `gch analyze` 新增 `--ai` 选项：结合 LLM 生成「Git 提交周报」（`## 概览` / `## 主要变更` / `## 建议`），LLM 不可用时降级为规则版周报。
- 安全一致性：抽出 `security.scan_and_redact`，git hook 自动生成路径与交互式 `commit` 一致地脱敏后再发 LLM。
- 可移植性：git hook 脚本固化 `sys.executable`；`commit-msg` 校验读取用户 `SUBJECT_MAX_LENGTH` 配置。
- 健壮性：LLM 调用细化异常并记录原因，鉴权类错误不重试；`git` 命令加超时；`analyze` 写报告自动建目录并处理异常；`commit` 编辑后回到交互菜单形成闭环。
- 打包：`pyproject.toml` 声明 `[project].dependencies` 与 `[project.optional-dependencies].dev`，`pip install -e .` 自洽。

## Capabilities

### New Capabilities

- `config-init`: 配置初始化命令，生成 `.env` 并引导密钥走环境变量。
- `llm-weekly-report`: 结合 LLM 的提交周报生成，含规则版降级。

### Modified Capabilities

- `sensitive-scanning`: 新增非交互 `scan_and_redact`，覆盖 git hook 自动生成路径。
- `git-hooks`: hook 脚本固化解释器路径；校验读取用户配置。

## 验收标准

- [x] `gch init` 生成的 `.env` 不含任何有效的 `LLM_API_KEY` 配置行；已存在时默认不覆盖、`--force` 可覆盖
- [x] 未设置 `LLM_API_KEY` 环境变量时给出 `export` 引导；已设置时提示就绪
- [x] `gch analyze --ai` 输出含「概览/主要变更/建议」三段；LLM 失败时降级为规则版且结构一致
- [x] git hook 自动生成路径对敏感信息脱敏后再发 LLM（与交互式 commit 一致）
- [x] `pip install -e .` 后 `gch` 可直接运行（依赖随包安装）
- [x] 全量 pytest 通过、覆盖率 ≥80%（实际 100 用例 / 90%）

## Impact

- **新增代码**：`initializer.py`、`cli.init` 子命令、`llm.generate_weekly_report`、`history.format_stats/format_commits/build_weekly_fallback`、`template.render_report`、`security.scan_and_redact`。
- **修改**：`cli.analyze`（`--ai` 与写文件防护）、`cli.commit`（编辑闭环）、`hooks.py`（脱敏/解释器/配置）、`git_ops._run`（超时）、`config.py`（`report_prompt_template_path`）、`pyproject.toml`（依赖）。
- **依赖**：无新增第三方依赖。
- **安全**：API Key 不再出现在项目文件中。
