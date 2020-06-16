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
from neophile.exceptions import UncommittedChangesError
from neophile.update.helm import HelmUpdate
from neophile.update.python import PythonFrozenUpdate

if TYPE_CHECKING:
    from typing import Any, Dict


def yaml_to_string(data: Dict[str, Any]) -> str:
    yaml = YAML()
    output = StringIO()
    yaml.dump(data, output)
    return output.getvalue()


@pytest.mark.asyncio
async def test_analyzer_helm(cache_path: Path) -> None:
    datapath = Path(__file__).parent / "data" / "helm"
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
        async with aiohttp.ClientSession() as session:
            analyzer = Analyzer(str(datapath), session)
            results = await analyzer.analyze()
            analyzer = Analyzer(str(datapath), session, allow_expressions=True)
            results_expressions = await analyzer.analyze()

    assert sorted(results, key=lambda r: r.name) == [
        HelmUpdate(
            name="fluentd-elasticsearch",
            current=">=3.0.0",
            latest="3.0.0",
            path=str(datapath / "logging" / "requirements.yaml"),
        ),
        HelmUpdate(
            name="gafaelfawr",
            current="1.3.1",
            latest="v1.4.0",
            path=str(datapath / "gafaelfawr" / "Chart.yaml"),
        ),
        HelmUpdate(
            name="kibana",
            current=">=3.0.0",
            latest="3.0.1",
            path=str(datapath / "logging" / "requirements.yaml"),
        ),
    ]

    assert sorted(results_expressions, key=lambda r: r.name) == [
        HelmUpdate(
            name="gafaelfawr",
            current="1.3.1",
            latest="v1.4.0",
            path=str(datapath / "gafaelfawr" / "Chart.yaml"),
        )
    ]


@pytest.mark.asyncio
async def test_analyzer_python_frozen(tmp_path: Path) -> None:
    datapath = Path(__file__).parent / "data" / "python"
    shutil.copytree(str(datapath), str(tmp_path), dirs_exist_ok=True)
    repo = Repo.init(str(tmp_path))
    repo.index.add(
        [str(tmp_path / "Makefile"), str(tmp_path / "requirements")]
    )
    actor = Actor("Someone", "someone@example.com")
    repo.index.commit("Initial commit", author=actor, committer=actor)

    async with aiohttp.ClientSession() as session:
        analyzer = Analyzer(str(tmp_path), session)
        results = await analyzer.analyze()

    assert results == [
        PythonFrozenUpdate(
            name="python-deps", path=str(tmp_path / "requirements")
        )
    ]

    # Ensure that the tree is restored to the previous contents.
    assert not repo.is_dirty()

    # If the repo is dirty, analysis will fail.
    subprocess.run(["make", "update-deps"], cwd=str(tmp_path), check=True)
    assert repo.is_dirty()
    async with aiohttp.ClientSession() as session:
        analyzer = Analyzer(str(tmp_path), session)
        with pytest.raises(UncommittedChangesError):
            results = await analyzer.analyze()

    # Commit the changed dependencies.  Analysis should now return no changes.
    repo.index.add(str(tmp_path / "requirements"))
    repo.index.commit("Update dependencies", author=actor, committer=actor)
    async with aiohttp.ClientSession() as session:
        analyzer = Analyzer(str(tmp_path), session)
        results = await analyzer.analyze()
    assert results == []
