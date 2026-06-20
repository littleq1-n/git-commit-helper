## ADDED Requirements

### Requirement: 提供内置默认 prompt 模板
The system SHALL 内置一个默认的 prompt 模板，包含 Conventional Commits 规则说明与 diff 占位符，在用户未自定义时使用。

#### Scenario: 使用默认模板
- **WHEN** 用户未配置自定义模板路径
- **THEN** 系统使用内置默认模板渲染 prompt 并调用 LLM

### Requirement: 支持自定义 prompt 模板
The system SHALL 允许用户通过配置指定自定义 Jinja2 模板文件，以覆盖默认生成风格。

#### Scenario: 自定义模板生效
- **WHEN** 用户在 `.env` 中配置了存在的 `PROMPT_TEMPLATE_PATH`
- **THEN** 系统加载该模板并用其渲染 prompt

#### Scenario: 自定义模板路径不存在
- **WHEN** 配置的模板路径指向不存在的文件
- **THEN** 系统回退到内置默认模板，并提示模板未找到

### Requirement: 模板渲染注入上下文
The system SHALL 在渲染模板时注入必要的上下文变量（至少包含暂存 diff）。

#### Scenario: 注入 diff 变量
- **WHEN** 系统渲染 prompt 模板
- **THEN** 模板中的 diff 占位符被替换为实际的暂存 diff 内容
