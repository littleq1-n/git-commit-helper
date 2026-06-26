## ADDED Requirements

### Requirement: 配置初始化命令
The system SHALL 提供 `gch init` 命令生成 `.env` 配置，且 API Key 绝不写入项目文件，强制通过环境变量注入。

#### Scenario: 全新生成配置
- **GIVEN** 当前目录不存在 `.env`
- **WHEN** 用户运行 `gch init --yes`
- **THEN** 系统生成 `.env`（仅含 base_url/model/采样参数等非敏感项），且不含任何有效的 `LLM_API_KEY` 配置行

#### Scenario: 已存在不覆盖
- **GIVEN** 当前目录已存在 `.env`
- **WHEN** 用户运行 `gch init --yes`（未加 `--force`）
- **THEN** 系统保留现有 `.env` 不覆盖，并提示可用 `--force` 覆盖

#### Scenario: 强制覆盖
- **GIVEN** 当前目录已存在 `.env`
- **WHEN** 用户运行 `gch init --yes --force`
- **THEN** 系统用新内容覆盖 `.env`

### Requirement: API Key 环境变量引导
The system SHALL 在初始化后检测 `LLM_API_KEY` 环境变量并给出相应引导。

#### Scenario: 未设置环境变量
- **GIVEN** 环境变量 `LLM_API_KEY` 未设置
- **WHEN** `gch init` 执行完成
- **THEN** 系统打印 `export LLM_API_KEY=...` 引导，提示密钥不写入项目文件

#### Scenario: 已设置环境变量
- **GIVEN** 环境变量 `LLM_API_KEY` 已设置
- **WHEN** `gch init` 执行完成
- **THEN** 系统提示已检测到 `LLM_API_KEY`，无需额外操作
