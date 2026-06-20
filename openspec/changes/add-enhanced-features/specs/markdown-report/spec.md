## ADDED Requirements

### Requirement: 历史分析导出 Markdown 报告
The system SHALL 允许 `gch analyze` 通过选项将历史分析结果导出为 Markdown 报告文件。

#### Scenario: 导出到指定文件
- **WHEN** 用户运行 `gch analyze --markdown report.md`
- **THEN** 系统在该路径写入包含类型分布、提交总数与合规率的 Markdown 报告，并提示已生成

#### Scenario: 默认仍输出终端表格
- **WHEN** 用户运行 `gch analyze` 而未指定 `--markdown`
- **THEN** 系统保持原有行为，仅在终端以表格形式展示，不写出文件

#### Scenario: 空仓库不生成报告
- **WHEN** 仓库无任何提交且指定了 `--markdown`
- **THEN** 系统提示暂无提交历史，不写出报告文件
