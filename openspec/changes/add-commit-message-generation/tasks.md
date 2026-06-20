## 1. 项目骨架与配置

- [x] 1.1 在 `src/git_commit_helper/` 补 `__main__.py` 入口（`python -m git_commit_helper`）
- [x] 1.2 实现 `errors.py`：`NotAGitRepo` / `NoStagedChanges` / `LLMError` / `InvalidMessage`
- [x] 1.3 实现 `config.py`：用 pydantic-settings 读取 `.env`（base_url/api_key/model/温度/max_tokens/重试次数/模板路径/首行长度阈值）
- [x] 1.4 为 `config` 写单测：缺省值、环境变量覆盖

## 2. Git 操作层（R1 R5 R7）

- [x] 2.1 `git_ops.is_git_repo()`：判断当前目录是否 git 仓库
- [x] 2.2 `git_ops.get_staged_diff()`：读 `git diff --staged`，为空抛 `NoStagedChanges`
- [x] 2.3 `git_ops.commit(message)`：执行 `git commit -m`，失败抛错
- [x] 2.4 `git_ops.get_log(count)`：读取 `git log` 原始数据供历史分析
- [x] 2.5 `test_git_ops.py`：mock `subprocess`，覆盖正常 / 无暂存 / commit 失败 / 非仓库

## 3. 格式校验模块（R8）

- [x] 3.1 `validator.py`：定义 `ValidationResult(passed, errors)`
- [x] 3.2 正则解析 `type(scope)?: subject`，校验 type 在合法集合内
- [x] 3.3 校验规则：subject 非空、首行 ≤ 阈值、空行分隔 body/footer
- [x] 3.4 `validate(message)` 汇总全部错误
- [x] 3.5 `test_validator.py`：合法 / 缺 type / 非法 type / 超长 / 空 subject

## 4. 自定义模板（R6）

- [x] 4.1 内置默认 prompt 模板（含 Conventional Commits 规则说明）
- [x] 4.2 `template.load_template()`：优先读 `PROMPT_TEMPLATE_PATH`，缺失回退默认
- [x] 4.3 `template.render(diff, **ctx)`：Jinja2 渲染并注入 diff
- [x] 4.4 `test_template.py`：默认 / 自定义生效 / 路径缺失回退

## 5. LLM 调用与降级（R2 R9）

- [x] 5.1 `llm.py`：用 `openai.OpenAI` 初始化客户端（读 config）
- [x] 5.2 `generate_commit_message(diff)`：渲染模板 → 调 API → 取纯 message
- [x] 5.3 diff 超长截断逻辑
- [x] 5.4 重试：N 次指数退避（超时/限流/5xx）
- [x] 5.5 降级：重试耗尽 → 返回模板兜底 message 并标记 degraded
- [x] 5.6 生成后自动调 `validator.validate()`
- [x] 5.7 `test_llm.py`：mock 客户端，覆盖正常 / 空响应 / 重试后成功 / 全失败降级

## 6. 历史分析（R7）

- [x] 6.1 `history.parse(raw_log)`：解析为提交记录列表
- [x] 6.2 `history.analyze()`：统计 type 分布、提交数、合规率（复用 validator）
- [x] 6.3 Rich 表格输出报告
- [x] 6.4 `test_history.py`：正常统计 / 空仓库 / 含不合规提交

## 7. CLI 编排（R3 R4 R5）

- [x] 7.1 `cli.py`：Typer app + `commit` 子命令
- [x] 7.2 `commit` 流程：读 diff → 生成 → 校验 → Rich 展示
- [x] 7.3 交互确认：questionary `[y] 提交 / [e] 编辑 / [n] 取消`
- [x] 7.4 `e` 编辑：`$EDITOR` 或行内编辑后再校验
- [x] 7.5 `analyze` 子命令：调 history 输出报告
- [x] 7.6 全局异常捕获 → 友好错误提示与退出码
- [x] 7.7 `test_cli.py`：用 Typer `CliRunner` mock 依赖，覆盖 y/e/n 三分支 + 降级提示

## 8. 文档与验收（R10）

- [x] 8.1 完善 README：安装、配置、用法（commit/analyze）、示例
- [ ] 8.2 录制/截图运行效果，存 `docs/`（需手动截图）
- [x] 8.3 生成测试报告 `pytest --cov --cov-report=html`，截图存档
- [ ] 8.4 整理演示脚本与 AI 协作记录（需手动）
- [x] 8.5 确认整体 `pytest` 通过率 ≥80%
