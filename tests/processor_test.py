"""Test for the Processor class."""

from __future__ import annotations

import json
import re
import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import call, patch

import pytest
from aioresponses import CallbackResult, aioresponses
from git import Actor, PushInfo, Remote, Repo
from ruamel.yaml import YAML

from neophile.config import Configuration, GitHubRepository
from neophile.factory import Factory
from neophile.pr import CommitMessage
from tests.util import (
    register_mock_github_tags,
    register_mock_helm_repository,
    setup_kubernetes_repo,
    setup_python_repo,
)

if TYPE_CHECKING:
    from aiohttp import ClientSession
    from typing import Any, Callable, Iterator


def create_upstream_git_repository(repo: Repo, upstream_path: Path) -> None:
    """Create an upstream Git repository with Python files.

    Parameters
    ----------
    repo : `git.Repo`
        The repository to use as the contents of the upstream repository.
    upstream_path : `pathlib.Path`
        Where to put the upstream repository.
    """
    upstream_path.mkdir()
    Repo.init(str(upstream_path), bare=True)
    origin = repo.create_remote("origin", str(upstream_path))
    origin.push(all=True)


@contextmanager
def patch_clone_from(owner: str, repo: str, path: Path) -> Iterator[None]:
    """Patch :py:func:`git.Repo.clone_from` to check out a local repository.

    Parameters
    ----------
    owner : `str`
        GitHub repository owner to expect.
    repo : `str`
        GitHub repository name to expect.
    path : `pathlib.Path`
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
async def test_processor(tmp_path: Path, session: ClientSession) -> None:
    tmp_repo = setup_python_repo(tmp_path / "tmp", require_venv=True)
    upstream_path = tmp_path / "upstream"
    create_upstream_git_repository(tmp_repo, upstream_path)
    config = Configuration(
        repositories=[GitHubRepository(owner="foo", repo="bar")],
        work_area=tmp_path / "work",
    )
    user = {"name": "Someone", "email": "someone@example.com"}
    push_result = [PushInfo(PushInfo.NEW_HEAD, None, "", None)]
    created_pr = False

    def check_pr_post(url: str, **kwargs: Any) -> CallbackResult:
        changes = [
            "Update frozen Python dependencies",
            "Update ambv/black pre-commit hook from 19.10b0 to 20.0.0",
        ]
        body = "- " + "\n- ".join(changes) + "\n"
        assert json.loads(kwargs["data"]) == {
            "title": CommitMessage.title,
            "body": body,
            "head": "u/neophile",
            "base": "master",
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
        return CallbackResult(status=201)

    with aioresponses() as mock:
        register_mock_github_tags(mock, "ambv", "black", ["20.0.0", "19.10b0"])
        mock.get("https://api.github.com/user", payload=user)
        pattern = re.compile(r"https://api.github.com/repos/foo/bar/pulls\?.*")
        mock.get(pattern, payload=[])
        mock.post(
            "https://api.github.com/repos/foo/bar/pulls",
            callback=check_pr_post,
        )

        # Unfortunately, the mock_push fixture can't be used here because we
        # want to use git.Remote.push in create_upstream_git_repository.
        factory = Factory(config, session)
        processor = factory.create_processor()
        with patch_clone_from("foo", "bar", upstream_path):
            with patch.object(Remote, "push") as mock_push:
                mock_push.return_value = push_result
                await processor.process()

    assert mock_push.call_args_list == [call("u/neophile:u/neophile")]
    assert created_pr
    repo = Repo(str(tmp_path / "work" / "bar"))
    assert not repo.is_dirty()
    assert repo.head.ref.name == "master"
    assert "u/neophile" not in [h.name for h in repo.heads]
    assert "tmp-neophile" not in [r.name for r in repo.remotes]


@pytest.mark.asyncio
async def test_no_updates(tmp_path: Path, session: ClientSession) -> None:
    data_path = Path(__file__).parent / "data" / "kubernetes" / "sqrbot-jr"
    tmp_repo_path = tmp_path / "tmp"
    tmp_repo_path.mkdir()
    tmp_repo = Repo.init(str(tmp_repo_path))
    shutil.copytree(str(data_path), str(tmp_repo_path / "sqrbot-jr"))
    actor = Actor("Someone", "someone@example.com")
    tmp_repo.index.commit("Initial commit", author=actor, committer=actor)
    upstream_path = tmp_path / "upstream"
    create_upstream_git_repository(tmp_repo, upstream_path)
    config = Configuration(
        repositories=[GitHubRepository(owner="foo", repo="bar")],
        work_area=tmp_path / "work",
    )
    user = {"name": "Someone", "email": "someone@example.com"}

    # Don't register any GitHub tag lists, so we shouldn't see any updates.
    with aioresponses() as mock:
        mock.get("https://api.github.com/user", payload=user)
        factory = Factory(config, session)
        processor = factory.create_processor()
        with patch_clone_from("foo", "bar", upstream_path):
            with patch.object(Remote, "push") as mock_push:
                await processor.process()

    assert mock_push.call_count == 0
    repo = Repo(str(tmp_path / "work" / "bar"))
    assert not repo.is_dirty()
    assert repo.head.ref.name == "master"


@pytest.mark.asyncio
async def test_allow_expressions(
    tmp_path: Path, session: ClientSession
) -> None:
    tmp_repo = setup_kubernetes_repo(tmp_path / "tmp")
    upstream_path = tmp_path / "upstream"
    create_upstream_git_repository(tmp_repo, upstream_path)
    config = Configuration(
        allow_expressions=True,
        cache_enabled=False,
        repositories=[GitHubRepository(owner="foo", repo="bar")],
        work_area=tmp_path / "work",
    )
    user = {"name": "Someone", "email": "someone@example.com"}
    push_result = [PushInfo(PushInfo.NEW_HEAD, None, "", None)]
    created_pr = False

    def check_pr_post(url: str, **kwargs: Any) -> CallbackResult:
        assert json.loads(kwargs["data"]) == {
            "title": CommitMessage.title,
            "body": "- Update gafaelfawr Helm chart from 1.3.1 to v1.4.0\n",
            "head": "u/neophile",
            "base": "master",
            "maintainer_can_modify": True,
            "draft": False,
        }

        nonlocal created_pr
        created_pr = True
        return CallbackResult(status=201)

    with aioresponses() as mock:
        register_mock_helm_repository(
            mock,
            "https://kubernetes-charts.storage.googleapis.com/index.yaml",
            {"elasticsearch": ["1.26.2"], "kibana": ["3.0.1"]},
        )
        register_mock_helm_repository(
            mock,
            "https://kiwigrid.github.io/index.yaml",
            {"fluentd-elasticsearch": ["3.0.0"]},
        )
        register_mock_helm_repository(
            mock,
            "https://lsst-sqre.github.io/charts/index.yaml",
            {"gafaelfawr": ["1.3.1", "v1.4.0"]},
        )
        mock.get("https://api.github.com/user", payload=user)
        pattern = re.compile(r"https://api.github.com/repos/foo/bar/pulls\?.*")
        mock.get(pattern, payload=[])
        mock.post(
            "https://api.github.com/repos/foo/bar/pulls",
            callback=check_pr_post,
        )

        # Unfortunately, the mock_push fixture can't be used here because we
        # want to use git.Remote.push in create_upstream_git_repository.
        factory = Factory(config, session)
        processor = factory.create_processor()
        with patch_clone_from("foo", "bar", upstream_path):
            with patch.object(Remote, "push") as mock_push:
                mock_push.return_value = push_result
                await processor.process()

    assert created_pr
