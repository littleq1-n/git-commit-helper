## ADDED Requirements

### Requirement: 解析 Git 提交历史
The system SHALL 通过 `analyze` 子命令读取并解析当前仓库的 Git 提交历史，得到结构化的提交记录。

#### Scenario: 正常解析历史
- **WHEN** 仓库存在若干提交且用户运行 `gch analyze`
- **THEN** 系统读取 `git log` 并解析为提交记录列表（含 type、subject 等）

#### Scenario: 空仓库无提交
- **WHEN** 仓库尚无任何提交时运行 `gch analyze`
- **THEN** 系统提示"暂无提交历史"并正常退出，不抛出异常

#### Scenario: 限定分析数量
- **WHEN** 用户指定 `--count N` 参数
- **THEN** 系统仅分析最近 N 条提交

### Requirement: 统计提交类型分布与合规率
The system SHALL 基于解析结果统计提交类型分布、提交总数，并复用校验能力计算 Conventional Commits 合规率。

#### Scenario: 输出统计报告
- **WHEN** 历史解析完成
- **THEN** 系统以表格形式展示各 type 的数量分布、提交总数与合规率

#### Scenario: 含不合规提交
- **WHEN** 历史中存在不符合规范的提交信息
- **THEN** 系统在合规率统计中将其计为不合规，并可列出不合规的提交摘要
