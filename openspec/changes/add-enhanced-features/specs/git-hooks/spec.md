## ADDED Requirements

### Requirement: 安装 Git hook
The system SHALL 提供 `gch hook install` 命令，在当前仓库的 `.git/hooks/` 下安装 `prepare-commit-msg` 与 `commit-msg` 两个钩子脚本。

#### Scenario: 成功安装
- **WHEN** 在 Git 仓库中运行 `gch hook install`
- **THEN** 系统写入两个可执行 hook 脚本并提示安装成功

#### Scenario: 非 Git 仓库
- **WHEN** 在非 Git 仓库目录运行 `gch hook install`
- **THEN** 系统提示当前目录不是 Git 仓库并以非零退出码结束

#### Scenario: 已存在 hook 时备份
- **WHEN** 目标 hook 文件已存在
- **THEN** 系统在覆盖前对原文件进行备份（如追加 `.bak` 后缀）

### Requirement: prepare-commit-msg 自动生成
The system SHALL 通过 `prepare-commit-msg` 钩子，在用户未显式提供提交信息时自动生成 Conventional Commits 提交信息。

#### Scenario: 自动填充提交信息
- **WHEN** 用户执行 `git commit` 且未通过 `-m` 指定信息
- **THEN** 钩子调用本工具基于暂存 diff 生成提交信息并写入提交信息文件

### Requirement: commit-msg 校验
The system SHALL 通过 `commit-msg` 钩子校验最终提交信息是否符合 Conventional Commits 规范，不符合时阻止提交。

#### Scenario: 校验通过放行
- **WHEN** 提交信息符合规范
- **THEN** 钩子以退出码 0 放行提交

#### Scenario: 校验失败阻止提交
- **WHEN** 提交信息不符合规范
- **THEN** 钩子输出错误原因并以非零退出码阻止提交

### Requirement: 卸载 Git hook
The system SHALL 提供 `gch hook uninstall` 命令移除已安装的钩子。

#### Scenario: 卸载已安装的 hook
- **WHEN** 用户运行 `gch hook uninstall`
- **THEN** 系统移除由本工具安装的 hook 脚本并提示完成
