## 1. 敏感信息扫描与脱敏（sensitive-scanning）

- [ ] 1.1 `security.py`：定义 `Finding(kind, snippet)` 数据结构
- [ ] 1.2 实现 `scan(diff) -> list[Finding]`：正则匹配 API key / token / secret / `.env` 行 / 私钥头
- [ ] 1.3 实现 `redact(diff) -> str`：将命中片段替换为 `***REDACTED***`
- [ ] 1.4 `test_security.py`：无命中 / 命中各类模式 / 脱敏后不含原值 / 脱敏不改变结构

## 2. 集成扫描到 commit 流程

- [ ] 2.1 `cli.commit`：生成前调用 `security.scan`
- [ ] 2.2 命中时展示清单并提示「脱敏后继续 / 取消」（抽 `_prompt_sensitive` 便于测试）
- [ ] 2.3 选脱敏→用 `redact(diff)` 发送；选取消→安全退出
- [ ] 2.4 `test_cli.py`：补充 无敏感正常 / 命中后脱敏继续 / 命中后取消

## 3. 环境检查命令（environment-doctor）

- [ ] 3.1 `doctor.py`：定义 `CheckResult(name, passed, detail, suggestion)`
- [ ] 3.2 实现 `run_checks(settings)`：Python 版本 / git 可用 / Git 仓库 / `.env` 存在 / LLM 配置 / 关键依赖
- [ ] 3.3 `cli.doctor`：渲染表格，存在失败项时非零退出
- [ ] 3.4 `test_doctor.py`：全通过 / 缺配置失败 / 非仓库

## 4. 历史分析 Markdown 报告（markdown-report）

- [ ] 4.1 `history.build_markdown(report) -> str`：类型分布表 + 总数 + 合规率 + 不合规列表
- [ ] 4.2 `cli.analyze` 增 `--markdown/-m PATH` 选项：写文件并提示
- [ ] 4.3 空仓库且指定 `--markdown` 时不写文件
- [ ] 4.4 `test_history.py` / `test_cli.py`：Markdown 内容正确 / 写文件 / 空仓库不写

## 5. Git hook 安装（git-hooks）

- [ ] 5.1 `hooks.py`：内置 `prepare-commit-msg` 与 `commit-msg` 脚本模板
- [ ] 5.2 `install(repo_root)`：写入 `.git/hooks/`、加可执行权限、已存在则备份 `.bak`
- [ ] 5.3 `uninstall(repo_root)`：移除本工具安装的 hook
- [ ] 5.4 `cli.hook`：`install` / `uninstall` 子命令，非仓库时报错
- [ ] 5.5 `test_hooks.py`：安装写入并可执行 / 已存在备份 / 卸载移除 / 非仓库报错

## 6. 验收与文档

- [ ] 6.1 全量 `pytest` 通过，覆盖率 ≥80%
- [ ] 6.2 `ruff`/lint 无错误
- [ ] 6.3 更新 README：新增 doctor / 敏感扫描 / markdown 报告 / hook 用法
- [ ] 6.4 `openspec validate add-enhanced-features` 通过
