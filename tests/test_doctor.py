"""doctor 测试：环境检查项。"""

from __future__ import annotations

from git_commit_helper import doctor
from git_commit_helper.config import Settings


def test_all_pass(mocker, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("x", encoding="utf-8")
    mocker.patch.object(doctor.git_ops, "is_git_repo", return_value=True)
    mocker.patch.object(doctor.shutil, "which", return_value="/usr/bin/git")

    settings = Settings(llm_api_key="k", llm_base_url="u", llm_model="m")
    results = doctor.run_checks(settings)

    by_name = {r.name: r for r in results}
    assert by_name["Git 仓库"].passed
    assert by_name["git 可用"].passed
    assert by_name[".env 配置文件"].passed
    assert by_name["LLM 配置"].passed
    assert by_name["依赖包"].passed


def test_missing_llm_config(mocker, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mocker.patch.object(doctor.git_ops, "is_git_repo", return_value=True)

    settings = Settings(llm_api_key="", llm_base_url="u", llm_model="m")
    results = doctor.run_checks(settings)

    llm_check = next(r for r in results if r.name == "LLM 配置")
    assert not llm_check.passed
    assert "LLM_API_KEY" in llm_check.detail


def test_not_a_repo(mocker, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mocker.patch.object(doctor.git_ops, "is_git_repo", return_value=False)

    results = doctor.run_checks(Settings(llm_api_key="k"))

    repo_check = next(r for r in results if r.name == "Git 仓库")
    assert not repo_check.passed
    # 其余检查项仍应产出
    assert len(results) == 6
