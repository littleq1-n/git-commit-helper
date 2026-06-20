## ADDED Requirements

### Requirement: 发送前扫描敏感信息
The system SHALL 在将 diff 发送给 LLM 之前扫描其中疑似敏感信息（如 API key、secret/token、`.env` 文件内容等），并返回命中的敏感项列表。

#### Scenario: 未发现敏感信息
- **WHEN** diff 中不含任何疑似敏感内容
- **THEN** 系统不做任何提示，直接进入正常的生成流程

#### Scenario: 发现敏感信息
- **WHEN** diff 中包含疑似密钥、令牌或敏感文件名
- **THEN** 系统展示检测到的敏感项清单，并提示用户选择「脱敏后继续」或「取消」

### Requirement: 脱敏后继续或取消
The system SHALL 在发现敏感信息后，根据用户选择执行脱敏继续或取消操作。

#### Scenario: 用户选择脱敏后继续
- **WHEN** 用户在敏感信息提示中选择「脱敏后继续」
- **THEN** 系统将敏感片段替换为占位符（如 `***REDACTED***`）后，再把脱敏后的 diff 发送给 LLM

#### Scenario: 用户选择取消
- **WHEN** 用户在敏感信息提示中选择「取消」
- **THEN** 系统不调用 LLM、不提交，直接安全退出

### Requirement: 脱敏不修改工作区文件
The system SHALL 仅对发送给 LLM 的 diff 文本做脱敏，不得修改用户暂存区或工作区的真实文件内容。

#### Scenario: 脱敏仅作用于传输文本
- **WHEN** 系统对 diff 执行脱敏
- **THEN** 用户的暂存内容与工作区文件保持不变，仅发送给 LLM 的副本被脱敏
