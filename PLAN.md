# 执行计划 · SD-05 智能 Git 提交助手

> 本文档是项目的"作战地图"，对应培训方案的 SDD 五阶段流程与 100 分评审标准。
> 技术选型：**Python + Typer CLI + OpenAI 协议（可切换多家 LLM）+ Jinja2 模板 + pytest**。
>
> 范围分两版：**标准版（必做，覆盖任务全部需求）** + **增强版（选做，加分项）**。

---

## 0. 环境现状（已搭建完成）

| 组件 | 版本/状态 | 说明 |
|------|-----------|------|
| Python | 3.11.13（venv 内） | 虚拟环境 `.venv/` 已创建并装好依赖 |
| Node.js | v20.20.2 | 供 OpenSpec 使用 |
| OpenSpec CLI | 1.4.1 | 已 `openspec init`，集成 Cursor + Claude |
| Git | 2.34.1 | 仓库已 `git init`（main 分支） |
| LLM 依赖 | openai 2.x | 通过 `.env` 的 `base_url` 切换提供商 |

### ⚠️ 你需要手动做的两件事

1. **配置 Git 身份**（出于安全，工具未替你改全局配置）：
   ```bash
   git config --global user.name "你的名字"
   git config --global user.email "你的邮箱@example.com"
   ```
2. **配置 LLM 密钥**：
   ```bash
   cd /root/xinruipeixun/01_git_helper
   cp .env.example .env
   # 编辑 .env，填入 LLM_BASE_URL / LLM_API_KEY / LLM_MODEL
   ```

---

## 1. 目标与范围（两版）

### 标准版（必做）——覆盖任务全部需求

| 编号 | 需求 | 说明 |
|------|------|------|
| **R1** | 读取 staged diff | `git diff --staged`，无暂存改动时友好提示 |
| **R2** | 调 LLM 生成 1 条 message | 符合 Conventional Commits 规范 |
| **R3** | 展示结果 | Rich 面板展示生成的 message |
| **R4** | 用户确认 / 编辑 / 取消 | `[y] 提交 / [e] 编辑 / [n] 取消` |
| **R5** | 可选择执行 commit | 确认后调用 `git commit` |
| **R6** | 自定义 prompt 模板 | Jinja2 模板文件，用户可改写生成风格 |
| **R7** | 提交历史分析 | 解析 `git log`，统计类型分布、活跃度等 |
| **R8** | commit message 格式校验 | 独立校验模块，校验是否符合 Conventional Commits |
| **R9** | API 失败时的降级处理 | 超时/报错/限流时重试 + 降级到模板兜底 |
| **R10** | README + 截图 + 测试报告 | 文档与验证产物齐全 |

### 增强版（选做）——加分项 / 演示亮点
见第 7 节路线图（多候选、多 provider、git hook、周报、breaking change 检测、多语言等）。

---

## 2. 架构与模块设计

```
                          ┌─────────────┐
   git add ───────────▶   │   cli.py    │  入口/命令/交互编排（Typer + Rich + questionary）
                          └──────┬──────┘
        ┌─────────┬──────────────┼──────────────┬─────────────┐
        ▼         ▼              ▼              ▼             ▼
 ┌───────────┐┌──────────┐┌─────────────┐┌─────────────┐┌──────────┐
 │ git_ops.py ││  llm.py  ││ validator.py││ template.py ││history.py│
 │ 读 diff /  ││ 调 LLM + ││ 校验 CC 格式 ││ Jinja2 模板 ││ git log  │
 │ commit/log ││ 降级处理 ││  (R8)       ││ 加载渲染(R6)││ 分析(R7) │
 └───────────┘└──────────┘└─────────────┘└─────────────┘└──────────┘
        │            │            │              │             │
        └────────────┴──────┬─────┴──────────────┴─────────────┘
                            ▼
                    ┌───────────────┐
                    │ config.py /   │  配置(.env) + 自定义异常
                    │ errors.py     │
                    └───────────────┘
```

| 模块 | 文件 | 职责 | 关键函数（建议） | 覆盖需求 |
|------|------|------|------------------|----------|
| 入口 | `cli.py` | 命令与交互编排（`commit`/`analyze` 子命令） | `commit_cmd()` / `analyze_cmd()` | R3 R4 R5 |
| Git 操作 | `git_ops.py` | 读暂存 diff、执行提交、读 log | `get_staged_diff()` / `commit()` / `get_log()` / `is_git_repo()` | R1 R5 R7 |
| LLM 调用 | `llm.py` | 调 API + 重试 + 降级兜底 | `generate_commit_message(diff, prompt)` | R2 R9 |
| **格式校验** | `validator.py` | 校验 Conventional Commits 格式（**新增**） | `validate(message) -> ValidationResult` | R8 |
| 模板 | `template.py` | 加载/渲染自定义 Jinja2 prompt 模板 | `load_template()` / `render(diff)` | R6 |
| 历史分析 | `history.py` | 解析 `git log`，统计输出 | `analyze(commits) -> Report` | R7 |
| 配置 | `config.py` | 读取 `.env`（base_url/key/model/模板路径/重试次数等） | `Settings`（pydantic-settings） | 全局 |
| 异常 | `errors.py` | 自定义异常类型 | `NotAGitRepo` / `NoStagedChanges` / `LLMError` / `InvalidMessage` | 全局 |

**设计要点**
- Git 操作统一用 `subprocess.run([...], capture_output=True)`，便于测试 mock。
- LLM 用 `openai.OpenAI(base_url=..., api_key=...)`，换提供商只改配置。
- **R8 校验**独立成 `validator.py`：用正则按 `type(scope)?: subject` 解析，校验 type 合法性、subject 非空、首行长度 ≤ 阈值（默认 72）、可选 body/footer。返回结构化结果（是否通过 + 错误列表）。生成后自动校验，不通过则提示重生成或进入编辑。
- **R9 降级**：`llm.py` 内做 N 次指数退避重试；全部失败时返回模板兜底 message（如 `chore: update <主改动文件名>`）并明确提示"已降级"，保证流程不中断。
- **R6 模板**：默认模板内置，用户可在 `.env` 指定 `PROMPT_TEMPLATE_PATH` 覆盖，用 Jinja2 渲染（变量含 diff、历史风格等）。

---

## 3. 需求—功能—测试 映射表

> 用于验证「每条需求都有实现 + 有测试」，对应评审的 specs 覆盖与测试覆盖项。

| 需求 | 对应功能/模块 | Specs 场景（正常+异常） | 测试用例（tests/） |
|------|---------------|-------------------------|--------------------|
| R1 读取 staged diff | `git_ops.get_staged_diff()` | 有暂存改动→返回 diff；无暂存→提示退出 | `test_git_ops.py::test_get_staged_diff_ok` / `::test_no_staged_changes` |
| R2 生成 message | `llm.generate_commit_message()` | 正常返回 1 条；返回空→报错 | `test_llm.py::test_generate_ok` / `::test_empty_response` |
| R3 展示结果 | `cli` + Rich | 正常渲染面板 | `test_cli.py::test_render_message` |
| R4 确认/编辑/取消 | `cli` + questionary | y→提交；e→编辑后提交；n→取消不提交 | `test_cli.py::test_confirm_yes/edit/cancel` |
| R5 执行 commit | `git_ops.commit()` | 确认后成功提交；commit 失败→报错 | `test_git_ops.py::test_commit_ok` / `::test_commit_fail` |
| R6 自定义模板 | `template.py` | 默认模板可用；自定义模板生效；模板缺失→回退默认 | `test_template.py::test_default/custom/missing` |
| R7 提交历史分析 | `history.py` + `analyze` 子命令 | 正常统计类型分布；空仓库→提示无提交 | `test_history.py::test_analyze_ok` / `::test_empty_repo` |
| **R8 格式校验** | `validator.validate()` | 合法 message 通过；缺 type/超长/空 subject→不通过并给出原因 | `test_validator.py::test_valid` / `::test_missing_type` / `::test_too_long` / `::test_empty_subject` |
| R9 API 降级 | `llm.py` 重试+兜底 | 首次失败重试后成功；多次失败→返回模板兜底并提示 | `test_llm.py::test_retry_then_ok` / `::test_fallback_on_failure` |
| R10 文档/报告 | README + docs | — | 人工：README 截图、`pytest` 报告归档 |

---

## 4. SDD 五阶段执行计划

OpenSpec change 已创建：`openspec/changes/add-commit-message-generation/`
（用 `openspec status --change add-commit-message-generation` 查看制品状态）

> 说明：标准版需求较多，specs 建议**按能力分文件**编写（如 `commit-generation`、`message-validation`、`history-analysis` 等），都归于该 change 之下。

### 阶段 1 · Proposal + Specs 初稿　【评分 5+10】
- [ ] `proposal.md`：背景 / 目标 / 范围（标准版 R1–R10 + 增强版「不包含」）/ 验收标准 / 技术栈
- [ ] specs 初稿：按映射表为 R1–R9 各列场景
- 命令参考：`openspec instructions proposal --change add-commit-message-generation`

### 阶段 2 · 完善 Specs　【评分 10】
- [ ] 每条需求 **≥2 场景（正常 + 异常）**，Given/When/Then
- [ ] 边界覆盖：无暂存、非 git 仓库、空 diff、超大 diff、API 超时/限流、非法 message、空仓库历史
- [ ] 使用 RFC 2119 关键词（SHALL/MUST/SHOULD/MAY）
- [ ] `openspec validate --change add-commit-message-generation` 通过

### 阶段 3 · Design + Tasks　【评分 10+5】
- [ ] `design.md`：填入第 2 节架构图、模块表、接口、技术选型理由、R8/R9 方案细节
- [ ] `tasks.md`：复制第 5 节任务清单

### 阶段 4 · Implementation　【评分 30｜代码质量】
按第 5 节任务逐个实现，**每个 Task 一次 commit**，message 用本工具规范（dogfooding）。

### 阶段 5 · Verification + Demo　【评分 10】
- [ ] 映射表中每条 specs 场景都有对应测试，`pytest` 通过率 ≥80%
- [ ] 生成测试报告：`pytest --cov --cov-report=html` → 归档到 `docs/`
- [ ] README 补运行截图、测试结果（R10）
- [ ] 10 分钟演示：3 分钟介绍 + 5 分钟演示（含 analyze 子命令）+ 2 分钟 SDD 心得
- [ ] 保留与 AI 协作的对话记录（AI 工具使用占 20 分）

---

## 5. 实现任务拆解（tasks.md 蓝本 · 细化版）

### Phase 0 · 项目骨架
- [ ] T0.1 确认包结构 `src/git_commit_helper/`，补 `__main__.py` 入口
- [ ] T0.2 `errors.py`：定义 `NotAGitRepo` / `NoStagedChanges` / `LLMError` / `InvalidMessage`
- [ ] T0.3 `config.py`：pydantic-settings 读取 `.env`（base_url/key/model/温度/重试次数/模板路径/首行长度阈值）
- [ ] T0.4 为 `config` 写单测（缺省值、环境变量覆盖）

### Phase 1 · Git 操作层（R1 R5 R7）
- [ ] T1.1 `git_ops.is_git_repo()`：判断当前目录是否 git 仓库
- [ ] T1.2 `git_ops.get_staged_diff()`：读 `git diff --staged`，空时抛 `NoStagedChanges`
- [ ] T1.3 `git_ops.commit(message)`：执行 `git commit -m`，失败抛错
- [ ] T1.4 `git_ops.get_log(n)`：读 `git log` 原始数据供历史分析
- [ ] T1.5 `test_git_ops.py`：mock `subprocess`，覆盖正常 + 无暂存 + commit 失败 + 非仓库

### Phase 2 · 格式校验模块（R8 · 新增）
- [ ] T2.1 `validator.py`：定义 `ValidationResult`（passed: bool, errors: list）
- [ ] T2.2 正则解析 `type(scope)?: subject`，校验 type 在合法集合内
- [ ] T2.3 校验规则：subject 非空、首行 ≤ 阈值（默认 72）、空行分隔 body/footer
- [ ] T2.4 `validate(message)` 汇总所有错误
- [ ] T2.5 `test_validator.py`：合法 / 缺 type / 非法 type / 超长 / 空 subject / 多行 body

### Phase 3 · 自定义模板（R6）
- [ ] T3.1 内置默认 prompt 模板（含 Conventional Commits 规则说明）
- [ ] T3.2 `template.load_template()`：优先读 `PROMPT_TEMPLATE_PATH`，缺失回退默认
- [ ] T3.3 `template.render(diff, **ctx)`：Jinja2 渲染
- [ ] T3.4 `test_template.py`：默认 / 自定义生效 / 路径缺失回退

### Phase 4 · LLM 调用 + 降级（R2 R9）
- [ ] T4.1 `llm.py`：用 `openai.OpenAI` 初始化客户端（读 config）
- [ ] T4.2 `generate_commit_message(diff)`：渲染模板 → 调 API → 取纯 message
- [ ] T4.3 diff 超长截断逻辑
- [ ] T4.4 重试：N 次指数退避（超时/限流/5xx）
- [ ] T4.5 降级：重试耗尽 → 返回模板兜底 message + 标记 degraded
- [ ] T4.6 生成后自动调 `validator.validate()`，不通过则提示
- [ ] T4.7 `test_llm.py`：mock 客户端，覆盖正常 / 空响应 / 重试后成功 / 全失败降级

### Phase 5 · 历史分析（R7）
- [ ] T5.1 `history.parse(raw_log)`：解析为提交对象列表
- [ ] T5.2 `history.analyze()`：统计 type 分布、提交数、合规率（调 validator）
- [ ] T5.3 Rich 表格/图形化输出报告
- [ ] T5.4 `test_history.py`：正常统计 / 空仓库 / 含不合规提交

### Phase 6 · CLI 编排（R3 R4 R5）
- [ ] T6.1 `cli.py`：Typer app + `commit` 子命令
- [ ] T6.2 `commit` 流程：读 diff → 生成 → 校验 → Rich 展示
- [ ] T6.3 交互确认：questionary `[y] 提交 / [e] 编辑 / [n] 取消`
- [ ] T6.4 `e` 编辑：打开 `$EDITOR` 或行内编辑后再校验
- [ ] T6.5 `analyze` 子命令：调 history 输出报告
- [ ] T6.6 全局异常捕获 → 友好错误提示与退出码
- [ ] T6.7 `test_cli.py`：用 Typer `CliRunner`，mock 各依赖，覆盖 y/e/n 三分支 + 降级提示

### Phase 7 · 文档与验收（R10）
- [ ] T7.1 完善 README：安装、配置、用法（commit/analyze）、示例
- [ ] T7.2 录制/截图运行效果，存 `docs/`
- [ ] T7.3 生成测试报告 `pytest --cov --cov-report=html`，截图存档
- [ ] T7.4 整理演示脚本与 AI 协作记录

> 提交节奏示例：`feat: T1.2 读取 staged diff` → `test: T1.5 git_ops 单测` → `feat: T2.1 校验模块骨架` ……

---

## 6. 测试策略

| 类型 | 工具 | 要点 |
|------|------|------|
| 单元测试 | pytest + pytest-mock | mock `subprocess.run` 与 openai 客户端，**不真连网络/不真提交** |
| 校验测试 | pytest | `validator` 各规则的正反用例（R8 重点） |
| 降级测试 | pytest | 用副作用让 mock 抛异常，验证重试与兜底（R9 重点） |
| 异常覆盖 | pytest | 每个自定义异常都有用例 |
| 集成测试 | pytest + tmp_path | `tmp_path` 建临时 git 仓库跑全流程（mock LLM） |
| 覆盖率 | pytest-cov | 已配置自动输出，目标 ≥80%，HTML 报告归档 |

运行：`source .venv/bin/activate && pytest`

---

## 7. 增强版路线图（选做 · 加分项）

| 优先级 | 拓展点 | 价值 |
|--------|--------|------|
| ★★ | 生成多个候选 message 供选择 | 体验提升 |
| ★★ | 真正的多 provider 适配器 + 自动探测可用模型 | 工程深度 |
| ★★ | 历史分析生成「周报 / 月报」Markdown | 实用、演示亮点 |
| ★ | 安装为 `git aic` 子命令 / prepare-commit-msg hook | 落地实用性 |
| ★ | 自动识别 breaking change、自动补 scope | 规范完整度 |
| ★ | 多语言提交信息（中/英切换） | 锦上添花 |
| ★ | message 评分 / 多轮改写 | AI 协作深度 |

---

## 8. 下一步

1. 你先完成第 0 节的两件手动配置（git 身份 + `.env`）。
2. 确认后进入 **阶段 1**：起草 `proposal.md` 与 specs 初稿（按需求—功能—测试映射表组织）。
3. 之后按 Phase 0→7 推进，每个 Task 用 `openspec validate` 校验产物、用 git 单独提交。
