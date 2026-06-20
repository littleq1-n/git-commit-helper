"""template 测试：默认模板、自定义模板生效、路径缺失回退。"""

from __future__ import annotations

from git_commit_helper import template


def test_default_template_used_when_no_path():
    source, used_default = template.load_template_source(None)
    assert used_default is True
    assert "Conventional Commits" in source


def test_custom_template_loaded(tmp_path):
    custom = tmp_path / "tpl.j2"
    custom.write_text("自定义模板\n{{ diff }}", encoding="utf-8")

    source, used_default = template.load_template_source(str(custom))

    assert used_default is False
    assert "自定义模板" in source


def test_missing_path_falls_back_to_default(tmp_path):
    missing = tmp_path / "nope.j2"
    source, used_default = template.load_template_source(str(missing))

    assert used_default is True
    assert source == template.DEFAULT_TEMPLATE


def test_render_injects_diff():
    rendered = template.render("diff --git a/x b/x\n+hello")
    assert "hello" in rendered


def test_render_with_custom_template(tmp_path):
    custom = tmp_path / "tpl.j2"
    custom.write_text("PREFIX >>> {{ diff }}", encoding="utf-8")

    rendered = template.render("DIFFBODY", template_path=str(custom))

    assert rendered == "PREFIX >>> DIFFBODY"
