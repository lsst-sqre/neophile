"""Tests for the command-line interface."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from unittest.mock import Mock, call

import respx
from click.testing import CliRunner
from git import Remote
from git.repo import Repo
from git.util import Actor
from httpx import Request, Response
from ruamel.yaml import YAML

from neophile.cli import main
from neophile.pr import CommitMessage

from .support.github import (
    mock_app_authenticate,
    mock_enable_auto_merge,
    mock_github_tags,
    mock_github_tags_from_precommit,
)


def test_help() -> None:
    runner = CliRunner()

    result = runner.invoke(main, ["-h"])
    assert result.exit_code == 0
    assert "Commands:" in result.output

    result = runner.invoke(main, ["help"])
    assert result.exit_code == 0
    assert "Commands:" in result.output

    result = runner.invoke(main, ["help", "scan"])
    assert result.exit_code == 0
    assert "Commands:" not in result.output
    assert "Options:" in result.output

    result = runner.invoke(main, ["help", "unknown-command"])
    assert result.exit_code != 0
    assert "Unknown help topic unknown-command" in result.output


def test_analyze(tmp_path: Path, respx_mock: respx.Router) -> None:
    runner = CliRunner()
    src = Path(__file__).parent / "data" / "python" / ".pre-commit-config.yaml"
    dst = tmp_path / ".pre-commit-config.yaml"
    shutil.copy(src, dst)
    mock_github_tags_from_precommit(
        respx_mock, src, {"ambv/black": ["20.0.0"]}
    )

    result = runner.invoke(main, ["analyze", "--path", str(tmp_path)])
    assert result.exit_code == 0
    yaml = YAML()
    data = yaml.load(result.output)
    repository = "https://github.com/ambv/black"
    assert data["pre-commit"][0]["repository"] == repository
    assert data["pre-commit"][0]["current"] == "19.10b0"
    assert data["pre-commit"][0]["latest"] == "20.0.0"

    # Try again with no changes required.
    mock_github_tags_from_precommit(respx_mock, src)
    result = runner.invoke(main, ["analyze", "--path", str(tmp_path)])
    assert not result.output
    assert result.exit_code == 0


def test_check(tmp_path: Path, respx_mock: respx.Router) -> None:
    runner = CliRunner()
    src = Path(__file__).parent / "data" / "python" / ".pre-commit-config.yaml"
    dst = tmp_path / ".pre-commit-config.yaml"
    shutil.copy(src, dst)
    mock_github_tags_from_precommit(
        respx_mock, src, {"ambv/black": ["20.0.0"]}
    )

    result = runner.invoke(main, ["check", "--path", str(tmp_path)])
    assert result.exit_code == 1
    assert result.output == "pre-commit dependencies out of date\n"

    # Try again with no changes required.
    mock_github_tags_from_precommit(respx_mock, src)
    result = runner.invoke(main, ["check", "--path", str(tmp_path)])
    assert not result.output
    assert result.exit_code == 0


def test_github_inventory(respx_mock: respx.Router) -> None:
    mock_github_tags(respx_mock, "foo/bar", ["1.1.0", "1.2.0"])

    runner = CliRunner()
    result = runner.invoke(main, ["github-inventory", "foo", "bar"])
    assert result.exit_code == 0
    assert result.output == "1.2.0\n"


def test_scan() -> None:
    runner = CliRunner()

    path = Path(__file__).parent / "data" / "python"
    result = runner.invoke(main, ["scan", "--path", str(path)])
    assert result.exit_code == 0
    yaml = YAML()
    data = yaml.load(result.output)
    pre_commit_results = sorted(data["pre-commit"], key=lambda r: r["repo"])
    assert pre_commit_results[0]["version"] == "19.10b0"


def test_update(tmp_path: Path, respx_mock: respx.Router) -> None:
    runner = CliRunner()
    src = Path(__file__).parent / "data" / "python" / ".pre-commit-config.yaml"
    dst = tmp_path / ".pre-commit-config.yaml"
    shutil.copy(src, dst)
    yaml = YAML()
    mock_github_tags_from_precommit(
        respx_mock, src, {"ambv/black": ["20.0.0"]}
    )

    result = runner.invoke(
        main, ["update", "--path", str(tmp_path), "pre-commit"]
    )
    assert result.exit_code == 0
    data = yaml.load(dst)
    assert data["repos"][2]["rev"] == "20.0.0"


def test_update_pr(
    tmp_path: Path, respx_mock: respx.Router, github_key: str, mock_push: Mock
) -> None:
    runner = CliRunner()
    repo = Repo.init(str(tmp_path), initial_branch="main")
    Remote.create(repo, "origin", "https://github.com/foo/bar")
    src = Path(__file__).parent / "data" / "python" / ".pre-commit-config.yaml"
    dst = tmp_path / ".pre-commit-config.yaml"
    shutil.copy(src, dst)
    repo.index.add(str(dst))
    actor = Actor("Someone", "someone@example.com")
    repo.index.commit("Initial commit", author=actor, committer=actor)
    created_pr = False

    def check_pr_post(request: Request) -> Response:
        change = "Update ambv/black pre-commit hook from 19.10b0 to 20.0.0"
        assert json.loads(request.content) == {
            "title": CommitMessage.title,
            "body": f"- {change}\n",
            "head": "u/neophile",
            "base": "main",
            "maintainer_can_modify": True,
            "draft": False,
        }

        assert repo.head.ref.name == "u/neophile"
        yaml = YAML()
        data = yaml.load(dst)
        assert data["repos"][2]["rev"] == "20.0.0"
        commit = repo.head.commit
        assert commit.author.name == "neophile"
        assert commit.author.email == "neophile@example.com"
        assert commit.message == f"{CommitMessage.title}\n\n- {change}\n"

        nonlocal created_pr
        created_pr = True
        return Response(201, json={"number": 42})

    mock_github_tags_from_precommit(
        respx_mock, src, {"ambv/black": ["20.0.0"]}
    )
    mock_app_authenticate(respx_mock, "foo/bar")
    respx_mock.get("https://api.github.com/repos/foo/bar").mock(
        return_value=Response(200, json={"default_branch": "main"})
    )
    pattern = r"https://api.github.com/repos/foo/bar/pulls\?.*"
    respx_mock.get(url__regex=pattern).mock(
        return_value=Response(200, json=[])
    )
    respx_mock.post("https://api.github.com/repos/foo/bar/pulls").mock(
        side_effect=check_pr_post
    )
    mock_enable_auto_merge(respx_mock, "foo", "bar", "42")

    result = runner.invoke(
        main,
        ["update", "--path", str(tmp_path), "--pr"],
        env={
            "NEOPHILE_GITHUB_PRIVATE_KEY": github_key,
            "NEOPHILE_COMMIT_EMAIL": "neophile@example.com",
        },
    )
    assert result.exit_code == 0
    assert created_pr
    assert mock_push.call_args_list == [
        call("u/neophile:u/neophile", force=True)
    ]
    assert repo.head.ref.name == "main"
