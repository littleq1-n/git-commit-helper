## 1. 配置初始化（config-init）

- [x] 1.1 `initializer.py`：`render_env`（不含密钥）/ `write_env`（覆盖控制）/ `default_values` / `api_key_present` / `export_hint`
- [x] 1.2 `cli.init`：交互/`--yes`/`--force`，生成 `.env` 并打印密钥环境变量引导
- [x] 1.3 `test_initializer.py` + `test_cli.py`：渲染无密钥 / 不覆盖 / 强制覆盖 / 环境变量检测

## 2. LLM 提交周报（llm-weekly-report）

- [x] 2.1 `template.DEFAULT_REPORT_TEMPLATE` + `render_report`（支持自定义模板路径）
- [x] 2.2 `history.format_stats` / `format_commits` / `build_weekly_fallback`（规则版+启发式建议）
- [x] 2.3 `llm.generate_weekly_report`：成功返回 LLM 周报，失败降级规则版
- [x] 2.4 `cli.analyze --ai`：终端渲染 / `-m` 导出 / 降级提示
- [x] 2.5 `test_llm.py` + `test_cli.py`：成功 / 降级 / 导出

## 3. 安全与可移植性修复

- [x] 3.1 `security.scan_and_redact`（非交互），`hooks.run_prepare` 复用以脱敏
- [x] 3.2 hook 脚本固化 `sys.executable`
- [x] 3.3 `hooks.run_validate` 读取 `SUBJECT_MAX_LENGTH` 配置
- [x] 3.4 `test_hooks.py`：prepare 脱敏后再发 LLM

## 4. 健壮性与打包

- [x] 4.1 `llm._complete`：细化异常 + 日志 + 鉴权类不重试
- [x] 4.2 `git_ops._run`：加超时并转 `GitCommandError`
- [x] 4.3 `cli._write_report`：自动建目录 + 写入异常处理
- [x] 4.4 `cli.commit`：编辑后回到交互菜单（闭环）
- [x] 4.5 `pyproject.toml`：声明 `dependencies` 与 `optional-dependencies.dev`

## 5. 验收与文档

- [x] 5.1 全量 `pytest` 通过，覆盖率 ≥80%（实际 100 用例 / 90%）
- [x] 5.2 lint 无错误
- [x] 5.3 更新 README：init / env 变量密钥 / `--ai` 周报 / 结构与依赖
- [x] 5.4 SDD：proposal 补验收标准、specs 补 GIVEN
