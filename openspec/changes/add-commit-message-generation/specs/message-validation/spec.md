## ADDED Requirements

### Requirement: 校验提交信息符合 Conventional Commits 格式
The system SHALL 提供独立的校验能力，判断一条提交信息是否符合 Conventional Commits 规范，并在不符合时返回结构化的错误原因列表。

#### Scenario: 合法的提交信息
- **WHEN** 校验 `feat(parser): add diff truncation` 这样的合法信息
- **THEN** 校验结果为通过，错误列表为空

#### Scenario: 缺少 type 前缀
- **WHEN** 校验首行不含 `type: ` 前缀的信息（如 `update something`）
- **THEN** 校验结果为不通过，错误列表包含"缺少合法的 type 前缀"

#### Scenario: 非法的 type
- **WHEN** 校验 type 不在允许集合内的信息（如 `feet: add x`）
- **THEN** 校验结果为不通过，错误列表指出 type 非法并列出允许的取值

#### Scenario: subject 为空
- **WHEN** 校验形如 `fix: ` 但冒号后无描述的信息
- **THEN** 校验结果为不通过，错误列表包含"subject 不能为空"

#### Scenario: 首行超过长度上限
- **WHEN** 校验首行长度超过配置上限（默认 72 字符）的信息
- **THEN** 校验结果为不通过，错误列表包含"首行超过 N 字符"

### Requirement: 校验能力可被生成与历史分析复用
The system SHALL 将校验能力暴露为可复用接口，供提交生成流程与历史分析流程调用。

#### Scenario: 生成后自动校验
- **WHEN** LLM 生成提交信息后
- **THEN** 系统自动调用校验，若不通过则提示用户重新生成或进入编辑

#### Scenario: 历史合规率统计复用校验
- **WHEN** 历史分析需要计算提交规范合规率
- **THEN** 系统对每条历史提交调用同一校验接口判定是否合规
