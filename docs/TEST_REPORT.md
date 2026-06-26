# 测试报告

> 运行命令：`pytest`（配置见 `pyproject.toml`，自动启用 coverage）
> 环境：Python 3.11.13 / pytest 9.x / pytest-mock / pytest-cov

## 结果汇总（含增强版 v2 两批迭代全部能力）

- 用例总数：**101 passed**
- 通过率：**100%**（≥80% 要求达标）
- 总覆盖率：**90%**（≥80% 要求达标）

## 覆盖率明细

| 模块 | 覆盖率 | 说明 |
|------|--------|------|
| `config.py` | 100% | 配置加载 |
| `errors.py` | 100% | 异常类型 |
| `validator.py` | 100% | 格式校验（R8） |
| `security.py` | 100% | 敏感信息扫描/脱敏 + scan_and_redact |
| `doctor.py` | 100% | 环境自检 |
| `initializer.py` | 98% | 配置初始化脚手架（v3） |
| `history.py` | 95% | 历史分析 + Markdown + 规则版周报（R7/v3） |
| `hooks.py` | 93% | git hook 安装/校验（脱敏/解释器/配置） |
| `llm.py` | 91% | LLM 调用 + 降级 + 周报（R2/R9/v3） |
| `git_ops.py` | 89% | Git 操作层（含超时） |
| `cli.py` | 80% | CLI 编排（未覆盖为 questionary/click 真实交互分支） |
| `template.py` | 89% | 自定义提交/周报模板（R6/v3） |
| `__main__.py` | 0% | 仅入口转发，运行时验证 |

> 未覆盖部分集中在需要真实终端交互（questionary 选择、`$EDITOR` 编辑）的代码路径，
> 已通过将交互抽象为 `_prompt_action` / `_edit_message` 并在 CLI 测试中 mock 来覆盖三条主分支（提交/编辑/取消）。

## 需求—测试 对应（验证全部标准版需求）

| 需求 | 测试文件 |
|------|----------|
| R1 读取 staged diff | `test_git_ops.py` |
| R2 生成 message | `test_llm.py` |
| R3 展示结果 / R4 确认·编辑·取消 / R5 执行 commit | `test_cli.py` |
| R6 自定义模板 | `test_template.py` |
| R7 历史分析 | `test_history.py` |
| R8 格式校验 | `test_validator.py` |
| R9 API 降级 | `test_llm.py`（重试后成功 / 全失败降级） |

### 增强版（v2）能力—测试 对应

| 能力 | 测试文件 |
|------|----------|
| 环境自检 doctor | `test_doctor.py` + `test_cli.py` |
| 敏感信息扫描/脱敏 | `test_security.py` + `test_cli.py`（脱敏继续/取消） |
| Markdown 报告 | `test_history.py` + `test_cli.py`（导出/空仓库不写） |
| git hook | `test_hooks.py` + `test_cli.py`（install/uninstall） |

### 增强版 v2 后续迭代能力—测试 对应

| 能力 | 测试文件 |
|------|----------|
| 配置初始化 `gch init` | `test_initializer.py` + `test_cli.py`（生成/不覆盖/强制覆盖） |
| LLM 提交周报 `analyze --ai` | `test_llm.py`（成功/降级/鉴权不重试）+ `test_cli.py`（渲染/导出） |
| hook 脱敏一致性 | `test_hooks.py`（prepare 脱敏后再发 LLM） |
| scan_and_redact | `test_security.py` |

## 复现实步骤

```bash
source .venv/bin/activate
pytest                       # 运行全部测试 + 终端覆盖率
pytest --cov-report=html     # 生成 HTML 覆盖率报告到 htmlcov/
```

## CLI 冒烟验证

```text
$ gch analyze -n 20
   提交历史分析
┏━━━━━━━━━━┳━━━━━━┓
┃ type     ┃ 数量 ┃
┡━━━━━━━━━━╇━━━━━━┩
│ feat     │    7 │
│ docs     │    2 │
│ chore    │    1 │
├──────────┼──────┤
│ 总提交数 │   10 │
│ 合规率   │ 100% │
└──────────┴──────┘
```

> 提示：将上述命令运行截图替换/补充到本文件，作为演示与提交材料。
