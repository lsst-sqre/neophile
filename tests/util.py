"""Utility functions for tests."""

from __future__ import annotations

import shutil
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING

from git import Actor, Repo
from ruamel.yaml import YAML

if TYPE_CHECKING:
    from aioresponses import aioresponses
    from typing import Any, Mapping, Sequence


def dict_to_yaml(data: Mapping[str, Any]) -> str:
    """Convert any mapping to YAML serialized as a string.

    Parameters
    ----------
    data : Mapping[`str`, Any]
        The data.

    Returns
    -------
    yaml : `str`
        The data serialized as YAML.
    """
    yaml = YAML()
    output = StringIO()
    yaml.dump(data, output)
    return output.getvalue()


def register_mock_helm_repository(
    mock: aioresponses, url: str, versions: Mapping[str, Sequence[str]]
) -> None:
    """Register a list of versions for a Helm repository.

    Parameters
    ----------
    mock : `aioresponses.aioresponses`
        The mock object for aiohttp requests.
    url : `str`
        The URL of the repository index.
    versions : Mapping[`str`, Sequence[`str`]]
        A mapping of Helm chart names to lists of version numbers that should
        appear in the index for that chart.
    """
    data = {
        "entries": {
            chart: [{"version": ver} for ver in vers]
            for chart, vers in versions.items()
        }
    }
    mock.get(url, body=dict_to_yaml(data))


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
    tags : Sequence[`str`]
        The list of tags to return for that repository.
    """
    data = [{"name": version} for version in tags]
    mock.get(
        f"https://api.github.com/repos/{owner}/{repo}/tags",
        payload=data,
        repeat=True,
    )


def setup_kubernetes_repo(tmp_path: Path) -> Repo:
    """Set up a test repository with the Kubernetes test files.

    Parameters
    ----------
    tmp_path : `pathlib.Path`
        The directory in which to create the repository.

    Returns
    -------
    repo : `git.Repo`
        The repository object.
    """
    data_path = Path(__file__).parent / "data" / "kubernetes"
    shutil.copytree(str(data_path), str(tmp_path), dirs_exist_ok=True)
    repo = Repo.init(str(tmp_path))
    for path in tmp_path.iterdir():
        if not path.name.startswith("."):
            repo.index.add(str(path))
    actor = Actor("Someone", "someone@example.com")
    repo.index.commit("Initial commit", author=actor, committer=actor)
    return repo


def setup_python_repo(tmp_path: Path) -> Repo:
    """Set up a test repository with the Python test files.

    Parameters
    ----------
    tmp_path : `pathlib.Path`
        The directory in which to create the repository.

    Returns
    -------
    repo : `git.Repo`
        The repository object.
    """
    data_path = Path(__file__).parent / "data" / "python"
    shutil.copytree(str(data_path), str(tmp_path), dirs_exist_ok=True)
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
    return repo
