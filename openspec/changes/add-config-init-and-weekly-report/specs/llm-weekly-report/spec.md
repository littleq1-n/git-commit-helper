## ADDED Requirements

### Requirement: LLM 提交周报
The system SHALL 在 `gch analyze --ai` 下结合 LLM 生成结构化的「Git 提交周报」，包含概览、主要变更与建议三部分。

#### Scenario: 成功生成周报
- **GIVEN** 仓库存在提交历史且 LLM 正常响应
- **WHEN** 用户运行 `gch analyze --ai`
- **THEN** 系统输出含 `## 概览`、`## 主要变更`、`## 建议` 三段的 Markdown 周报

#### Scenario: 导出周报到文件
- **GIVEN** 仓库存在提交历史
- **WHEN** 用户运行 `gch analyze --ai -m weekly.md`
- **THEN** 系统将周报写入指定路径（必要时创建父目录）并提示已生成

#### Scenario: LLM 不可用降级
- **GIVEN** 仓库存在提交历史但 LLM 调用失败
- **WHEN** 用户运行 `gch analyze --ai`
- **THEN** 系统降级为规则版周报（结构一致，建议基于类型分布启发式），并提示"已降级"，流程不中断

#### Scenario: 空仓库
- **GIVEN** 仓库无任何提交
- **WHEN** 用户运行 `gch analyze --ai`
- **THEN** 系统提示暂无提交历史，不调用 LLM、不写出文件
