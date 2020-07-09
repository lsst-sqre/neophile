"""Tests for the command-line interface."""

from __future__ import annotations

import json
import shutil
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import call

from aioresponses import CallbackResult, aioresponses
from click.testing import CliRunner
from git import Actor, Remote, Repo
from ruamel.yaml import YAML

from neophile.cli import main
from tests.util import yaml_to_string

if TYPE_CHECKING:
    from typing import Any
    from unittest.mock import Mock


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


def test_analyze(cache_path: Path) -> None:
    runner = CliRunner()

    yaml = YAML()
    output = StringIO()
    yaml.dump({"entries": {"gafaelfawr": [{"version": "1.4.0"}]}}, output)
    sqre = output.getvalue()
    root = Path(__file__).parent / "data" / "kubernetes" / "gafaelfawr"
    with aioresponses() as mock:
        mock.get("https://lsst-sqre.github.io/charts/index.yaml", body=sqre)
        result = runner.invoke(main, ["analyze", "--path", str(root)])

    assert result.exit_code == 0
    data = yaml.load(result.output)
    assert data["helm"][0]["name"] == "gafaelfawr"
    assert data["helm"][0]["current"] == "1.3.1"
    assert data["helm"][0]["latest"] == "1.4.0"


def test_analyze_update(tmp_path: Path, cache_path: Path) -> None:
    runner = CliRunner()
    src = (
        Path(__file__).parent
        / "data"
        / "kubernetes"
        / "gafaelfawr"
        / "Chart.yaml"
    )
    dst = tmp_path / "Chart.yaml"
    shutil.copy(src, dst)
    yaml = YAML()
    output = StringIO()
    yaml.dump({"entries": {"gafaelfawr": [{"version": "1.4.0"}]}}, output)
    sqre = output.getvalue()

    with aioresponses() as mock:
        mock.get("https://lsst-sqre.github.io/charts/index.yaml", body=sqre)
        result = runner.invoke(
            main, ["analyze", "--path", str(tmp_path), "--update"]
        )

    assert result.exit_code == 0
    data = yaml.load(dst)
    assert data["dependencies"][0]["version"] == "1.4.0"


def test_analyze_pr(tmp_path: Path, cache_path: Path, mock_push: Mock) -> None:
    runner = CliRunner()
    repo = Repo.init(str(tmp_path))
    Remote.create(repo, "origin", "https://github.com/foo/bar")
    src = (
        Path(__file__).parent
        / "data"
        / "kubernetes"
        / "gafaelfawr"
        / "Chart.yaml"
    )
    dst = tmp_path / "Chart.yaml"
    shutil.copy(src, dst)
    repo.index.add(str(dst))
    actor = Actor("Someone", "someone@example.com")
    repo.index.commit("Initial commit", author=actor, committer=actor)
    sqre = yaml_to_string({"entries": {"gafaelfawr": [{"version": "1.4.0"}]}})
    payload = {"name": "Someone", "email": "someone@example.com"}
    created_pr = False

    def check_pr_post(url: str, **kwargs: Any) -> CallbackResult:
        change = "Update gafaelfawr Helm chart from 1.3.1 to 1.4.0"
        assert json.loads(kwargs["data"]) == {
            "title": "Update dependencies",
            "body": f"- {change}\n",
            "head": "u/neophile",
            "base": "master",
            "maintainer_can_modify": True,
            "draft": False,
        }

        assert repo.head.ref.name == "u/neophile"
        yaml = YAML()
        data = yaml.load(dst)
        assert data["dependencies"][0]["version"] == "1.4.0"
        commit = repo.head.commit
        assert commit.author.name == "Someone"
        assert commit.author.email == "someone@example.com"
        assert commit.message == f"Update dependencies\n\n- {change}\n"

        nonlocal created_pr
        created_pr = True
        return CallbackResult(status=201)

    with aioresponses() as mock:
        mock.get("https://lsst-sqre.github.io/charts/index.yaml", body=sqre)
        mock.get("https://api.github.com/user", payload=payload)
        mock.post(
            "https://api.github.com/repos/foo/bar/pulls",
            callback=check_pr_post,
        )
        result = runner.invoke(
            main, ["analyze", "--path", str(tmp_path), "--pr"]
        )

    assert created_pr
    assert result.exit_code == 0
    assert mock_push.call_args_list == [call("u/neophile:u/neophile")]
    assert repo.head.ref.name == "master"


def test_github_inventory() -> None:
    runner = CliRunner()
    tags = [{"name": "1.1.0"}, {"name": "1.2.0"}]

    with aioresponses() as mock:
        mock.get("https://api.github.com/repos/foo/bar/tags", payload=tags)
        result = runner.invoke(main, ["github-inventory", "foo", "bar"])

    assert result.exit_code == 0
    assert result.output == "1.2.0\n"


def test_helm_inventory(cache_path: Path) -> None:
    runner = CliRunner()

    index_path = (
        Path(__file__).parent / "data" / "kubernetes" / "sample-index.yaml"
    )
    index_data = index_path.read_bytes()
    with aioresponses() as mock:
        mock.get("https://example.com/index.yaml", body=index_data)
        result = runner.invoke(
            main, ["helm-inventory", "https://example.com/"]
        )

    assert result.exit_code == 0
    yaml = YAML()
    data = yaml.load(result.output)
    assert data["gafaelfawr"] == "1.3.1"


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

    path = Path(__file__).parent / "data" / "kubernetes"
    result = runner.invoke(main, ["scan", "--path", str(path)])
    assert result.exit_code == 0
    yaml = YAML()
    data = yaml.load(result.output)
    helm_results = sorted(data["helm"], key=lambda r: r["name"])
    assert helm_results[0]["name"] == "elasticsearch"
