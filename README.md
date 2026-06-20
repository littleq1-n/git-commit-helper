# Git Commit Helper（智能 Git 提交助手）

> 校招 AI Coding 入职培训课题 **SD-05**。一个命令行工具：读取暂存区改动，调用 LLM 生成符合
> [Conventional Commits](https://www.conventionalcommits.org/) 规范的提交信息，交互确认后自动提交。

## 功能（MVP）

- 读取 `git diff --staged`
- 调用 LLM 生成 Conventional Commits 提交信息
- 终端展示并交互确认：提交 / 编辑后提交 / 取消
- 通过 `.env` 切换不同 LLM 提供商（DeepSeek / 通义 / Kimi / Ollama / OpenAI 等）

> 后续增强与拓展见 `PLAN.md` 中的路线图。

## 环境要求

- Python ≥ 3.9
- Git
- Node.js ≥ 18（仅 OpenSpec 流程需要）
- 一个可访问的 LLM API（兼容 OpenAI 协议）

## 快速开始

```bash
# 1. 激活虚拟环境
source .venv/bin/activate

# 2. 安装依赖（已在搭建环境时安装，重装用）
pip install -r requirements.txt

# 3. 配置 LLM
cp .env.example .env   # 然后编辑 .env 填入 base_url / api_key / model

# 4. 运行（实现阶段完成后可用）
# gch            # 对暂存区改动生成提交信息
```

## 项目结构

```
01_git_helper/
├── src/git_commit_helper/   # 源码包
├── tests/                   # pytest 测试
├── docs/                    # 文档与演示材料
├── openspec/                # SDD 规范产物（proposal/specs/design/tasks）
├── requirements.txt         # Python 依赖
├── pyproject.toml           # 打包与 pytest 配置
├── .env.example             # LLM 配置模板
├── PLAN.md                  # 详细执行计划
└── README.md
```

## 测试

```bash
pytest        # 运行单元测试并输出覆盖率
```

## SDD 流程

本项目遵循规范驱动开发（OpenSpec），各阶段产物位于 `openspec/changes/`。详见 `PLAN.md`。
