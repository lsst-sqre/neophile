"""Utility functions for tests."""

from __future__ import annotations

import json
import shutil
from collections.abc import Mapping, Sequence
from io import StringIO
from pathlib import Path
from typing import Any

import respx
from gidgethub import QueryError
from git.repo import Repo
from git.util import Actor
from httpx import Request, Response
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
    respx_mock: respx.Router,
    owner: str,
    repo: str,
    pr_number: str,
    *,
    fail: bool = False,
) -> None:
    """Set up mocks for the GitHub API call to enable auto-merge.

    Parameters
    ----------
    respx_mock
        Mock object for HTTP requests.
    owner
        Owner of the repository.
    repo
        Name of the repository.
    pr_number
        Number of the PR for which auto-merge will be set.
    fail
        Whether to fail the request for automerge
    """
    first = True

    def graphql(request: Request) -> Response:
        data = json.loads(request.content)
        nonlocal first
        if first:
            assert data == {
                "query": _GRAPHQL_PR_ID,
                "variables": {
                    "owner": owner,
                    "repo": repo,
                    "pr_number": int(pr_number),
                },
            }
            first = False
            return Response(
                200,
                json={
                    "data": {"repository": {"pullRequest": {"id": "some-id"}}}
                },
            )
        else:
            assert data == {
                "query": _GRAPHQL_ENABLE_AUTO_MERGE,
                "variables": {"pr_id": "some-id"},
            }
            if fail:
                msg = (
                    "Pull request is not in the correct state to enable"
                    " auto-merge"
                )
                response = {"errors": [{"message": msg}]}
                raise QueryError(response)
            return Response(
                200, json={"data": {"actor": {"login": "some-user"}}}
            )

    url = "https://api.github.com/graphql"
    respx_mock.post(url).mock(side_effect=graphql)


def register_mock_github_tags(
    respx_mock: respx.Router, owner: str, repo: str, tags: Sequence[str]
) -> None:
    """Register a list of tags for a GitHub repository.

    Parameters
    ----------
    respx_mock
        Mock object for HTTP requests.
    repo
        Name of the GitHub repository.
    tags
        List of tags to return for that repository.
    """
    data = [{"name": version} for version in tags]
    respx_mock.get(f"https://api.github.com/repos/{owner}/{repo}/tags").mock(
        return_value=Response(200, json=data)
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
