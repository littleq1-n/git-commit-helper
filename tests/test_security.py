"""security 测试：扫描与脱敏。"""

from __future__ import annotations

from git_commit_helper import security


def test_scan_clean_diff():
    diff = "diff --git a/app.py b/app.py\n+print('hello world')\n"
    assert security.scan(diff) == []


def test_scan_detects_sk_key():
    diff = "+OPENAI_KEY = sk-abcdef0123456789ABCDEF\n"
    findings = security.scan(diff)
    assert any("sk-" in f.snippet for f in findings)


def test_scan_detects_keyvalue_secret():
    diff = '+api_key: "myS3cretValue123"\n'
    findings = security.scan(diff)
    assert findings
    assert any("myS3cretValue123" in f.snippet for f in findings)


def test_scan_detects_env_var():
    diff = "+DATABASE_PASSWORD=supersecret123\n"
    findings = security.scan(diff)
    assert findings


def test_scan_detects_private_key_header():
    diff = "+-----BEGIN RSA PRIVATE KEY-----\n"
    findings = security.scan(diff)
    assert any("私钥" in f.kind for f in findings)


def test_scan_dedupes():
    diff = "+token=abc123abc123\n+token=abc123abc123\n"
    findings = security.scan(diff)
    snippets = [f.snippet for f in findings]
    assert len(snippets) == len(set(snippets))


def test_redact_removes_secret_value():
    diff = "+api_key=SuperSecretValue999\n"
    redacted = security.redact(diff)
    assert "SuperSecretValue999" not in redacted
    assert security.REDACTION_PLACEHOLDER in redacted


def test_redact_keeps_key_name():
    diff = "+api_key=SuperSecretValue999\n"
    redacted = security.redact(diff)
    # 键名应保留，仅值被脱敏
    assert "api_key" in redacted


def test_redact_clean_diff_unchanged():
    diff = "diff --git a/x b/x\n+normal code line\n"
    assert security.redact(diff) == diff
