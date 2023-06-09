"""Tests for the command-line interface."""

from __future__ import annotations

import json
import re
import shutil
from io import StringIO
from pathlib import Path
from typing import Any
from unittest.mock import Mock, call

from aioresponses import CallbackResult, aioresponses
from click.testing import CliRunner
from git import Remote
from git.repo import Repo
from git.util import Actor
from ruamel.yaml import YAML

from neophile.cli import main
from neophile.pr import CommitMessage

from .util import mock_enable_auto_merge, register_mock_github_tags


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


def test_analyze(tmp_path: Path) -> None:
    runner = CliRunner()
    src = Path(__file__).parent / "data" / "python" / ".pre-commit-config.yaml"
    dst = tmp_path / ".pre-commit-config.yaml"
    shutil.copy(src, dst)

    with aioresponses() as mock:
        register_mock_github_tags(mock, "ambv", "black", ["20.0.0", "19.10b0"])
        register_mock_github_tags(
            mock, "pre-commit", "pre-commit-hooks", ["v3.1.0"]
        )
        register_mock_github_tags(
            mock, "timothycrosley", "isort", ["4.3.21-2"]
        )
        register_mock_github_tags(mock, "pycqa", "flake8", ["3.8.1"])
        result = runner.invoke(main, ["analyze", "--path", str(tmp_path)])

    assert result.exit_code == 0
    yaml = YAML()
    data = yaml.load(result.output)
    repository = "https://github.com/ambv/black"
    assert data["pre-commit"][0]["repository"] == repository
    assert data["pre-commit"][0]["current"] == "19.10b0"
    assert data["pre-commit"][0]["latest"] == "20.0.0"


def test_analyze_update(tmp_path: Path) -> None:
    runner = CliRunner()
    src = Path(__file__).parent / "data" / "python" / ".pre-commit-config.yaml"
    dst = tmp_path / ".pre-commit-config.yaml"
    shutil.copy(src, dst)
    yaml = YAML()
    output = StringIO()
    output.getvalue()

    with aioresponses() as mock:
        register_mock_github_tags(mock, "ambv", "black", ["20.0.0", "19.10b0"])
        register_mock_github_tags(
            mock, "pre-commit", "pre-commit-hooks", ["v3.1.0"]
        )
        register_mock_github_tags(
            mock, "timothycrosley", "isort", ["4.3.21-2"]
        )
        register_mock_github_tags(mock, "pycqa", "flake8", ["3.8.1"])
        result = runner.invoke(
            main,
            ["analyze", "--path", str(tmp_path), "--update"],
            env={"NEOPHILE_CACHE_ENABLED": "0"},
        )

    assert result.exit_code == 0
    data = yaml.load(dst)
    assert data["repos"][2]["rev"] == "20.0.0"


def test_analyze_pr(tmp_path: Path, mock_push: Mock) -> None:
    runner = CliRunner()
    repo = Repo.init(str(tmp_path), initial_branch="main")
    Remote.create(repo, "origin", "https://github.com/foo/bar")
    src = Path(__file__).parent / "data" / "python" / ".pre-commit-config.yaml"
    dst = tmp_path / ".pre-commit-config.yaml"
    shutil.copy(src, dst)
    repo.index.add(str(dst))
    actor = Actor("Someone", "someone@example.com")
    repo.index.commit("Initial commit", author=actor, committer=actor)
    payload = {"name": "Someone", "email": "someone@example.com"}
    created_pr = False

    def check_pr_post(url: str, **kwargs: Any) -> CallbackResult:
        change = "Update ambv/black pre-commit hook from 19.10b0 to 20.0.0"
        assert json.loads(kwargs["data"]) == {
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
        assert commit.author.name == "Someone"
        assert commit.author.email == "someone@example.com"
        assert commit.message == f"{CommitMessage.title}\n\n- {change}\n"

        nonlocal created_pr
        created_pr = True
        return CallbackResult(status=201, payload={"number": 42})

    with aioresponses() as mock:
        register_mock_github_tags(mock, "ambv", "black", ["20.0.0", "19.10b0"])
        register_mock_github_tags(
            mock, "pre-commit", "pre-commit-hooks", ["v3.1.0"]
        )
        register_mock_github_tags(
            mock, "timothycrosley", "isort", ["4.3.21-2"]
        )
        register_mock_github_tags(mock, "pycqa", "flake8", ["3.8.1"])
        mock.get("https://api.github.com/user", payload=payload)
        mock.get(
            "https://api.github.com/repos/foo/bar",
            payload={"default_branch": "main"},
        )
        pattern = re.compile(r"https://api.github.com/repos/foo/bar/pulls\?.*")
        mock.get(pattern, payload=[])
        mock.post(
            "https://api.github.com/repos/foo/bar/pulls",
            callback=check_pr_post,
        )
        mock_enable_auto_merge(mock, "foo", "bar", "42")
        result = runner.invoke(
            main, ["analyze", "--path", str(tmp_path), "--pr"]
        )

    assert result.exit_code == 0
    assert created_pr
    assert mock_push.call_args_list == [
        call("u/neophile:u/neophile", force=True)
    ]
    assert repo.head.ref.name == "main"


def test_github_inventory() -> None:
    runner = CliRunner()
    tags = [{"name": "1.1.0"}, {"name": "1.2.0"}]

    with aioresponses() as mock:
        mock.get("https://api.github.com/repos/foo/bar/tags", payload=tags)
        result = runner.invoke(main, ["github-inventory", "foo", "bar"])

    assert result.exit_code == 0
    assert result.output == "1.2.0\n"


def test_process(tmp_path: Path) -> None:
    """Test the process subcommand.

    Notes
    -----
    This tests processing an empty set of repositories, since otherwise the
    amount of setup required to mock everything out is too tedious.
    Processing with all of the mocks is tested separately in the unit test for
    the processor object.
    """
    runner = CliRunner()
    config = {
        "repositories": [],
        "work_area": str(tmp_path),
    }
    config_path = tmp_path / "neophile.yaml"
    with config_path.open("w") as f:
        yaml = YAML()
        yaml.dump(config, f)

    result = runner.invoke(main, ["-c", str(config_path), "process"])
    assert result.exit_code == 0


def test_scan() -> None:
    runner = CliRunner()

    path = Path(__file__).parent / "data" / "python"
    result = runner.invoke(main, ["scan", "--path", str(path)])
    assert result.exit_code == 0
    yaml = YAML()
    data = yaml.load(result.output)
    pre_commit_results = sorted(data["pre-commit"], key=lambda r: r["repo"])
    assert pre_commit_results[0]["version"] == "19.10b0"
