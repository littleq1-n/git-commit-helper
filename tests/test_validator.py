"""validator 测试：覆盖合法与各类不合法场景。"""

from __future__ import annotations

from git_commit_helper.validator import validate


def test_valid_simple():
    result = validate("feat: add diff truncation")
    assert result.passed is True
    assert result.errors == []


def test_valid_with_scope_and_breaking():
    result = validate("feat(parser)!: change diff format")
    assert result.passed is True


def test_valid_with_body():
    msg = "fix: handle empty diff\n\n详细说明降级逻辑。"
    result = validate(msg)
    assert result.passed is True


def test_missing_type_prefix():
    result = validate("update something without type")
    assert result.passed is False
    assert any("type 前缀" in e for e in result.errors)


def test_invalid_type():
    result = validate("feet: typo type")
    assert result.passed is False
    assert any("非法" in e for e in result.errors)


def test_empty_subject():
    result = validate("fix: ")
    assert result.passed is False
    assert any("subject 不能为空" in e for e in result.errors)


def test_too_long_first_line():
    long_subject = "feat: " + "x" * 100
    result = validate(long_subject, subject_max_length=72)
    assert result.passed is False
    assert any("超过上限" in e for e in result.errors)


def test_body_without_blank_line():
    msg = "fix: something\n紧接正文没有空行"
    result = validate(msg)
    assert result.passed is False
    assert any("空一行" in e for e in result.errors)


def test_empty_message():
    result = validate("   ")
    assert result.passed is False
