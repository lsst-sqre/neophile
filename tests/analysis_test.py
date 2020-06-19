"""Tests for the Analyzer class."""

from __future__ import annotations

import shutil
import subprocess
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING

import aiohttp
import pytest
from aioresponses import aioresponses
from git import Actor, Repo
from ruamel.yaml import YAML

from neophile.analysis import Analyzer
from neophile.config import Configuration
from neophile.exceptions import UncommittedChangesError
from neophile.update.helm import HelmUpdate
from neophile.update.kustomize import KustomizeUpdate
from neophile.update.pre_commit import PreCommitUpdate
from neophile.update.python import PythonFrozenUpdate

if TYPE_CHECKING:
    from typing import Any, Dict, Sequence


def register_mock_github_tags(
    mock: aioresponses, owner: str, repo: str, tags: Sequence[str]
) -> None:
    """Register a list of tags for a GitHub repository.

    Parameters
    ----------
    mock : `aioresponses.aioresponses`
        The mock object for aiohttp requests.
    repo : `str`
        The name of the GitHub repository.
    tags : List[`str`]
        The list of tags to return for that repository.
    """
    data = [{"name": version} for version in tags]
    mock.get(
        f"https://api.github.com/repos/{owner}/{repo}/tags",
        payload=data,
        repeat=True,
    )


def yaml_to_string(data: Dict[str, Any]) -> str:
    yaml = YAML()
    output = StringIO()
    yaml.dump(data, output)
    return output.getvalue()


@pytest.mark.asyncio
async def test_analyzer_kubernetes(cache_path: Path) -> None:
    config = Configuration()
    datapath = Path(__file__).parent / "data" / "kubernetes"
    googleapis = yaml_to_string(
        {
            "entries": {
                "elasticsearch": [
                    {"version": "1.24.0"},
                    {"version": "1.26.2"},
                    {"version": "1.25.3"},
                ],
                "kibana": [{"version": "3.0.0"}, {"version": "3.0.1"}],
            }
        }
    )
    kiwigrid = yaml_to_string(
        {"entries": {"fluentd-elasticsearch": [{"version": "3.0.0"}]}}
    )
    sqre = yaml_to_string({"entries": {"gafaelfawr": [{"version": "v1.4.0"}]}})

    with aioresponses() as mock:
        mock.get(
            "https://kubernetes-charts.storage.googleapis.com/index.yaml",
            body=googleapis,
            repeat=True,
        )
        mock.get(
            "https://kiwigrid.github.io/index.yaml", body=kiwigrid, repeat=True
        )
        mock.get(
            "https://lsst-sqre.github.io/charts/index.yaml",
            body=sqre,
            repeat=True,
        )
        register_mock_github_tags(
            mock, "lsst-sqre", "sqrbot-jr", ["0.6.0", "0.6.1", "0.7.0"]
        )
        register_mock_github_tags(
            mock, "lsst-sqre", "sqrbot", ["0.5.0", "0.6.0", "0.6.1", "0.7.0"]
        )
        async with aiohttp.ClientSession() as session:
            analyzer = Analyzer(str(datapath), config, session)
            results = await analyzer.analyze()
            analyzer = Analyzer(
                str(datapath), config, session, allow_expressions=True
            )
            results_expressions = await analyzer.analyze()

    expected = [
        HelmUpdate(
            path=str(datapath / "gafaelfawr" / "Chart.yaml"),
            name="gafaelfawr",
            current="1.3.1",
            latest="v1.4.0",
        ),
        HelmUpdate(
            path=str(datapath / "logging" / "requirements.yaml"),
            name="fluentd-elasticsearch",
            current=">=3.0.0",
            latest="3.0.0",
        ),
        HelmUpdate(
            path=str(datapath / "logging" / "requirements.yaml"),
            name="kibana",
            current=">=3.0.0",
            latest="3.0.1",
        ),
        KustomizeUpdate(
            path=str(datapath / "sqrbot-jr" / "kustomization.yaml"),
            url="github.com/lsst-sqre/sqrbot-jr.git//manifests/base?ref=0.6.0",
            current="0.6.0",
            latest="0.7.0",
        ),
    ]
    assert len(results) == 4
    for update in expected:
        assert update in results

    assert results_expressions == [
        HelmUpdate(
            name="gafaelfawr",
            current="1.3.1",
            latest="v1.4.0",
            path=str(datapath / "gafaelfawr" / "Chart.yaml"),
        ),
        KustomizeUpdate(
            path=str(datapath / "sqrbot-jr" / "kustomization.yaml"),
            url="github.com/lsst-sqre/sqrbot-jr.git//manifests/base?ref=0.6.0",
            current="0.6.0",
            latest="0.7.0",
        ),
    ]


@pytest.mark.asyncio
async def test_analyzer_python(tmp_path: Path) -> None:
    config = Configuration()
    datapath = Path(__file__).parent / "data" / "python"
    shutil.copytree(str(datapath), str(tmp_path), dirs_exist_ok=True)
    repo = Repo.init(str(tmp_path))
    repo.index.add(
        [
            str(tmp_path / ".pre-commit-config.yaml"),
            str(tmp_path / "Makefile"),
            str(tmp_path / "requirements"),
        ]
    )
    actor = Actor("Someone", "someone@example.com")
    repo.index.commit("Initial commit", author=actor, committer=actor)

    with aioresponses() as mock:
        register_mock_github_tags(
            mock,
            "pre-commit",
            "pre-commit-hooks",
            ["v3.0.0", "v3.1.0", "v3.2.0"],
        )
        register_mock_github_tags(
            mock, "timothycrosley", "isort", ["4.3.21-2"]
        )
        register_mock_github_tags(mock, "ambv", "black", ["20.0.0", "19.10b0"])
        register_mock_github_tags(mock, "pycqa", "flake8", ["3.7.0", "3.9.0"])
        async with aiohttp.ClientSession() as session:
            analyzer = Analyzer(str(tmp_path), config, session)
            results = await analyzer.analyze()

    pre_commit_path = tmp_path / ".pre-commit-config.yaml"
    assert results == [
        PreCommitUpdate(
            path=str(pre_commit_path),
            repository="https://github.com/pre-commit/pre-commit-hooks",
            current="v3.1.0",
            latest="v3.2.0",
        ),
        PreCommitUpdate(
            path=str(pre_commit_path),
            repository="https://github.com/ambv/black",
            current="19.10b0",
            latest="20.0.0",
        ),
        PreCommitUpdate(
            path=str(pre_commit_path),
            repository="https://gitlab.com/pycqa/flake8",
            current="3.8.1",
            latest="3.9.0",
        ),
        PythonFrozenUpdate(path=str(tmp_path / "requirements")),
    ]

    # Ensure that the tree is restored to the previous contents and remove the
    # pre-commit configuration file, since the remaining tests are only for
    # the Python dependencies.
    assert not repo.is_dirty()
    repo.index.remove(str(pre_commit_path), working_tree=True)
    repo.index.commit("Remove pre-commit", author=actor, committer=actor)

    # If the repo is dirty, analysis will fail.
    subprocess.run(["make", "update-deps"], cwd=str(tmp_path), check=True)
    assert repo.is_dirty()
    async with aiohttp.ClientSession() as session:
        analyzer = Analyzer(str(tmp_path), config, session)
        with pytest.raises(UncommittedChangesError):
            results = await analyzer.analyze()

    # Commit the changed dependencies and remove the pre-commit configuration
    # file.  Analysis should now return no changes.
    repo.index.add(str(tmp_path / "requirements"))
    repo.index.commit("Update dependencies", author=actor, committer=actor)
    async with aiohttp.ClientSession() as session:
        analyzer = Analyzer(str(tmp_path), config, session)
        results = await analyzer.analyze()
    assert results == []
