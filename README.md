# Git Commit Helper（智能 Git 提交助手）

> 校招 AI Coding 入职培训课题 **SD-05**。一个命令行工具：读取暂存区改动，调用 LLM 生成符合
> [Conventional Commits](https://www.conventionalcommits.org/) 规范的提交信息，校验并交互确认后自动提交，并支持提交历史分析。

## 功能

- **读取暂存区改动**：`git diff --staged`
- **LLM 生成提交信息**：符合 Conventional Commits 规范
- **格式校验**：独立校验 type/subject/首行长度/正文空行，生成后自动校验
- **交互确认**：提交 / 编辑后提交 / 取消
- **自定义 prompt 模板**：通过 Jinja2 模板覆盖默认生成风格
- **API 失败降级**：超时/限流时指数退避重试，耗尽后回退模板兜底信息，流程不中断
- **提交历史分析**：统计提交类型分布、提交数与规范合规率
- **多 LLM 提供商**：通过 `.env` 切换（DeepSeek / 通义 / Kimi / Ollama / OpenAI 等，均兼容 OpenAI 协议）

## 环境要求

- Python ≥ 3.9
- Git
- 一个可访问的 LLM API（兼容 OpenAI 协议）
- Node.js ≥ 18（仅 OpenSpec/SDD 流程需要）

## 安装与配置

```bash
# 1. 创建并激活虚拟环境
python -m venv .venv && source .venv/bin/activate

# 2. 安装项目（可编辑模式，提供 gch 命令）
pip install -e .

# 3. 配置 LLM
cp .env.example .env   # 编辑 .env，填入 LLM_BASE_URL / LLM_API_KEY / LLM_MODEL
```

## 使用

```bash
# 暂存改动
git add .

# 生成提交信息并交互确认后提交
gch commit

# 分析最近 N 条提交（类型分布 + 合规率）
gch analyze -n 50

# 也可用模块方式调用
python -m git_commit_helper commit
```

`gch commit` 流程：读取 staged diff → LLM 生成 → 格式校验 → 终端展示 → 选择「提交 / 编辑后提交 / 取消」→ 执行 `git commit`。
若 LLM 调用失败，会自动降级为模板兜底信息并显式提示。

### 自定义 prompt 模板

在 `.env` 中设置 `PROMPT_TEMPLATE_PATH` 指向一个 Jinja2 模板文件（需包含 `{{ diff }}` 占位符），即可覆盖默认生成风格；路径不存在时自动回退默认模板。

## 配置项（.env）

| 变量 | 默认 | 说明 |
|------|------|------|
| `LLM_BASE_URL` | DeepSeek | OpenAI 兼容端点 |
| `LLM_API_KEY` | — | API 密钥 |
| `LLM_MODEL` | `deepseek-chat` | 模型名 |
| `LLM_TEMPERATURE` | `0.2` | 采样温度 |
| `LLM_MAX_TOKENS` | `512` | 单次最大 token |
| `LLM_MAX_RETRIES` | `3` | 失败重试次数 |
| `DIFF_MAX_CHARS` | `12000` | diff 截断阈值 |
| `PROMPT_TEMPLATE_PATH` | 空 | 自定义模板路径 |
| `SUBJECT_MAX_LENGTH` | `72` | 首行长度上限 |

## 项目结构

```
01_git_helper/
├── src/git_commit_helper/   # 源码包
│   ├── cli.py               # CLI 编排（commit/analyze）
│   ├── git_ops.py           # Git 操作（读 diff/提交/读 log）
│   ├── llm.py               # LLM 调用 + 重试 + 降级
│   ├── validator.py         # Conventional Commits 校验
│   ├── template.py          # 自定义 prompt 模板
│   ├── history.py           # 提交历史分析
│   ├── config.py            # 配置加载
│   └── errors.py            # 自定义异常
├── tests/                   # pytest 测试（46 用例）
├── docs/TEST_REPORT.md      # 测试报告
├── openspec/                # SDD 规范产物（proposal/specs/design/tasks）
├── requirements.txt / pyproject.toml / .env.example
├── PLAN.md                  # 详细执行计划
└── README.md
```

## 测试

```bash
pytest                     # 运行全部测试 + 终端覆盖率
pytest --cov-report=html   # 生成 HTML 覆盖率报告到 htmlcov/
```

当前：**46 用例全部通过，覆盖率 88%**。详见 `docs/TEST_REPORT.md`。

## SDD 流程

本项目遵循规范驱动开发（OpenSpec），各阶段产物位于 `openspec/changes/add-commit-message-generation/`：
`proposal.md`（背景/范围）、`specs/`（四个能力的需求场景）、`design.md`（架构决策）、`tasks.md`（任务清单）。详见 `PLAN.md`。
