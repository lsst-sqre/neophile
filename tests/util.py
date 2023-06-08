"""Utility functions for tests."""

from __future__ import annotations

import json
import shutil
from collections.abc import Mapping, Sequence
from io import StringIO
from pathlib import Path
from typing import Any

from aioresponses import CallbackResult, aioresponses
from gidgethub import QueryError
from git.repo import Repo
from git.util import Actor
from ruamel.yaml import YAML

from neophile.pr import _GRAPHQL_ENABLE_AUTO_MERGE, _GRAPHQL_PR_ID

__all__ = [
    "dict_to_yaml",
    "mock_enable_auto_merge",
    "register_mock_github_tags",
    "setup_python_repo",
]


def dict_to_yaml(data: Mapping[str, Any]) -> str:
    """Convert any mapping to YAML serialized as a string.

    Parameters
    ----------
    data
        Data to convert.

    Returns
    -------
    str
        Data serialized as YAML.
    """
    yaml = YAML()
    output = StringIO()
    yaml.dump(data, output)
    return output.getvalue()


def mock_enable_auto_merge(
    mock: aioresponses,
    owner: str,
    repo: str,
    pr_number: str,
    *,
    fail: bool = False,
) -> None:
    """Set up mocks for the GitHub API call to enable auto-merge.

    Parameters
    ----------
    mock
        Mock object for aiohttp requests.
    owner
        Owner of the repository.
    repo
        Name of the repository.
    pr_number
        Number of the PR for which auto-merge will be set.
    fail
        Whether to fail the request for automerge
    """

    def graphql_1(url: str, **kwargs: Any) -> CallbackResult:
        assert str(url) == "https://api.github.com/graphql"
        expected = json.dumps(
            {
                "query": _GRAPHQL_PR_ID,
                "variables": {
                    "owner": owner,
                    "repo": repo,
                    "pr_number": int(pr_number),
                },
            }
        ).encode()
        assert kwargs["data"] == expected
        return CallbackResult(
            status=200,
            payload={
                "data": {"repository": {"pullRequest": {"id": "some-id"}}}
            },
        )

    def graphql_2(url: str, **kwargs: Any) -> CallbackResult:
        assert str(url) == "https://api.github.com/graphql"
        expected = json.dumps(
            {
                "query": _GRAPHQL_ENABLE_AUTO_MERGE,
                "variables": {"pr_id": "some-id"},
            }
        ).encode()
        assert kwargs["data"] == expected
        if fail:
            msg = (
                "Pull request is not in the correct state to enable auto-merge"
            )
            response = {"errors": [{"message": msg}]}
            raise QueryError(response)
        return CallbackResult(
            status=200, payload={"data": {"actor": {"login": "some-user"}}}
        )

    mock.post("https://api.github.com/graphql", callback=graphql_1)
    mock.post("https://api.github.com/graphql", callback=graphql_2)


def register_mock_github_tags(
    mock: aioresponses, owner: str, repo: str, tags: Sequence[str]
) -> None:
    """Register a list of tags for a GitHub repository.

    Parameters
    ----------
    mock
        Mock object for aiohttp requests.
    repo
        Name of the GitHub repository.
    tags
        List of tags to return for that repository.
    """
    data = [{"name": version} for version in tags]
    mock.get(
        f"https://api.github.com/repos/{owner}/{repo}/tags",
        payload=data,
        repeat=True,
    )


def setup_python_repo(tmp_path: Path, *, require_venv: bool = False) -> Repo:
    """Set up a test repository with the Python test files.

    Parameters
    ----------
    tmp_path
        The directory in which to create the repository.
    require_venv
        Whether ``make update-deps`` should fail if no virtualenv is in use.

    Returns
    -------
    Repo
        Repository object.
    """
    data_path = Path(__file__).parent / "data" / "python"
    shutil.copytree(str(data_path), str(tmp_path), dirs_exist_ok=True)
    if require_venv:
        (tmp_path / "Makefile-venv").rename(tmp_path / "Makefile")
    else:
        (tmp_path / "Makefile-venv").unlink()
    repo = Repo.init(str(tmp_path), initial_branch="main")
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
