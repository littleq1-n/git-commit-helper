## ADDED Requirements

### Requirement: 读取暂存区改动
The system SHALL 读取当前 Git 仓库暂存区（staged）的代码改动，作为生成提交信息的输入。

#### Scenario: 存在暂存改动
- **WHEN** 用户已通过 `git add` 暂存了改动并运行 `gch commit`
- **THEN** 系统读取 `git diff --staged` 的内容并继续生成流程

#### Scenario: 没有暂存改动
- **WHEN** 暂存区为空时运行 `gch commit`
- **THEN** 系统提示"无暂存改动，请先 git add"并以非零退出码结束，不调用 LLM

#### Scenario: 非 Git 仓库
- **WHEN** 在非 Git 仓库目录运行 `gch commit`
- **THEN** 系统提示"当前目录不是 Git 仓库"并以非零退出码结束

### Requirement: 调用 LLM 生成提交信息
The system SHALL 将暂存 diff 提交给 LLM，生成 1 条符合 Conventional Commits 规范的提交信息。

#### Scenario: 成功生成
- **WHEN** 存在有效暂存 diff 且 LLM 正常响应
- **THEN** 系统得到 1 条非空提交信息并进入展示环节

#### Scenario: diff 过大
- **WHEN** 暂存 diff 超过模型可接受的长度
- **THEN** 系统对 diff 进行截断后再调用 LLM，并保证请求成功

#### Scenario: LLM 返回空内容
- **WHEN** LLM 返回空字符串或无有效内容
- **THEN** 系统判定为生成失败并进入降级处理流程

### Requirement: 展示生成结果
The system SHALL 在终端清晰展示生成的提交信息，供用户审阅。

#### Scenario: 展示提交信息
- **WHEN** 系统获得一条生成的提交信息
- **THEN** 系统以可读的面板形式展示该信息全文

### Requirement: 用户确认、编辑或取消
The system SHALL 提供交互式选择，允许用户确认提交、编辑后提交或取消操作。

#### Scenario: 用户确认提交
- **WHEN** 用户在交互菜单选择"确认"
- **THEN** 系统使用当前提交信息执行提交

#### Scenario: 用户编辑后提交
- **WHEN** 用户选择"编辑"
- **THEN** 系统允许用户修改提交信息，并在修改后重新进行格式校验

#### Scenario: 用户取消
- **WHEN** 用户选择"取消"
- **THEN** 系统不执行任何提交并正常退出

### Requirement: 可选执行提交
The system SHALL 在用户确认后调用 `git commit` 完成提交，并在失败时给出明确反馈。

#### Scenario: 提交成功
- **WHEN** 用户确认且 `git commit` 执行成功
- **THEN** 系统提示提交成功并显示生成的提交哈希或摘要

#### Scenario: 提交失败
- **WHEN** `git commit` 执行返回非零状态（如 pre-commit hook 拒绝）
- **THEN** 系统展示底层错误信息并以非零退出码结束

### Requirement: LLM 失败时的降级处理
The system SHALL 在 LLM 调用失败时进行有限次重试，并在重试耗尽后回退到模板兜底信息以保证流程不中断。

#### Scenario: 重试后成功
- **WHEN** LLM 首次调用因超时或限流失败，但在重试中成功返回
- **THEN** 系统使用成功返回的结果继续后续流程

#### Scenario: 重试耗尽后降级
- **WHEN** LLM 在达到最大重试次数后仍然失败
- **THEN** 系统生成基于模板的兜底提交信息（如 `chore: update <主要改动文件>`），并明确提示"已降级"，流程继续到展示与确认环节
