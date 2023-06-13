"""Mocks for testing code interacting with GitHub."""

from __future__ import annotations

import json
from collections.abc import Sequence
from copy import deepcopy
from pathlib import Path
from urllib.parse import urlparse

import respx
from gidgethub import QueryError
from httpx import Request, Response
from ruamel.yaml import YAML

from neophile.pr import _GRAPHQL_ENABLE_AUTO_MERGE, _GRAPHQL_PR_ID

__all__ = [
    "mock_enable_auto_merge",
    "mock_github_tags",
    "mock_github_tags_from_precommit",
]


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
            data = {"data": {"repository": {"pullRequest": {"id": "some-id"}}}}
            return Response(200, json=data)
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
            data = {"data": {"actor": {"login": "some-user"}}}
            return Response(200, json=data)

    url = "https://api.github.com/graphql"
    respx_mock.post(url).mock(side_effect=graphql)


def mock_github_tags(
    respx_mock: respx.Router, path: str, tags: Sequence[str]
) -> None:
    """Register a list of tags for a GitHub repository.

    Parameters
    ----------
    respx_mock
        Mock object for HTTP requests.
    path
        GitHub repository as :samp:`{owner}/{repo}`.
    tags
        List of tags to return for that repository.
    """
    data = [{"name": version} for version in tags]
    respx_mock.get(f"https://api.github.com/repos/{path}/tags").mock(
        return_value=Response(200, json=data)
    )


def mock_github_tags_from_precommit(
    respx_mock: respx.Router,
    pre_commit: Path,
    extra: dict[str, list[str]] | None = None,
) -> None:
    """Register all the tags found in a pre-commit file, plus extras.

    Ensure all the tags currently found in a pre-commit file will be returned
    by the mocks of GitHub API queries, and add the additional versions
    listed.

    Parameters
    ----------
    respx_mock
        Mock object for HTTP requests.
    pre_commit
        Path to the pre-commit file whose versions should be registered.
    extra
        Mapping of GitHub repository (as :samp:`{owner}/{path}`) to additional
        tags that should be returned for that repository.
    """
    versions = deepcopy(extra or {})
    yaml = YAML()
    with pre_commit.open("r") as f:
        pre_commit_data = yaml.load(f)
        for entry in pre_commit_data["repos"]:
            repo = urlparse(entry["repo"]).path.lstrip("/")
            if repo not in versions:
                versions[repo] = []
            versions[repo].append(entry["rev"])
    for repo, tags in versions.items():
        mock_github_tags(respx_mock, repo, tags)
