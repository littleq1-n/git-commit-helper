## ADDED Requirements

### Requirement: 环境自检命令
The system SHALL 提供 `gch doctor` 命令，检查工具运行所需的环境与配置，并以表格形式输出每项的状态与修复建议。

#### Scenario: 全部检查通过
- **WHEN** Python 版本满足要求、git 可用、当前为 Git 仓库、`.env` 存在且含 LLM 配置、依赖已安装
- **THEN** 系统对各检查项显示通过状态，并以退出码 0 结束

#### Scenario: 存在未通过项
- **WHEN** 某项检查未通过（如缺少 `.env` 或未配置 `LLM_API_KEY`）
- **THEN** 系统标记该项为失败并给出对应修复建议，以非零退出码结束

#### Scenario: 不在 Git 仓库中
- **WHEN** 在非 Git 仓库目录运行 `gch doctor`
- **THEN** 系统将「Git 仓库」一项标记为未通过，但仍完成其余检查项的输出
