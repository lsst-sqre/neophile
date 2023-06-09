"""Test for the Processor class."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import Mock, call, patch

import pytest
import respx
from git import PushInfo, Remote
from git.repo import Repo
from git.util import Actor
from httpx import AsyncClient, Request, Response
from ruamel.yaml import YAML

from neophile.config import Config, GitHubRepository
from neophile.factory import Factory
from neophile.pr import CommitMessage

from .util import (
    mock_enable_auto_merge,
    register_mock_github_tags,
    setup_python_repo,
)


def create_upstream_git_repository(repo: Repo, upstream_path: Path) -> None:
    """Create an upstream Git repository with Python files.

    Parameters
    ----------
    repo
        The repository to use as the contents of the upstream repository.
    upstream_path
        Where to put the upstream repository.
    """
    upstream_path.mkdir()
    Repo.init(str(upstream_path), bare=True, initial_branch="main")
    origin = repo.create_remote("origin", str(upstream_path))
    origin.push(all=True)


@contextmanager
def patch_clone_from(owner: str, repo: str, path: Path) -> Iterator[None]:
    """Patch :py:func:`git.Repo.clone_from` to check out a local repository.

    Parameters
    ----------
    owner
        GitHub repository owner to expect.
    repo
        GitHub repository name to expect.
    path
        File path to use as the true upstream location.
    """
    expected_url = f"https://github.com/{owner}/{repo}"

    def mock_clone_from(
        url: str,
        to_path: str,
        orig_clone: Callable[..., Repo] = Repo.clone_from,
        **kwargs: Any,
    ) -> Repo:
        assert url == expected_url
        repo = orig_clone(str(path), to_path)
        repo.remotes.origin.set_url(expected_url)
        return repo

    with patch.object(Repo, "clone_from", side_effect=mock_clone_from):
        yield


@pytest.mark.asyncio
async def test_processor(
    tmp_path: Path, client: AsyncClient, respx_mock: respx.Router
) -> None:
    tmp_repo = setup_python_repo(tmp_path / "tmp", require_venv=True)
    upstream_path = tmp_path / "upstream"
    create_upstream_git_repository(tmp_repo, upstream_path)
    config = Config(
        repositories=[GitHubRepository(owner="foo", repo="bar")],
        work_area=tmp_path / "work",
    )
    remote = Mock(spec=Remote)
    push_result = [PushInfo(PushInfo.NEW_HEAD, None, "", remote)]
    created_pr = False

    def check_pr_post(request: Request) -> Response:
        changes = [
            "Update frozen Python dependencies",
            "Update ambv/black pre-commit hook from 19.10b0 to 20.0.0",
        ]
        body = "- " + "\n- ".join(changes) + "\n"
        assert json.loads(request.content) == {
            "title": CommitMessage.title,
            "body": body,
            "head": "u/neophile",
            "base": "main",
            "maintainer_can_modify": True,
            "draft": False,
        }

        repo = Repo(str(tmp_path / "work" / "bar"))
        assert repo.head.ref.name == "u/neophile"
        yaml = YAML()
        data = yaml.load(tmp_path / "work" / "bar" / ".pre-commit-config.yaml")
        assert data["repos"][2]["rev"] == "20.0.0"
        commit = repo.head.commit
        assert commit.author.name == "Someone"
        assert commit.author.email == "someone@example.com"
        assert commit.message == f"{CommitMessage.title}\n\n{body}"

        nonlocal created_pr
        created_pr = True
        return Response(201, json={"number": 42})

    register_mock_github_tags(
        respx_mock, "ambv", "black", ["20.0.0", "19.10b0"]
    )
    register_mock_github_tags(
        respx_mock, "pre-commit", "pre-commit-hooks", ["v3.1.0"]
    )
    register_mock_github_tags(
        respx_mock, "timothycrosley", "isort", ["4.3.21-2"]
    )
    register_mock_github_tags(respx_mock, "pycqa", "flake8", ["3.8.1"])
    respx_mock.get("https://api.github.com/user").mock(
        return_value=Response(
            200, json={"name": "Someone", "email": "someone@example.com"}
        )
    )
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

    # Unfortunately, the mock_push fixture can't be used here because we
    # want to use git.Remote.push in create_upstream_git_repository.
    factory = Factory(config, client)
    processor = factory.create_processor()
    with patch_clone_from("foo", "bar", upstream_path):
        with patch.object(Remote, "push") as mock_push:
            mock_push.return_value = push_result
            await processor.process()

    assert mock_push.call_args_list == [
        call("u/neophile:u/neophile", force=True)
    ]
    assert created_pr
    repo = Repo(str(tmp_path / "work" / "bar"))
    assert not repo.is_dirty()
    assert repo.head.ref.name == "main"
    assert "u/neophile" not in [h.name for h in repo.heads]
    assert "tmp-neophile" not in [r.name for r in repo.remotes]


@pytest.mark.asyncio
async def test_no_updates(
    tmp_path: Path, client: AsyncClient, respx_mock: respx.Router
) -> None:
    tmp_repo = setup_python_repo(tmp_path / "tmp")
    subprocess.run(
        ["make", "update-deps"], cwd=str(tmp_path / "tmp"), check=True
    )
    tmp_repo.index.add(str(tmp_path / "tmp" / "requirements"))
    actor = Actor("Someone", "someone@example.com")
    tmp_repo.index.commit("Update dependencies", author=actor, committer=actor)
    upstream_path = tmp_path / "upstream"
    create_upstream_git_repository(tmp_repo, upstream_path)
    config = Config(
        repositories=[GitHubRepository(owner="foo", repo="bar")],
        work_area=tmp_path / "work",
    )
    register_mock_github_tags(respx_mock, "ambv", "black", ["19.10b0"])
    register_mock_github_tags(
        respx_mock, "pre-commit", "pre-commit-hooks", ["v3.1.0"]
    )
    register_mock_github_tags(
        respx_mock, "timothycrosley", "isort", ["4.3.21-2"]
    )
    register_mock_github_tags(respx_mock, "pycqa", "flake8", ["3.8.1"])

    factory = Factory(config, client)
    processor = factory.create_processor()
    with patch_clone_from("foo", "bar", upstream_path):
        with patch.object(Remote, "push") as mock_push:
            await processor.process()

    assert mock_push.call_count == 0
    repo = Repo(str(tmp_path / "work" / "bar"))
    assert not repo.is_dirty()
    assert repo.head.ref.name == "main"
